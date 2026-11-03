"""Export the approved, unchanged F1 SVG to application/browser icon formats.

Development only: python -m pip install cairosvg pillow
Then: python tools/ui/export_brand_icons.py
"""
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
SVG = "{http://www.w3.org/2000/svg}"
BACKGROUND = "#F7F5F0"


def render(size: int, *, maskable: bool = False) -> bytes:
    symbol = ET.fromstring((ASSETS / "branding/f1-symbol.svg").read_text())
    inset = 20 if maskable else 8
    symbol.attrib.update(x=str(inset), y=str(inset), width=str(100 - 2 * inset),
                         height=str(100 - 2 * inset))
    canvas = ET.Element(SVG + "svg", width=str(size), height=str(size), viewBox="0 0 100 100")
    ET.SubElement(canvas, SVG + "rect", width="100", height="100", fill=BACKGROUND)
    canvas.append(symbol)
    return cairosvg.svg2png(bytestring=ET.tostring(canvas), output_width=size, output_height=size)


def export() -> None:
    icons = ASSETS / "icons"
    icons.mkdir(exist_ok=True)
    normal = {size: render(size) for size in (64, 192, 512)}
    maskable = {size: render(size, maskable=True) for size in (192, 512)}
    for name, data in {
        "favicon.png": normal[64], "icon.png": normal[512],
        "icon_192.png": normal[192], "icon_512.png": normal[512],
        "icon_maskable_512.png": maskable[512],
        "icons/icon-192.png": normal[192], "icons/icon-512.png": normal[512],
        "icons/apple-touch-icon-192.png": normal[192],
        "icons/icon-maskable-192.png": maskable[192],
        "icons/icon-maskable-512.png": maskable[512],
    }.items():
        (ASSETS / name).write_bytes(data)
    with Image.open(BytesIO(normal[512])) as image:
        image.save(ASSETS / "icon.ico", format="ICO",
                   sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])


if __name__ == "__main__":
    export()
