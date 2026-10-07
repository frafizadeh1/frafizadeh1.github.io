#!/usr/bin/env python3
"""Add one before/after case to the portfolio on index.html (newest first).

Face mode (eyes are always covered):
  --before-eyes x1,y1,x2,y2   centres of the two eyes in the ORIGINAL before photo (pixels)
  --after-eyes  x1,y1,x2,y2   same for the after photo
Box mode (crop to one area, e.g. lips; the crop must not contain the eyes):
  --before-box x0,y0,x1,y1 / --after-box x0,y0,x1,y1   crop boxes in ORIGINAL pixels
Use the same mode for both photos.

Example:
  python3 tools/add_case.py --id abc123 --cat filler --title "فیلر لب" \
    --caption "نیم سی‌سی فیلر لب." --before b.jpg --after a.jpg \
    --before-box 100,900,1100,1650 --after-box 0,850,1800,1900
"""
import argparse, datetime, html, os, re
from PIL import Image, ImageDraw, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "images", "cases")
GREEN = (63, 76, 41)
CATS = {"filler": "فیلر", "thread": "لیفت با نخ", "botox": "بوتاکس", "prp": "PRP",
        "meso": "مزوتراپی", "skin": "اسکین‌کر", "other": "سایر"}


def nums(s):
    v = [float(x) for x in s.split(",")]
    assert len(v) == 4, s
    return v


def face(src, eyes, dst):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    x1, y1, x2, y2 = eyes
    if x1 > x2:
        x1, y1, x2, y2 = x2, y2, x1, y1
    d = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    ey, cx = (y1 + y2) / 2, (x1 + x2) / 2
    ImageDraw.Draw(im).rounded_rectangle(
        [x1 - 0.42 * d, ey - 0.2 * d, x2 + 0.42 * d, ey + 0.2 * d], radius=int(0.2 * d), fill=GREEN)
    w = 2.75 * d
    h = w * 4 / 3
    top = ey - 0.33 * h
    box = [max(0, int(cx - w / 2)), max(0, int(top)), min(im.width, int(cx + w / 2)), min(im.height, int(top + h))]
    c = im.crop(box)
    c = c.resize((720, int(720 * c.height / c.width)), Image.LANCZOS)
    c.save(dst, quality=82, optimize=True, progressive=True)
    return "3/4"


def crop(src, box, dst):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    c = im.crop([int(v) for v in box])
    c = c.resize((800, int(800 * c.height / c.width)), Image.LANCZOS)
    c.save(dst, quality=82, optimize=True, progressive=True)
    return f"{c.width}/{c.height}"


def img_btn(name, which, ratio, title):
    lab = "قبل" if which == "before" else "بعد"
    bg, fg = ("#FFFFFF", "#2B3122") if which == "before" else ("#4B5A31", "#FFFFFF")
    return (f'<button type="button" class="case-img" data-full="images/cases/{name}-{which}.jpg" aria-label="بزرگ‌نمایی عکس {lab}" '
            f'style="position: relative; display: block; padding: 0; border: 0; background: #E6EDDD; border-radius: 14px; overflow: hidden; cursor: zoom-in; aspect-ratio: {ratio}">\n'
            f'<img src="images/cases/{name}-{which}.jpg" alt="{title} – {lab}" loading="lazy" style="width: 100%; height: 100%; object-fit: cover; display: block">\n'
            f'<span style="position: absolute; top: 8px; right: 8px; padding: 2px 10px; border-radius: 999px; background: {bg}; color: {fg}; font-size: 12px; font-weight: 700">{lab}</span>\n'
            f'</button>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--cat", required=True, choices=list(CATS))
    ap.add_argument("--title", required=True)
    ap.add_argument("--caption", required=True)
    ap.add_argument("--note", default="", help="optional highlighted note under the caption")
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--before-eyes")
    ap.add_argument("--after-eyes")
    ap.add_argument("--before-box")
    ap.add_argument("--after-box")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    name = "case-" + re.sub(r"[^A-Za-z0-9_-]", "", a.id)
    path = os.path.join(ROOT, "index.html")
    s = open(path, encoding="utf-8").read()
    if f'data-case-id="{name}"' in s:
        print("already on the site:", name)
        return
    if a.before_eyes and a.after_eyes:
        r1 = face(a.before, nums(a.before_eyes), os.path.join(OUT, name + "-before.jpg"))
        r2 = face(a.after, nums(a.after_eyes), os.path.join(OUT, name + "-after.jpg"))
    elif a.before_box and a.after_box:
        r1 = crop(a.before, nums(a.before_box), os.path.join(OUT, name + "-before.jpg"))
        r2 = crop(a.after, nums(a.after_box), os.path.join(OUT, name + "-after.jpg"))
    else:
        raise SystemExit("give --before-eyes/--after-eyes or --before-box/--after-box")
    ratio = r1  # both cells use the before ratio so the pair lines up

    t, c = html.escape(a.title), html.escape(a.caption)
    note = ""
    if a.note:
        note = ('</p>\n<p style="margin: 4px 0 0; padding: 8px 12px; border-radius: 10px; background: #FFF6E5; '
                f'font-size: 13.5px; color: #5B4210">{html.escape(a.note)}')
    added = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    art = (f'<article class="case" data-added="{added}" data-case-id="{name}" data-cat="{a.cat}" '
           'style="background: #FFFFFF; border: 1px solid #DDE5D3; border-radius: 20px; padding: 14px; display: flex; flex-direction: column; gap: 12px">\n'
           '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">\n'
           f'{img_btn(name, "before", ratio, t)}\n{img_btn(name, "after", ratio, t)}\n</div>\n'
           '<div style="display: flex; flex-direction: column; gap: 4px; padding: 0 4px 4px">\n'
           f'<h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #2B3122">{t}</h3>\n'
           f'<p style="margin: 0; font-size: 14px; color: #4A5340">{c}{note}</p>\n</div>\n</article>\n')

    m = re.search(r'<div id="case-list"[^>]*>\n', s)
    assert m, "case-list not found"
    s = s[:m.end()] + art + s[m.end():]

    if f'data-filter="{a.cat}"' not in s:
        btn = (f'<button type="button" class="case-filter" data-filter="{a.cat}" aria-pressed="false" '
               'style="min-height: 44px; padding: 0 20px; border-radius: 999px; border: 1px solid #C9D6B8; font: inherit; '
               f'font-size: 14px; font-weight: 500; cursor: pointer">{CATS[a.cat]}</button>\n')
        g = re.search(r'(<div role="group" aria-label="دسته‌ی نمونه‌کارها"[^>]*>\n(?:<button[^\n]*\n)*)', s)
        assert g, "filter group not found"
        s = s[:g.end()] + btn + s[g.end():]

    open(path, "w", encoding="utf-8").write(s)
    print("added", name, "->", a.cat)


if __name__ == "__main__":
    main()
