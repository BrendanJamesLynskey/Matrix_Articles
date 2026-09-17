# Matrix Articles — sources and models

The generators behind four published sets of material: three companion articles on
matrix methods in engineering, and the eleven-deck
[Signal Integrity & High-Speed Digital Design](https://github.com/BrendanJamesLynskey/Signal_Integrity)
series.

Nothing in any of the published decks or reports is a number typed in by hand. Each one
is computed here, serialised, and embedded in the output — so a figure changes only when
a model changes.

---

## What this repository produces

| Output | Form | Built by |
|---|---|---|
| [Matrix Methods in Network Parameters](https://brendanjameslynskey.github.io/Matrix_Methods_Network_Parameters/) | 20-slide deck + 14 pp PDF | `deck_network_body.html`, `build_network.py`, `figs_network.py` |
| [Matrix Concepts in Digital Filters](https://brendanjameslynskey.github.io/Matrix_Concepts_Digital_Filters/) | 12-slide deck + 7 pp PDF | `deck_filters_body.html`, `build_filters.py`, `figs_filters.py` |
| [Equalisation in High-Speed Serial Links](https://brendanjameslynskey.github.io/SerDes_Equalisation/) | 20-slide deck + 27 pp PDF | `deck_serdes_body.html`, `build_serdes.py`, `figs_serdes.py`, **`serdes_model.py`** |
| [Signal Integrity & High-Speed Digital Design](https://brendanjameslynskey.github.io/Signal_Integrity/) | 11 decks, 130 slides | `deck_si_*_body.html`, `assemble_si.py`, **`si_models/`** |

---

## `serdes_model.py` — the channel

The source of truth for the equalisation article, and imported read-only by two of the
signal-integrity decks so that the article's published results are never disturbed.

It builds a 28.8 inch backplane channel as an ABCD cascade of lossy differential
transmission-line sections, vias, connectors and an un-backdrilled via stub; takes the
pulse response by inverse transform of the resulting S<sub>dd21</sub>; designs the CTLE,
transmit feed-forward and decision-feedback taps against that pulse response; and
computes the noise budget plus a sweep of candidate remedies.

Its headline results: &minus;33.3 dB at Nyquist, Q of 6.01, **1.36 dB short** of a
10<sup>&minus;12</sup> error rate — and changing the board buys 1.5–2.5 dB while more
silicon buys 0.26–0.46 dB.

## `si_models/` — the signal-integrity series

One module per deck, plus a shared field solver.

| Module | Deck | What it computes |
|---|---|---|
| `fdm2d.py` | shared | A 2-D electrostatic field solver for PCB cross-sections. Capacitance matrices by relaxation, inductance from `L = μ₀ε₀·inv(C_air)`. Validated against Cohn's exact coupled-stripline result to better than 0.2 % |
| `tline.py` | 01 | Propagation regions, coaxial impedance optima, reflection series, synthesised TDR |
| `retpath.py` | 02 | Return-current distribution, slot-crossing inductance, stitching vias, plane-cavity modes |
| `materials.py` | 03 | Skin effect, Hammerstad and Huray roughness, Djordjević–Sarkar causal permittivity, Kramers–Kronig check, fibre-weave skew |
| `via.py` | 04 | Via capacitance and inductance, stub resonance, back-drill sweep, launch-compensated optimisation |
| `diffpair.py` | 05 | Modal impedances, the loss cost of tight coupling, skew and modal-velocity mode conversion |
| `xtalk.py` | 06 | NEXT and FEXT coefficients, spacing sweeps, guard traces, integrated crosstalk noise |
| `pdn.py` | 07 | Decoupling-ladder impedance, anti-resonance, simultaneous switching noise, supply-noise-to-jitter |
| `jitter.py` | 08 | Dual-Dirac, bathtub curves, extrapolation error, phase-noise integration, CDR transfer and tolerance |
| `timing.py` | 09 | Flight time, setup and hold, statistical versus worst-case budgets, bus-clocking comparison |
| `sparam_qc.py` | 10 | Passivity, reciprocity, causality (time-domain and minimum-phase), truncation, de-embedding, correlation |
| `com.py` | 11 | A scoped channel-operating-margin implementation and the compliance masks |
| `run_all.py` | — | Runs everything and writes `_si_data/*.json`, including `verification.json` |

---

## Rebuilding

```bash
# the signal-integrity series
python3 si_models/run_all.py          # compute everything -> _si_data/*.json
python3 assemble_si.py                # build the 11 decks + landing page
python3 make_si_readme.py             # regenerate that repo's README

# the three matrix-methods decks
python3 assemble_decks.py

# the PDFs (written to ~/Downloads and copied into each repo)
python3 figs_network.py && python3 build_network.py
python3 figs_filters.py && python3 build_filters.py
python3 figs_serdes.py  && python3 build_serdes.py
```

`_house_style.css.html` is the shared `<style>` block, lifted verbatim from the
`MML_04_Matrix_Decompositions` deck so that everything drops into the existing family;
only the accent colour changes per deck.

**Do not re-run `serdes_model.py` casually.** The equalisation article quotes its output
throughout, and the remedies table's conclusion — board 1.5–2.5 dB against silicon
0.26–0.46 dB — has to survive any retune.

---

## Verification

Every model that has an independently published worked example is checked against it,
and the results are written to `_si_data/verification.json` and surfaced on the
[series landing page](https://brendanjameslynskey.github.io/Signal_Integrity/). Sources
used as checks include Johnson and Graham's propagation-region table, Hall and Heck's
roughness and fibre-weave examples, and Cohn's exact coupled-stripline result.

---

## Related

- [Signal Integrity & High-Speed Digital Design](https://github.com/BrendanJamesLynskey/Signal_Integrity) — the eleven-deck series
- [Hardware](https://github.com/BrendanJamesLynskey/Hardware#signal-integrity--high-speed-digital-design) — where the series is indexed
- [Mathematics](https://github.com/BrendanJamesLynskey/Mathematics#linear-algebra) — where the three matrix decks are indexed
- [SI_SERIES_BRIEF.md](SI_SERIES_BRIEF.md) — the brief the series was built from
