"""Genera il carosello "Scommettere vs Investire" (HTML -> PNG 1080x1350).

Uso:  python3 build.py          -> scrive carosello.html
      node render.js            -> esporta le slide in png/
"""
import re
from pathlib import Path

# ---------------------------------------------------------------- DATI
RACCOLTA = 157.4e9      # ADM, Bilancio 2024: raccolta gioco legale 2024
VINCITE = 135.8e9       # ADM, Bilancio 2024: vincite 2024
SPESA = 21.5e9          # ADM, Bilancio 2024: spesa effettiva (perdite)
GIOCATORI = 16.6e6      # Istat: italiani che hanno giocato con vincita in denaro nel 2024
R_MSCI = 0.1008         # MSCI World (EUR) net, annualizzato 10 anni al 30/06/2025
R_PRUD = 0.04           # scenario prudente
ANNI = 10
TASSA = 0.26

PAYOUT = VINCITE / RACCOLTA                    # 0,863
MESE = round(RACCOLTA / GIOCATORI / 12, -1)    # 790 EUR
ANNO_PP = RACCOLTA / GIOCATORI                 # 9.482 EUR
PERDITA_MESE = SPESA / GIOCATORI / 12          # 108 EUR


def fv_path(m, r, n=ANNI * 12):
    rm = (1 + r) ** (1 / 12) - 1
    v, out = 0.0, []
    for _ in range(n):
        v = (v + m) * (1 + rm)
        out.append(v)
    return out


def eur(x):
    return f"{round(x):,}".replace(",", ".") + " €"


def num(x):
    return f"{round(x):,}".replace(",", ".")


VERSATO = MESE * 12 * ANNI
INV = fv_path(MESE, R_MSCI)
INV_END = INV[-1]
INV_NET = INV_END - (INV_END - VERSATO) * TASSA
GAMB_END = VERSATO * PAYOUT
DIFF = INV_END - GAMB_END


def scen(m):
    v = m * 12 * ANNI
    a = fv_path(m, R_MSCI)[-1]
    p = fv_path(m, R_PRUD)[-1]
    return dict(g=v * PAYOUT, a=a, p=p, pn=p - (p - v) * TASSA)


TOTAL = 10

# ---------------------------------------------------------------- COMPONENTI
COIN = '<div class="coin" style="{s}"><span>€</span></div>'


def header(n, dark):
    return f"""
  <div class="hdr">
    <div class="brand"><div class="nm">GIULIO<br>FILIERI</div><div class="sep"></div>
      <div class="role">FINANCIAL<br>ADVISOR<div class="fin">FINECO</div></div></div>
    <div class="pg">{n}/{TOTAL}</div>
  </div>"""


