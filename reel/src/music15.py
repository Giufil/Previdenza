"""Original royalty-free beat, 150 BPM, beat-synced to the reel timeline.
Outputs: music_full.wav (music+sfx), sfx_only.wav (impacts/ticks only, for use under an Instagram trending audio)."""
import numpy as np, wave
SR = 48000
DUR = 15.2
N = int(SR * DUR)
BEAT = 0.4
HOOK, SEG, NCR = 1.2, 1.6, 7
OUTRO = HOOK + SEG * NCR
rng = np.random.default_rng(7)

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.002, r=0.2, sus=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e
def add(buf, x, at, g=1.0):
    i = int(round(at * SR))
    if i < 0: x = x[-i:]; i = 0
    if i >= len(buf): return
    j = min(len(buf), i + len(x))
    buf[i:j] += g * x[:j - i]
def lp(x, a):  # one-pole lowpass, a in (0,1)
    y = np.empty_like(x); acc = 0.0
    # vectorised via cumulative filter approximation
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)
def hp(x, a):
    return x - lp(x, a)
def midi(m): return 440 * 2 ** ((m - 69) / 12)

# ------------- instruments -------------
def kick():
    t = t_(0.45)
    f = 45 + 110 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * 1.0 + 0.3 * np.sin(ph * 2) * np.exp(-t * 40)
def snare():
    t = t_(0.35)
    n = rng.standard_normal(len(t))
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    return 0.55 * hp(n, 0.25) * np.exp(-t * 14) + 0.4 * body
def clap():
    t = t_(0.3); out = np.zeros(len(t))
    n = hp(rng.standard_normal(len(t)), 0.3)
    for k, d in enumerate([0, 0.011, 0.022]):
        i = int(d * SR); out[i:] += n[:len(t) - i] * np.exp(-t[:len(t) - i] * (60 if k < 2 else 13))
    return out * 0.5
def hat(open_=False):
    t = t_(0.25 if open_ else 0.06)
    n = hp(rng.standard_normal(len(t)), 0.08)
    n = hp(n, 0.08)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.35
def bass808(f, d):
    t = t_(d)
    ph = 2 * np.pi * f * t
    x = np.tanh(1.8 * np.sin(ph)) * np.minimum(1, t / 0.005) * np.exp(-t * 1.2)
    rel = np.ones(len(t)); r = int(0.05 * SR); rel[-r:] = np.linspace(1, 0, r)
    return x * rel * 0.6
def pad(freqs, d):
    t = t_(d); x = np.zeros(len(t))
    for f in freqs:
        for det in (-0.12, 0, 0.12):
            ff = f * 2 ** (det / 12)
            saw = 2 * ((ff * t + rng.random()) % 1) - 1
            x += saw
    x = lp(x / (len(freqs) * 3), 0.06)
    a = np.minimum(1, t / 0.25); r = np.minimum(1, (d - t) / 0.3)
    return x * a * r * 0.32
def pluck(f, d=0.35):
    t = t_(d)
    x = (2 * ((f * t) % 1) - 1) * np.exp(-t * 9)
    return lp(x, 0.25) * 0.25
def impact():
    t = t_(1.6)
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-t * 6)) * t) * np.exp(-t * 2.2)
    n = lp(rng.standard_normal(len(t)), 0.05) * np.exp(-t * 3) * 0.8
    return (boom + n) * 0.9
def whoosh(d=0.45, rev=True):
    t = t_(d)
    n = rng.standard_normal(len(t))
    e = (t / d) ** 2.2 if rev else np.exp(-t * 6)
    # sweeping band: crude via mixing lowpass amounts
    lo = lp(n, 0.02); hi = hp(n, 0.2)
    mix = (t / d)
    return (lo * (1 - mix) * 3 + hi * mix) * e * 0.35
def tick(f=2400):
    t = t_(0.03)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 180) * 0.25
def ding(f=1320):
    t = t_(0.9)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.01 * t) + 0.25 * np.sin(2 * np.pi * f * 3 * t)
    return x * np.exp(-t * 5) * 0.22
def riser(d):
    t = t_(d)
    f = 200 * 2 ** (3 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (2 * ((ph / (2 * np.pi)) % 1) - 1) * 0.4 + hp(rng.standard_normal(len(t)), 0.1) * 0.6
    return x * (t / d) ** 2 * 0.3

def reverb(x, secs=1.8, wet=0.22):
    from scipy.signal import fftconvolve
    t = t_(secs)
    ir = rng.standard_normal(len(t)) * np.exp(-t * 3.5)
    ir = lp(ir, 0.3); ir /= np.sqrt((ir ** 2).sum())
    return x + wet * fftconvolve(x, ir)[:len(x)]

# ------------- arrangement -------------
music = np.zeros(N); drums = np.zeros(N); sfx = np.zeros(N); bass = np.zeros(N)
# chord progression per bar (1.6s = 4 beats): Am F C G  (i VI III VII)
prog = [(57, [57, 60, 64, 69]), (53, [53, 57, 60, 65]), (48, [55, 60, 64, 67]), (55, [55, 59, 62, 67])]
bar = 4 * BEAT
ORG = HOOK - bar
nb = int(np.ceil((DUR - ORG) / bar))
for b in range(nb):
    s = ORG + b * bar
    root, ch = prog[b % 4]
    add(music, pad([midi(m) for m in ch], bar + 0.25), s, 1.0)
    # arpeggio plucks in main section
    if HOOK - 0.01 <= s < OUTRO + 0.8:
        for k, m in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 12]):
            add(music, pluck(midi(m)), s + k * BEAT / 2, 0.8)
    # 808
    if s >= HOOK - 0.01:
        add(bass, bass808(midi(root - 24 if root > 50 else root - 12), bar * 0.62), s, 1.0)
        add(bass, bass808(midi(root - 24 if root > 50 else root - 12), bar * 0.3), s + 2.5 * BEAT, 0.8)
