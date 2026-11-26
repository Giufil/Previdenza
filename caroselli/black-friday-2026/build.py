"""Genera il carosello "Black Friday 2026: lo scontrino che nessuno ti fa leggere" (HTML -> PNG 1080x1350).

Uso:  python3 build.py          -> scrive carosello.html
      node render.js            -> esporta le slide in png/
"""
import re
from pathlib import Path

# ---------------------------------------------------------------- DATI
SPESA_MEDIA = 262        # Confcommercio-Format Research, Black Friday 2026: spesa media prevista
GIRO_AFFARI = "6,6"      # Confcommercio, mld € giro d'affari settimana Black Friday 2026
QUOTA_ACQ = "2 su 3"     # Confcommercio: italiani che faranno acquisti
RATE_PCT = 42            # Scalapay, Black Friday 2025: quota che pensa di pagare a rate
R_ALTO = 0.07            # scenario ipotetico azionario globale
R_PRUD = 0.04            # scenario prudente
ANNI = 30
TASSA = 0.26

TOTAL = 7


def fv_path(m, r, n=ANNI):
    """Versamento annuo a inizio anno, capitalizzazione annuale."""
    v, out = 0.0, [0.0]
    for _ in range(n):
        v = (v + m) * (1 + r)
        out.append(v)
    return out


def num(x):
    return f"{round(x):,}".replace(",", ".")


def eur(x):
    return num(x) + " €"


ALTO = fv_path(SPESA_MEDIA, R_ALTO)
PRUD = fv_path(SPESA_MEDIA, R_PRUD)
VERS = [SPESA_MEDIA * i for i in range(ANNI + 1)]
ALTO_END, PRUD_END, VERS_END = ALTO[-1], PRUD[-1], VERS[-1]
ALTO_NET = ALTO_END - (ALTO_END - VERS_END) * TASSA
PRUD_NET = PRUD_END - (PRUD_END - VERS_END) * TASSA

# ---------------------------------------------------------------- COMPONENTI
ARROW = '<svg width="64" height="26" viewBox="0 0 64 26"><path d="M2 13h56M46 2l12 11-12 11" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def header(n):
    return f"""
  <div class="hdr">
    <div class="brand"><div class="nm">GIULIO<br>FILIERI</div><div class="sep"></div>
      <div class="role">FINANCIAL<br>ADVISOR<div class="fin">FINECO</div></div></div>
    <div class="pg">{n}/{TOTAL}</div>
  </div>"""


# Oggetti "ponte": metà sulla slide n, metà sulla n+1 (stessa posizione rispetto al bordo).
BRIDGES = {
    1: dict(w=330, h=160, top=1120, html='<div class="btag"><i></i><b>−30%</b><span>BLACK FRIDAY</span></div>', rot=-12),
    2: dict(w=300, h=360, top=1110, html='<div class="bpol"><div class="ph"><img src="img/bf_vetrina.jpg" style="object-position:50% 30%"></div><p>ultimo giorno!!</p></div>', rot=7),
    3: dict(w=380, h=238, top=1150, html='<div class="bcard"><div class="chip"></div><div class="cn">•••• •••• •••• 2026</div><div class="cr">RATA 1 DI 3</div><div class="cl2">PAGA DOPO</div></div>', rot=-9),
    5: dict(w=320, h=320, top=1090, html='<div class="bcoin"><img src="img/eurocoins.jpg"></div>', rot=0),
}
# bagliori di sfondo continui sul bordo tra slide
GLOW = {1: ("255,46,77", 300), 2: ("235,193,99", 760), 3: ("255,46,77", 420), 4: ("235,193,99", 900), 5: ("255,46,77", 380), 6: ("235,193,99", 700)}


def bridge(b, left):
    return f'<div class="bridge" style="left:{left}px;top:{b["top"]}px;width:{b["w"]}px;height:{b["h"]}px;transform:rotate({b["rot"]}deg)">{b["html"]}</div>'


def bg(n):
    g = []
    if n in GLOW:
        c, y = GLOW[n]
        g.append(f"radial-gradient(circle at 1080px {y}px,rgba({c},.30) 0,rgba({c},.10) 260px,transparent 520px)")
    if n - 1 in GLOW:
        c, y = GLOW[n - 1]
        g.append(f"radial-gradient(circle at 0px {y}px,rgba({c},.30) 0,rgba({c},.10) 260px,transparent 520px)")
    return f'<div class="bgfx" style="background:{",".join(g) or "none"}"></div>'