def footer(n, cue, left=True, right=True, y=1240):
    """Linea oro + monete a cavallo tra le slide (effetto panorama)."""
    parts = [f'<div class="gline" style="top:{y}px"></div>']
    if left and n > 1:
        parts.append(COIN.format(s=f"left:-80px;top:{y-80}px"))
    if right and n < TOTAL:
        parts.append(COIN.format(s=f"left:1000px;top:{y-80}px"))
    if cue:
        parts.append(f'<div class="cue" style="top:{y-110}px">{cue} <svg width="64" height="26" viewBox="0 0 64 26"><path d="M2 13h56M46 2l12 11-12 11" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
    return "\n".join(parts)


ABS = re.compile(r'\s*<div class="(?:pill|bgphoto|coin big)"[^>]*>.*?</div>(?:</div>)?', re.S)


def slide(n, theme, body, cue, **kw):
    fixed = "".join(ABS.findall(body))
    flow = ABS.sub("", body)
    flow = re.sub(r' style="top:\d+px"', "", flow)
    return f"""
<section class="slide {theme}" id="s{n}">
  <div class="rings"></div>
  {header(n, theme == 'blue')}
  {fixed}
  <div class="content">{flow}</div>
  {footer(n, cue, **kw)}
</section>"""


# ---------------------------------------------------------------- SLIDE
S = []

# 1 — HOOK
S.append(slide(1, "blue", f"""
  <div class="pill">SCOMMESSE VS BORSA · 10 ANNI</div>
  <h1 class="t1" style="top:262px">LA SCHEDINA<br>TI STA COSTANDO<br><span class="gold" style="font-size:1.3em">78.000 €.</span></h1>
  <p class="lead" style="top:600px">Stessi {num(MESE)} € al mese per 10 anni: <b>uno scommette, l'altro investe.</b><br>Alla fine uno ha <b class="gold">il doppio</b> dell'altro.</p>
  <div class="vs-wrap">
    <div class="vs-card">
      <img src="img/slot.jpg" style="object-position:50% 40%">
      <div class="vs-shade red"></div>
      <div class="vs-lbl"><span class="emo">🎰</span>LO SCOMMETTITORE</div>
    </div>
    <div class="vs-card">
      <img src="img/nyse.jpg" style="object-position:50% 50%">
      <div class="vs-shade blue"></div>
      <div class="vs-lbl"><span class="emo">📈</span>L'INVESTITORE</div>
    </div>
    <div class="vs-badge">VS</div>
  </div>
""", "Scorri e scopri chi vince", left=False))

# 2 — I NUMERI
S.append(slide(2, "cream", f"""
  <div class="pill">I NUMERI · ITALIA 2024</div>
  <h1 class="t3" style="top:262px">QUANTO GIOCA IN MEDIA<br><span class="gold">UN ITALIANO?</span></h1>
  <div class="photo-strip" style="top:470px"><img src="img/sansiro.jpg" style="object-position:50% 62%">
    <div class="strip-txt">⚽ Ogni weekend, una schedina. Poi un gratta e vinci al bar. Poi una slot.</div></div>
  <div class="calc" style="top:680px">
    <div class="cbox"><div class="cv">157,4<small> mld €</small></div><div class="cl">giocati in Italia<br>nel 2024</div></div>
    <div class="op">÷</div>
    <div class="cbox"><div class="cv">16,6<small> mln</small></div><div class="cl">italiani che<br>hanno giocato</div></div>
    <div class="op">=</div>
    <div class="cbox hi"><div class="cv">{num(ANNO_PP)}<small> €</small></div><div class="cl">a testa<br>in un anno</div></div>
  </div>
  <div class="big-red" style="top:905px">{num(MESE)} €<span> al mese</span></div>
  <p class="note" style="top:1062px">Raccolta del gioco legale 2024 (ADM) ÷ persone che hanno giocato con vincite in denaro (Istat).
  È una media: c'è chi gioca molto meno e chi molto di più.</p>
""", "Scorri: dove finiscono"))

# 3 — IL BANCO VINCE SEMPRE
dots = "".join(f'<i class="{"lost" if i >= 86 else ""}"></i>' for i in range(100))
S.append(slide(3, "blue", f"""
  <div class="bgphoto"><img src="img/roulette.jpg"></div>
  <div class="pill">LA REGOLA DEL BANCO</div>
  <h1 class="t-one" style="top:262px">IL BANCO <span class="gold">VINCE SEMPRE.</span></h1>
  <p class="lead" style="top:480px">Ogni <b>100 €</b> giocati, in media te ne tornano <b class="gold">86</b>.<br>Gli altri <b class="redt">14</b> restano al banco.</p>
  <div class="dots-wrap" style="top:625px">
    <div class="dots">{dots}</div>
    <div class="dots-leg">
      <div><span class="sw g"></span><b>86 €</b><br>tornano in vincite</div>
      <div><span class="sw r"></span><b>14 €</b><br>persi, ad ogni giro</div>
      <div class="dl-note">E chi rigioca le vincite perde il 14% <b>di nuovo</b>. E di nuovo. E di nuovo.</div>
    </div>
  </div>
  <p class="note light" style="top:1075px">Payout medio 2024: vincite 135,8 mld € ÷ raccolta 157,4 mld € = {f"{PAYOUT*100:.1f}".replace(".", ",")}% (ADM).
  Per legge, le slot da bar possono restituire anche solo il 65%.</p>
""", "Scorri: i protagonisti"))

# 4 — MARCO VS LUCA
S.append(slide(4, "cream", f"""
  <div class="pill">L'ESPERIMENTO</div>
  <h1 class="t2" style="top:262px">MARCO <span class="gold">VS</span> LUCA</h1>
  <p class="lead dark" style="top:378px">Stessa età, stesso stipendio. Ogni mese mettono da parte <b>{num(MESE)} €</b>.</p>
  <div class="duo" style="top:480px">
    <div class="pcard">
      <div class="pimg"><img src="img/slot.jpg" style="object-position:30% 45%"><div class="ptag red">🎰 MARCO</div></div>
      <div class="pbody"><b>Lo scommettitore</b>
        <ul><li>⚽ schedine del weekend</li><li>🎟️ gratta e vinci</li><li>🎰 slot e casinò online</li></ul></div>
    </div>
    <div class="pcard">
      <div class="pimg"><img src="img/nyse.jpg"><div class="ptag blue">📈 LUCA</div></div>
      <div class="pbody"><b>L'investitore</b>
        <ul><li>🌍 un ETF sull'MSCI World</li><li>🏭 1.300+ aziende, 23 Paesi</li><li>🗓️ un versamento al mese</li></ul></div>
    </div>
  </div>
  <div class="navybar" style="top:1020px">In 10 anni ognuno mette <span class="gold">{eur(VERSATO)}</span>.<br>Vediamo come finisce.</div>
""", "Scorri: Marco, 10 anni dopo"))

# 5 — MARCO 10 ANNI DOPO
pct_g = GAMB_END / VERSATO * 100
S.append(slide(5, "blue", f"""
  <div class="pill">MARCO · 10 ANNI DOPO</div>
  <h1 class="t2" style="top:262px">LO SCOMMETTITORE<br><span class="gold">CHIUDE IN PERDITA.</span></h1>
  <div class="sc-box" style="top:480px">
    <div class="sc-tag">SCENARIO PIÙ GENEROSO: MARCO METTE DA PARTE OGNI VINCITA</div>
    <div class="row-lbl">Giocati in 10 anni</div>
    <div class="hbar"><div class="fill blue" style="width:100%">{eur(VERSATO)}</div></div>
    <div class="row-lbl">Vinti (86,3%)</div>
    <div class="hbar"><div class="fill gold2" style="width:{pct_g:.1f}%">{eur(GAMB_END)}</div><div class="fill red" style="width:{100-pct_g:.1f}%"></div></div>
    <div class="sc-res">Risultato: <b class="redt">−{eur(VERSATO-GAMB_END)}</b></div>
  </div>
  <div class="glass" style="top:900px"><span class="emo-l">🔁</span><div><b>Nella realtà è peggio.</b> Le vincite si rigiocano: lo scommettitore medio perde circa <b class="gold">{num(PERDITA_MESE)} € al mese</b>, quasi <b class="gold">13.000 €</b> in 10 anni. Patrimonio costruito: <b>zero</b>.</div></div>
  <p class="note light" style="top:1085px">Perdita media: spesa effettiva 2024 (21,5 mld €, ADM) ÷ 16,6 mln giocatori ÷ 12 mesi.</p>
""", "Scorri: e Luca?"))

# 6 — LUCA 10 ANNI DOPO (grafico)
W, H = 880, 225
x0, y0 = 0, H
ymax = 170000
pts_v = [(0, 0)] + [((k) / 10 * W, MESE * 12 * k) for k in range(1, 11)]
pts_i = [(0, 0)] + [((k) / 10 * W, INV[12 * k - 1]) for k in range(1, 11)]


def path(pts):
    return " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{H - y / ymax * H:.1f}" for i, (x, y) in enumerate(pts))