# drums: half-time trap
t = ORG
step = BEAT / 2  # 8ths
i = 0
while t < DUR - 0.01:
    beat_in_bar = round(((t - ORG) % bar) / BEAT, 6) % 4
    main = HOOK - 0.001 <= t < OUTRO
    outro_drums = OUTRO + 0.8 - 0.001 <= t < DUR - 0.6
    if main or outro_drums:
        if abs(beat_in_bar - 0) < 1e-6 or abs(beat_in_bar - 1.5) < 1e-6 or (abs(beat_in_bar - 3.5) < 1e-6 and int((t - ORG) / bar) % 2):
            add(drums, kick(), t, 1.0)
        if abs(beat_in_bar - 2) < 1e-6:
            add(drums, snare(), t, 0.8); add(drums, clap(), t, 0.7)
        add(drums, hat(), t, 0.7 if i % 2 == 0 else 0.45)
        # hat roll before each segment change
        nxt = HOOK + SEG * (np.floor((t - HOOK) / SEG) + 1)
        if main and 0 < nxt - t <= BEAT + 1e-6:
            for r in range(1, 4):
                add(drums, hat(), t + r * step / 4, 0.35)
    t = round(t + step, 6); i += 1
# hook: impact at 0, kick, riser into first crisis
add(sfx, impact(), 0.0, 1.0); add(drums, kick(), 0.0, 1.0)
add(sfx, riser(0.8), HOOK - 0.8, 0.8)
add(sfx, whoosh(0.25), 0.3, 0.5)  # highlight wipe
add(sfx, whoosh(0.3), 1.0, 0.0)
# per crisis
for k in range(NCR):
    s = HOOK + SEG * k
    add(sfx, impact(), s, 0.75 if k < NCR - 1 else 1.0)
    add(sfx, whoosh(0.22), s - 0.22, 0.6)
    for j in range(8):
        add(sfx, tick(1800 - j * 90), s + 0.08 + j * 0.05, 0.8)
    add(sfx, kick(), s + 0.5, 0.3)
    for j in range(9):
        add(sfx, tick(1500 + j * 140), s + 0.45 + j * 0.055, 0.8)
    add(sfx, ding(1320 if k < NCR - 1 else 1760), s + 0.95, 0.9 if k < NCR - 1 else 1.4)
# outro
add(sfx, impact(), OUTRO, 1.1)
add(sfx, ding(990), OUTRO + 0.2, 0.7)
for j in range(7):
    add(sfx, tick(2000), OUTRO + 0.32 + j * 0.06, 1.0)
add(sfx, ding(1760), OUTRO + 1.2, 1.0)
# drum dropout at outro start (filter music for 1.6s)
o0, o1 = int(OUTRO * SR), int((OUTRO + 0.8) * SR)
music[o0:o1] = lp(music[o0:o1], 0.08) * 1.4

music = reverb(music, 2.2, 0.35)
sfx_r = reverb(sfx, 1.2, 0.18)
mixm = 0.9 * music + 0.95 * drums + 0.9 * bass
# sidechain-ish duck of music under impacts
duck = np.ones(N)
for k in list(range(NCR)) + [None]:
    s = OUTRO if k is None else HOOK + SEG * k
    i = int(s * SR); L = int(0.25 * SR)
    duck[i:i + L] = np.minimum(duck[i:i + L], 0.55 + 0.45 * np.linspace(0, 1, L))
mixm *= duck
# fades
fo = int(0.6 * SR); mixm[-fo:] *= np.linspace(1, 0, fo) ** 1.5
fi = int(0.02 * SR); mixm[:fi] *= np.linspace(0, 1, fi)
full = mixm + 0.85 * sfx_r

def norm(x, peak=0.89):
    x = np.tanh(x / np.max(np.abs(x)) * 1.4) / np.tanh(1.4)
    return x * peak
def save(name, x):
    x = norm(x)
    st = np.stack([x, x], 1)
    # tiny stereo width on music via delay
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
save("music15_full.wav", full)
save("sfx15_only.wav", sfx_r)
print("ok")
