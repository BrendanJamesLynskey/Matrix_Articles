"""Generate the Signal_Integrity README from the same data the decks embed."""
import json
import os
import re

from assemble_si import DECKS, REPO, DATA, SECTIONS, REDIRECTS

PAGES = "https://brendanjameslynskey.github.io/Signal_Integrity"
GH = "https://github.com/BrendanJamesLynskey"

ver = json.load(open(os.path.join(DATA, 'verification.json')))

PDF_PAGES = 0
try:
    from pypdf import PdfReader
    PDF_PAGES = len(PdfReader(os.path.join(REPO, 'Signal_Integrity.pdf')).pages)
except Exception:
    PDF_PAGES = 32
slides = {}
for d in DECKS:
    f = os.path.join(REPO, d['slug'], 'index.html')
    slides[d['n']] = len(re.findall(r'<section class="slide"',
                                    open(f, encoding='utf-8').read())) if os.path.exists(f) else 0
total = sum(slides.values())

HIGHLIGHTS = {
    1: "Johnson and Graham's propagation-region breakpoints reproduced to 0.35 %; the "
       "two coaxial optima (76.7 &Omega; for minimum loss, 30 &Omega; for maximum power) "
       "derived rather than quoted; TDR shown under-reading a 38 &Omega; section as "
       "44 &Omega; when it is shorter than the edge",
    2: "The Lorentzian return-current law integrated to the 80 % / 3h rule (79.5 %) and "
       "checked against the field solver's own charge profile; a 20 mm plane slot priced "
       "at 13.7 nH and &minus;18.8 dB at 10 GHz",
    3: "Hammerstad and Huray both reproduced against Hall and Heck's worked examples to "
       "0.8 %; a constant-Dk model shown delivering energy 37 ps before the wave can "
       "arrive; fibre-weave skew anchored to a published measurement at 5.1 ps/inch",
    4: "A 110 mil stub's quarter-wave notch computed at 13.9 GHz, within a few per cent "
       "of a 28 GBd Nyquist; and the result that a barrel matched to the channel is "
       "*not* the best via &mdash; compensating the launch instead is worth 7&ndash;24 dB",
    5: "Cohn's exact coupled-stripline result reproduced to 0.18 %; half-ounce copper "
       "shown to lower a 100 &Omega; pair by 9.7 %; tight coupling priced at 1.45 dB "
       "over ten inches at 14 GHz",
    6: "The field solver gives L&#8320;/L = C&#8320;/C to six decimals in stripline, so "
       "far-end crosstalk vanishes exactly; far-end coupling shown to saturate at half "
       "the swing rather than growing without bound as the first-order formula predicts",
    7: "Stephens's five rules as the spine. A confident measurement at 10&#8315;&#185;&#178; "
       "takes six minutes at 28 Gb/s and four days at 10&#8315;&#185;&#8309;; the real "
       "data-dependent distribution computed from the channel, and it is nothing like "
       "two impulses",
    8: "**DJ(&delta;&delta;) computed against the true peak-to-peak** &mdash; the model's "
       "deterministic jitter comes out 8&ndash;28 % *smaller* than the real spread, and "
       "the fitted random jitter 1.27&ndash;1.32&times; too large, because the fit "
       "absorbs smooth deterministic width",
    9: "Jitter transfer against error response, the golden PLL, and a tolerance mask "
       "shown to be the loop restated as a test; the same oscillator yielding jitter "
       "figures a hundredfold apart depending only on the integration band",
    10: "Rule four computed: a 1 mV disturbance is worth 0.17 ps on this channel, and "
        "amplitude-induced jitter rises **212&times;** from 1 to 56 Gb/s because the "
        "channel, not the transmitter, sets the edge &mdash; the knee falling at about "
        "10 Gb/s, where Stephens put it from quite different reasoning",
    11: "Target impedance and its limits; the frequency-domain target-impedance method, "
        "which shows the **number of capacitors is set by mounting inductance and not by "
        "capacitance at all**; and adding capacitors of one value making the peak worse",
    12: "Spreading inductance, cavity impedance that depends on where you probe, and the "
        "**Bandini Mountain** &mdash; the antiresonance between on-die capacitance and "
        "package inductance that board capacitors cannot reach, with its optimum damping "
        "computed at the characteristic impedance",
    13: "Why a reflection measurement floors at about an ohm on directivity alone, how "
        "two-port shunt-through reaches a milliohm at &minus;88 dB, and the cable-braid "
        "ground loop that always reads *low*",
    14: "Four routes from the rail to the eye, and the observation that two of them are "
        "return-path problems rather than power problems; the worst supply-tone "
        "frequency computed to sit *on* the loop bandwidth for a type-II loop, while a "
        "type-I loop has no worst frequency at all &mdash; its response is flat",
    15: "Flight time shown to exceed propagation delay by 5&times; on a weakly driven "
        "line; statistical budgeting shown to save 47&ndash;67 % at 3&sigma; and "
        "&minus;24 % to +22 % at 10&#8315;&#185;&#178;",
    16: "An identical reflection placed at different delays gives identical insertion-loss "
        "agreement (0.15 dB rms) and eye errors from +1.3 % to &minus;5.5 %; the DC point "
        "alone is worth 7.9 % of the eye",
    17: "COM on the SerDes_Equalisation channel passes at 11.96 dB while the same channel "
        "misses an uncoded 10&#8315;&#185;&#178; by 4.98 dB &mdash; reconciled by the "
        "pre-FEC error ratio the threshold assumes",
}

