set -e
cd "$(dirname "$0")"
OUT=/home/user/Previdenza/reel
mkdir -p $OUT
# Versione A: musica originale + SFX, -14 LUFS (standard IG)
ffmpeg -loglevel error -y -i video_gfx.mp4 -i music_full.wav -map 0:v -map 1:a -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:v libx264 -crf 17 -preset slow -profile:v high -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -ar 48000 -shortest $OUT/reel_crisi_finanziarie.mp4
# Versione B: solo effetti sonori, da usare con un audio di tendenza aggiunto in Instagram
ffmpeg -loglevel error -y -i video_gfx.mp4 -i sfx_only.wav -map 0:v -map 1:a -af "loudnorm=I=-18:TP=-2" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest $OUT/reel_crisi_finanziarie_solo_sfx.mp4
ls -la $OUT