def footer(n, cue):
    parts = []
    if n in BRIDGES:
        b = BRIDGES[n]
        parts.append(bridge(b, 1080 - b["w"] // 2))
    if n - 1 in BRIDGES:
        b = BRIDGES[n - 1]
        parts.append(bridge(b, -(b["w"] // 2)))
    if cue:
        parts.append(f'<div class="cue2">{cue} {ARROW}</div>')
    return "\n".join(parts)


ABS = re.compile(r'\s*<div class="(?:pill|receipt-wrap)"[^>]*>.*?<!--/abs-->', re.S)


def slide(n, theme, body, cue):
    fixed = "".join(ABS.findall(body))
    flow = ABS.sub("", body)
    return f"""
<section class="slide dark" id="s{n}">
  {bg(n)}
  <div class="grain"></div>
  {header(n)}
  {fixed}
  <div class="content">{flow}</div>
  {footer(n, cue)}
</section>"""


S = []

# 1 — HOOK: LO SCONTRINO
righe = [("CUFFIE WIRELESS", 79.90), ("SNEAKERS", 89.00), ("FELPA", 39.90), ("SMART SPEAKER", 29.90), ("COVER TELEFONO", 12.90), ("CALZINI NATALIZI", 10.40)]
totale = sum(v for _, v in righe)
pieno = totale / 0.7


def cifra(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


rr = "".join(f'<div class="rl"><span>{k}</span><span>{cifra(v)}</span></div>' for k, v in righe)
S.append(slide(1, "dark", f"""
  <div class="pill">BLACK FRIDAY 2026 · È DOMANI</div><!--/abs-->
  <h1 class="t2">LO SCONTRINO<br>CHE NESSUNO<br><span class="gold">TI FA LEGGERE.</span></h1>
  <div class="receipt-wrap"><div class="receipt">
    <div class="rc-h">★ BLACK FRIDAY STORE ★</div>
    <div class="rc-s">27/11/2026 &nbsp; 23:58 &nbsp; CASSA 03</div>
    <div class="rc-d"></div>
    {rr}
    <div class="rc-d"></div>
    <div class="rl"><span>SUBTOTALE</span><span>{cifra(pieno)}</span></div>
    <div class="rl red"><span>SCONTO BLACK FRIDAY −30%</span><span>−{cifra(pieno-totale)}</span></div>
    <div class="rl tot"><span>TOTALE €</span><span>{cifra(totale)}</span></div>
    <div class="rc-d"></div>
    <div class="rl hl"><span>INVESTITI · 30 ANNI*</span><span>{num(ALTO_END)},00</span></div>
    <div class="bar"></div>
  </div>
  <div class="hand">il numero<br>che conta ↓</div>
  <div class="stamp">GRAZIE<br>E ARRIVEDERCI<br><b>AL CONTO</b></div></div><!--/abs-->
  <p class="note s1note">*{SPESA_MEDIA} € (spesa media 2026) ogni anno per {ANNI} anni, ipotesi 7% annuo lordo. Esempio illustrativo.</p>
""", "Scorri: ti spiego quel numero"))

# 2 — NUMERI (secondo hook: Instagram ripropone il carosello dalla slide 2)
S.append(slide(2, "cream", f"""
  <div class="pill">I NUMERI · ITALIA 2026</div><!--/abs-->
  <h1 class="t2">{GIRO_AFFARI} MILIARDI<br><span class="gold">IN UNA SETTIMANA.</span></h1>
  <div class="photo-strip"><img src="img/bf_buste.jpg" style="object-position:50% 60%"><div class="strip-txt">🛍️ Una settimana di offerte. Poi arriva gennaio.</div></div>
  <div class="calc">
    <div class="cbox"><div class="cv">{QUOTA_ACQ}</div><div class="cl">italiani pronti<br>a comprare</div></div>
    <div class="op">·</div>
    <div class="cbox"><div class="cv">{SPESA_MEDIA} <small>€</small></div><div class="cl">spesa media<br>a testa</div></div>
    <div class="op">·</div>
    <div class="cbox hi"><div class="cv">{GIRO_AFFARI} <small>mld €</small></div><div class="cl">giro d'affari<br>stimato</div></div>
  </div>
  <div class="navybar">Il problema non è comprare.<br>È comprare <span class="gold">ciò che non avevi in programma.</span></div>
  <p class="note">Stime Confcommercio–Format Research, Black Friday 2026 (settimana di sconti, online e negozi fisici).</p>
""", "Scorri: la trappola n°1"))

# 3 — TRAPPOLA 1: SCONTI GONFIATI (meccanismo illustrativo)
PW, PH = 880, 330
pts = [("SET", 99), ("OTT", 99), ("INIZIO NOV", 129), ("BLACK FRIDAY", 99), ("DIC", 99), ("GEN", 99)]
def px(i): return 60 + (PW - 120) * i / (len(pts) - 1)
def py(v): return 40 + (PH - 110) * (1 - (v - 80) / 60)
d = "M" + " L".join(f"{px(i):.0f},{py(v):.0f}" for i, (_, v) in enumerate(pts))
lbls = "".join(f'<text class="ax" x="{px(i):.0f}" y="{PH-14}" text-anchor="middle"{" style=\'font-weight:800;fill:#FF2E4D;opacity:1\'" if k=="BLACK FRIDAY" else ""}>{k}</text>' for i, (k, _) in enumerate(pts))
dots3 = "".join(f'<circle cx="{px(i):.0f}" cy="{py(v):.0f}" r="10" fill="{"#FF2E4D" if k=="BLACK FRIDAY" else "#F5F3EE"}" stroke="#0A0A0C" stroke-width="4"/>' for i, (k, v) in enumerate(pts))
pchart = f"""<svg class="chart" viewBox="0 0 {PW} {PH}">
  <line class="grid" x1="40" x2="{PW-40}" y1="{py(99):.0f}" y2="{py(99):.0f}" stroke-dasharray="8 8"/>
  <rect x="{px(1.6):.0f}" y="{py(129)-14:.0f}" width="{px(2.4)-px(1.6):.0f}" height="{py(99)-py(129)+14:.0f}" rx="12" fill="#FF2E4D" fill-opacity=".12"/>
  <path d="{d}" fill="none" stroke="#F5F3EE" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>
  {dots3}
  <text x="{px(2):.0f}" y="{py(129)-26:.0f}" text-anchor="middle" style="font:800 26px Poppins;fill:#FF2E4D">129 € «prezzo pieno»</text>
  <g transform="translate({px(3)+18:.0f},{py(99)+26:.0f})"><rect width="150" height="50" rx="25" fill="#FF2E4D"/><text x="75" y="35" text-anchor="middle" style="font:900 28px Poppins;fill:#fff">−23% 🔥</text></g>
  <text x="{px(5):.0f}" y="{py(99)-24:.0f}" text-anchor="end" style="font:700 24px Poppins;fill:#F5F3EE">99 € · sempre lo stesso</text>
  {lbls}
</svg>"""
S.append(slide(3, "blue", f"""
  <div class="pill">TRAPPOLA N°1 · LO SCONTO</div>
  <!--/abs-->
  <h1 class="t2">LO SCONTO<br><span class="gold">È VERO?</span></h1>
  <p class="lead">Altroconsumo ha confrontato i prezzi del Black Friday con quelli di gennaio: <b class="gold">spesso sono identici.</b></p>
  <div class="chart-box pbox"><div class="legend"><span>📈 Alzo il prezzo, poi lo «sconto»</span><span class="yrs">esempio illustrativo</span></div>{pchart}</div>
  <div class="glass"><span class="emo-l">🛡️</span><div><b>La legge è dalla tua parte:</b> lo sconto va calcolato sul <span class="gold"><b>prezzo più basso degli ultimi 30 giorni</b></span> (Direttiva Omnibus). Qui il vero sconto è <b>0%</b>.</div></div>
""", "Scorri: la trappola n°2"))

# 4 — TRAPPOLA 2: LE RATE
items = [("📱", "Smartphone", 600), ("🎧", "Cuffie", 150), ("👟", "Sneakers", 120), ("🎁", "Regali", 240)]
mesi = ["DIC", "GEN", "FEB"]
rows = ""
for e, k, p in items:
    cells = "".join(f'<div class="rt">{num(p/3)} €</div>' for _ in mesi)
    rows += f'<div class="rr"><div class="rk"><span>{e}</span><div><b>{k}</b><small>{p} € in 3 rate</small></div></div>{cells}</div>'
tot = sum(p for *_, p in items) / 3
S.append(slide(4, "cream", f"""
  <div class="pill">TRAPPOLA N°2 · LE RATE</div><!--/abs-->
  <h1 class="t2">COMPRI OGGI,<br><span class="gold">PAGHI A GENNAIO.</span></h1>
  <p class="lead">Il <b>{RATE_PCT}%</b> di chi compra al Black Friday pensa di pagare <b>a rate</b>. Sembrano piccole. Insieme:</p>
  <div class="rcal">
    <div class="rr rh"><div></div>{''.join(f'<div class="mh">{m}</div>' for m in mesi)}</div>
    {rows}
    <div class="rr rtot"><div class="rk"><span>💳</span><div><b>Totale</b><small>ogni mese</small></div></div>{''.join(f'<div class="rt">{num(tot)} €</div>' for _ in mesi)}</div>
  </div>
  <div class="navybar warn">⚠️ 4 acquisti «a zero interessi» = <span class="gold">12 rate</span> tra Natale e i saldi. E se ne salti una, possono scattare penali.</div>
""", "Scorri: fai due conti"))

# 5 — LA MATEMATICA DELLO SCONTO
S.append(slide(5, "blue", f"""
  <div class="pill">LA MATEMATICA DELLO SCONTO</div><!--/abs-->
  <h1 class="t3">−30% SU CIÒ CHE<br>NON TI SERVE<br><span class="gold">= SPENDI IL 70%.</span></h1>
  <div class="sc-box">
    <div class="sc-tag">UN PRODOTTO DA 100 €, SCONTATO DEL 30%</div>
    <div class="row-lbl">🏷️ Come te lo raccontano</div>
    <div class="hbar"><div class="fill gold2" style="width:30%">+30 €</div><div class="fill grey" style="width:70%">paghi 70 €</div></div>
    <div class="row-lbl">🧾 Se non ti serviva davvero</div>
    <div class="hbar"><div class="fill red2" style="width:70%">−70 € dal conto</div></div>
    <div class="row-lbl">🧠 Se non lo compri</div>
    <div class="hbar"><div class="fill gold2" style="width:100%">100 € restano tuoi · −100%</div></div>
  </div>
  <div class="glass"><span class="emo-l">💡</span><div>Uno sconto è un risparmio <span class="gold"><b>solo se l'acquisto era già nel tuo budget.</b></span> Altrimenti è solo una spesa.</div></div>
""", "Scorri: e se lo investissi?"))

# 6 — INTERESSE COMPOSTO
W, H, PADL, PADB, PADT = 820, 300, 70, 44, 16
ymax = 28000


def path(vals):
    pts = []
    for i, v in enumerate(vals):
        x = PADL + (W - PADL - 20) * i / ANNI
        y = PADT + (H - PADT - PADB) * (1 - v / ymax)
        pts.append(f"{x:.1f},{y:.1f}")
    return "M" + " L".join(pts)


def ypx(v):
    return PADT + (H - PADT - PADB) * (1 - v / ymax)


grid = ""
for v in (0, 10000, 20000):
    grid += f'<line class="grid" x1="{PADL}" x2="{W-20}" y1="{ypx(v):.1f}" y2="{ypx(v):.1f}"/><text class="ax" x="{PADL-12}" y="{ypx(v)+8:.1f}" text-anchor="end">{v//1000}k</text>'
for t in (0, 10, 20, 30):
    x = PADL + (W - PADL - 20) * t / ANNI
    grid += f'<text class="ax" x="{x:.1f}" y="{H-8}" text-anchor="middle">{t}</text>'
xe = W - 20
area_v = path(VERS) + f" L{xe},{ypx(0):.1f} L{PADL},{ypx(0):.1f} Z"
area_a = path(ALTO) + f" L{xe},{ypx(0):.1f} L{PADL},{ypx(0):.1f} Z"
chart = f"""<svg class="chart" viewBox="0 0 {W} {H}">
  <defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E9B94C" stop-opacity=".55"/><stop offset="1" stop-color="#E9B94C" stop-opacity=".05"/></linearGradient></defs>
  {grid}
  <path d="{area_a}" fill="url(#ga)"/>
  <path d="{path(ALTO)}" fill="none" stroke="#D9A133" stroke-width="7" stroke-linecap="round"/>
  <path d="{path(PRUD)}" fill="none" stroke="#7FA7FF" stroke-width="5" stroke-dasharray="2 12" stroke-linecap="round"/>
  <path d="{area_v}" fill="#F5F3EE" fill-opacity=".10"/>
  <path d="{path(VERS)}" fill="none" stroke="#F5F3EE" stroke-width="4"/>
  <circle cx="{xe}" cy="{ypx(ALTO_END):.1f}" r="11" fill="#0A0A0C" stroke="#D9A133" stroke-width="6"/>
  <text x="{xe-20}" y="{ypx(PRUD_END)-16:.1f}" text-anchor="end" style="font:700 22px Poppins;fill:#7FA7FF">{eur(PRUD_END)}</text>
  <text x="{xe-20}" y="{ypx(VERS_END)-14:.1f}" text-anchor="end" style="font:700 22px Poppins;fill:#F5F3EE">{eur(VERS_END)}</text>
</svg>"""
S.append(slide(6, "cream", f"""
  <div class="pill">{SPESA_MEDIA} € L'ANNO · {ANNI} ANNI</div><!--/abs-->
  <h1 class="t3">E SE IL CARRELLO<br><span class="gold">FOSSE UN PAC?</span></h1>
  <div class="chart-box">
    <div class="legend"><span><i class="lg g"></i>7% annuo</span><span><i class="lg b dash"></i>4% prudente</span><span><i class="lg n"></i>Soldi versati</span><span class="yrs">anni →</span></div>
    {chart}
  </div>
  <div class="split">
    <div><small>Versati</small><b>{eur(VERS_END)}</b></div>
    <div class="plus">+</div>
    <div><small>Interesse composto</small><b class="goldt">{eur(ALTO_END - VERS_END)}</b></div>
  </div>
  <div class="result"><div class="eq">=</div><div><small>DOPO {ANNI} BLACK FRIDAY «SALTATI»</small><b>{eur(ALTO_END)}</b></div></div>
  <p class="note">Ipotesi: {SPESA_MEDIA} € a inizio anno, rendimento costante, lordo di tasse e costi. Netto 26%: {eur(ALTO_NET)} (7%), {eur(PRUD_NET)} (4%). Rendimenti ipotetici, non garantiti.</p>
""", "Ultima: da salvare"))

# 7 — CHECKLIST + CTA
qs = [
    ("1", "Lo avrei comprato <b>anche a prezzo pieno?</b>"),
    ("2", "Lo sconto è sul <b>prezzo minimo degli ultimi 30 giorni?</b>"),
    ("3", "Posso pagarlo <b>subito, senza rate?</b>"),
    ("4", "Ho già messo da parte <b>la quota per il mio futuro?</b>"),
]
ql = "".join(f'<div class="q"><span class="qn">{n}</span><div>{t}</div><span class="qc">✓</span></div>' for n, t in qs)
S.append(slide(7, "blue", f"""
  <div class="pill">DA SALVARE 🔖</div><!--/abs-->
  <h1 class="t3">PRIMA DI PAGARE,<br><span class="gold">4 DOMANDE.</span></h1>
  <div class="qlist">{ql}</div>
  <div class="ctabar">
    <div class="ctab"><span>💬</span><div>Scrivi <b>«SCONTO»</b> in chat: trasformiamo il budget del Black Friday in un piano.</div></div>
    <div class="ctab"><span>🗳️</span><div>Tu domani? Commenta <b>🛒</b> se compri, <b>📈</b> se investi.</div></div>
    <div class="ctab"><span>📤</span><div>Mandalo a chi ha già il carrello pieno.</div></div>
  </div>
  <p class="disc light">Contenuto informativo: non è consulenza personalizzata né raccomandazione di investimento. Esempi illustrativi; i rendimenti passati non garantiscono quelli futuri. Investire comporta il rischio di perdite.<br>Fonti: Confcommercio–Format Research, Black Friday 2026; Altroconsumo, «Offerte online: a gennaio i prezzi sono spesso uguali a quelli dell'ultimo Black Friday»; Scalapay, Black Friday 2025; D.Lgs. 26/2023 (Omnibus). Foto: Wikimedia Commons — Kgbo (CC BY-SA 4.0), Eric.Ray (CC BY-SA 2.0), Mario Pena «oneras».</p>
""", ""))

CSS = Path(__file__).with_name("style.css").read_text()
EXTRA = Path(__file__).with_name("style-bf.css").read_text() + Path(__file__).with_name("style-dark.css").read_text()
html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=Space+Mono:wght@400;700&family=Permanent+Marker&display=block" rel="stylesheet">
<title>Black Friday 2026</title><style>{CSS}
{EXTRA}</style></head><body>
{''.join(S)}
</body></html>"""
Path(__file__).with_name("carosello.html").write_text(html)
print("alto", round(ALTO_END), "prud", round(PRUD_END), "vers", VERS_END, "alto net", round(ALTO_NET), "prud net", round(PRUD_NET), "rata tot", round(tot))
