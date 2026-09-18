"""Assemble the Signal Integrity & High-Speed Digital Design deck series.

Same house style as the Matrix Methods decks: the shared <style> block is
lifted verbatim from MML_04_Matrix_Decompositions, only --accent changes per
deck, and each deck is one self-contained index.html with no build step at the
far end. The difference here is that the whole series lives in one repository
with a deck per subdirectory and a landing page above them, which keeps the
cross-references between decks internal.

Each deck body is glued to the JSON its model produced, so a deck cannot quote
a number that `si_models/run_all.py` did not compute.
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/home/brendan/Claude_sandbox"
REPO = os.path.join(ROOT, "Signal_Integrity")
DATA = os.path.join(HERE, "_si_data")
STYLE = open(os.path.join(HERE, "_house_style.css.html"), encoding="utf-8").read()
GH = "https://github.com/BrendanJamesLynskey/Signal_Integrity"
PAGES = "https://brendanjameslynskey.github.io/Signal_Integrity"

SECTIONS = [
    ("The passive channel", 1, 4,
     "What a transmission line is, where the return current flows, what the "
     "materials do to the signal, and what happens at the one feature made by "
     "drilling."),
    ("The signal on it", 5, 6,
     "Why every fast link is differential, and the one impairment no equaliser "
     "can remove."),
    ("Jitter", 7, 10,
     "Organised around Ransom Stephens's five rules: it is about the bit error "
     "ratio, total jitter can only be measured on a bit error ratio tester, "
     "measurement is always a comparison against a reference clock, and timing "
     "noise and amplitude noise are not really separable."),
    ("Power integrity", 11, 14,
     "The power delivery network as an impedance, as an ecology of resonances, "
     "as something that has to be measured in milliohms, and finally as a "
     "source of signal-integrity failures."),
    ("The verdict", 15, 17,
     "Whether the timing closes, whether the measurements can be believed, and "
     "how a standard turns all of it into a pass or a fail."),
]

DECKS = [
    dict(n=1, slug="01-transmission-lines", body="deck_si_01_body.html",
         data="deck01", accent="#22d3ee",
         title="The Transmission Line and the Physical Channel",
         short="Transmission lines",
         blurb="When a trace stops being a wire, where the fifty-ohm "
               "convention comes from, and what a reflection actually is."),
    dict(n=2, slug="02-return-paths", body="deck_si_02_body.html",
         data="deck02", accent="#34d399",
         title="Return Paths and Reference Planes",
         short="Return paths",
         blurb="Every signal current is a loop. Where the other half of it "
               "flows, and what happens when the board will not let it."),
    dict(n=3, slug="03-materials-and-loss", body="deck_si_03_body.html",
         data="deck03", accent="#fbbf24",
         title="Materials, Loss and Causality",
         short="Materials and loss",
         blurb="Copper roughness, dielectric loss, and why a constant "
               "dielectric constant describes a material that cannot exist."),
    dict(n=4, slug="04-vias-and-discontinuities", body="deck_si_04_body.html",
         data="deck04", accent="#f59e0b",
         title="Vias, Connectors and Discontinuities",
         short="Vias",
         blurb="The only part of a channel made by drilling, and the one "
               "that decides whether the link runs at 28 gigabaud."),
    dict(n=5, slug="05-differential-signalling", body="deck_si_05_body.html",
         data="deck05", accent="#a78bfa",
         title="Differential Signalling",
         short="Differential pairs",
         blurb="Why every fast link is differential, what tight coupling "
               "really costs, and how symmetry is lost."),
    dict(n=6, slug="06-crosstalk", body="deck_si_06_body.html",
         data="deck06", accent="#f472b6",
         title="Crosstalk",
         short="Crosstalk",
         blurb="The impairment no equaliser can remove, and the one place "
               "near-end and far-end coupling genuinely differ."),
    dict(n=7, slug="07-total-jitter", body="deck_si_07_body.html",
         data="deck07", accent="#c084fc",
         title="Total Jitter and the Bit Error Ratio",
         short="Total jitter",
         blurb="Why jitter is defined against an error ratio, what a bit "
               "error ratio tester does that nothing else can, and the "
               "decomposition tree done properly."),
    dict(n=8, slug="08-dual-dirac", body="deck_si_08_body.html",
         data="deck08", accent="#a855f7",
         title="The Dual-Dirac Model and Its Limits",
         short="Dual-Dirac",
         blurb="Five assumptions, a fitting parameter that is not the "
               "peak-to-peak deterministic jitter, and the tails a "
               "measurement cannot reach."),
    dict(n=9, slug="09-clock-recovery", body="deck_si_09_body.html",
         data="deck09", accent="#8b5cf6",
         title="Clock Recovery, the Reference Clock and Tolerance",
         short="Clock recovery",
         blurb="Every jitter measurement compares a test clock against a "
               "reference. Which reference, how much it tracks, and what the "
               "tolerance mask is really testing."),
    dict(n=10, slug="10-amplitude-noise", body="deck_si_10_body.html",
         data="deck10", accent="#d946ef",
         title="Crosstalk, Amplitude Noise and the Two-Dimensional View",
         short="Amplitude noise",
         blurb="Timing noise and amplitude noise are not separable, the "
               "separation fails above about ten gigabits per second, and "
               "crosstalk is where it fails first."),
    dict(n=11, slug="11-pdn-impedance", body="deck_si_11_body.html",
         data="deck11", accent="#60a5fa",
         title="The Power Delivery Network as an Impedance",
         short="PDN impedance",
         blurb="Target impedance and what the rule is worth, real capacitors, "
               "and why the number of parts is set by inductance rather than "
               "by capacitance."),
    dict(n=12, slug="12-planes-and-ecology", body="deck_si_12_body.html",
         data="deck12", accent="#3b82f6",
         title="Planes, Cavities and the PDN Ecology",
         short="Planes and ecology",
         blurb="Spreading inductance, cavity resonances, and the Bandini "
               "Mountain \u2014 the peak the board cannot reach because it is "
               "behind the package."),
    dict(n=13, slug="13-measuring-low-impedance", body="deck_si_13_body.html",
         data="deck13", accent="#0ea5e9",
         title="Measuring Low Impedance",
         short="Measuring milliohms",
         blurb="Why a reflection measurement stops at about an ohm, how the "
               "two-port shunt-through method reaches a milliohm, and the "
               "ground loop that ruins it."),
    dict(n=14, slug="14-pi-meets-si", body="deck_si_14_body.html",
         data="deck14", accent="#38bdf8",
         title="Power Integrity Meets Signal Integrity",
         short="PI meets SI",
         blurb="The routes by which a disturbance on the supply becomes an "
               "error at a receiver \u2014 switching noise, cavity coupling, "
               "and supply-induced jitter."),
    dict(n=15, slug="15-timing-and-budgets", body="deck_si_15_body.html",
         data="deck15", accent="#2dd4bf",
         title="Timing, Flight Time and the Budget",
         short="Timing budgets",
         blurb="Flight time is not propagation delay, and the arithmetic "
               "that ended the wide parallel bus."),
    dict(n=16, slug="16-measurement-and-correlation",
         body="deck_si_16_body.html", data="deck16", accent="#fb923c",
         title="Measurement, De-embedding and Correlation",
         short="Measurement",
         blurb="Where S-parameters come from, how they are damaged, and "
               "what correlation honestly means."),
    dict(n=17, slug="17-com-and-compliance", body="deck_si_17_body.html",
         data="deck17", accent="#4ade80",
         title="Channel Operating Margin and Compliance",
         short="COM and compliance",
         blurb="How a standard decides a channel is legal, run on the same "
               "channel the equalisation deck could not close."),
]

# Paths the series used before the jitter and power-integrity sections were
# added. They are kept as redirects so that published links do not rot.
REDIRECTS = {
    "07-power-integrity": "11-pdn-impedance",
    "08-jitter": "07-total-jitter",
    "09-timing-and-budgets": "15-timing-and-budgets",
    "10-measurement-and-correlation": "16-measurement-and-correlation",
    "11-com-and-compliance": "17-com-and-compliance",
}

EXTRA_CSS = """
        .legend{display:flex;flex-wrap:wrap;gap:1rem;justify-content:center;margin-top:.6rem;font-family:var(--font-mono);font-size:.72rem;color:var(--text-secondary)}
        .legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:.35rem;vertical-align:middle}
        .verdict{font-family:var(--font-mono);font-size:.8rem;padding:.35rem .7rem;border-radius:4px;display:inline-block;margin-top:.5rem}
        .verdict.ok{color:var(--accent-4);border:1px solid var(--accent-4);background:rgba(52,211,153,.12)}
        .verdict.bad{color:var(--accent-2);border:1px solid var(--accent-2);background:rgba(244,114,182,.12)}
        .canvas-wrap canvas{image-rendering:auto}
        .metric-label .katex,.callout-label .katex,.series-label .katex,
        .metric-label .katex *,.callout-label .katex *{text-transform:none}
        .note{font-size:.85rem;color:var(--text-secondary);font-style:italic;margin-top:.5rem}
        .seriesnav{display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin:1.2rem 0}
        .seriesnav a{font-family:var(--font-mono);font-size:.7rem;padding:.25rem .6rem;border-radius:4px;border:1px solid var(--border);color:var(--text-secondary);text-decoration:none}
        .seriesnav a:hover{border-color:var(--accent);color:var(--accent)}
        .seriesnav a.here{border-color:var(--accent);color:var(--accent);background:var(--accent-dim)}
        .checktab td:last-child,.checktab th:last-child{text-align:right}
        .ok{color:var(--accent-4)} .bad{color:var(--accent-2)}
        /* keep the page itself from ever scrolling sideways: wide tables and
           wide display maths each scroll inside their own box instead */
        .slide table{display:block;overflow-x:auto;max-width:100%}
        .katex-mathml{position:absolute!important;clip:rect(1px,1px,1px,1px);
            width:1px!important;height:1px!important;overflow:hidden}
        .katex-display{max-width:100%;overflow-x:auto;overflow-y:hidden}
        .slide select{max-width:100%}
