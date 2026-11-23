import sys, subprocess, math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = sys.argv[1]
OUT = sys.argv[2]
ONLY = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None  # preview frames

F = "/usr/share/fonts/opentype/inter/"
@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype(F + name + ".otf", int(size))

# ---------------- DATA (closing prices, price index) ----------------
# reference "oggi" = close of 20/11/2026: S&P 500 ~6,901.86 ; Dow Jones ~48,147
CRISES = [  # name, years, drawdown %, rally %
    ("Inflazione\ne rialzo tassi", "2022", -25.4, 93, "S&P 500"),
    ("Crash\nCovid-19", "2020", -33.9, 208, "S&P 500"),
    ("Crisi finanziaria\nglobale", "2007–2009", -56.8, 920, "S&P 500"),
    ("Bolla\nDot-com", "2000–2002", -49.1, 789, "S&P 500"),
    ("Black\nMonday", "1987", -33.5, 2980, "S&P 500"),
    ("Crisi\npetrolifera", "1973–1974", -48.2, 10980, "S&P 500"),
    ("Grande\nDepressione", "1929–1932", -89.2, 116700, "Dow Jones"),
]
BEAT = 0.4
HOOK = 2.4
SEG = 3.2
OUTRO = HOOK + SEG * len(CRISES)  # 24.8
TOTAL = 30.4

RED = (255, 77, 90)
GREEN = (46, 224, 140)
GOLD = (255, 196, 61)
WHITE = (255, 255, 255)
GREY = (190, 198, 214)
TINT = (12, 16, 26)

def itn(x, dec=0):
    s = f"{abs(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lin(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eout(x): return 1 - (1 - x) ** 3
def eoutq(x): return 1 - (1 - x) ** 5
def eback(x, s=1.6):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1
def einout(x): return 3 * x * x - 2 * x * x * x

# ---------------- drawing helpers ----------------
def rr_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    return m

@functools.lru_cache(64)
def shadow(w, h, r, blur=28, a=120):
    pad = blur * 2
    m = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([pad, pad + 10, pad + w, pad + h + 10], r, fill=a)
    return m.filter(ImageFilter.GaussianBlur(blur)), pad

