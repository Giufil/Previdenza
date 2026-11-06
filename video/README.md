# Reel: Buono postale per minori vs ETF MSCI World (18 anni)

- `reel_buono_vs_msci_world.mp4` — 1080×1920, 30 fps, H.264 + AAC, ~44 s, audio normalizzato a -14 LUFS (formato Reel Instagram).
- `copertina.jpg` — fotogramma consigliato come copertina.

## Ipotesi dei numeri (stime, non previsioni)

| | Buono fruttifero postale minori | ETF MSCI World |
|---|---|---|
| Rendimento lordo | ~4% annuo effettivo a scadenza (serie TF118A260724, durata massima; da verificare sul foglio informativo Poste) | 7% medio annuo (ipotesi, storicamente plausibile ma non garantita) |
| Costi | nessuno | TER 0,2% + imposta di bollo 0,2% annuo |
| Tassazione | 12,5% sugli interessi | 26% sulla plusvalenza |
| Valore netto a 18 anni | ~€9.500 | ~€13.000 |
| Valore netto a 30 anni | ~€9.500 (il buono scade a 18 anni, gli interessi si fermano) | ~€26.400 |

Semplificazioni: il bollo sui buoni (dovuto oltre €5.000 di valore complessivo) è ignorato; l'ETF è soggetto a oscillazioni anche forti (es. crolli di mercato) non rappresentate dalla curva liscia.

## Rigenerare

```bash
pip install kokoro-onnx soundfile numpy pillow
# modelli: kokoro-v1.0.onnx e voices-v1.0.bin (github.com/thewh1teagle/kokoro-onnx, release model-files-v1.0)
python3 src/tts.py <models_dir> <build_dir>      # voce (Kokoro, im_nicola) + tempi per parola
python3 src/music.py <build_dir>                  # musica originale procedurale + effetti + mix
python3 src/render.py <build_dir>                 # grafica e sottotitoli karaoke -> frames_00000.mp4
```
Il testo parlato e i sottotitoli sono in `src/script.py`.
