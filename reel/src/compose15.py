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
HOOK = 1.2
SEG = 1.6
OUTRO = HOOK + SEG * len(CRISES)  # 12.4
TOTAL = 15.2

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
def bg_transform(img, t):
    # gentle push-in + punch-zoom at every segment start
    base = 1.03 + 0.05 * (t / TOTAL)
    punch = 0.0
    starts = [HOOK + SEG * k for k in range(len(CRISES))] + [OUTRO]
    for s in starts:
        if s - 0.001 <= t < s + 0.3:
            punch = 0.06 * (1 - eout(lin(t, s, s + 0.3)))
    if t < 0.35: punch = 0.10 * (1 - eout(lin(t, 0, 0.35)))
    z = base + punch
    cx, cy = 600, 760  # keep face area centred while zooming
    w, h = W / z, H / z
    x0 = clamp(cx - w * cx / W, 0, W - w); y0 = clamp(cy - h * cy / H, 0, H - h)
    out = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
    return out

def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.75)) ** 2)
    v = 1 - 0.28 * np.clip(d - 0.35, 0, 1) ** 1.4
    return v[..., None].astype(np.float32)
VIG = vignette()

# ---------------- elements ----------------
def progress(frame, t, idx_float):
    """7 story-like segments at top."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    n = len(CRISES); x0, x1, y = 60, 1020, 168; gap = 10
    sw = (x1 - x0 - gap * (n - 1)) / n
    op = lin(t, HOOK - 0.15, HOOK) * (1 - lin(t, OUTRO + 0.1, OUTRO + 0.3))
    if op <= 0: return
    for k in range(n):
        xa = x0 + k * (sw + gap)
        d.rounded_rectangle([xa, y, xa + sw, y + 8], 4, fill=(255, 255, 255, int(90 * op)))
        fill = clamp(idx_float - k)
        if fill > 0:
            d.rounded_rectangle([xa, y, xa + max(8, sw * fill), y + 8], 4, fill=GOLD + (int(255 * op),))
    overlay(frame, lay)

def sparkline(d, box, dd, prog, op):
    """schematic: peak -> trough (red) -> today (green)."""
    x0, y0, x1, y1 = box
    if op <= 0: return
    h = y1 - y0
    pk = (x0 + 8, y0 + h * 0.30)
    depth = 0.30 + 0.62 * min(1, abs(dd) / 90)
    tr = (x0 + (x1 - x0) * 0.36, y0 + h * 0.30 + (h * 0.66) * (abs(dd) / 90))
    end = (x1 - 8, y0 + 6)
    def seg(a, b, p, col, wdt=7):
        if p <= 0: return
        pts = []
        for i in range(25):
            u = i / 24 * p
            # slight wobble for "market" look
            wob = math.sin(u * 19 + a[0]) * 5 * math.sin(u * math.pi)
            pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + wob))
        d.line(pts, fill=col + (int(255 * op),), width=wdt, joint="curve")
        return pts[-1]
    # dashed reference line at peak
    for xx in range(int(x0), int(x1), 16):
        d.line([(xx, pk[1]), (xx + 7, pk[1])], fill=(255, 255, 255, int(70 * op)), width=2)
    p1 = clamp(prog * 2); p2 = clamp(prog * 2 - 1)
    e = seg(pk, tr, eout(p1), RED)
    if e and p2 <= 0:
        d.ellipse([e[0] - 9, e[1] - 9, e[0] + 9, e[1] + 9], fill=RED + (int(255 * op),))
    if p2 > 0:
        d.ellipse([tr[0] - 9, tr[1] - 9, tr[0] + 9, tr[1] + 9], fill=RED + (int(255 * op),))
        e2 = seg(tr, end, eout(p2), GREEN)
        d.ellipse([e2[0] - 10, e2[1] - 10, e2[0] + 10, e2[1] + 10], fill=GREEN + (int(255 * op),))


def crisis_scene(frame, t, k):
    name, years, dd, up, idx = CRISES[k]
    s = HOOK + SEG * k
    lt = t - s
    # persistent containers: enter once, leave at outro
    tin = lin(t, HOOK, HOOK + 0.25)
    opc = clamp(tin * 3) * (1 - lin(t, OUTRO - 0.1, OUTRO))
    slide = (1 - eback(tin, 1.3)) * -1100
    rise = (1 - eback(lin(t, HOOK + 0.05, HOOK + 0.3), 1.2)) * 380
    bx = (50 + slide, 205, 1030 + slide, 505)
    glass(frame, bx, op=opc)
    by0 = 1330 + rise
    glass(frame, (50, by0, 940, by0 + 345), op=opc)
    # per-segment content swap
    cin = lin(lt, 0.0, 0.16)
    cout = lin(lt, SEG - 0.09, SEG) if k < len(CRISES) - 1 else 0
    xo = (1 - eout(cin)) * 90 - cout * 60
    op = opc * clamp(cin * 2) * (1 - cout)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    X = bx[0] + xo
    chip = f"CRISI {k + 1}/{len(CRISES)}"
    fc = font("Inter-ExtraBold", 28)
    cw = fc.getlength(chip) + 36
    d.rounded_rectangle([bx[0] + 40, 236, bx[0] + 40 + cw, 280], 22, fill=GOLD + (int(255 * opc),))
    d.text((bx[0] + 40 + cw / 2, 258), chip, font=fc, fill=(20, 20, 20, int(255 * opc)), anchor="mm")
    text(d, (X + 40 + cw + 18, 258), idx, font("Inter-SemiBold", 28), GREY, op, anchor="lm", shadow_=False)
    fn = fit_font("InterDisplay-Black", name, 560, 70)
    text(d, (X + 40, 300), name, fn, WHITE, op, spacing=2)
    text(d, (X + 40, 300 + fn.size * 2 + 14), years, font("InterDisplay-ExtraBold", 40), GOLD, op)
    sparkline(d, (bx[0] + 640, 300, bx[0] + 940, 470), dd, lin(lt, 0.08, 1.0), op)
    # stats
    text(d, (90, by0 + 40), "DAL MASSIMO\nAL MINIMO", font("Inter-Bold", 25), GREY, opc, shadow_=False, spacing=4)
    text(d, (535, by0 + 40), "DAL MINIMO\nA OGGI", font("Inter-Bold", 25), GREY, opc, shadow_=False, spacing=4)
    d.line([(495, by0 + 40), (495, by0 + 252)], fill=(255, 255, 255, int(50 * opc)), width=2)
    d.rounded_rectangle([90, by0 + 240, 430, by0 + 252], 6, fill=(255, 255, 255, int(40 * opc)))
    d.rounded_rectangle([535, by0 + 240, 875, by0 + 252], 6, fill=(255, 255, 255, int(40 * opc)))
    colw = 445
    p_dd = eoutq(lin(lt, 0.08, 0.5))
    vdd = dd * p_dd
    shake = math.sin((lt - 0.5) * 120) * 6 if 0 < lt - 0.5 < 0.14 else 0
    fdd = fit_font("InterDisplay-Black", "−" + itn(dd, 1) + "%", colw - 70, 100)
    if p_dd > 0:
        text(d, (88 + shake + xo * 0.5, by0 + 128), "−" + itn(vdd, 1) + "%", fdd, RED, op)
        d.rounded_rectangle([90, by0 + 240, 90 + max(12, 340 * abs(vdd) / 100), by0 + 252], 6, fill=RED + (int(255 * op),))
    p_up = lin(lt, 0.45, 0.95)
    fup = fit_font("InterDisplay-Black", "+" + itn(up) + "%", colw - 80, 100)
    if p_up > 0:
        vup = up * eoutq(p_up)
        pop = 1 + 0.14 * math.sin(math.pi * lin(lt, 0.95, 1.15))
        fu = font("InterDisplay-Black", fup.size * pop) if pop > 1.001 else fup
        text(d, (533 + xo * 0.5, by0 + 128 + (fup.size - fu.size) * 0.5), "+" + itn(round(vup)) + "%", fu, GREEN, op)
        frac = min(1, math.log10(1 + vup / 100) / math.log10(1 + 116700 / 100)) if vup > 0 else 0
        d.rounded_rectangle([535, by0 + 240, 535 + max(12, 340 * max(frac, 0.04)), by0 + 252], 6, fill=GREEN + (int(255 * op),))
    d.line([(90, by0 + 280), (900, by0 + 280)], fill=(255, 255, 255, int(35 * opc)), width=1)
    text(d, (495, by0 + 296), f"{idx} · prezzi di chiusura · “oggi” = 20/11/2026", font("Inter-Medium", 23), GREY, op, anchor="ma", shadow_=False)
    overlay(frame, lay)

def hook_scene(frame, t):
    out = lin(t, HOOK - 0.1, HOOK)
    a = lin(t, 0.0, 0.22)
    op = clamp(a * 3) * (1 - out)
    sc = eback(a, 1.4)
    glass(frame, (60, 215, 1020, 215 + 330 * max(sc, 0.05)), op=op)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if sc > 0.6:
        text(d, (540, 262), "7 CROLLI DI BORSA", font("InterDisplay-Black", 82), WHITE, op * lin(t, 0.05, 0.2), anchor="ma")
        text(d, (540, 368), "che sembravano", font("InterDisplay-ExtraBold", 54), GREY, op * lin(t, 0.22, 0.34), anchor="ma")
        hl = lin(t, 0.36, 0.56)
        f2 = font("InterDisplay-Black", 64); s2 = "la fine del mondo."; w2 = f2.getlength(s2)
        if hl > 0:
            d.rounded_rectangle([540 - w2 / 2 - 18, 438, 540 - w2 / 2 - 18 + (w2 + 36) * eout(hl), 520], 14, fill=RED + (int(235 * op),))
            text(d, (540, 442), s2, f2, WHITE, op * clamp(hl * 2), anchor="ma")
    overlay(frame, lay)
    b = lin(t, 0.5, 0.7)
    opb = clamp(b * 3) * (1 - out)
    if opb > 0:
        y = 1430 + (1 - eback(b)) * 200
        glass(frame, (110, y, 970, y + 130), r=65, op=opb)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        text(d, (540, y + 34), "Quanto è risalito il mercato dopo?", font("Inter-Bold", 38), WHITE, opb, anchor="ma")
        text(d, (540, y + 82 + abs(math.sin(t * 9)) * 8), "Resta fino alla fine ↓", font("Inter-SemiBold", 30), GOLD, opb, anchor="ma")
        overlay(frame, lay)

def outro_scene(frame, t):
    rh = 58; y0 = 1085
    lt = t - OUTRO
    a = lin(lt, 0.0, 0.22)
    op = clamp(a * 3)
    dy = -(1 - eout(a)) * 300
    glass(frame, (60, 205 + dy, 1020, 475 + dy), op=op)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    text(d, (540, 240 + dy), "7 crisi.", font("InterDisplay-Black", 84), WHITE, op, anchor="ma")
    text(d, (540, 340 + dy), "7 recuperi.", font("InterDisplay-Black", 84), GREEN, lin(lt, 0.2, 0.34), anchor="ma")
    overlay(frame, lay)
    r_in = lin(lt, 0.25, 0.45)
    opr = clamp(r_in * 3)
    rows = list(reversed(CRISES))
    if opr > 0:
        glass(frame, (50, y0, 940, y0 + 140 + rh * len(rows)), op=opr, tint_a=185)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        fh = font("Inter-Bold", 22)
        text(d, (90, y0 + 30), "CRISI", fh, GREY, opr, shadow_=False)
        text(d, (690, y0 + 30), "CALO", fh, GREY, opr, anchor="ra", shadow_=False)
        text(d, (900, y0 + 30), "RIALZO", fh, GREY, opr, anchor="ra", shadow_=False)
        fr = font("Inter-SemiBold", 30); fb = font("InterDisplay-ExtraBold", 32)
        for i, (name, years, dd, up, idx) in enumerate(rows):
            ro = lin(lt, 0.32 + i * 0.06, 0.46 + i * 0.06) * opr
            yy = y0 + 72 + i * rh
            xo = (1 - eout(ro)) * 60
            text(d, (90 + xo, yy), years.split("–")[0] + "  " + name.replace("\n", " "), fr, WHITE, ro)
            text(d, (690 + xo, yy - 2), "−" + itn(dd, 1) + "%", fb, RED, ro, anchor="ra")
            text(d, (900 + xo, yy - 2), "+" + itn(up) + "%", fb, GREEN, ro, anchor="ra")
        dsc = lin(lt, 0.8, 1.0)
        text(d, (495, y0 + 84 + rh * len(rows)), "S&P 500 (1929: Dow Jones) · chiusure · “oggi” = 20/11/2026", font("Inter-Medium", 21), GREY, dsc, anchor="ma", shadow_=False)
        text(d, (495, y0 + 112 + rh * len(rows)), "Dati storici, non è consulenza. I rendimenti passati non garantiscono quelli futuri.", font("Inter-Medium", 19), GREY, dsc, anchor="ma", shadow_=False)
        overlay(frame, lay)
    c = lin(lt, 1.2, 1.45)
    if c > 0:
        y = 1660 + (1 - eback(c)) * 140
        pul = 1 + 0.03 * math.sin(lt * 9) * clamp((lt - 1.5) * 3)
        w2 = 860 * pul; h2 = 104 * pul
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([540 - w2 / 2, y, 540 + w2 / 2, y + h2], int(h2 / 2), fill=GOLD + (int(255 * clamp(c * 3)),))
        d.text((540, y + h2 / 2), "Salvalo per il prossimo crollo", font=font("InterDisplay-Black", 44 * pul), fill=(18, 18, 18, int(255 * clamp(c * 3))), anchor="mm")
        overlay(frame, lay)

def flash(arr, t):
    starts = [HOOK + SEG * k for k in range(len(CRISES))] + [OUTRO]
    for s in starts:
        if s <= t < s + 0.08:
            a = 0.16 * (1 - lin(t, s, s + 0.08))
            return arr * (1 - a) + 255 * a
    return arr

def render_frame(src, i):
    t = i / FPS
    img = bg_transform(src, t)
    arr = np.asarray(img).astype(np.float32) * VIG
    if t >= OUTRO:  # dim for outro legibility
        arr *= 1 - 0.28 * eout(lin(t, OUTRO, OUTRO + 0.3))
    elif t < HOOK:
        arr *= 0.92
    arr = flash(arr, t)
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if t < HOOK:
        hook_scene(frame, t)
    elif t < OUTRO:
        k = int((t - HOOK) // SEG)
        progress(frame, t, k + clamp((t - HOOK - SEG * k) / SEG))
        crisis_scene(frame, t, k)
    else:
        progress(frame, t, len(CRISES))
        outro_scene(frame, t)
    return frame

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