def glass(frame, box, r=34, op=1.0, tint_a=168, border=True, tint=TINT):
    """frosted dark glass panel composited directly onto frame (RGB)."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    if w <= 4 or h <= 4 or op <= 0.003: return
    # shadow
    sm, pad = shadow(w, h, r)
    blk = Image.new("RGB", sm.size, (0, 0, 0))
    frame.paste(blk, (x0 - pad, y0 - pad), sm.point(lambda v: int(v * op * 0.8)))
    region = frame.crop((x0, y0, x1, y1))
    small = region.resize((max(1, w // 6), max(1, h // 6)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    bl = small.resize((w, h), Image.BILINEAR)
    bl = Image.blend(bl, Image.new("RGB", (w, h), tint), tint_a / 255)
    m = rr_mask(w, h, r)
    if op < 1: m = m.point(lambda v: int(v * op))
    frame.paste(bl, (x0, y0), m)
    if border:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle([0, 0, w - 1, h - 1], r, outline=(255, 255, 255, int(46 * op)), width=2)
        frame.paste(ov, (x0, y0), ov)

def text(draw, xy, s, f, fill, op=1.0, anchor="la", shadow_=True, spacing=0):
    a = int(255 * clamp(op))
    if a <= 2: return
    if shadow_:
        draw.text((xy[0], xy[1] + 3), s, font=f, fill=(0, 0, 0, int(a * 0.45)), anchor=anchor, spacing=spacing)
    draw.text(xy, s, font=f, fill=fill + (a,), anchor=anchor, spacing=spacing)

def fit_font(name, s, maxw, start, minsize=30):
    size = start
    while size > minsize:
        f = font(name, size)
        if max(f.getlength(line) for line in s.split("\n")) <= maxw: return f
        size -= 2
    return font(name, minsize)

def overlay(frame, layer):
    frame.paste(layer, (0, 0), layer)

# ---------------- background with camera moves ----------------
def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.75)) ** 2)
    v = 1 - 0.28 * np.clip(d - 0.35, 0, 1) ** 1.4
    return v[..., None].astype(np.float32)
VIG = vignette()


# ======================= V3: stacked liquid-glass rows =======================
TOTAL = 15.2
# S&P 500, closing prices. Rebound = 12 months after the closing low.
ROWS = [  # name, years, drawdown, rebound 12m
    ("Black Monday", "1987", -33.5, 21.4),
    ("Bolla Dot-com", "2000–2002", -49.1, 33.1),
    ("Crisi finanziaria", "2007–2009", -56.8, 68.6),
    ("Crash Covid-19", "2020", -33.9, 74.8),
    ("Inflazione e tassi", "2022", -25.4, 21.6),
]
T_ROW0, T_STEP = 1.6, 2.0          # 120 BPM: a row every 4 beats
OUT_T = T_ROW0 + T_STEP * len(ROWS) - 0.8   # 10.8 -> final message
RX0, RX1 = 40, 945
RY0, RH, RG = 905, 128, 14

def liquid_glass(frame, box, r=36, op=1.0, tint_a=120):
    """Liquid-glass: lens-magnified, blurred backdrop + light tint + specular edge."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    if w < 8 or h < 8 or op <= 0.003: return
    sm, pad = shadow(w, h, r, blur=24, a=90)
    frame.paste(Image.new("RGB", sm.size, (0, 0, 0)), (x0 - pad, y0 - pad), sm.point(lambda v: int(v * op * 0.7)))
    # lens: sample slightly larger area -> subtle magnification/refraction
    m = 0.035
    sx0, sy0 = max(0, x0 - w * m), max(0, y0 - h * m)
    sx1, sy1 = min(W, x1 + w * m), min(H, y1 + h * m)
    src = frame.crop((int(sx0), int(sy0), int(sx1), int(sy1)))
    small = src.resize((max(1, w // 7), max(1, h // 7)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2.2))
    bl = small.resize((w, h), Image.BICUBIC)
    arr = np.asarray(bl).astype(np.float32)
    # tint (cool dark) + vertical light gradient (specular sheen)
    tint = np.array([14, 18, 30], np.float32)
    a = tint_a / 255
    arr = arr * (1 - a) + tint * a
    g = np.linspace(1, 0, h, dtype=np.float32)[:, None, None]
    arr = arr + 38 * g ** 3
    bl = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    mask = rr_mask(w, h, r)
    frame.paste(bl, (x0, y0), mask.point(lambda v: int(v * op)))
    # edges: bright rim top-left, softer bottom-right
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, outline=(255, 255, 255, int(70 * op)), width=2)
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dh = ImageDraw.Draw(hl)
    dh.rounded_rectangle([1, 1, w - 2, h - 2], r - 1, outline=(255, 255, 255, int(130 * op)), width=2)
    fade = Image.linear_gradient("L").resize((w, h)).point(lambda v: 255 - v)
    hl.putalpha(Image.composite(hl.getchannel("A"), Image.new("L", (w, h), 0), fade))
    ov.alpha_composite(hl)
    frame.paste(ov, (x0, y0), ov)

def bg_transform(img, t):
    z = 1.02 + 0.06 * (t / TOTAL)
    for k in range(len(ROWS)):
        s = T_ROW0 + T_STEP * k
        if s <= t < s + 0.25: z += 0.025 * (1 - eout(lin(t, s, s + 0.25)))
    if t < 0.3: z += 0.08 * (1 - eout(lin(t, 0, 0.3)))
    cx, cy = 600, 700
    w, h = W / z, H / z
    x0 = clamp(cx - w * cx / W, 0, W - w); y0 = clamp(cy - h * cy / H, 0, H - h)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))

def header(frame, t):
    a = lin(t, 0.0, 0.25)
    op = clamp(a * 3)
    dy = -(1 - eback(a, 1.3)) * 260
    swap = lin(t, OUT_T, OUT_T + 0.25)
    liquid_glass(frame, (60, 200 + dy, 1020, 475 + dy), op=op)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    o1 = op * (1 - swap)
    if o1 > 0:
        text(d, (540, 236 + dy), "5 CROLLI DI BORSA", font("InterDisplay-Black", 80), WHITE, o1 * lin(t, 0.05, 0.2), anchor="ma")
        text(d, (540, 340 + dy), "Quanto è sceso il mercato…", font("InterDisplay-ExtraBold", 46), (255, 150, 158), o1 * lin(t, 0.3, 0.45), anchor="ma")
        text(d, (540, 398 + dy), "…e quanto è rimbalzato in 12 mesi", font("InterDisplay-ExtraBold", 46), (120, 240, 180), o1 * lin(t, 0.6, 0.75), anchor="ma")
    if swap > 0:
        o2 = op * swap
        yo = (1 - eout(swap)) * 30
        text(d, (540, 262 + yo), "Dopo ogni crollo,", font("InterDisplay-Black", 64), WHITE, o2, anchor="ma")
        text(d, (540, 340 + yo), "è arrivato il rimbalzo.", font("InterDisplay-Black", 64), GREEN, o2, anchor="ma")
    overlay(frame, lay)

