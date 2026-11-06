"""Renderer del reel 1080x1920 @30fps: grafica, grafici animati e sottotitoli karaoke.

Uso: python3 render.py <build_dir> [--frames a:b] [--still t1,t2,...]
Legge timing.json (generato da tts.py) e invia i frame RGB a ffmpeg.
"""
import json, math, sys, subprocess, functools, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = sys.argv[1]
W, H, FPS = 1080, 1920, 30
T = json.load(open(f'{B}/timing.json'))
DUR = T['duration']
LINES, WORDS = T['lines'], T['words']

# ------------------------------------------------------------------ stile
FD = '/usr/share/fonts/opentype/inter/'
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
BG1, BG2 = (9, 13, 30), (20, 28, 60)
AMBER = (255, 184, 48)
GREEN = (34, 214, 150)
WHITE = (255, 255, 255)
MUTED = (150, 160, 190)
HL = (255, 222, 40)       # parola attiva karaoke
RED = (255, 84, 84)

@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype(FD + name, size)

@functools.lru_cache(None)
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new('RGBA', (160, 160))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    r = size / max(im.size)
    return im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)

# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, d): return clamp((t - t0) / d) if d > 0 else float(t >= t0)
def ease_out(x): return 1 - (1 - x) ** 3
def ease_io(x): return 3 * x * x - 2 * x * x * x
def back_out(x, s=1.7):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, x): return a + (b - a) * x

# ------------------------------------------------------------------ tempi delle scene
SC = {}
for l in LINES:
    s = SC.setdefault(l['scene'], {'s': l['s'], 'e': l['e'], 'lines': []})
    s['e'] = l['e']; s['lines'].append(l)
order = list(dict.fromkeys(l['scene'] for l in LINES))
for i, k in enumerate(order):
    SC[k]['next'] = SC[order[i + 1]]['s'] if i + 1 < len(order) else DUR + 1

def word_t(text, scene=None, default=None):
    """Istante d'inizio della prima parola che contiene `text` (opz. nella scena)."""
    for w in WORDS:
        if text.lower() in w['w'].lower() and (scene is None or LINES[w['line']]['scene'] == scene):
            return w['s']
    return default

def vis(t, t0, t1, fin=0.35, fout=0.25):
    """Alpha di un elemento visibile tra t0 e t1 con fade in/out."""
    return ease_out(prog(t, t0, fin)) * (1 - prog(t, t1 - fout, fout))

# ------------------------------------------------------------------ primitive di disegno
def layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))

def paste_alpha(base, im, xy, a):
    if a <= 0.003: return
    if a < 0.999:
        im = im.copy(); al = im.getchannel('A').point(lambda v: int(v * a)); im.putalpha(al)
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))

def text_img(txt, fnt, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0), shadow=True):
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    bb = d.textbbox((0, 0), txt, font=fnt, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 24, bb[3] - bb[1] + 24
    im = Image.new('RGBA', (w, h))
    if shadow:
        sh = Image.new('RGBA', (w, h))
        ImageDraw.Draw(sh).text((12 - bb[0], 16 - bb[1]), txt, font=fnt, fill=(0, 0, 0, 150),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((12 - bb[0], 12 - bb[1]), txt, font=fnt, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im

@functools.lru_cache(4096)
def ctext(txt, fname, size, fill=WHITE, stroke=0, shadow=True):
    return text_img(txt, font(fname, size), fill, stroke, (0, 0, 0), shadow)

def draw_text(base, txt, cx, cy, fname, size, fill=WHITE, a=1.0, scale=1.0, stroke=0, anchor='c', shadow=True):
    im = ctext(txt, fname, size, fill, stroke, shadow)
    if abs(scale - 1) > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    x = cx - im.width / 2 if anchor == 'c' else (cx if anchor == 'l' else cx - im.width)
    paste_alpha(base, im, (x, cy - im.height / 2), a)
    return im.width

def draw_emoji(base, ch, cx, cy, size, a=1.0):
    im = emoji(ch, int(size))
    paste_alpha(base, im, (cx - im.width / 2, cy - im.height / 2), a)

@functools.lru_cache(256)
def rrect(w, h, r, fill, outline=None, ow=0):
    w, h = max(int(w), 4), max(int(h), 4); r = min(r, h // 2, w // 2)
    im = Image.new('RGBA', (int(w), int(h)))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, int(w) - 1, int(h) - 1), r, fill=fill, outline=outline, width=ow)
    return im

@functools.lru_cache(64)
def glow(w, h, color, rad=40, alpha=110):
    pad = rad * 2
    im = Image.new('RGBA', (int(w) + 2 * pad, int(h) + 2 * pad))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + int(w), pad + int(h)), 30, fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(rad)), pad

