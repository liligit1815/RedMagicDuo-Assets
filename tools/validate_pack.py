"""Validate data-only RedMagic Duo status-bar packs. Never extracts or executes them."""
from __future__ import annotations
import hashlib
import io
import json
import re
import stat
import sys
import warnings
import zipfile
from pathlib import Path
from PIL import Image
from fontTools.ttLib import TTCollection, TTFont

MAX_ZIP = 20 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
HASH = re.compile(r"[0-9a-f]{64}\Z")
PATH = re.compile(r"(?:manifest\.json|images/[0-9a-f]{64}\.(?:png|jpg|jpeg|webp|gif)|fonts/[0-9a-f]{64}\.(?:ttf|otf|ttc|font))\Z")
ROLES = ["global", "clock", "network", "metrics", "battery", "bluetooth", "other"]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def strict_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result

def references(theme, fonts):
    require(isinstance(theme, str) and len(theme) <= 65536, "invalid theme")
    require(isinstance(fonts, str) and len(fonts) <= 2048, "invalid fonts")
    images, font_files, previous, bands = set(), set(), "", []
    if theme:
        rows = theme.split(";")
        require(rows[0] == "1" and 1 < len(rows) <= 385, "invalid theme version/count")
        for row in rows[1:]:
            parts = row.split(",")
            require(len(parts) == 10, "invalid binding")
            icon, state, layer, sha, color, scale, x, y, opacity, mirror = parts
            require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,79}", icon), "invalid icon ID")
            require(re.fullmatch(r"[A-Za-z0-9_.:-]{1,48}", state), "invalid state")
            require(layer in {"whole", "background", "foreground"} and HASH.fullmatch(sha), "invalid layer/hash")
            require(color in {"0", "1"} and mirror in {"0", "1"}, "invalid flags")
            numbers = [int(n) for n in [scale, x, y, opacity]]
            require([str(n) for n in numbers] == [scale, x, y, opacity], "noncanonical numbers")
            scale, x, y, opacity = numbers
            require(10 <= scale <= 400 and -64 <= x <= 64 and -64 <= y <= 64 and 0 <= opacity <= 100, "binding out of range")
            key = ",".join(parts[:3])
            require(key > previous, "duplicate or noncanonical binding order")
            previous = key
            if state.startswith("battery"):
                match = re.fullmatch(r"battery([0-9]{1,3})_([0-9]{1,3})", state)
                if match:
                    low, high = map(int, match.groups())
                    require(low <= high <= 100, "invalid battery interval")
                    for prior_icon, prior_layer, prior_low, prior_high in bands:
                        require(icon != prior_icon or layer != prior_layer or high < prior_low or low > prior_high, "overlapping battery intervals")
                    bands.append((icon, layer, low, high))
                else:
                    require(re.fullmatch(r"battery(?:[0-9]|[1-9][0-9]|100)", state), "invalid battery state")
            images.add(sha)
    if fonts:
        rows = fonts.split(";")
        require(rows[0] == "1" and 1 < len(rows) <= 8, "invalid font version/count")
        previous_role = -1
        for row in rows[1:]:
            parts = row.split("=")
            require(len(parts) == 2 and parts[0] in ROLES, "invalid font role")
            role, value = parts
            require(ROLES.index(role) > previous_role, "duplicate or noncanonical font order")
            previous_role = ROLES.index(role)
            require(value == "original" or (value.startswith("font:") and HASH.fullmatch(value[5:])), "invalid font choice")
            if value.startswith("font:"):
                font_files.add(value[5:])
    return images, font_files