def row(frame, t, k):
    name, years, dd, rb = ROWS[k]
    s = T_ROW0 + T_STEP * k
    a = lin(t, s, s + 0.28)
    if a <= 0: return
    op = clamp(a * 2.5)
    xo = (1 - eback(a, 1.25)) * 700
    y = RY0 + k * (RH + RG)
    box = (RX0 + xo, y, RX1 + xo, y + RH)
    liquid_glass(frame, box, r=34, op=op)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    X = RX0 + xo
    # index badge
    d.ellipse([X + 26, y + RH / 2 - 26, X + 78, y + RH / 2 + 26], fill=GOLD + (int(255 * op),))
    d.text((X + 52, y + RH / 2 + 1), str(k + 1), font=font("InterDisplay-Black", 32), fill=(18, 18, 18, int(255 * op)), anchor="mm")
    # name + years
    fn = fit_font("InterDisplay-Black", name, 340, 42, 28)
    text(d, (X + 100, y + 24), name, fn, WHITE, op)
    text(d, (X + 100, y + 78), years, font("InterDisplay-ExtraBold", 32), GOLD, op)
    # numbers appear directly with a quick pop
    p = lin(t, s + 0.12, s + 0.32)
    sc = 1 + 0.18 * (1 - eout(p)) if p < 1 else 1
    fnum = font("InterDisplay-Black", 50 * sc)
    fl = font("Inter-Bold", 19)
    cx1, cx2 = X + 563, X + 785
    text(d, (cx1, y + 22), "CALO MAX", fl, (225, 228, 238), op, anchor="ma")
    text(d, (cx1, y + 52 - (sc - 1) * 22), "−" + itn(dd, 1) + "%", fnum, RED, op * clamp(p * 3 + 0.2), anchor="ma")
    text(d, (cx2, y + 22), "RIMBALZO 12 MESI", fl, (225, 228, 238), op, anchor="ma")
    text(d, (cx2, y + 52 - (sc - 1) * 22), "+" + itn(rb, 1) + "%", fnum, GREEN, op * clamp(p * 3 + 0.2), anchor="ma")
    d.line([(X + 452, y + 22), (X + 452, y + RH - 22)], fill=(255, 255, 255, int(60 * op)), width=2)
    overlay(frame, lay)

def flash(arr, t):
    for k in range(len(ROWS)):
        s = T_ROW0 + T_STEP * k
        if s <= t < s + 0.07:
            a = 0.10 * (1 - lin(t, s, s + 0.07))
            return arr * (1 - a) + 255 * a
    return arr

def render_frame(src, i):
    t = i / FPS
    img = bg_transform(src, t)
    arr = np.asarray(img).astype(np.float32) * VIG
    arr = flash(arr, t)
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    header(frame, t)
    for k in range(len(ROWS)):
        row(frame, t, k)
    footnote(frame, t)
    return frame

def footnote(frame, t):
    a = lin(t, 0.8, 1.1)
    if a <= 0: return
    y = RY0 + len(ROWS) * (RH + RG) + 4
    liquid_glass(frame, (RX0, y, RX1, y + 50), r=25, op=a, tint_a=150)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    text(d, ((RX0 + RX1) / 2, y + 25), "Fonte: S&P 500, prezzi di chiusura · rimbalzo = 12 mesi dal minimo · non è consulenza", font("Inter-Medium", 19), (230, 234, 242), a, anchor="mm", shadow_=False)
    overlay(frame, lay)
def main():
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", BG, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = None
    if ONLY is None:
        enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    i = 0; fs = W * H * 3
    while True:
        buf = dec.stdout.read(fs)
        if len(buf) < fs: break
        if ONLY is None or i in ONLY:
            src = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)
            fr = render_frame(src, i)
            if ONLY is None: enc.stdin.write(fr.tobytes())
            else: fr.save(f"{OUT}_{i:04d}.jpg", quality=90)
        if ONLY is not None and i >= max(ONLY): break
        i += 1
        if i % 100 == 0: print("frame", i, file=sys.stderr)
    dec.kill()
    if enc: enc.stdin.close(); enc.wait()

main()
