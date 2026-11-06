"""Genera la voce narrante (Kokoro, voce im_nicola, italiano) e i tempi per parola."""
import json, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from script import SCENES

MODELS = sys.argv[1]; OUT = sys.argv[2]
SPEED = 1.2; SR = 24000
k = Kokoro(f'{MODELS}/kokoro-v1.0.onnx', f'{MODELS}/voices-v1.0.bin')

def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    return a[max(idx[0]-240,0): idx[-1]+480]

def pauses(a, min_len=0.11):
    """Intervalli di silenzio interni (inizio, fine) in secondi."""
    hop = SR//100; e = np.array([np.sqrt((a[i:i+hop]**2).mean()) for i in range(0, len(a)-hop, hop)])
    sil = e < 0.01; out=[]; i=0
    while i < len(sil):
        if sil[i]:
            j=i
            while j < len(sil) and sil[j]: j+=1
            if (j-i)/100 >= min_len and i>5 and j<len(sil)-5: out.append((i/100, j/100))
            i=j
        else: i+=1
    return out

def weight(w):
    p = k.tokenizer.phonemize(w.replace('_',' '), 'it')
    return max(len(re.sub(r"[ˈˌː\s.,:;?!]", "", p)), 1)

audio=[]; t=0.0; words=[]; lines=[]; prev=None
PAUSE={',':0.10,':':0.16,'?':0.22,'!':0.2,'.':0.2,';':0.14}
for scene, spoken, sub in SCENES:
    gap = 0.0 if prev is None else (0.30 if scene!=prev else 0.16)
    audio.append(np.zeros(int(gap*SR), np.float32)); t += gap
    sw, dw = spoken.split(), sub.split()
    # una sintesi per ogni segmento separato da punteggiatura: confini esatti per i sottotitoli
    segs=[]; st=0
    for i,w in enumerate(sw):
        if re.search(r'[,:;?!.]$', w) or i==len(sw)-1: segs.append((st,i)); st=i+1
    t_line=t
    for a0,a1 in segs:
        s,_ = k.create(' '.join(sw[a0:a1+1]).replace('_',' '), voice='im_nicola', speed=SPEED, lang='it')
        s = trim(s.astype(np.float32)); dur=len(s)/SR
        ws=[weight(w) for w in sw[a0:a1+1]]; tot=sum(ws); c=0
        for j,wgt in enumerate(ws):
            d=dur*wgt/tot
            words.append({'w':dw[a0+j].replace('_',' '),'s':round(t+c,3),'e':round(t+c+d,3),'line':len(lines)})
            c+=d
        audio.append(s); t+=dur
        if a1 < len(sw)-1:
            p=PAUSE.get(sw[a1][-1],0.1); audio.append(np.zeros(int(p*SR),np.float32)); t+=p
    lines.append({'scene':scene,'s':round(t_line,3),'e':round(t,3),'text':sub.replace('_',' ')})
    prev=scene
    print(f'{lines[-1]["s"]:6.2f}-{lines[-1]["e"]:6.2f} {scene:6s} {sub}')
audio.append(np.zeros(int(2.2*SR),np.float32))
a=np.concatenate(audio); a=a/np.abs(a).max()*0.89
sf.write(f'{OUT}/voice.wav', a, SR)
json.dump({'duration':len(a)/SR,'lines':lines,'words':words}, open(f'{OUT}/timing.json','w'), ensure_ascii=False, indent=1)
print('durata totale', len(a)/SR)
