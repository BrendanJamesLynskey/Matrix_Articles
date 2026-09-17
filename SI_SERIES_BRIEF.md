# Brief: Signal Integrity & High-Speed Digital Design presentation series

Handover written 2026-09-17 at the end of the session that produced
`SerDes_Equalisation`. Everything below is verified state, not plan.

---

## 1. What is being asked for

A **new multi-deck series** on Signal Integrity, high-speed digital design and
high-speed serial links, built in the same house style as the existing decks,
indexed from the **Hardware** repo, cross-referenced to the existing material,
with all relevant READMEs updated and everything published to GitHub Pages.

Four reference libraries were named by the user:

| Source | What is there | Use it for |
| --- | --- | --- |
| <https://www.colorado.edu/faculty/bogatin/publications/si-journal> | Eric Bogatin's SI Journal columns, 2017–2025. Transmission-line design and characterisation, fine-line differential pairs, split ground planes, power integrity disagreements, FFT with real-time scopes, EM simulator accuracy, fine-line PCBs with high-density BGAs | Pedagogy and the "what practitioners actually argue about" angle. Bogatin is opinionated and quotable |
| <https://www.simberian.com/AppNotes.php> and <https://www.simberian.com/Articles.php> | Yuriy Shlepnev's app notes. Dielectric and conductor-roughness models, material identification, via design to 120 GHz, "Via Design for 112 Gbps and Beyond", decompositional EM analysis, fabrication-tolerance effects, the "How Interconnects Work" series | The rigorous end: causal material models, roughness, via design, how to validate an EM model against measurement |
| <https://siguys.com/published-works/> | Donald Telian. Serial-link simulation and analysis, IBIS-AMI, S-parameter correlation, "The Two Things that Make Serial Links Work", the 1-to-70 Gbps SI cheat sheet, DesignCon best papers 1997/2009/2014/2022 | The simulation-and-correlation workflow, and the practitioner's rules of thumb |
| <https://www.signalintegrityjournal.com/blogs/12-fundamentals> | SIJ Fundamentals blog. PAM2 vs PAM4, planning PCB layouts, anatomy of crosstalk, why 50 ohms, unbounded jitter, bandwidth for modelling and measurement, absorption/dissipation/dispersion, PI impedance vs frequency, impedance-corrected de-embedding | Ready-made deck topics. Several map one-to-one onto slides |

**Do not copy from these.** Read them, verify the physics independently, and
write original material that cites them. The existing articles' credibility
rests on every number being computed rather than asserted — keep that.

---

## 2. What already exists (verified this session)

### The three finished decks in this family
All live, all in the house style, all with a long-form PDF alongside.

| Repo | Content |
| --- | --- |
| `Matrix_Methods_Network_Parameters` | 20 slides. S/Z/Y, travelling vs power waves, mixed-mode and skew, passivity, causality, Smith chart |
| `Matrix_Concepts_Digital_Filters` | 12 slides. State-space stability, Wiener–Hopf, eigenfilter, paraunitary banks |
| `SerDes_Equalisation` | 20 slides, 27 pp PDF. The worked 28 GBd backplane channel end to end |

### Adjacent material already on GitHub — link to it, do not duplicate it
- **`SoC`** — 16 decks. `04-serdes-io` (SerDes & I/O, 23 slides), `01-soc-packaging`,
  `08-cxl-in-ml-accelerator-socs`, `09-power-delivery`, `13-clocks-and-resets`.
  **Check this first for overlap before writing any deck.**
- **`Interview_High_Speed_Serial_Links`** — markdown notes + worked problems.
  Sections: foundations (link budget, channel loss, COM, NRZ/PAM4/PAM6),
  transmitter (drivers, FIR, PLL/jitter), receiver (CTLE, DFE, CDR), protocols
  (PCIe Gen5/6, UCIe, NVLink), **signal integrity** (eye analysis, crosstalk,
  power-supply noise coupling), system integration. **Closest neighbour — a lot
  of the intended series content is already written here as prose.** The natural
  move is to make the new decks the *visual, computed, interactive* companion to
  these notes, and cross-link both ways.
- **`Interview_LPDDRx_Layout`**, **`AMBA`**, **`Kramers_Kronig_Relations`**,
  `NVIDIA_GPU_14_PCIe_and_GPUDirect`, `NVIDIA_GPU_05_NVLink_NVSwitch`,
  `Google_TPU_10_ICI_and_OCS`.

### Indexing done in this session (already pushed — do not redo)
- `Hardware/README.md` has a new **"Signal Integrity & High-Speed Digital Design"**
  section listing SerDes_Equalisation, both Matrix decks, Kramers–Kronig, and the
  two interview repos. `Hardware/index.html` has a matching card.
  **This is where the new series goes.**
- `SerDes_Equalisation/README.md` has a "Related material" table pointing at all
  of the above.
- `Mathematics` (README + index.html) indexes the three decks under
  Linear Algebra → "Matrix Methods in Engineering".
- `DSP_and_Music` (README + `SignalProcessingGuides.md#matrix-methods`) too.

---

## 3. How to build a deck in this house style

**Read `reference_deck_house_style` in memory first**, then:

```
cd ~/Claude_sandbox/Matrix_Articles
python3 assemble_decks.py      # builds all decks from deck_*_body.html
```