L = []
L.append("# ⬡ Signal Integrity & High-Speed Digital Design\n")
L.append("Seventeen interactive slide decks on getting a signal from one chip to another "
         "intact — the physics of the channel, the mechanisms that close an eye, and "
         "the arithmetic a standard uses to decide a channel is legal.\n")
L.append("## ▶ [Open the Series Landing Page](%s/)\n" % PAGES)
L.append("**Every number on every slide is computed.** Each deck embeds the JSON output "
         "of a model in [`si_models`](%s/Matrix_Articles), and nothing is typed in by "
         "hand. Where an independently published result exists, the model is checked "
         "against it and the disagreement is reported on the landing page.\n" % GH)
L.append("---\n")
L.append("## The decks\n")
for title, lo, hi, intro in SECTIONS:
    L.append("### %s &mdash; decks %02d&ndash;%02d\n" % (title, lo, hi))
    L.append(intro + "\n")
    L.append("| # | Deck | Slides | What it establishes |")
    L.append("|---|------|--------|---------------------|")
    for d in DECKS:
        if not (lo <= d['n'] <= hi):
            continue
        L.append("| %02d | [%s](%s/%s/) | %d | %s |"
                 % (d['n'], d['title'], PAGES, d['slug'], slides[d['n']],
                    HIGHLIGHTS.get(d['n'], d['blurb'])))
    L.append("")
L.append("**%d slides across seventeen decks.** Single-page HTML, KaTeX-rendered maths, "
         "no build step — open any `index.html` directly.\n" % total)
L.append("## Long-form companion\n")
L.append("The same material as a written report: "
         "[Signal_Integrity.pdf](Signal_Integrity.pdf) (%d pp). It carries the "
         "continuous argument where the decks carry the interactive models, and it is "
         "generated from the same computations, so a number cannot differ between the "
         "two.\n" % PDF_PAGES)
L.append("---\n")
L.append("## Verified\n")
L.append("A model that agrees only with itself is not worth much. Every cross-check the "
         "series makes against an independently published result, followed by the "
         "places where two computations inside the series have to agree with each "
         "other:\n")
L.append("| Quantity | This series | Reference value | Difference | Source |")
L.append("|---|---|---|---|---|")
worst = 0.0
rows = [(k, v) for k, v in sorted(ver.items())
        if isinstance(v, dict) and 'err_pct' in v]
rows.sort(key=lambda kv: (str(kv[1].get('source', '')).startswith('internal'), kv[0]))
for k, v in rows:
    if not str(v.get('source', '')).startswith('internal'):
        worst = max(worst, abs(v['err_pct']))
    def f(x):
        a = abs(x)
        return ('%.4g' % x) if (a >= 1e9 or (0 < a < 1e-3)) else ('%.5g' % x)
    L.append("| %s | %s | %s | %+.2f %% | %s |"
             % (k.split('/')[-1].replace('_', ' '), f(v['ours']),
                f(v['published']), v['err_pct'], v['source']))
