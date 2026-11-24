import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD = "../fonts/"
W, H = 1080, 1920
YEL = (245, 200, 66); NAVY = (18, 44, 92); BLUE = (40, 88, 168)
def F(n, s): return ImageFont.truetype(FD + n, s)
INTER = "/usr/share/fonts/opentype/inter/"

bg = Image.open("../imgs/nyse13.jpg").convert("RGB")
sc = H / bg.height
bg = bg.resize((int(bg.width * sc) + 1, H), Image.LANCZOS)
xo = (bg.width - W) // 2
img = bg.crop((xo, 0, xo + W, H))
a = np.asarray(img).astype(np.float32)
a = np.clip((a - 128) * 1.1 + 128, 0, 255) * 0.78          # contrast, slightly darker
yy = np.arange(H)[:, None, None]
g = np.clip((yy - 760) / 650, 0, 1) ** 1.1 * 0.70           # bottom dark gradient for text
a = a * (1 - g)
gt = np.clip(1 - abs(yy - 260) / 260, 0, 1) * 0.25            # soft top shade behind badge
a = a * (1 - gt)
img = Image.fromarray(a.astype(np.uint8))

# ---------- rebound chart (illustrative, no values) ----------
def chart(img):
    import math
    pts = []
    xs = np.linspace(70, 1010, 60)
    for i, x in enumerate(xs):
        u = i / (len(xs) - 1)
        if u < 0.88:   # ~7 weeks of decline (-11.6%)
            v = 0.08 + 0.84 * (u / 0.88) ** 1.15 + 0.04 * math.sin(u * 40) * (1 - u)
        else:          # one-day rebound (+4.7% ~ 40% of the drop)
            v = 0.92 - 0.36 * ((u - 0.88) / 0.12)
        pts.append((x, 640 + v * 330))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    split = int(round((len(pts) - 1) * 0.88))
    red, green = (255, 70, 85), (40, 235, 140)
    # area fill under green segment
    for seg, col, wdt in ((pts[:split + 1], red, 12), (pts[split:], green, 18)):
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).line(seg, fill=col + (255,), width=wdt * 3, joint="curve")
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        lay.alpha_composite(glow)
        d.line(seg, fill=col + (255,), width=wdt, joint="curve")
    # low point marker + rebound arrow head
    lx, ly = pts[split]
    d.ellipse([lx - 14, ly - 14, lx + 14, ly + 14], fill=red + (255,), outline=(255, 255, 255, 230), width=4)
    ex, ey = pts[-1]
    ang = math.atan2(ey - pts[-3][1], ex - pts[-3][0])
    L = 60
    p1 = (ex + L * 0.55 * math.cos(ang), ey + L * 0.55 * math.sin(ang))
    p2 = (ex + L * math.cos(ang + 2.5) * 0.9, ey + L * math.sin(ang + 2.5) * 0.9)
    p3 = (ex + L * math.cos(ang - 2.5) * 0.9, ey + L * math.sin(ang - 2.5) * 0.9)
    d.polygon([p1, p2, p3], fill=green + (255,))
    img.paste(lay, (0, 0), lay)
chart(img)