def validate(path):
    path = Path(path)
    require(path.stat().st_size <= MAX_ZIP, "ZIP exceeds 20 MiB")
    entries = {}
    expanded = 0
    with zipfile.ZipFile(path) as archive:
        require(len(archive.infolist()) <= 512, "too many ZIP entries")
        for entry in archive.infolist():
            require(PATH.fullmatch(entry.filename) and not entry.is_dir(), f"unsafe/unsupported path: {entry.filename}")
            require(entry.filename not in entries, "duplicate ZIP entry")
            require(not stat.S_ISLNK(entry.external_attr >> 16) and not entry.flag_bits & 1, "symlink/encrypted file")
            limit = 256 * 1024 if entry.filename == "manifest.json" else 8 * 1024 * 1024
            require(entry.file_size <= limit, "entry too large")
            expanded += entry.file_size
            require(expanded <= MAX_EXPANDED, "expanded ZIP exceeds 64 MiB")
            with archive.open(entry) as stream:
                data = stream.read(limit + 1)
                require(len(data) <= limit and len(data) == entry.file_size, "invalid expanded size")
            entries[entry.filename] = data
    require("manifest.json" in entries, "missing manifest")
    manifest = json.loads(entries.pop("manifest.json").decode("utf-8"), object_pairs_hook=strict_object)
    require(isinstance(manifest, dict) and set(manifest) == {"format", "version", "metadata", "theme", "fonts", "images", "fontFiles"}, "unsupported manifest fields")
    require(manifest["format"] == "RedMagicDuo.StatusBarAssets" and type(manifest["version"]) is int and manifest["version"] == 1, "unsupported format/version")
    metadata = manifest["metadata"]
    allowed = {"name", "author", "license", "licenseText", "source", "description"}
    require(isinstance(metadata, dict) and set(metadata) <= allowed and {"name", "author", "license"} <= set(metadata), "invalid metadata")
    for key, value in metadata.items():
        limit = 100 if key in {"name", "author"} else 200 if key == "license" else 65536 if key == "licenseText" else 2048
        require(isinstance(value, str) and value.strip() and len(value) <= limit and "\0" not in value, "invalid metadata text")
    image_refs, font_refs = references(manifest["theme"], manifest["fonts"])
    require(isinstance(manifest["images"], dict) and isinstance(manifest["fontFiles"], dict), "invalid resource maps")
    require(set(manifest["images"]) == image_refs and set(manifest["fontFiles"]) == font_refs, "resource references disagree")
    animated = 0
    for section, prefix in [("images", "images/"), ("fontFiles", "fonts/")]:
        for sha, filename in manifest[section].items():
            require(HASH.fullmatch(sha) and isinstance(filename, str) and filename.startswith(prefix + sha + "."), "invalid resource path")
            require(filename in entries, "missing or reused resource")
            data = entries.pop(filename)
            require(hashlib.sha256(data).hexdigest() == sha, "SHA-256 mismatch")
            if section == "images":
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(data)) as image:
                        require(image.format in {"PNG", "JPEG", "WEBP", "GIF"}, "unsupported image type")
                        count = getattr(image, "n_frames", 1)
                        side_limit = 1024 if count > 1 else 4096
                        require(0 < image.width <= side_limit and 0 < image.height <= side_limit, "image dimensions exceed limits")
                        require(count <= 240, "animation exceeds community 240-frame limit")
                        for frame in range(count):
                            image.seek(frame)
                            image.load()
                        animated += count > 1
            else:
                require(12 <= len(data) <= 4 * 1024 * 1024, "font exceeds 4 MiB")
                if data[:4] == b"ttcf":
                    font_collection = TTCollection(io.BytesIO(data), lazy=False)
                    fonts = font_collection.fonts
                else:
                    fonts = [TTFont(io.BytesIO(data), lazy=False)]
                try:
                    for font in fonts:
                        require(font.getBestCmap(), "font contains no usable character mapping")
                        # Force actual table parsing, rather than accepting a header only.
                        for tag in font.keys():
                            font[tag]
                finally:
                    for font in fonts:
                        font.close()
    require(not entries, "unreferenced ZIP files")
    return {"name": metadata["name"], "images": len(image_refs), "fonts": len(font_refs), "animated": animated, "bytes": expanded}

if __name__ == "__main__":
    require(len(sys.argv) > 1, "usage: python tools/validate_pack.py package.zip [...]")
    for filename in sys.argv[1:]:
        print(filename, json.dumps(validate(filename), ensure_ascii=False))