def card(base, cx, cy, w, h, color, a=1.0, border=None, glow_on=True, r=36):
    if glow_on and border:
        g, pad = glow(w, h, border)
        paste_alpha(base, g, (cx - w / 2 - pad, cy - h / 2 - pad), a * 0.8)
    paste_alpha(base, rrect(w, h, r, color, border, 4 if border else 0), (cx - w / 2, cy - h / 2), a)

def pill(base, txt, cx, cy, bg, fg=(10, 12, 25), size=34, a=1.0, scale=1.0):
    f = font('Inter-Black.otf', size)
    tw = ImageDraw.Draw(Image.new('L', (1, 1))).textlength(txt, font=f)
    w, h = (tw + 56) * scale, (size + 30) * scale
    paste_alpha(base, rrect(int(w), int(h), int(h / 2), bg + (255,)), (cx - w / 2, cy - h / 2), a)
    draw_text(base, txt, cx, cy - 2 * scale, 'Inter-Black.otf', size, fg, a, scale, shadow=False)

# ------------------------------------------------------------------ sfondo
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    g = np.clip(y * 0.9 + 0.1 * x, 0, 1)
    arr = np.zeros((H, W, 3))
    for c in range(3):
        arr[..., c] = BG1[c] * (1 - g) + BG2[c] * g
    # vignettatura
    v = 1 - 0.35 * (((x - 0.5) * 1.4) ** 2 + ((y - 0.45) * 1.1) ** 2)
    arr *= np.clip(v, 0.55, 1)[..., None]
    # rumore fine anti-banding
    arr += np.random.default_rng(1).normal(0, 1.4, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
BG = make_bg()

@functools.lru_cache(8)
def blob(color, r):
    im = Image.new('RGBA', (r * 4, r * 4))
    ImageDraw.Draw(im).ellipse((r, r, 3 * r, 3 * r), fill=color + (70,))
    return im.filter(ImageFilter.GaussianBlur(r * 0.6))

def blob_mix(t):
    """Colore dominante dei bagliori a seconda della scena (ambra = buono, verde = MSCI)."""
    s = scene_at(t)
    if s in ('bfp', 'bfp18'): return 1.0, 0.25
    if s in ('msci',): return 0.2, 1.0
    if s in ('vs18', 'vs30', 'cta'): return 0.55, 1.0
    return 0.7, 0.7

def scene_at(t):
    cur = order[0]
    for k in order:
        if t >= SC[k]['s'] - 0.15: cur = k
    return cur

# ------------------------------------------------------------------ dati finanziari (stima, vedi README)
P0 = 5000
def bfp_net(y):
    y = min(y, 18)  # alla scadenza (18 anni) gli interessi si fermano
    g = P0 * 1.04 ** y
    return P0 + (g - P0) * 0.875
def etf_net(y):
    v = P0 * (1.068 * 0.998) ** y  # 7% lordo - TER 0,2%, - bollo 0,2% annuo
    return P0 + (v - P0) * 0.74
# valori chiave arrotondati mostrati a video
V_BFP18, V_ETF18, V_ETF30 = 9500, 13000, 26400

def eur(v):
    return '€' + f'{int(round(v)):,}'.replace(',', '.')

# ------------------------------------------------------------------ elementi fissi
def header(base, t):
    a = ease_out(prog(t, 0.0, 0.35))
    y = 250
    x0 = W / 2
    # "BUONO POSTALE  vs  MSCI WORLD"
    f = 'Inter-Black.otf'; s = 46
    wa = ctext('BUONO POSTALE', f, s, AMBER).width
    wv = ctext('vs', f, s, WHITE).width
    wm = ctext('MSCI WORLD', f, s, GREEN).width
    tot = wa + wv + wm - 30
    x = x0 - tot / 2
    sl = (1 - a) * -30
    draw_text(base, 'BUONO POSTALE', x, y + sl, f, s, AMBER, a, anchor='l'); x += wa - 15
    draw_text(base, 'vs', x, y + sl, f, s, WHITE, a, anchor='l'); x += wv - 15
    draw_text(base, 'MSCI WORLD', x, y + sl, f, s, GREEN, a, anchor='l')
    draw_text(base, '€5.000 alla nascita · 18 anni (e oltre)', x0, y + 58 + sl, 'Inter-SemiBold.otf', 30, MUTED, a)
    # barra di avanzamento
    pw = 760; px = (W - pw) / 2
    paste_alpha(base, rrect(pw, 8, 4, (255, 255, 255, 40)), (px, y + 100), a)
    p = clamp(t / (SC['cta']['e']))
    if p > 0.01:
        paste_alpha(base, rrect(max(8, int(pw * p)), 8, 4, HL + (255,)), (px, y + 100), a)

def disclaimer(base, t):
    a = vis(t, SC['bfp']['s'], DUR + 5, 0.6)
    lines = ['*Stime al netto di tasse e costi. Buono minori: ~4% lordo/anno (serie 2026),',
             'tassazione 12,5%. ETF MSCI World: ipotesi 7% lordo/anno, costi 0,2% +',
             'bollo 0,2%/anno, tassazione 26%. Rendimenti passati non garantiscono',
             'quelli futuri. Contenuto informativo, non è consulenza finanziaria.']
    for i, l in enumerate(lines):
        draw_text(base, l, W / 2, 1470 + i * 32, 'Inter-Medium.otf', 23, (120, 130, 160), a * 0.95, shadow=False)

# ------------------------------------------------------------------ scena: hook
def scene_hook(base, t):
    sc = SC['hook']; t_q = word_t('Dove', 'hook')
    a = vis(t, 0, t_q + 0.05, 0.01, 0.3)
    if a > 0:
        # famiglia -> bimba
        for i, (ch, dx) in enumerate([('👴', -250), ('👵', -130)]):
            p = back_out(prog(t, 0.05 + i * 0.12, 0.45))
            draw_emoji(base, ch, W / 2 + dx, 560, 120 * p, a)
        pa = ease_out(prog(t, 0.35, 0.4))
        draw_emoji(base, '➡️', W / 2 + 25 + 20 * pa, 560, 80, a * pa)
        p = back_out(prog(t, word_t('Sofia', 'hook') - 0.1, 0.5))
        draw_emoji(base, '👶', W / 2 + 190, 560, 150 * p, a)
        # contatore €5.000
        c = ease_out(prog(t, 0.15, 1.3))
        val = int(round(5000 * c / 50) * 50)
        sc_pop = 1 + 0.08 * math.sin(math.pi * prog(t, 1.3, 0.35))
        g, pad = glow(560, 170, AMBER, 60, 70)
        paste_alpha(base, g, (W / 2 - 280 - pad, 800 - 85 - pad), a * c)
        draw_text(base, eur(val), W / 2, 800, 'InterDisplay-Black.otf', 210, WHITE, a, sc_pop)
        draw_text(base, 'per la nipotina Sofia, appena nata', W / 2, 960, 'Inter-Bold.otf', 44, MUTED,
                  a * ease_out(prog(t, 0.9, 0.5)))
    # "Dove li mette?" -> due strade
    a2 = vis(t, t_q - 0.05, sc['next'], 0.25)
    if a2 > 0:
        for i, (lab, sub, col, ch, dx) in enumerate([('BUONO', 'POSTALE', AMBER, '📮', -250),
                                                       ('MSCI', 'WORLD', GREEN, '🌍', 250)]):
            p = back_out(prog(t, t_q + i * 0.12, 0.5))
            cx = W / 2 + dx * p
            card(base, cx, 760, 400, 470, (18, 24, 48, 245), a2, border=col)
            draw_emoji(base, ch, cx, 650, 130, a2)
            draw_text(base, lab, cx, 790, 'Inter-Black.otf', 64, col, a2)
            draw_text(base, sub, cx, 860, 'Inter-Black.otf', 48, WHITE, a2)
        q = back_out(prog(t, t_q + 0.25, 0.4))
        bob = math.sin(t * 7) * 6
        g, pad = glow(120, 120, HL, 30, 90)
        paste_alpha(base, g, (W / 2 - 60 - pad, 760 - 60 - pad + bob), a2 * q)
        draw_text(base, '?', W / 2, 760 + bob, 'InterDisplay-Black.otf', 170, HL, a2, max(q, 0.01))

# ------------------------------------------------------------------ scena: buono (strada 1)
def info_rows(base, t, rows, col, a, y0=830):
    for i, (t0, ch, txt) in enumerate(rows):
        p = ease_out(prog(t, t0, 0.4))
        if p <= 0: continue
        y = y0 + i * 125
        x = 150 + (1 - p) * 60
        card(base, W / 2 + (1 - p) * 60, y, 800, 104, (255, 255, 255, 18), a * p, glow_on=False, r=26)
        draw_emoji(base, ch, x + 50, y, 62, a * p)
        draw_text(base, txt, x + 110, y, 'Inter-ExtraBold.otf', 46, WHITE, a * p, anchor='l')

def scene_bfp(base, t):
    sc = SC['bfp']; a = vis(t, sc['s'] - 0.1, sc['next'] + 0.05)
    if a <= 0: return
    p = back_out(prog(t, sc['s'], 0.45))
    pill(base, 'STRADA 1', W / 2, 450, AMBER, a=a, scale=max(p, 0.01))
    draw_text(base, 'Buono Fruttifero', W / 2, 560, 'InterDisplay-Black.otf', 84, WHITE, a * ease_out(prog(t, sc['s'] + 0.1, 0.4)))
    draw_text(base, 'Postale per Minori', W / 2, 655, 'InterDisplay-Black.otf', 84, AMBER, a * ease_out(prog(t, sc['s'] + 0.2, 0.4)))
    rows = [(word_t('Garantito'), '🛡️', 'Garantito dallo Stato'),
            (word_t('4%'), '📈', 'Circa 4% lordo l\'anno*'),
            (word_t('4%') + 0.9, '🎂', 'Scade ai 18 anni')]
    info_rows(base, t, rows, AMBER, a)

# ------------------------------------------------------------------ scena: MSCI (strada 2)
DOTS = None
def scene_msci(base, t):
    global DOTS
    sc = SC['msci']; a = vis(t, sc['s'] - 0.1, sc['next'] + 0.05)
    if a <= 0: return
    p = back_out(prog(t, sc['s'], 0.45))
    pill(base, 'STRADA 2', W / 2, 450, GREEN, a=a, scale=max(p, 0.01))
    draw_text(base, 'ETF MSCI World', W / 2, 560, 'InterDisplay-Black.otf', 92, WHITE, a * ease_out(prog(t, sc['s'] + 0.1, 0.4)))
    draw_text(base, 'un solo fondo, le grandi aziende di 23 Paesi', W / 2, 640, 'Inter-SemiBold.otf', 38, MUTED,
              a * ease_out(prog(t, sc['s'] + 0.3, 0.4)))
    # griglia di ~1.300 puntini = aziende, si accendono a ondate
    t0 = word_t('oltre', 'msci')
    if DOTS is None:
        rng = random.Random(3); cols, rows = 52, 25
        DOTS = [(i, j, rng.random()) for j in range(rows) for i in range(cols)]
    cols, rows = 52, 25; gx0, gy0, step = 132, 720, 16
    pg = prog(t, t0 - 0.2, 1.6)
    lay = Image.new('RGBA', (cols * step + 20, rows * step + 20)); d = ImageDraw.Draw(lay)
    for i, j, r in DOTS:
        on = (i / cols * 0.6 + r * 0.4) < pg * 1.05
        c = GREEN + (255,) if on else (255, 255, 255, 30)
        d.ellipse((10 + i * step, 10 + j * step, 10 + i * step + 9, 10 + j * step + 9), fill=c)
    paste_alpha(base, lay, (gx0 - 10, gy0 - 10), a)
    n = int(1300 * ease_out(pg))
    pc = back_out(prog(t, t0 + 0.3, 0.5))
    if pc > 0:
        card(base, W / 2, 1155, 620, 110, (10, 16, 34, 240), a, border=GREEN)
        draw_text(base, f'{n:,}+ aziende'.replace(',', '.'), W / 2, 1153, 'InterDisplay-Black.otf', 62, GREEN, a, max(pc, 0.01))

# ------------------------------------------------------------------ grafico (buono vs ETF)
CX0, CX1, CY0, CY1 = 170, 960, 540, 1090   # area del grafico

def chart(base, t):
    s1, s2, s3 = SC['bfp18'], SC['vs18'], SC['vs30']
    a = max(vis(t, s1['s'] - 0.1, s1['next'] + 0.05), vis(t, s2['s'] - 0.1, s3['next'] + 0.3))
    if a <= 0: return
    # domini animati
    px = ease_io(prog(t, s3['s'] - 0.1, 1.0))
    xmax = lerp(18, 30, px)
    ymax = lerp(14000, 28000, px)
    def X(y): return CX0 + (CX1 - CX0) * y / xmax
    def Y(v): return CY1 - (CY1 - CY0) * v / ymax
    lay = layer(); d = ImageDraw.Draw(lay)
    # griglia
    step = 5000 if ymax > 16000 else 2500
    v = 0
    while v <= ymax + 1:
        yy = Y(v); d.line((CX0, yy, CX1, yy), fill=(255, 255, 255, 28), width=2)
        lab = '€0' if v == 0 else f'€{v // 1000}k' if v % 1000 == 0 else f'€{v / 1000:.1f}k'.replace('.', ',')
        d.text((CX0 - 18, yy), lab, font=font('Inter-SemiBold.otf', 26), fill=MUTED + (255,), anchor='rm')
        v += step
    for yr in ([0, 6, 12, 18] if xmax < 24 else [0, 6, 12, 18, 24, 30]):
        xx = X(yr)
        if xx <= CX1 + 2:
            d.text((xx, CY1 + 26), f'{yr} anni' if yr else 'nascita', font=font('Inter-SemiBold.otf', 26),
                   fill=(MUTED if yr != 18 else WHITE) + (255,), anchor='mm')
    xx18 = X(18)
    d.line((xx18, CY0 - 10, xx18, CY1), fill=(255, 255, 255, 60), width=2)
    # linee
    def series(fn, y_end, p_end):
        pts = []; n = 90
        for k in range(n + 1):
            yr = y_end * k / n
            if yr > p_end: break
            pts.append((X(yr), Y(fn(yr))))
        if p_end < y_end and pts: pts.append((X(p_end), Y(fn(p_end))))
        return pts
    def stroke(pts, col, wdt=10, dash=False):
        if len(pts) < 2: return
        if not dash:
            d.line(pts, fill=col + (255,), width=wdt, joint='curve')
        else:
            for k in range(0, len(pts) - 1, 2):
                d.line(pts[k:k + 2], fill=col + (200,), width=wdt - 3)
    # buono: 0->18 durante bfp18, poi piatto (fermo) 18->30 in vs30
    pb = ease_io(prog(t, s1['s'] + 0.2, 2.6))
    bpts = series(bfp_net, 18, 18 * pb)
    # area sotto la curva ETF
    pe = ease_io(prog(t, s2['s'] + 0.1, 3.4))
    pe30 = ease_io(prog(t, s3['s'] + 0.6, 2.6))
    ye = 18 * pe + 12 * pe30
    epts = series(etf_net, 30, ye) if pe > 0 else []
    if len(epts) > 1:
        poly = epts + [(epts[-1][0], CY1), (epts[0][0], CY1)]
        area = Image.new('RGBA', (W, H)); ImageDraw.Draw(area).polygon(poly, fill=GREEN + (40,))
        lay.alpha_composite(area)
    bpoly = bpts + [(bpts[-1][0], CY1), (bpts[0][0], CY1)] if len(bpts) > 1 else None
    if bpoly:
        area = Image.new('RGBA', (W, H)); ImageDraw.Draw(area).polygon(bpoly, fill=AMBER + (34,))
        lay.alpha_composite(area)
    stroke(bpts, AMBER)
    if pe30 > 0:
        flat = [(X(18 + 12 * k / 30), Y(bfp_net(18))) for k in range(int(30 * pe30) + 1)]
        stroke(flat, (170, 150, 110), 9, dash=True)
    stroke(epts, GREEN, 11)
    # punto finale
    for pts, col in ((bpts, AMBER), (epts, GREEN)):
        if len(pts) > 1:
            x, y = pts[-1]; r = 15
            d.ellipse((x - r - 8, y - r - 8, x + r + 8, y + r + 8), fill=col + (60,))
            d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,), outline=(255, 255, 255, 255), width=4)
    paste_alpha(base, lay, (0, 0), a)
    # legenda
    ly = 1170
    for i, (txt, col) in enumerate((('Buono minori', AMBER), ('ETF MSCI World', GREEN))):
        cx = W / 2 - 200 + i * 400
        if i == 1 and pe <= 0: continue
        paste_alpha(base, rrect(26, 26, 13, col + (255,)), (cx - 130, ly - 13), a)
        draw_text(base, txt, cx - 95, ly, 'Inter-Bold.otf', 32, WHITE, a, anchor='l')
    # etichette valori
    if pb > 0.98:
        p = back_out(prog(t, s1['s'] + 2.75, 0.45))
        x, y = X(18), Y(bfp_net(18))
        lx = min(x - 120, CX1 - 150) if xmax < 24 else x
        bubble(base, eur(V_BFP18), lx, y + 85, AMBER, a, p)
    t_stop = word_t('fermano', 'bfp18')
    if t_stop and t < s1['next']:
        p = back_out(prog(t, t_stop - 0.1, 0.45))
        if p > 0:
            card(base, X(18) - 210, CY0 - 40, 380, 92, (60, 16, 20, 235), a * min(1, p * 2), border=RED)
            draw_emoji(base, '⛔', X(18) - 355, CY0 - 40, 48, a * min(1, p * 2))
            draw_text(base, 'Interessi stop', X(18) - 185, CY0 - 40, 'Inter-Black.otf', 40, WHITE, a, max(p, 0.01))
    if pe > 0.98 and pe30 <= 0:
        p = back_out(prog(t, s2['s'] + 3.55, 0.45))
        bubble(base, eur(V_ETF18), X(18) - 150, Y(etf_net(18)) - 70, GREEN, a, p)
        t_n = word_t('netti', 'vs18')
        pd = back_out(prog(t, t_n - 0.1, 0.45))
        if pd > 0:
            card(base, 440, CY0 + 110, 500, 106, (10, 40, 32, 240), a, border=GREEN)
            draw_text(base, '+€3.500  (+37%)', 440, CY0 + 110, 'InterDisplay-Black.otf', 56, GREEN, a, max(pd, 0.01))
    if pe30 > 0.98:
        p = back_out(prog(t, s3['s'] + 3.25, 0.45))
        bubble(base, eur(V_ETF30), X(30) - 120, Y(etf_net(30)) + 85, GREEN, a, p)
        pf = ease_out(prog(t, s3['s'] + 1.2, 0.5))
        draw_text(base, 'fermo', X(24), Y(bfp_net(18)) - 42, 'Inter-Bold.otf', 30, (190, 170, 120), a * pf)
        pm = back_out(prog(t, s3['s'] + 3.6, 0.5))
        if pm > 0:
            card(base, 420, CY0 + 60, 480, 140, (10, 40, 32, 245), a, border=GREEN)
            draw_text(base, '×2,8', 315, CY0 + 60, 'InterDisplay-Black.otf', 96, GREEN, a, max(pm, 0.01))
            draw_text(base, 'rispetto', 520, CY0 + 38, 'Inter-Black.otf', 36, WHITE, a * clamp(pm))
            draw_text(base, 'al buono', 520, CY0 + 82, 'Inter-Black.otf', 36, WHITE, a * clamp(pm))
    # titoletto sopra il grafico
    draw_text(base, 'Valore netto dei €5.000*', W / 2, 410, 'Inter-Bold.otf', 34, MUTED, a)