# ---------- badge (top-left, inside 3:4 grid crop) ----------
def badge(img, x, y, s=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ph = int(86 * s); pw = int(330 * s); R = int(52 * s)
    cx, cy = x + R, y + ph // 2
    # yellow accent tab
    d.rounded_rectangle([cx + 10 * s, cy - ph / 2 - 12 * s, cx + 150 * s, cy - ph / 2 + 22 * s], int(14 * s), fill=YEL)
    # blue pill
    d.rounded_rectangle([cx, cy - ph / 2, cx + pw, cy + ph / 2], int(14 * s), fill=BLUE)
    tx = cx + R + 16 * s
    fn = F("Montserrat-ExtraBold.ttf", int(25 * s))
    d.text((tx, cy - 2 * s), "GIULIO", font=fn, fill="white", anchor="ls")
    d.text((tx, cy + 26 * s), "FILIERI", font=fn, fill="white", anchor="ls")
    dx = tx + fn.getlength("FILIERI") + 14 * s
    d.line([(dx, cy - 26 * s), (dx, cy + 26 * s)], fill=(255, 255, 255, 160), width=max(1, int(2 * s)))
    fs = F("Montserrat-SemiBold.ttf", int(10 * s))
    d.text((dx + 12 * s, cy - 24 * s), "FINANCIAL", font=fs, fill=(220, 230, 245))
    d.text((dx + 12 * s, cy - 12 * s), "ADVISOR", font=fs, fill=(220, 230, 245))
    fb = F("Montserrat-ExtraBold.ttf", int(13 * s))
    bw = fb.getlength("FINECO") + 14 * s
    d.rounded_rectangle([dx + 12 * s, cy + 4 * s, dx + 12 * s + bw, cy + 26 * s], int(6 * s), outline="white", width=max(1, int(2 * s)))
    d.text((dx + 12 * s + bw / 2, cy + 15 * s), "FINECO", font=fb, fill="white", anchor="mm")
    # avatar circle with white + navy ring
    prof = Image.open("../up/profile.jpg").convert("RGB")
    av = prof.crop((50, 8, 214, 172)).resize((2 * R, 2 * R), Image.LANCZOS)
    m = Image.new("L", av.size, 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    d.ellipse([cx - R - 5 * s, cy - R - 5 * s, cx + R + 5 * s, cy + R + 5 * s], fill="white")
    d.ellipse([cx - R - 1 * s, cy - R - 1 * s, cx + R + 1 * s, cy + R + 1 * s], fill=NAVY)
    lay.paste(av, (int(cx - R), int(cy - R)), m)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.35))
    img.paste((0, 0, 0), (0, 4), sh)
    img.paste(lay, (0, 0), lay)

badge(img, 110, 262, 1.0)

# ---------- headline ----------
def shadowed(img, xy, s, font, fill, anchor="ma", blur=10, off=7, sa=200, stroke=0):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0], xy[1] + off), s, font=font, fill=(0, 0, 0, sa), anchor=anchor, stroke_width=stroke + 4, stroke_fill=(0, 0, 0, sa))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    img.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))

lead = sys.argv[1] if len(sys.argv) > 1 else "Jensen Huang torna in Nvidia:"
L1 = sys.argv[2] if len(sys.argv) > 2 else "WALL STREET"
L2 = sys.argv[3] if len(sys.argv) > 3 else "VOLA +4,7%"
out = sys.argv[4] if len(sys.argv) > 4 else "/home/user/Previdenza/reel/copertina_reel.jpg"

shadowed(img, (540, 1000), lead, F("Montserrat-SemiBold.ttf", 50), (255, 255, 255), blur=8, off=4, sa=220)
def fit(s, maxw, size):
    while F("Anton.ttf", size).getlength(s) > maxw: size -= 4
    return F("Anton.ttf", size)
size = min(fit(L1, 900, 230).size, fit(L2, 900, 230).size)
fa = F("Anton.ttf", size)
y1 = 1062
shadowed(img, (540, y1), L1, fa, YEL, blur=14, off=10, sa=230, stroke=2)
shadowed(img, (540, y1 + int(size * 1.02)), L2, fa, YEL, blur=14, off=10, sa=230, stroke=2)

d = ImageDraw.Draw(img)
d.text((1040, 1668), "Foto: Martin Furtschegger, Wikimedia Commons, CC BY 3.0 (modificata)", font=F("Montserrat-SemiBold.ttf", 15), fill=(200, 200, 205), anchor="rs")
img.save(out, quality=95)
img.crop((0, 240, 1080, 1680)).resize((370, 493), Image.LANCZOS).save("prev/cover3_grid.jpg", quality=92)
img.resize((540, 960)).save("prev/cover3_full.jpg", quality=92)
print("ok", size)