"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>
__STYLE__
</head>
<body>
<script>const SI = __DATA__;</script>
"""

FOOT = """
<div class="footer">
    <p>Deck __N__ of eleven in <a href="../">Signal Integrity &amp; High-Speed
    Digital Design</a>. Every figure on this page is computed by
    <a href="https://github.com/BrendanJamesLynskey/Matrix_Articles">si_models/__MODEL__</a>
    and embedded as data; nothing is typed in by hand.</p>
    __NAV__
    <p style="margin-top:.6rem">Single-page HTML &middot; KaTeX-rendered maths &middot; no build step.
    <a href="__GH__">Source on GitHub</a></p>
</div>

</body>
</html>
"""


def nav(cur):
    out = ['<div class="seriesnav">']
    for d in DECKS:
        cls = ' class="here"' if d['n'] == cur else ''
        href = '../%s/' % d['slug'] if d['n'] != cur else '#'
        out.append('<a href="%s"%s>%02d %s</a>' % (href, cls, d['n'], d['short']))
    out.append('</div>')
    return ''.join(out)


def build_deck(d, quiet=False):
    body_path = os.path.join(HERE, d['body'])
    if not os.path.exists(body_path):
        return None
    style = STYLE.replace('#a78bfa', d['accent'])
    r, g, b = (int(d['accent'][i:i + 2], 16) for i in (1, 3, 5))
    style = style.replace('rgba(167,139,250,.25)', 'rgba(%d,%d,%d,.25)' % (r, g, b))
    style = style.replace('    </style>', EXTRA_CSS + '    </style>')

    data = {}
    dp = os.path.join(DATA, d['data'] + '.json')
    if os.path.exists(dp):
        data = json.load(open(dp))
    vp = os.path.join(DATA, 'verification.json')
    if os.path.exists(vp):
        data['_verify'] = json.load(open(vp))

    head = (HEAD.replace('__TITLE__', d['title'])
                .replace('__STYLE__', style)
                .replace('__DATA__', json.dumps(data, separators=(',', ':'))))
    body = open(body_path, encoding='utf-8').read()
    body = body.replace('__NAV__', nav(d['n']))
    foot = (FOOT.replace('__N__', str(d['n']))
                .replace('__NAV__', nav(d['n']))
                .replace('__MODEL__', d['data'])
                .replace('__GH__', GH))
    html = head + body + foot
    out = os.path.join(REPO, d['slug'], 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(html)
    n = len(re.findall(r'<section class="slide"', html))
    if not quiet:
        print('  %-34s %2d slides  %6d kB' % (d['slug'], n, len(html) // 1024))
    return n


REDIRECT_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=../__TARGET__/">
<link rel="canonical" href="__PAGES__/__TARGET__/">
<title>Moved &mdash; Signal Integrity &amp; High-Speed Digital Design</title>
<style>body{background:#0a0a0a;color:#e6edf3;font-family:system-ui,sans-serif;
max-width:38rem;margin:18vh auto;padding:0 1.5rem;line-height:1.7}
a{color:#22d3ee}</style>
</head>
<body>
<h1>This deck has moved</h1>
<p>The series grew a jitter section and a power-integrity section, so the decks
after the sixth were renumbered. This page now lives at
<a href="../__TARGET__/">__TARGET__</a>, and you should be sent there
automatically.</p>
<p><a href="../">Back to the series</a></p>
</body>
</html>
'''


def build_redirects():
    n = 0
    for old, new in REDIRECTS.items():
        out = os.path.join(REPO, old, 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(REDIRECT_HTML.replace('__TARGET__', new)
                                  .replace('__PAGES__', PAGES))
        n += 1
    print('  %-34s %d redirect stubs for the old paths' % ('(moved)', n))


def build_all():
    print('building Signal_Integrity')
    total = 0
    for d in DECKS:
        n = build_deck(d)
        if n is None:
            print('  %-34s (body not written yet)' % d['slug'])
        else:
            total += n
    print('  %d slides across %d decks' % (total, len(DECKS)))
    build_redirects()
    build_landing()




LANDING_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Signal Integrity &amp; High-Speed Digital Design</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet" />
<style>
  :root { --bg:#0a0a0f; --surface:#131318; --border:#23232a; --text:#d4d4d8;
          --text2:#a1a1aa; --dim:#71717a; --accent:#22d3ee; --green:#10b981;
          --purple:#8b5cf6; --blue:#60a5fa; --red:#ef4444; }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { font-size: 16px; scroll-behavior: smooth; }
  body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
         line-height:1.6; min-height:100vh; }
  a { color: var(--blue); text-decoration: none; }
  a:hover { color: #93c5fd; }
  .container { max-width: 980px; margin: 0 auto; padding: 3rem 1.5rem 4rem; }
  header { text-align: center; margin-bottom: 2.5rem; }
  header .icon { font-size: 3rem; margin-bottom: 0.5rem; }
  header h1 { font-family:'Playfair Display',serif; font-weight:900; font-size:2.6rem;
              letter-spacing:-0.02em; color:#fafafa; margin-bottom:0.3rem; line-height:1.1; }
  header .subtitle { font-size:1rem; color:var(--accent); font-weight:500;
                     letter-spacing:0.15em; text-transform:uppercase; margin-bottom:1rem; }
  header p { color: var(--text2); max-width: 680px; margin: 0 auto 0.8rem;
             font-size: 0.95rem; }
  .grid { display: flex; flex-direction: column; gap: 1rem; }
  .card { display:grid; grid-template-columns:56px 1fr auto; align-items:center;
          gap:1.2rem; background:var(--surface); border:1px solid var(--border);
          border-radius:10px; padding:1.25rem 1.5rem;
          transition:border-color .2s, box-shadow .2s; }
  .card:hover { border-color: rgba(34,211,238,.3); box-shadow: 0 0 20px rgba(34,211,238,.06); }
  .card .num { font-family:'Playfair Display',serif; font-weight:900; font-size:1.8rem;
               text-align:center; line-height:1; }
  .card .info h2 { font-family:'Playfair Display',serif; font-weight:700; font-size:1.15rem;
                   color:#fafafa; margin-bottom:0.2rem; }
  .card .info p { font-size:0.82rem; color:var(--dim); line-height:1.4; }
  .card .action { text-align:right; white-space:nowrap; display:flex;
                  flex-direction:column; align-items:flex-end; gap:0.4rem; }
  .btn { display:inline-block; padding:0.45em 1.3em; border-radius:6px; font-weight:700;
         font-size:0.85rem; transition:background .2s, transform .1s; }
  .btn:active { transform: scale(0.97); }
  .btn-launch { background: var(--accent); color:#0a0a0f; }
  .btn-launch:hover { background:#67e8f9; color:#0a0a0f; }
  .badge { display:inline-block; padding:0.25em 0.8em; border-radius:999px;
           font-size:0.72rem; font-weight:700; font-family:'JetBrains Mono',monospace; }
  .badge-complete { background:rgba(16,185,129,.12); color:var(--green);
                    border:1px solid rgba(16,185,129,.25); }
  .section-title { font-family:'Playfair Display',serif; font-size:1.45rem; color:#fafafa;
                   margin:2.6rem 0 0.35rem; display:flex; align-items:baseline;
                   gap:0.8rem; flex-wrap:wrap; }
  .section-title .secrange { font-family:'JetBrains Mono',monospace; font-size:0.72rem;
                   color:var(--accent); letter-spacing:0.12em; text-transform:uppercase;
                   font-weight:700; }
  .secintro { color:var(--dim); font-size:0.88rem; margin:0 0 1rem; max-width:62ch; }
  .panel { background:var(--surface); border:1px solid var(--border); border-radius:10px;
           padding:1.25rem 1.5rem; font-size:0.9rem; color:var(--text2); }
  .panel ul { margin:0.5rem 0 0 1.1rem; }
  .panel li { margin-bottom:0.35rem; }
  table { width:100%; border-collapse:collapse; font-size:0.85rem; margin-top:0.5rem; }
  th { text-align:left; color:var(--accent); font-weight:700; padding:0.5rem 0.7rem;
       border-bottom:1px solid var(--border); font-family:'JetBrains Mono',monospace;
       font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; }
  td { padding:0.45rem 0.7rem; border-bottom:1px solid var(--border); color:var(--text2);
       vertical-align:top; }
  tr:last-child td { border-bottom:none; }
  .ok { color: var(--green); font-family:'JetBrains Mono',monospace; }
  footer { text-align:center; margin-top:3rem; padding-top:1.5rem;
           border-top:1px solid var(--border); font-size:0.82rem; color:var(--dim); }
  footer a { color: var(--dim); }
  footer a:hover { color: var(--text2); }
  @media (max-width:600px){ .card{grid-template-columns:40px 1fr;gap:0.8rem}
    .card .action{grid-column:1/-1;text-align:left;align-items:flex-start}
    header h1{font-size:1.9rem} .container{padding:2rem 1rem 3rem} }
</style>
</head>
<body>
<div class="container">
"""