def bubble(base, txt, cx, cy, col, a, p):
    if p <= 0: return
    w = ctext(txt, 'InterDisplay-Black.otf', 58).width + 20
    card(base, cx, cy, w, 96, col + (255,), a * min(1, p * 2), glow_on=False, r=48)
    draw_text(base, txt, cx, cy - 2, 'InterDisplay-Black.otf', 58, (10, 12, 25), a, max(p, 0.01), shadow=False)

# ------------------------------------------------------------------ scena finale (rischio + CTA)
def volatile_path():
    rng = np.random.default_rng(7); n = 120
    r = rng.normal(0.0, 0.03, n); r = r - r.mean() + 0.012
    r[38:45] = [-0.07, -0.09, -0.06, -0.05, 0.02, -0.06, -0.03]  # crolli illustrativi
    r[82:85] = [-0.07, -0.05, -0.04]
    v = np.cumprod(1 + r); return v
VP = volatile_path()

def scene_cta(base, t):
    sc = SC['cta']; l1, l2, l3 = sc['lines']
    # 1) volatilità
    a = vis(t, sc['s'] - 0.1, l2['s'] + 0.1)
    if a > 0:
        draw_text(base, 'Crolli? Ci saranno.', W / 2, 470, 'InterDisplay-Black.otf', 76, WHITE, a)
        p = ease_io(prog(t, sc['s'] + 0.1, 2.2))
        n = max(2, int(len(VP) * p))
        x0, x1, y0, y1 = 140, 940, 600, 1100
        vmin, vmax = VP.min() * 0.95, VP.max() * 1.03
        pts = [(x0 + (x1 - x0) * i / (len(VP) - 1), y1 - (y1 - y0) * (VP[i] - vmin) / (vmax - vmin)) for i in range(n)]
        lay = layer(); d = ImageDraw.Draw(lay)
        for i in range(len(pts) - 1):
            col = RED if VP[i + 1] < VP[i] else GREEN
            d.line((pts[i], pts[i + 1]), fill=col + (255,), width=8)
        paste_alpha(base, lay, (0, 0), a)
        pc = back_out(prog(t, word_t('pazienza') - 0.1, 0.45))
        if pc > 0:
            pill(base, 'serve pazienza ⏳'.replace(' ⏳', ''), W / 2, 1170, HL, a=a, scale=max(pc, 0.01), size=40)
        draw_text(base, 'andamento illustrativo', W / 2, 560, 'Inter-Medium.otf', 24, MUTED, a * 0.8 * p)
    # 2) il tempo
    a = vis(t, l2['s'] - 0.05, l3['s'] + 0.05)
    if a > 0:
        p = back_out(prog(t, l2['s'], 0.5))
        draw_emoji(base, '⏳', W / 2, 600, 190 * max(p, 0.01), a)
        draw_text(base, 'Il TEMPO è', W / 2, 820, 'InterDisplay-Black.otf', 96, WHITE, a * ease_out(prog(t, l2['s'] + 0.1, 0.4)))
        draw_text(base, 'il regalo più', W / 2, 930, 'InterDisplay-Black.otf', 96, WHITE, a * ease_out(prog(t, l2['s'] + 0.3, 0.4)))
        draw_text(base, 'prezioso 🎁'.replace(' 🎁', ''), W / 2, 1040, 'InterDisplay-Black.otf', 110, HL, a * ease_out(prog(t, l2['s'] + 0.6, 0.4)))
    # 3) call to action
    a = vis(t, l3['s'] - 0.05, DUR + 5)
    if a > 0:
        p = back_out(prog(t, l3['s'], 0.5))
        draw_emoji(base, '👶', W / 2, 560, 170 * max(p, 0.01), a)
        draw_text(base, 'Giralo a chi ha', W / 2, 760, 'InterDisplay-Black.otf', 92, WHITE, a * ease_out(prog(t, l3['s'] + 0.1, 0.4)))
        draw_text(base, 'un bimbo in arrivo', W / 2, 865, 'InterDisplay-Black.otf', 92, HL, a * ease_out(prog(t, l3['s'] + 0.3, 0.4)))
        pp = back_out(prog(t, l3['s'] + 0.9, 0.5))
        if pp > 0:
            pulse = 1 + 0.04 * math.sin((t - l3['s']) * 6)
            for i, (ch, lab, col) in enumerate((('📲', 'Condividi', GREEN), ('🔖', 'Salva', AMBER))):
                cx = W / 2 - 200 + i * 400
                card(base, cx, 1030, 370, 110, (18, 24, 48, 245), a * clamp(pp), border=col)
                draw_emoji(base, ch, cx - 125, 1030, 56 * max(pp, 0.01) * pulse, a)
                draw_text(base, lab, cx + 30, 1030, 'Inter-Black.otf', 44, WHITE, a, max(pp, 0.01) * pulse)

