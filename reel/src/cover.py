import sys
sys.argv = ["x", "bg15.mp4", "out", "0"]
exec(open("cover_lib.py").read())
src = Image.open("cover_bg.png").convert("RGB")
img = bg_transform(src, 0.6)  # light zoom
arr = np.asarray(img).astype(np.float32) * VIG
# darken bottom half gently for contrast
g = np.clip((np.arange(H) - 900) / 800, 0, 1)[:, None, None] * 0.35
arr = arr * (1 - g)
frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ---- TOP: context card (friday) ----
liquid_glass(frame, (90, 250, 990, 505), op=1, tint_a=150)
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
text(d, (540, 282), "DAL PANICO AL RIMBALZO", font("InterDisplay-Black", 64), WHITE, 1, anchor="ma")
f = font("InterDisplay-ExtraBold", 40)
s1 = "Venerdì 20/11:"; s2 = "  −11,6% dai massimi"
w1, w2 = f.getlength(s1), f.getlength(s2)
x = 540 - (w1 + w2) / 2
text(d, (x, 375), s1, f, (225, 228, 238), 1)
text(d, (x + w1, 375), s2, f, RED, 1)
text(d, (540, 437), "S&P 500 in correzione · Nasdaq negativo da inizio anno", font("Inter-SemiBold", 27), GREY, 1, anchor="ma", shadow_=False)
overlay(frame, lay)

# ---- BOTTOM: big rebound card ----
y0 = 905
liquid_glass(frame, (70, y0, 1010, y0 + 668), op=1, tint_a=150)
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
chip = "IERI · LUNEDÌ 23 NOVEMBRE"
fc = font("Inter-ExtraBold", 30); cw = fc.getlength(chip) + 48
d.rounded_rectangle([540 - cw / 2, y0 + 40, 540 + cw / 2, y0 + 92], 26, fill=GOLD + (255,))
d.text((540, y0 + 66), chip, font=fc, fill=(18, 18, 18, 255), anchor="mm")
text(d, (540, y0 + 118), "S&P 500", font("InterDisplay-ExtraBold", 46), WHITE, 1, anchor="ma")
# giant number with green glow
fg = font("InterDisplay-Black", 230)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).text((540, y0 + 160), "+4,7%", font=fg, fill=GREEN + (170,), anchor="ma")
glow = glow.filter(ImageFilter.GaussianBlur(22))
frame.paste(glow, (0, 0), glow)
text(d, (540, y0 + 160), "+4,7%", fg, GREEN, 1, anchor="ma")
text(d, (540, y0 + 418), "in un solo giorno", font("InterDisplay-ExtraBold", 50), WHITE, 1, anchor="ma")
d.line([(150, y0 + 500), (930, y0 + 500)], fill=(255, 255, 255, 60), width=2)
# reason line with emoji
em = emoji_img("\U0001F680", 56)
fr = font("InterDisplay-Black", 44)
r1 = "Jensen Huang torna in Nvidia"
r2 = "Il titolo vola: +31% in un giorno"
wr = fr.getlength(r1)
xr = 540 - (wr + 70) / 2
lay.alpha_composite(em, (int(xr), int(y0 + 528)))
text(d, (xr + 70, y0 + 530), r1, fr, WHITE, 1)
text(d, (540, y0 + 600), r2, font("InterDisplay-ExtraBold", 38), GREEN, 1, anchor="ma")
overlay(frame, lay)

# ---- teaser under card ----
liquid_glass(frame, (170, y0 + 686, 910, y0 + 750), r=32, op=1, tint_a=170)
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
text(d, (540, y0 + 718), "E le crisi passate? Ecco come è andata  ↓", font("Inter-Bold", 30), GOLD, 1, anchor="mm", shadow_=False)
overlay(frame, lay)

out = sys.argv_out if hasattr(sys, "argv_out") else "/home/user/Previdenza/reel/copertina_reel.jpg"
frame.save(out, quality=95)
frame.crop((0, 240, 1080, 1680)).resize((540, 720)).save("prev/cover_grid.jpg", quality=90)
frame.resize((540, 960)).save("prev/cover_small.jpg", quality=90)
print("ok")
