# Base synthwave originale, 80 BPM, 2 battute = 6.0 s, loop perfetto (code circolari).
import numpy as np, scipy.io.wavfile as w, scipy.signal as s
SR=44100; BPM=80; BEAT=60/BPM; N=int(SR*8*BEAT)  # 8 beat = 6 s
t=np.arange(N)/SR; out=np.zeros((N,2))
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*SR); n=len(sig); idx=(np.arange(n)+i)%N  # wrap circolare
    out[idx,0]+=sig*gain*(1-pan)/1.0; out[idx,1]+=sig*gain*(1+pan)/1.0
def env(n,a,d):
    x=np.arange(n)/SR; return np.minimum(1,x/a)*np.exp(-x/d)
def saw(f,dur,det=0.0):
    x=np.arange(int(dur*SR))/SR
    return sum(s.sawtooth(2*np.pi*f*(1+k*det)*x) for k in (-1,0,1))/3
def lp(sig,fc,o=2): b,a=s.butter(o,fc/(SR/2)); return s.lfilter(b,a,sig)
mid=lambda m:440*2**((m-69)/12)
# Kick 1 e 3, snare 2 e 4
for b in range(8):
    if b%2==0:
        n=int(0.45*SR); x=np.arange(n)/SR; f=45+110*np.exp(-x*28)
        add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*7),b*BEAT,0.9)
    else:
        n=int(0.5*SR); x=np.arange(n)/SR
        sn=lp(np.random.randn(n),5000)*np.exp(-x*9)*0.5+np.sin(2*np.pi*190*x)*np.exp(-x*20)*0.4
        add(sn,b*BEAT,0.55)
    for h in (0,0.5):
        n=int(0.06*SR); hh=s.lfilter(*s.butter(2,7000/(SR/2),'high'),np.random.randn(n))*np.exp(-np.arange(n)/SR*60)
        add(hh,(b+h)*BEAT,0.12,0.4)
# Accordi: Am7 | Fmaj7 (pad) + basso
chords=[[57,60,64,67],[53,57,60,64]]; roots=[33,29]
for bar,(ch,r) in enumerate(zip(chords,roots)):
    st=bar*4*BEAT; dur=4*BEAT
    pad=sum(lp(saw(mid(m),dur,0.004),1800) for m in ch)/4
    n=len(pad); pad*=np.minimum(1,np.arange(n)/(0.25*SR))*np.minimum(1,(n-np.arange(n))/(0.3*SR))
    add(pad,st,0.32,-0.1)
    for e in range(8):
        n=int(BEAT/2*SR*0.9); bs=lp(saw(mid(r+12),BEAT/2*0.9),600)*env(n,0.005,0.25)
        add(bs,st+e*BEAT/2,0.5)
    arp=[ch[i%4]+12 for i in (0,1,2,3,2,1,0,1)]*2
    for e,m in enumerate(arp):
        n=int(BEAT/4*SR); a=lp(s.square(2*np.pi*mid(m)*np.arange(n)/SR)*0.5,3000)*env(n,0.003,0.12)
        add(a,st+e*BEAT/4,0.09,0.5 if e%2 else -0.5)
# Riverbero circolare semplice (impulso esponenziale), mantiene il loop
ir=np.random.randn(int(1.2*SR))*np.exp(-np.arange(int(1.2*SR))/SR*4)*0.02
for c in range(2):
    wet=np.real(np.fft.ifft(np.fft.fft(out[:,c])*np.fft.fft(ir,N) if len(ir)<=N else 0))
    out[:,c]+=wet*0.6
out=np.tanh(out*1.1); out/=np.abs(out).max()*1.12
w.write('public/music.wav',SR,(out*32767).astype(np.int16)); print(N/SR,'s')
