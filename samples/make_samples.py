"""Generate the synthetic demo documents in samples/synthetic/.

Two matched sets, each a purchase order, a bill or invoice, and a goods-receipt note, drawn to look like
phone photos of paper: handwriting on a ruled pad, or a thermal till receipt. Run once; the PNGs are committed.

    python samples/make_samples.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent / "synthetic"
FONTS = Path("C:/Windows/Fonts")
random.seed(7)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    # shortcut: uses Windows handwriting fonts; on other systems it falls back to PIL's default font.
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        return ImageFont.load_default(size)


def ruled_page(w=900, h=1200) -> Image.Image:
    img = Image.new("RGB", (w, h), (250, 249, 244))
    d = ImageDraw.Draw(img)
    for y in range(150, h, 52):
        d.line([(0, y), (w, y)], fill=(198, 214, 236), width=2)
    d.line([(96, 0), (96, h)], fill=(236, 170, 170), width=2)
    return img


def hand(img: Image.Image, lines: list[str], top=110, size=40, ink=(28, 42, 110)) -> None:
    """Write each line on the ruling with a little drift in angle, start and baseline, like a person writing."""
    for i, text in enumerate(lines):
        if not text:
            continue
        f = font(random.choice(["Inkfree.ttf", "segoepr.ttf"]), size + random.randint(-3, 3))
        layer = Image.new("RGBA", (img.width, 90), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((118 + random.randint(-6, 10), 10), text, font=f, fill=(*ink, 235))
        layer = layer.rotate(random.uniform(-1.4, 1.4), resample=Image.BICUBIC, center=(118, 45))
        img.paste(layer, (0, top + i * 52 - 40 + random.randint(-4, 4)), layer)


def photo(img: Image.Image, angle: float) -> Image.Image:
    """Tilt, soften and shade the page so it reads as a phone photo, not a render."""
    bg = Image.new("RGB", (img.width + 120, img.height + 120), (92, 84, 76))
    bg.paste(img, (60, 60))
    bg = bg.rotate(angle, resample=Image.BICUBIC, fillcolor=(92, 84, 76))
    shade = Image.new("L", bg.size)
    sd = ImageDraw.Draw(shade)
    for x in range(0, bg.width, 6):
        sd.line([(x, 0), (x, bg.height)], fill=int(40 * (x / bg.width) ** 1.6))
    bg = Image.composite(Image.new("RGB", bg.size, (0, 0, 0)), bg, shade)
    return bg.filter(ImageFilter.GaussianBlur(0.7))


def till_receipt(lines: list[str], w=560) -> Image.Image:
    f = font("consola.ttf", 26)
    fb = font("consolab.ttf", 30)
    h = 90 + 40 * len(lines)
    img = Image.new("RGB", (w, h), (247, 246, 240))
    d = ImageDraw.Draw(img)
    y = 40
    for text in lines:
        bold = text.startswith("*")
        text = text.lstrip("*")
        tw = d.textlength(text, font=fb if bold else f)
        x = (w - tw) / 2 if bold else 34
        d.text((x, y), text, font=fb if bold else f, fill=(40, 40, 46))
        y += 40
    # Thermal print fades unevenly.
    fade = Image.new("L", img.size)
    fd = ImageDraw.Draw(fade)
    for yy in range(0, h, 3):
        fd.line([(0, yy), (w, yy)], fill=int(30 + 25 * math.sin(yy / 37)))
    return Image.composite(Image.new("RGB", img.size, (247, 246, 240)), img, fade)


def save(img: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT / name, quality=88)
    print("wrote", OUT / name)


# Set 1: team lunch. The bill adds a service charge the PO never allowed.
page = ruled_page()
hand(page, [
    "PURCHASE ORDER  PO #7310",
    "Vendor: Cafe Lido",
    "Team lunch, Friday",
    "4x Veg thali ......... $48.00",
    "4x Masala chai ....... $12.00",
    "Max authorized: $60.00",
    "No service charge or extras.",
    "Approved - R. Iyer",
])
save(photo(page, 2.2), "set1_handwritten_po_team_lunch.jpg")

save(photo(till_receipt([
    "*CAFE LIDO",
    "  12 Church Street",
    "Bill No: INV-0931",
    "PO Ref: PO #7310",
    "--------------------------------",
    "4 Veg thali            48.00",
    "4 Masala chai          12.00",
    "--------------------------------",
    "Subtotal               60.00",
    "Service charge 10%      6.00",
    "--------------------------------",
    "*TOTAL  $66.00",
    "   Thank you, visit again",
]), -3.0), "set1_restaurant_bill_cafe_lido.jpg")

page = ruled_page(h=760)
hand(page, ["Received - Cafe Lido order", "4 thalis + 4 chai, all there.", "Signed: front desk"], top=170)
save(photo(page, 1.0), "set1_receipt_note_lunch_all_received.jpg")

# Set 2: office chairs. Six ordered, four arrived, and the invoice adds a delivery fee.
page = ruled_page()
hand(page, [
    "PURCHASE ORDER  PO #5521",
    "Vendor: Northwind Office Supply",
    "6x Ergonomic office chair .... $720.00",
    "Max authorized: $720.00",
    "Delivery included. No extra fees.",
    "Approved - Facilities",
])
save(photo(page, -1.8), "set2_handwritten_po_office_chairs.jpg")

page = ruled_page()
hand(page, [
    "INVOICE  INV-2207",
    "Northwind Office Supply",
    "PO ref: PO #5521",
    "6x Ergonomic office chair .... $720.00",
    "Delivery fee ............... $40.00",
    "TOTAL DUE: $760.00",
], ink=(20, 20, 20))
save(photo(page, 2.6), "set2_handwritten_invoice_office_chairs.jpg")

page = ruled_page(h=900)
hand(page, ["Goods received - PO #5521", "Office chairs: 4 boxes arrived", "(6 ordered, 2 missing)", "Checked by: J. Rao"], top=170)
d = ImageDraw.Draw(page)
for i in range(6):  # a quick sketch of the pallet: four boxes drawn, two crossed out
    x, y = 150 + i * 115, 520
    d.rectangle([x, y, x + 90, y + 90], outline=(28, 42, 110), width=4)
    if i >= 4:
        d.line([(x, y), (x + 90, y + 90)], fill=(180, 30, 30), width=5)
        d.line([(x + 90, y), (x, y + 90)], fill=(180, 30, 30), width=5)
save(photo(page, -1.2), "set2_receipt_note_chairs_4_of_6.jpg")