area_i = path(pts_i) + f" L{W},{H} L0,{H} Z"
area_v = path(pts_v) + f" L{W},{H} L0,{H} Z"
grid = "".join(f'<line x1="0" x2="{W}" y1="{H - g / ymax * H:.1f}" y2="{H - g / ymax * H:.1f}" class="grid"/><text x="-12" y="{H - g / ymax * H + 6:.1f}" class="ax" text-anchor="end">{g//1000}k</text>' for g in (50000, 100000, 150000))
xt = "".join(f'<text x="{k/10*W:.1f}" y="{H+34}" class="ax" text-anchor="middle">{k}</text>' for k in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
ex, ey = W, H - INV_END / ymax * H
vx, vy = W, H - VERSATO / ymax * H
chart = f"""
<svg class="chart" viewBox="-70 -20 {W+90} {H+60}" width="{W+90}" height="{H+60}">
  <defs>
    <linearGradient id="gi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E8BD5E" stop-opacity=".75"/><stop offset="1" stop-color="#E8BD5E" stop-opacity=".08"/></linearGradient>
    <linearGradient id="gv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A62B8" stop-opacity=".85"/><stop offset="1" stop-color="#3A62B8" stop-opacity=".35"/></linearGradient>
  </defs>
  {grid}
  <path d="{area_i}" fill="url(#gi)"/>
  <path d="{area_v}" fill="url(#gv)"/>
  <path d="{path(pts_i)}" fill="none" stroke="#B8801C" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="{path(pts_v)}" fill="none" stroke="#14254F" stroke-width="3" stroke-dasharray="8 8"/>
  <circle cx="{ex}" cy="{ey:.1f}" r="13" fill="#fff" stroke="#B8801C" stroke-width="6"/>
  {xt}
  <text x="{W/2}" y="{H+60}" class="ax" text-anchor="middle" opacity="0"> </text>
</svg>"""
S.append(slide(6, "cream", f"""
  <div class="pill">LUCA · 10 ANNI DOPO</div>
  <h1 class="t2" style="top:262px">L'INVESTITORE<br><span class="gold">FA CRESCERE I SOLDI.</span></h1>
  <div class="chart-box" style="top:590px">
    <div class="legend"><span><i class="lg g"></i>Valore dell'investimento</span><span><i class="lg b"></i>Soldi versati</span><span class="yrs">anni →</span></div>
    {chart}
  </div>
  <div class="split" style="top:1010px">
    <div><small>Versati</small><b>{eur(VERSATO)}</b></div>
    <div class="plus">+</div>
    <div><small>Interesse composto</small><b class="goldt">{eur(INV_END-VERSATO)}</b></div>
  </div>
  <div class="result"><div class="eq">=</div><div><small>PATRIMONIO DI LUCA DOPO 10 ANNI</small><b>{eur(INV_END)}</b></div></div>
  <p class="note" style="top:1108px">Ipotesi: 10,08% annuo, rendimento netto annualizzato a 10 anni dell'indice MSCI World in euro (MSCI, 30/06/2025). Lordo di tasse e costi.</p>
""", "Scorri: il verdetto"))

# 7 — VERDETTO
BH, NB = 480, 84          # altezza barra Luca, altezza etichette sotto le barre
hg = GAMB_END / INV_END * BH
gap = BH - hg
S.append(slide(7, "blue", f"""
  <div class="pill">IL VERDETTO</div>
  <h1 class="t2" style="top:262px">LA VERA VINCITA<br><span class="gold">È QUESTA.</span></h1>
  <div class="cols v2" style="height:{BH+NB+66}px">
    <div class="col">
      <div class="cval">{eur(GAMB_END)}</div>
      <div class="cbar red" style="height:{hg:.0f}px"><img src="img/slot.jpg" style="object-position:35% 50%"><span>🎰</span></div>
      <div class="cname">MARCO<br><small>scommettitore</small></div>
    </div>
    <div class="col">
      <div class="cval gold">{eur(INV_END)}</div>
      <div class="cbar gold" style="height:{BH}px"><img src="img/euro.jpg"><span>📈</span></div>
      <div class="cname">LUCA<br><small>investitore</small></div>
    </div>
    <div class="gapline" style="bottom:{NB+BH}px"></div>
    <div class="gapline" style="bottom:{NB+hg:.0f}px;left:0"></div>
    <div class="diff v2" style="bottom:{NB+hg:.0f}px;height:{gap:.0f}px">
      <div class="dlab">DIFFERENZA</div>
      <div class="dval">+{eur(DIFF)}</div>
      <div class="dsub">Quasi il <b>doppio</b>, con gli stessi soldi.</div>
    </div>
    <div class="taxnote" style="right:0;top:{66+gap+18:.0f}px">E anche dopo il 26% di tasse sulle plusvalenze, Luca avrebbe <b>{eur(INV_NET)}</b>.</div>
  </div>
""", "Scorri: «giocare in Borsa»?"))

# 8 — MITO
rows = [
    ("🏦", "Chi vince alla fine", "Il banco", "Le aziende. E tu ne sei socio"),
    ("🧮", "Valore atteso", "−13,7% a ogni giocata", "Storicamente positivo nel lungo periodo"),
    ("⏳", "Il tempo", "Ti fa perdere di più", "Lavora per te (interesse composto)"),
    ("🧠", "Cosa serve", "Fortuna", "Metodo, obiettivi, pazienza"),
]
trs = "".join(f'<div class="tr"><div class="tk"><span>{e}</span>{k}</div><div class="ta">{a}</div><div class="tb">{b}</div></div>' for e, k, a, b in rows)
S.append(slide(8, "cream", f"""
  <div class="pill">MITO DA SFATARE</div>
  <h1 class="t3" style="top:262px">«GIOCARE IN BORSA»?<br><span class="gold">IN BORSA NON SI GIOCA.</span></h1>
  <div class="tbl" style="top:478px">
    <div class="th"><div></div><div class="ha">🎰 Azzardo</div><div class="hb">📈 Investimento</div></div>
    {trs}
  </div>
  <div class="navybar warn" style="top:1000px">⚠️ Attenzione: anche in Borsa si perde se si <span class="gold">specula</span> senza metodo, inseguendo il titolo del momento.</div>
""", "Scorri: e se giochi meno?"))

# 9 — TABELLA SCENARI (salvabile)
EMO9 = {50: "🍕", 100: "⚽", 300: "🛒", MESE: "🔥"}
trs9 = ""
for m in (50, 100, 300, MESE):
    s9 = scen(m)
    hot = " hot" if m == MESE else ""
    trs9 += f"""<div class="r9b{hot}">
      <div class="m9"><span class="e9">{EMO9[m]}</span><div><b>{num(m)} €</b><small>al mese</small></div></div>
      <div class="c9 bet">{eur(s9["g"])}</div>
      <div class="c9 inv">{eur(s9["a"])}<i>🏆</i></div>
      <div class="c9 pru">{eur(s9["pn"])}</div>
    </div>"""
S.append(slide(9, "blue", f"""
  <div class="pill">DA SALVARE 🔖</div>
  <h1 class="t-one" style="top:262px">E SE GIOCHI <span class="gold">MENO?</span></h1>
  <p class="lead">Cambia la cifra, non il finale. <b>Dopo 10 anni</b> 👇</p>
  <div class="t9b">
    <div class="h9b">
      <div></div>
      <div class="hb bet"><span>🎰</span>SCOMMETTI<small>tieni ogni vincita</small></div>
      <div class="hb inv"><span>📈</span>INVESTI<small>MSCI World 10%</small></div>
      <div class="hb pru"><span>🛡️</span>PRUDENTE<small>4%, dopo le tasse</small></div>
    </div>
    {trs9}
  </div>
  <p class="note light">Anche nello scenario prudente (4% annuo, al netto del 26% sulle plusvalenze) chi investe resta avanti. Rendimenti ipotetici, non garantiti.</p>
""", "Ultima: tocca a te"))

# 10 — CTA
S.append(slide(10, "cream", f"""
  <div class="pill">E ORA TOCCA A TE</div>
  <h1 class="t3" style="top:262px">CONOSCI UN MARCO?<br><span class="gold">MANDAGLI QUESTO POST.</span></h1>
  <p class="lead dark" style="top:478px">La schedina del weekend non ti cambia la vita.<br><b>Un piano coerente con i tuoi obiettivi, sì.</b></p>
  <div class="cta-zone">
    <div class="cta-row">
      <div class="cta"><span>💬</span><div>Scrivi <b>«PIANO»</b> nei commenti</div></div>
      <div class="cta"><span>📤</span><div>Invialo a chi gioca ogni weekend</div></div>
      <div class="cta"><span>🔖</span><div>Salvalo per la prossima tentazione</div></div>
    </div>
    <div class="polaroid">
      <div class="ph"><img src="img/euro.jpg"></div>
      <div class="poll"><div class="pq">TU CHI SEI?</div>
        <div class="po a">🎰 MARCO</div><div class="po b">📈 LUCA</div></div>
    </div>
  </div>
  <p class="disc" style="top:975px">Contenuto informativo: non è consulenza personalizzata né raccomandazione di investimento. Esempi illustrativi; i rendimenti passati non garantiscono quelli futuri. Investire in azioni comporta il rischio di perdite.
  <br>Fonti: ADM, Bilancio 2024; Istat, 2024; MSCI World Index (EUR) factsheet 30/06/2025. Foto: Wikimedia Commons, A. Taveneaux (CC BY-SA 3.0), R. Lawler (PD), T. Lozano (CC BY 2.0), LoreenU (CC BY-SA 4.0), PD.</p>
""", "", right=False))

CSS = Path(__file__).with_name("style.css").read_text()
html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400&display=block" rel="stylesheet">
<title>Scommettere vs Investire</title><style>{CSS}</style></head><body>
{''.join(S)}
</body></html>"""
Path(__file__).with_name("carosello.html").write_text(html)
print("mese", MESE, "versato", VERSATO, "gambler", round(GAMB_END), "inv", round(INV_END), "net", round(INV_NET), "diff", round(DIFF), "perdita/mese", round(PERDITA_MESE))
