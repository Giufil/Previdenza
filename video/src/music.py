"""Musica di sottofondo originale (sintesi procedurale) + effetti, con ducking sotto la voce."""
import json, sys, numpy as np, soundfile as sf
B = sys.argv[1]; SR = 44100
d = json.load(open(f'{B}/timing.json')); D = d['duration']
N = int(D*SR); t = np.arange(N)/SR
BPM = 100; beat = 60/BPM
def note(m): return 440*2**((m-69)/12)
# progressione I–V–vi–IV in Do (C G Am F), 1 accordo per battuta (4 beat)
CH = [[48,55,60,64,67],[43,55,59,62,67],[45,57,60,64,69],[41,53,57,60,65]]
mus = np.zeros(N)
bar = 4*beat
for b in range(int(D/bar)+1):
    s0 = b*bar; ch = CH[b%4]
    i0 = int(s0*SR); i1 = min(int((s0+bar+0.4)*SR), N)
    if i0>=N: break
    tt = t[i0:i1]-s0
    env = np.minimum(tt/0.35,1)*np.exp(-np.maximum(tt-bar,0)*6)
    pad = sum(np.sin(2*np.pi*note(m)*tt + 0.3*np.sin(2*np.pi*0.5*tt))*(0.5 if m<50 else 0.22) for m in ch)
    mus[i0:i1] += 0.10*pad*env
    # arpeggio "pluck" in ottavi
    for k in range(8):
        ps = s0 + k*beat/2; j0 = int(ps*SR); j1 = min(j0+int(0.5*SR), N)
        if j0>=N: break
        m = ch[[2,3,4,3,2,4,3,4][k]]+12; tp = t[j0:j1]-ps
        mus[j0:j1] += 0.07*(np.sin(2*np.pi*note(m)*tp)+0.3*np.sin(4*np.pi*note(m)*tp))*np.exp(-tp*7)
# kick morbido + hat (dopo l'intro di 1 battuta), stop nell'ultima frase per enfasi
for k in range(int(D/beat)):
    bt = k*beat
    if bt < bar: continue
    j0 = int(bt*SR); j1 = min(j0+int(0.25*SR), N); tp = t[j0:j1]-bt
    mus[j0:j1] += 0.35*np.sin(2*np.pi*(50+90*np.exp(-tp*30))*tp)*np.exp(-tp*14)
    h0 = int((bt+beat/2)*SR); h1 = min(h0+int(0.05*SR), N)
    if h0 < N: mus[h0:h1] += 0.025*np.random.randn(h1-h0)*np.exp(-np.arange(h1-h0)/SR*80)
# ducking: abbassa la musica quando parla la voce
v, vsr = sf.read(f'{B}/voice.wav', dtype='float32')
v = np.interp(np.arange(N)/SR, np.arange(len(v))/vsr, v); v = np.pad(v, (0, max(0, N-len(v))))[:N]
env = np.convolve(np.abs(v), np.ones(int(0.25*SR))/int(0.25*SR), 'same')
duck = 1 - 0.55*np.clip(env/0.05, 0, 1)
mus = mus/np.abs(mus).max()*0.30*duck
mus *= np.minimum(t/0.8,1)*np.minimum((D-t)/1.5,1)
# effetti: whoosh ai cambi scena, "ding" sulle cifre chiave
sfx = np.zeros(N)
def whoosh(at):
    j0=int(max(at-0.25,0)*SR); L=int(0.5*SR); j1=min(j0+L,N); n=np.random.randn(j1-j0)
    n=np.convolve(n,np.ones(30)/30,'same'); e=np.sin(np.linspace(0,np.pi,j1-j0))**2; sfx[j0:j1]+=0.22*n*e
def ding(at, f=1318.5):
    j0=int(at*SR); j1=min(j0+int(0.9*SR),N); tp=t[j0:j1]-at
    sfx[j0:j1]+=0.12*(np.sin(2*np.pi*f*tp)+0.5*np.sin(2*np.pi*f*1.5*tp))*np.exp(-tp*5)
prev=None
for l in d['lines']:
    if l['scene']!=prev and prev is not None: whoosh(l['s'])
    prev=l['scene']
for w in d['words']:
    if any(x in w['w'] for x in ['9.500','13.000','26.000']): ding(w['s']+0.05)
    if '5.000' in w['w']: ding(w['s']+0.05, 1046.5)
voice = np.pad(v*1.0, (0,0))
mix = voice + mus + sfx
mix = np.tanh(mix*1.1)/np.tanh(1.1)*0.95
sf.write(f'{B}/mix.wav', np.stack([mix,mix],1).astype(np.float32), SR)
print('ok', D)