def build_landing():
    import json as _json
    vp = os.path.join(DATA, 'verification.json')
    ver = _json.load(open(vp)) if os.path.exists(vp) else {}
    n_slides = 0
    for d in DECKS:
        f = os.path.join(REPO, d['slug'], 'index.html')
        if os.path.exists(f):
            n_slides += len(re.findall(r'<section class="slide"',
                                       open(f, encoding='utf-8').read()))

    out = [LANDING_HEAD]
    out.append("""
<header>
  <div class="icon">⬡</div>
  <div class="subtitle">Computed, interactive, verified</div>
  <h1>Signal Integrity &amp; High-Speed Digital Design</h1>
  <p>Seventeen decks in five sections on getting a signal from one chip to another
  intact &mdash; the physics of the channel, the mechanisms that close an eye, and the
  arithmetic a standard uses to decide a channel is legal.</p>
  <p>Every number on every slide is computed by a model in
  <a href="https://github.com/BrendanJamesLynskey/Matrix_Articles">si_models</a> and
  embedded as data. Nothing is asserted by hand, and the models are checked against
  published worked examples wherever one exists.</p>
</header>

""")
    for title, lo, hi, intro in SECTIONS:
        out.append('<h2 class="section-title">%s'
                   '<span class="secrange">decks %02d&ndash;%02d</span></h2>\n'
                   % (title, lo, hi))
        out.append('<p class="secintro">%s</p>\n' % intro)
        out.append('<div class="grid">\n')
        for d in DECKS:
            if not (lo <= d['n'] <= hi):
                continue
            out.append("""  <div class="card">
    <div class="num" style="color:%s">%02d</div>
    <div class="info"><h2>%s</h2><p>%s</p></div>
    <div class="action"><a class="btn btn-launch" href="%s/">Open</a>
      <span class="badge badge-complete">complete</span></div>
  </div>
""" % (d['accent'], d['n'], d['title'], d['blurb'], d['slug']))
        out.append("</div>\n")

    # verification table
    if ver:
        rows = []
        for k, v in sorted(ver.items()):
            if not isinstance(v, dict) or 'err_pct' not in v:
                continue
            rows.append((k, v))
        rows.sort(key=lambda kv: (str(kv[1].get('source', '')).startswith('internal'), kv[0]))
        if rows:
            pub = [v for _, v in rows
                   if not str(v.get('source', '')).startswith('internal')]
            worst = max(abs(v['err_pct']) for v in pub) if pub else 0.0
            out.append("""
<h2 class="section-title">What has been checked</h2>
<div class="panel">
<p>A model that agrees only with itself is not worth much. Every cross-check the series
makes against an independently published result is listed here, with the disagreement.
The last rows, marked <em>internal</em>, are not checks against anybody else: they are
places where two different computations in the series have to agree with each other,
and the quoted worst disagreement excludes them.
The worst is %.2f&nbsp;per&nbsp;cent.</p>
<table>
<thead><tr><th>Quantity</th><th>This series</th><th>Reference value</th><th>Difference</th><th>Source</th></tr></thead>
<tbody>
""" % worst)
            for k, v in rows:
                def f(x):
                    a = abs(x)
                    if a >= 1e9 or (a < 1e-3 and a > 0):
                        return '%.4g' % x
                    return '%.5g' % x
                out.append('<tr><td>%s</td><td>%s</td><td>%s</td>'
                           '<td class="ok">%+.2f&nbsp;%%</td><td>%s</td></tr>\n'
                           % (k.split('/')[-1].replace('_', ' '), f(v['ours']),
                              f(v['published']), v['err_pct'], v['source']))
            out.append("</tbody></table></div>\n")

    out.append("""
<h2 class="section-title">Long-form companion</h2>
<div class="panel">
<p>The same material as a written report:
<a href="Signal_Integrity.pdf">Signal_Integrity.pdf</a>. It carries the continuous
argument where the decks carry the interactive models, and it is generated from the same
computations, so a number cannot differ between the two.</p>
</div>

<h2 class="section-title">How to read the series</h2>
<div class="panel">
<ul>
<li><strong>Decks 01&ndash;04</strong> build the passive channel: what a transmission line
is, where the return current flows, what the materials do to the signal, and what happens
at the one feature that is made by drilling.</li>
<li><strong>Decks 05&ndash;06</strong> are about the signal on it &mdash; why it is
differential, and the one impairment no equaliser can remove.</li>
<li><strong>Decks 07&ndash;10</strong> are about jitter &mdash; the quantity a serial
link is finally judged on, and the one most often mis-stated.</li>
<li><strong>Decks 11&ndash;14</strong> are about power integrity, ending with the four
routes by which a disturbance on a rail reaches the eye.</li>
<li><strong>Deck 15</strong> assembles a timing budget; <strong>decks 16&ndash;17</strong>
ask whether any of it can be believed, and how a standard turns it into a verdict.</li>
</ul>
<p style="margin-top:0.8rem">Most decks are worked against one channel &mdash; the
28.8&nbsp;inch backplane characterised in
<a href="https://brendanjameslynskey.github.io/SerDes_Equalisation/">Equalisation in
High-Speed Serial Links</a> &mdash; so the numbers in one deck can be set against the
numbers in another.</p>
</div>

<h2 class="section-title">Related material</h2>
<div class="panel">
<table>
<thead><tr><th>Repository</th><th>How it relates</th></tr></thead>
<tbody>
<tr><td><a href="https://brendanjameslynskey.github.io/SerDes_Equalisation/">Equalisation in High-Speed Serial Links</a></td><td>The worked channel this series keeps returning to, taken from S-parameters to a closed link budget</td></tr>
<tr><td><a href="https://brendanjameslynskey.github.io/Matrix_Methods_Network_Parameters/">Matrix Methods in Network Parameters</a></td><td>The S-, Z- and Y-parameter algebra behind every cascade here</td></tr>
<tr><td><a href="https://brendanjameslynskey.github.io/Matrix_Concepts_Digital_Filters/">Matrix Concepts in Digital Filters</a></td><td>The optimal-tap theory behind every equaliser</td></tr>
<tr><td><a href="https://brendanjameslynskey.github.io/Kramers_Kronig_Relations/">Kramers&ndash;Kronig Relations</a></td><td>The causality constraint decks 03 and 16 both lean on</td></tr>
<tr><td><a href="https://github.com/BrendanJamesLynskey/Interview_High_Speed_Serial_Links">High-Speed Serial Links &mdash; interview preparation</a></td><td>The written companion: notes and worked problems on the same ground</td></tr>
<tr><td><a href="https://github.com/BrendanJamesLynskey/Interview_LPDDRx_Layout">LPDDRx Layout &mdash; interview preparation</a></td><td>The parallel-bus side of deck 15</td></tr>
<tr><td><a href="https://github.com/BrendanJamesLynskey/SoC">Modern SoC Design</a></td><td>The silicon side: its deck 04 on SerDes, 09 on power delivery, 13 on clocks</td></tr>
<tr><td><a href="https://github.com/BrendanJamesLynskey/Hardware">Hardware</a></td><td>The index this series sits in</td></tr>
</tbody>
</table>
</div>

<footer>
  <p>__NSLIDES__ slides across seventeen decks &middot; single-page HTML &middot;
  KaTeX-rendered maths &middot; no build step</p>
  <p style="margin-top:.5rem"><a href="https://github.com/BrendanJamesLynskey/Signal_Integrity">Source
  on GitHub</a> &middot; models in
  <a href="https://github.com/BrendanJamesLynskey/Matrix_Articles">Matrix_Articles</a></p>
</footer>

</div>
</body>
</html>
""")
    html = ''.join(out).replace('__NSLIDES__', str(n_slides))
    os.makedirs(REPO, exist_ok=True)
    with open(os.path.join(REPO, 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('  %-34s landing page, %d slides indexed' % ('index.html', n_slides))


if __name__ == '__main__':
    build_all()
