"""Reproducible original icon examples, plus unmodified OFL-licensed Noto Sans."""
from __future__ import annotations
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5"
FONT_URL = f"https://raw.githubusercontent.com/google/fonts/{UPSTREAM}/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf"
OFL_URL = f"https://raw.githubusercontent.com/google/fonts/{UPSTREAM}/ofl/notosans/OFL.txt"
BASE = "https://github.com/liligit1815/RedMagicDuo-Assets/releases/download/v1.0.0/"
WHITE = (255, 255, 255, 255)

def png(image):
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()

def icon(kind):
    image = Image.new("RGBA", (96, 96))
    draw = ImageDraw.Draw(image)
    if kind == "alarm_clock":
        draw.ellipse((20, 23, 76, 79), outline=WHITE, width=6)
        draw.line((48, 35, 48, 52, 60, 60), fill=WHITE, width=6)
        draw.arc((8, 8, 39, 39), 185, 285, fill=WHITE, width=7)
        draw.arc((57, 8, 88, 39), 255, 355, fill=WHITE, width=7)
        draw.line((27, 76, 19, 86), fill=WHITE, width=6)
        draw.line((69, 76, 77, 86), fill=WHITE, width=6)
    elif kind == "bluetooth":
        draw.line((47, 10, 47, 85), fill=WHITE, width=6)
        draw.line((47, 10, 68, 31, 27, 68), fill=WHITE, width=6)
        draw.line((47, 85, 68, 64, 27, 27), fill=WHITE, width=6)
    elif kind == "zen":
        draw.ellipse((14, 14, 82, 82), outline=WHITE, width=7)
        draw.rounded_rectangle((28, 44, 68, 51), radius=3, fill=WHITE)
    elif kind == "airplane":
        draw.polygon([(44, 8), (52, 8), (55, 37), (85, 58), (85, 65), (54, 55), (53, 77), (65, 84), (65, 89), (48, 85), (31, 89), (31, 84), (43, 77), (42, 55), (11, 65), (11, 58), (41, 37)], fill=WHITE)
    elif kind == "vpn":
        draw.rounded_rectangle((20, 42, 76, 83), radius=8, outline=WHITE, width=6)
        draw.arc((29, 12, 67, 66), 180, 360, fill=WHITE, width=6)
        draw.ellipse((43, 55, 53, 65), fill=WHITE)
        draw.line((48, 62, 48, 72), fill=WHITE, width=5)
    return image

def fan_frame(step):
    image = Image.new("RGBA", (96, 96))
    draw = ImageDraw.Draw(image)
    draw.ellipse((12, 12, 84, 84), outline=(255, 255, 255, 110), width=3)
    for blade in range(3):
        angle = 2 * math.pi * (blade / 3 + step / 24)
        points = []
        for distance, offset in [(7, -.18), (28, -.62), (34, -.20), (24, .28), (10, .35)]:
            points.append((48 + math.cos(angle + offset) * distance, 48 + math.sin(angle + offset) * distance))
        draw.polygon(points, fill=WHITE)
    draw.ellipse((41, 41, 55, 55), fill=WHITE)
    return image