- `_house_style.css.html` is the shared `<style>` block, lifted verbatim from
  `MML_04_Matrix_Decompositions`. Only `--accent` changes per deck.
- `assemble_decks.py` glues head + body + footer and writes `index.html` into
  each repo. Add a `build()` call per new deck.
- `docstyle.py` + `build_*.py` produce the matching ReportLab PDFs; `figs_*.py`
  produce the matplotlib figures. Follow `build_serdes.py` for structure.
- **Gotcha:** `text-transform:uppercase` on `.metric-label` / `.callout-label`
  corrupts rendered KaTeX (ω→Ω, σ→Σ). The override is already in
  `assemble_decks.py`'s `EXTRA_CSS`.
- **Gotcha:** `.canvas-wrap canvas` defaults to `image-rendering:pixelated`;
  already overridden.

### Verification (do this every time, it caught several real errors)
```
SC=<scratchpad>
NODE_PATH=/home/brendan/Claude_sandbox/node_modules node verify.js <file> <prefix>
```
Chrome + puppeteer are preinstalled. Allow `cdn.jsdelivr.net` through the
request interceptor or KaTeX will not render. Check `pageerrors`, that every
canvas painted, and `hscroll === false`. See `reference_web_verify_puppeteer`.

### Publishing
```
gh repo create BrendanJamesLynskey/<NAME> --public --source=. --push --description "..."
gh api --method POST repos/BrendanJamesLynskey/<NAME>/pages \
   -f 'source[branch]=main' -f 'source[path]=/'
```
Branch Pages, not a workflow. Then poll until the URL returns 200.

---

## 4. Standing instructions from the user, learned the hard way

These came from a reviewer over several rounds and **must not regress**:

1. **Every number must be computed, not asserted.** `serdes_model.py` is the
   source of truth for the SerDes article — an ABCD cascade channel model, pulse
   response by IFFT, equaliser taps designed against it, and a `remedies()`
   sweep. New decks should have an equivalent model file. The reviewer notices
   when they don't.
2. **Prose, not telegraphese.** Continuous argument in full sentences. No
   "Takeaway:" stubs, no noun-phrase fragments. This was the single biggest
   complaint about the first drafts.
3. **Define terms before using them.** The last round of feedback was precisely
   this — XAUI and CEI-28G were used unexplained. §2.1 of the SerDes article now
   decodes PCIe, IEEE 802.3 and OIF CEI naming. Apply the same discipline.
4. **Scale-invariant statements.** The reviewer correctly objected to "the cursor
   falls monotonically" because it depends on arbitrary gain. Prefer ratios.
5. **Flag collisions of terminology.** e.g. communications Q-factor vs resonator
   Q — the user's reviewer works across both and it genuinely bit.
6. Check figure captions against the figures. Two were wrong and he caught both.
7. British spelling: equalisation, normalised, laminate, behaviour.

---

## 5. Suggested series shape (a starting point, not a decision)

Six to eight decks, sized like the existing ones (12–20 slides), each with a
computed model and at least one interactive widget. Avoid the SoC series'
ground.

1. **Transmission lines and the physical channel** — why a trace is a waveguide,
   impedance, the 50 Ω convention and why it is a convention, propagation,
   reflections, TDR. (Bogatin; SIJ "Why 50 Ohms".)
2. **Materials and loss** — conductor loss and roughness (Hammerstad, Huray),
   dielectric loss and causal Djordjević–Sarkar models, fibre weave. (Simberian
   app notes are the authority here.) Partly drafted already as §3.2 of the
   SerDes article — extend, don't repeat.
3. **Vias, connectors and discontinuities** — stubs and back-drilling, antipads,
   the waveguiding view of via design, launch structures. (Simberian.)
4. **Crosstalk** — NEXT/FEXT, the anatomy of coupling, guard traces, GSSG,
   ICN. (SIJ "Anatomy of Crosstalk".)
5. **Power integrity** — PDN impedance vs frequency, target impedance,
   decoupling, SSN and its coupling into the link. (Bogatin; SIJ PI fundamentals.)
6. **Jitter** — taxonomy (RJ/DJ/PJ/DDJ/ISI), bathtub curves, unbounded jitter,
   phase noise to jitter, CDR jitter tolerance and transfer. (SIJ "Unbounded
   Jitter".)
7. **Measurement and correlation** — VNA vs TDR, de-embedding and fixture
   removal, S-parameter quality checks, correlating simulation to measurement,
   IBIS-AMI. (Telian; Simberian validation papers.)
8. **Putting it together: COM and compliance** — how a standard decides a channel
   is legal, and how that relates to the hand budget in `SerDes_Equalisation`.

Confirm the shape with the user before building all of them.

---

## 6. Things to be careful about

- The PDFs are written to `~/Downloads` and copied into each repo. Keep both.
- `Claude_sandbox` root is **not** a git repo; each project directory is its own.
- `DSP_and_Music` has no Pages site (README-only hub) — a 404 there is expected.
- Don't re-run `serdes_model.py` casually: the article quotes its output
  throughout and the remedies table's punchline (board buys 1.5–2.5 dB, silicon
  buys 0.26–0.46 dB) must survive any retune.
