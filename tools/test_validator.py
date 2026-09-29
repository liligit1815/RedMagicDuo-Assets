"""Adversarial packages exercise the same public validator used for submissions."""
import hashlib
import io
import json
import tempfile
import warnings
import zipfile
from pathlib import Path
from validate_pack import validate, reject_apng
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / "dist" / "mono-essentials-1.0.0.zip"
    with zipfile.ZipFile(source) as archive:
        baseline = {name: archive.read(name) for name in archive.namelist()}
    cases = []
    def altered(change):
        files = dict(baseline)
        manifest = json.loads(files["manifest.json"])
        change(manifest, files)
        files["manifest.json"] = json.dumps(manifest).encode()
        return list(files.items())
    cases.append(("unknown settings", altered(lambda m, f: m.update(settings={"device": "private"}))))
    cases.append(("string version", altered(lambda m, f: m.update(version="1"))))
    cases.append(("object theme", altered(lambda m, f: m.update(theme={}))))
    cases.append(("missing file", altered(lambda m, f: f.pop(next(iter(m["images"].values()))))))
    cases.append(("traversal", list(baseline.items()) + [("../outside", b"private")]))
    cases.append(("unlisted resource", list(baseline.items()) + [("images/" + "0" * 64 + ".png", b"invalid")]))
    cases.append(("duplicate ZIP entry", list(baseline.items()) + [("manifest.json", baseline["manifest.json"])]))
    duplicate = dict(baseline)
    duplicate["manifest.json"] = baseline["manifest.json"].replace(b'"version": 1', b'"version": 1, "version": 1')
    cases.append(("duplicate JSON key", list(duplicate.items())))
    cases.append(("hash mismatch", altered(lambda m, f: f.update({next(iter(m["images"].values())): b"broken"}))))
    def fake_image(m, files):
        old = next(iter(m["images"]))
        files.pop(m["images"].pop(old))
        data = b"not actually an image"
        new = hashlib.sha256(data).hexdigest()
        path = "images/" + new + ".png"
        m["images"][new] = path
        m["theme"] = m["theme"].replace(old, new)
        files[path] = data
    cases.append(("fake image with matching hash", altered(fake_image)))
    def apng(m, files):
        old = next(iter(m["images"]))
        files.pop(m["images"].pop(old))
        stream = io.BytesIO()
        first = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
        second = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
        first.save(stream, format="PNG", save_all=True, append_images=[second], duration=125, loop=0)
        data = stream.getvalue()
        sha = hashlib.sha256(data).hexdigest()
        path = "images/" + sha + ".png"
        m["images"][sha] = path
        m["theme"] = m["theme"].replace(old, sha)
        files[path] = data
    cases.append(("APNG unsupported by app", altered(apng)))
    cases.append(("oversized metadata", altered(lambda m, f: m["metadata"].update(name="x" * 101))))
    cases.append(("unreferenced listed image", altered(lambda m, f: m.update(theme=""))))
    with tempfile.TemporaryDirectory(prefix="redmagic-assets-test-") as folder:
        for name, entries in cases:
            path = Path(folder) / "case.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    for filename, content in entries:
                        archive.writestr(filename, content)
            try:
                validate(path)
            except (ValueError, KeyError, zipfile.BadZipFile, OSError):
                print("PASS rejects", name)
            else:
                raise AssertionError(name)
        truncated = Path(folder) / "truncated.zip"
        truncated.write_bytes(source.read_bytes()[:-22])
        try:
            validate(truncated)
        except zipfile.BadZipFile:
            print("PASS rejects missing ZIP central directory terminator")
        else:
            raise AssertionError("truncated ZIP accepted")
    # Even a one-frame APNG control chunk is rejected by the app's container policy.
    import struct
    import zlib
    payload = b"acTL" + struct.pack(">II", 1, 0)
    single_frame_control = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 8) + payload + struct.pack(">I", zlib.crc32(payload))
    try:
        reject_apng(single_frame_control)
    except ValueError:
        print("PASS rejects one-frame APNG control chunk")
    else:
        raise AssertionError("one-frame APNG accepted")
    for path in sorted((ROOT / "dist").glob("*.zip")):
        print("PASS valid", path.name, validate(path))
    print(f"{len(cases)+5} package validation scenarios passed")

if __name__ == "__main__":
    main()