def pack(slug, name, description, resources, font=None, font_license=None):
    images, fonts, blobs, bindings = {}, {}, {}, []
    for target, suffix, data in resources:
        sha = hashlib.sha256(data).hexdigest()
        path = f"images/{sha}.{suffix}"
        images[sha] = path
        blobs[path] = data
        bindings.append(f"{target},default,whole,{sha},0,100,0,0,100,0")
    font_spec = ""
    if font:
        sha = hashlib.sha256(font).hexdigest()
        path = f"fonts/{sha}.ttf"
        fonts[sha] = path
        blobs[path] = font
        font_spec = f"1;global=font:{sha}"
    license_id = "OFL-1.1" if font else "MIT"
    license_text = font_license if font else (ROOT / "LICENSE").read_text(encoding="utf-8")
    metadata = {"name": name, "author": "The Noto Project Authors" if font else "RedMagic Duo contributors", "license": license_id, "licenseText": license_text, "description": description}
    if font:
        metadata["source"] = f"https://github.com/google/fonts/tree/{UPSTREAM}/ofl/notosans"
    manifest = {"format": "RedMagicDuo.StatusBarAssets", "version": 1, "metadata": metadata, "theme": "1;" + ";".join(sorted(bindings)) if bindings else "", "fonts": font_spec, "images": images, "fontFiles": fonts}
    filename = slug + "-1.0.0.zip"
    destination = ROOT / "dist" / filename
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        entries = {"manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(), **blobs}
        for path, data in entries.items():
            entry = zipfile.ZipInfo(path, date_time=(2026, 9, 29, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    output = destination.read_bytes()
    return {"id": slug, "name": name, "version": "1.0.0", "description": description, "author": metadata["author"], "license": license_id, "formatVersion": 1, "downloadUrl": BASE + filename, "sha256": hashlib.sha256(output).hexdigest(), "sizeBytes": len(output), "previewUrl": f"https://raw.githubusercontent.com/liligit1815/RedMagicDuo-Assets/main/previews/{slug}." + ("webp" if slug == "gentle-spin" else "png")}

def download(url, destination):
    if not destination.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "RedMagicDuo-Assets-build"})
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())
    return destination.read_bytes()

def main():
    for folder in ["dist", "previews", "licenses"]:
        (ROOT / folder).mkdir(exist_ok=True)
    kinds = ["alarm_clock", "bluetooth", "zen", "airplane", "vpn"]
    resources = [(kind, "png", png(icon(kind))) for kind in kinds]
    preview = Image.new("RGB", (640, 168), (23, 28, 39))
    for i, kind in enumerate(kinds):
        preview.paste(icon(kind), (22 + i * 124, 36), icon(kind))
    preview.save(ROOT / "previews" / "mono-essentials.png")
    animated = io.BytesIO()
    frames = [fan_frame(step) for step in range(24)]
    frames[0].save(animated, format="WEBP", save_all=True, append_images=frames[1:], duration=125, loop=0, lossless=True, minimize_size=True)
    (ROOT / "previews" / "gentle-spin.webp").write_bytes(animated.getvalue())
    font = download(FONT_URL, ROOT / "dist" / "NotoSans-variable.ttf")
    ofl = download(OFL_URL, ROOT / "licenses" / "NotoSans-OFL.txt").decode("utf-8")
    from PIL import ImageFont
    face = ImageFont.truetype(io.BytesIO(font), 40)
    font_preview = Image.new("RGB", (640, 168), (23, 28, 39))
    draw = ImageDraw.Draw(font_preview)
    draw.text((24, 24), "Noto Sans", fill="white", font=face)
    draw.text((24, 85), "09:41    100%    5G", fill="white", font=face)
    font_preview.save(ROOT / "previews" / "noto-sans.png")
    catalog = {"format": "RedMagicDuo.AssetCatalog", "version": 1, "packs": [
        pack("mono-essentials", "Mono Essentials", "原创单色闹钟、蓝牙、勿扰、飞行模式与 VPN 图标", resources),
        pack("gentle-spin", "Gentle Spin", "原创 8 fps 散热风扇动画，24 帧循环", [("cooling_fan", "webp", animated.getvalue())]),
        pack("noto-sans", "Noto Sans", "Noto Sans 原版可变字体，适合数字和拉丁文字；中文使用系统回退", [], font, ofl)
    ]}
    (ROOT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "licenses" / "NotoSans-SOURCE.md").write_text(f"# Noto Sans 来源\n\n未修改的 Google Fonts Noto Sans 可变字体。\n\n- 来源提交：`{UPSTREAM}`\n- [字体原文件]({FONT_URL})\n- [OFL 原文]({OFL_URL})\n- 字体 SHA-256：`{hashlib.sha256(font).hexdigest()}`\n\n字体以 SIL Open Font License 1.1 分发，详见 NotoSans-OFL.txt。\n", encoding="utf-8")
    for item in catalog["packs"]:
        print(item["id"], item["sizeBytes"], item["sha256"])

if __name__ == "__main__":
    main()
