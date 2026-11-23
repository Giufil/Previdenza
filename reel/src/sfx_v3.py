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
sfx = np.zeros(N)
add(sfx, impact(), 0.0, 0.9); add(sfx, whoosh(0.3), 0.0, 0.4)
add(sfx, riser(0.8), 0.8, 0.5)
for k in range(5):
    s = 1.6 + 2.0 * k
    add(sfx, whoosh(0.25), s - 0.2, 0.6)
    add(sfx, kick(), s + 0.12, 0.45)
    add(sfx, ding(1100 + 110 * k), s + 0.14, 0.7)
add(sfx, impact(), 10.8, 1.0)
add(sfx, ding(1760), 11.3, 0.9)
sfx = reverb(sfx, 1.2, 0.18)
x = np.tanh(sfx / np.max(np.abs(sfx)) * 1.2) / np.tanh(1.2) * 0.89
with wave.open("sfx_v3.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([x, x], 1) * 32767).astype(np.int16).tobytes())
print("ok")