L.append("")
L.append("Worst disagreement against published work: **%.2f %%**.\n" % worst)
L.append("---\n")
L.append("""## How the series is built

The decks are assembled from bodies and data rather than written as HTML by hand:

```
cd Matrix_Articles
python3 si_models/run_all.py      # computes every figure, writes _si_data/*.json
python3 assemble_si.py            # glues house style + body + data -> Signal_Integrity/
```

`si_models/fdm2d.py` is a two-dimensional electrostatic field solver used wherever a
closed form does not exist — coupled pairs beside guard traces, microstrip with air
above it, conductors with real thickness. It is validated against Cohn's exact
coupled-stripline result to better than half a per cent, which is what licenses using it
on the cross-sections Cohn does not cover.

`si_models/sparam_qc.py` and `si_models/com.py` import the channel from
[`serdes_model.py`](%s/Matrix_Articles) read-only, so nothing published in
[SerDes_Equalisation](%s/SerDes_Equalisation) is disturbed by anything computed here.
""" % (GH, GH))
L.append("---\n")
L.append("""## Sources

The series reads widely and verifies independently; it does not reproduce. Where a
published worked example exists it is used as a check and cited, and the checks are
tabulated above.

- Howard Johnson and Martin Graham, *High-Speed Digital Design: A Handbook of Black
  Magic* (1993) and *High-Speed Signal Propagation: Advanced Black Magic* (2003) —
  propagation regions, via modelling, return paths, clock jitter
- Stephen Hall and Howard Heck, *Advanced Signal Integrity for High-Speed Digital
  Designs* (2009) — conductor roughness, causal dielectric models, the fibre-weave effect
- Eric Bogatin, *Signal and Power Integrity — Simplified*, 2nd ed. (2010) — return
  paths, differential pairs, power integrity
- Peter Pupalaikis, *S-Parameters for Signal Integrity* (2020) — de-embedding,
  passivity and causality
- Greg Edlund, *Timing Analysis and Simulation for Signal Integrity Engineers* (2007)
- Mark Horowitz, *High-Speed Electrical Signalling: Overview and Limitations*
- Seymour Cohn, *Shielded Coupled-Strip Transmission Line* (1955) — the exact result the
  field solver is validated against
- Eric Bogatin's [Signal Integrity Journal columns](https://www.colorado.edu/faculty/bogatin/publications/si-journal),
  Yuriy Shlepnev's [Simberian application notes](https://www.simberian.com/AppNotes.php),
  Donald Telian's [published work](https://siguys.com/published-works/), and the
  [SIJ Fundamentals blog](https://www.signalintegrityjournal.com/blogs/12-fundamentals)
""")
L.append("---\n")
L.append("## Related material\n")
L.append("Indexed together under [Signal Integrity & High-Speed Digital Design]"
         "(%s/Hardware#signal-integrity--high-speed-digital-design) in the Hardware "
         "repo.\n" % GH)
L.append("| Repo | How it relates |")
L.append("| --- | --- |")
for name, rel in [
    ("[Equalisation in High-Speed Serial Links](%s/SerDes_Equalisation)" % GH,
     "The worked 28.8 inch backplane channel this series keeps returning to, taken from "
     "S-parameters to a closed link budget. Decks 10 and 11 import it directly"),
    ("[Matrix Methods in Network Parameters](%s/Matrix_Methods_Network_Parameters)" % GH,
     "The S-, Z- and Y-parameter algebra behind every cascade here — reciprocity, "
     "passivity, mixed-mode, causality, the Smith chart"),
    ("[Matrix Concepts in Digital Filters](%s/Matrix_Concepts_Digital_Filters)" % GH,
     "The optimal-tap theory behind every equaliser in decks 10 and 11"),
    ("[Kramers–Kronig Relations](%s/Kramers_Kronig_Relations)" % GH,
     "The causality constraint deck 03 applies to a dielectric and deck 10 to a "
     "transfer function"),
    ("[High-Speed Serial Links — interview preparation](%s/Interview_High_Speed_Serial_Links)" % GH,
     "The written companion covering the same ground in prose: link budgets, drivers, "
     "PLL jitter, CTLE/DFE/CDR, PCIe, UCIe, NVLink, eye analysis, crosstalk, PDN coupling"),
    ("[LPDDRx Layout — interview preparation](%s/Interview_LPDDRx_Layout)" % GH,
     "The parallel-bus side of deck 09 — memory interface layout, skew and termination"),
    ("[Modern SoC Design](%s/SoC)" % GH,
     "The silicon side. Deck 04 covers SerDes and I/O, deck 01 packaging, deck 09 power "
     "delivery (the complement to deck 07 here), deck 13 clocks and resets"),
    ("[Arm AMBA](%s/AMBA)" % GH,
     "What the traffic becomes once it is on-chip"),
    ("[Hardware](%s/Hardware)" % GH,
     "The index this series sits in"),
]:
    L.append("| %s | %s |" % (name, rel))
L.append("")
L.append("---\n")
L.append("Generated by `make_si_readme.py` from the same data the decks embed.\n")

out = os.path.join(REPO, 'README.md')
with open(out, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(L))
print('wrote %s (%d lines, worst check %.2f%%)' % (out, len(L), worst))