# ------------------------------------------------------------------ sottotitoli karaoke
def build_chunks():
    chunks = []
    for li, l in enumerate(LINES):
        ws = [w for w in WORDS if w['line'] == li]
        cur = []
        for w in ws:
            cur.append(w)
            txt = ' '.join(x['w'] for x in cur)
            if len(cur) >= 3 or len(txt) >= 15 or w['w'][-1] in ',.:;?!':
                chunks.append(cur); cur = []
        if cur:
            if chunks and chunks[-1][0]['line'] == li and len(cur) == 1 and len(' '.join(x['w'] for x in chunks[-1] + cur)) < 20:
                chunks[-1] = chunks[-1] + cur
            else:
                chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        s = c[0]['s'] - 0.04
        nxt = chunks[i + 1][0]['s'] - 0.04 if i + 1 < len(chunks) else c[-1]['e'] + 0.6
        e = min(nxt, c[-1]['e'] + 0.5)
        out.append((s, e, c))
    return out
CHUNKS = build_chunks()

def clean(w):
    return w.strip(',.:;').upper()

def captions(base, t):
    for s, e, c in CHUNKS:
        if not (s <= t < e): continue
        cy = 1330; size = 84; fn = 'Inter-Black.otf'
        words = [clean(w['w']) for w in c]
        widths = [ctext(x, fn, size, WHITE, 9).width - 24 for x in words]
        gap = 30; tot = sum(widths) + gap * (len(words) - 1)
        sc0 = 0.92 + 0.08 * back_out(prog(t, s, 0.18))
        if tot > 980:
            size = int(size * 980 / tot); widths = [ctext(x, fn, size, WHITE, 9).width - 24 for x in words]
            tot = sum(widths) + gap * (len(words) - 1)
        x = W / 2 - tot / 2
        for w, txt, wd in zip(c, words, widths):
            active = w['s'] - 0.03 <= t < w['e'] + 0.02
            done = t >= w['e'] + 0.02
            if active:
                k = prog(t, w['s'] - 0.03, 0.12)
                scl = 1 + 0.08 * back_out(k) - 0.02 * k
                # box evidenziato dietro la parola attiva
                bw, bh = (wd + 20) * scl, 108 * scl
                paste_alpha(base, rrect(int(bw), int(bh), 22, (255, 222, 40, 255)), (x + wd / 2 - bw / 2, cy - bh / 2 + 4), 1)
                draw_text(base, txt, x + wd / 2, cy, fn, size, (12, 12, 20), 1, scl * sc0, 0, shadow=False)
            else:
                col = WHITE if done else (255, 255, 255)
                al = 1.0 if done else 0.7
                draw_text(base, txt, x + wd / 2, cy, fn, size, col, al, sc0, 9)
            x += wd + gap
        break

# ------------------------------------------------------------------ frame
def frame(t):
    im = BG.copy()
    ma, mg = blob_mix(t)
    b1 = blob(AMBER, 300); b2 = blob(GREEN, 320)
    paste_alpha(im, b1, (-350 + 120 * math.sin(t * 0.4), 300 + 90 * math.cos(t * 0.33)), ma)
    paste_alpha(im, b2, (W - 900 + 110 * math.cos(t * 0.37), 900 + 120 * math.sin(t * 0.29)), mg)
    header(im, t)
    scene_hook(im, t); scene_bfp(im, t); chart(im, t); scene_msci(im, t); scene_cta(im, t)
    disclaimer(im, t)
    captions(im, t)
    return im.convert('RGB')

if __name__ == '__main__':
    args = sys.argv[2:]
    if args and args[0] == '--still':
        for ts in args[1].split(','):
            frame(float(ts)).save(f'{B}/still_{float(ts):05.2f}.png')
        sys.exit()
    nf = int(DUR * FPS)
    a0, a1 = 0, nf
    if args and args[0] == '--frames':
        a0, a1 = map(int, args[1].split(':'))
    out = f'{B}/frames_{a0:05d}.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
                          '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(a0, min(a1, nf)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print('ok', out)
