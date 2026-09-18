"""Builds the long-form companion to the Signal Integrity deck series.

One chapter per deck. Every figure comes from figs_si.py and every number from
_si_data/*.json, which si_models/run_all.py computes, so the report and the
decks cannot disagree.
"""

import json
import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageTemplate, Paragraph, Spacer, PageBreak)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docstyle import (callout, datatable, page_furniture, register_fonts,  # noqa: E402
                      styles)
from simplemath import M  # noqa: E402

register_fonts()
S = styles()
FIG = os.path.join(HERE, "figs_si")
DATA = os.path.join(HERE, "_si_data")
CW = 158 * mm

D = {n: json.load(open(os.path.join(DATA, "deck%02d.json" % n)))
     for n in range(1, 18)}
VER = json.load(open(os.path.join(DATA, "verification.json")))

story = []
A = story.append


from reportlab.platypus import HRFlowable  # noqa: E402
from docstyle import RULE as _RULE  # noqa: E402


def CHAP():
    """Separate chapters with space and a rule rather than a forced page break.

    Forcing every chapter onto a fresh page left several pages nearly empty,
    which reads worse than a continuous flow in a report this length."""
    A(Spacer(1, 9))
    A(HRFlowable(width=CW, thickness=0.6, color=_RULE, spaceAfter=4))


def P(t): A(Paragraph(M(t), S["body"]))
def H1(t): A(Paragraph(M(t), S["h1"]))
def H2(t): A(Paragraph(M(t), S["h2"]))
def CO(t): A(callout(M(t), S, CW))
def SP(h=4): A(Spacer(1, h))


def img(name, width_mm):
    from PIL import Image as PILImage
    p = os.path.join(FIG, name + ".png")
    w, h = PILImage.open(p).size
    W = width_mm * mm
    return Image(p, width=W, height=W * h / w)


def FIGURE(name, caption, width_mm=150):
    A(KeepTogether([img(name, width_mm), Paragraph(M(caption), S["caption"])]))


def TABLE(rows, widths, caption=None):
    A(datatable([[M(c) for c in row] for row in rows],
                [w * mm for w in widths], S))
    if caption:
        A(Paragraph(M(caption), S["caption"]))
    else:
        SP(8)


# ============================================================ title page ===
A(Paragraph("Signal Integrity and<br/>High-Speed Digital Design", S["title"]))
A(Paragraph("The long-form companion to the seventeen-deck series", S["deck"]))
A(Paragraph("Brendan Lynskey &nbsp;·&nbsp; every figure computed, "
            "every model checked", S["byline"]))

P("This report accompanies seventeen interactive decks on getting a signal from one chip "
  "to another intact. It is not a summary of them: the decks carry the interactive "
  "models and this carries the continuous argument, and they are generated from the "
  "same computations so that a number cannot differ between the two.")

P("The organising discipline is that nothing is asserted. Every figure in this document "
  "is produced by a model in <font name='DejaVu-Bold'>si_models</font>, and wherever an "
  "independently published worked example exists the model is checked against it and "
  "the disagreement reported. Appendix A tabulates every such check; the worst "
  "disagreement across all of them is %.2f per cent."
  % max(abs(v['err_pct']) for v in VER.values()
        if isinstance(v, dict) and 'err_pct' in v
        and not str(v.get('source', '')).startswith('internal')))

P("Most chapters are worked against a single channel &mdash; the 28.8 inches of "
  "differential stripline across two line cards and an 18-inch backplane characterised "
  "in <i>Equalisation in High-Speed Serial Links</i> &mdash; so that a result in one "
  "chapter can be set against a result in another without an argument about whether the "
  "comparison is fair. Chapters 10, 16 and 17 import that channel directly.")

CO("<font name='DejaVu-Bold'>How to read this.</font> Chapters 1 to 4 build the passive "
   "channel: what a transmission line is, where the return current flows, what the "
   "materials do, and what happens at the one feature made by drilling. Chapters 5 and 6 "
   "concern the signal on it. Chapters 7 to 10 are about jitter, which is the quantity a "
   "serial link is finally judged on and the one most often mis-stated. Chapters 11 to "
   "14 are about power integrity, ending with the four routes by which it reaches the "
   "eye. Chapter 15 assembles a timing budget, and chapters 16 and 17 ask whether any of "
   "it can be believed and how a standard turns it into a verdict.")

A(PageBreak())

# ============================================================== chapter 1 ===
H1("1&nbsp;&nbsp;The Transmission Line and the Physical Channel")

P("A wire, in the sense a schematic means, has the same voltage everywhere along it at "
  "every instant. Nothing on a circuit board is that. A trace carries a disturbance at a "
  "finite speed, so while the disturbance is in transit the two ends hold different "
  "voltages, and the question is never whether that is true but whether it matters over "
  "the timescale in play.")

P("The timescale that matters is the rise time of the edge rather than the clock "
  "frequency. A hundred-megahertz clock with a two-hundred-picosecond edge contains "
  "energy well past ten gigahertz whatever its repetition rate. The useful comparison is "
  "between the rise time and the round trip: if the reflection returns while the driver "
  "is still moving, driver and line settle together and the net behaves as a lumped "
  "circuit; if it returns afterwards, the far end has already acted on a voltage that is "
  "about to change.")

r1 = D[1]['regions']
P("Beyond that threshold a line does not have one behaviour but several. Johnson and "
  "Graham's division into propagation regions is the most useful organising idea "
  "available, and each boundary follows from the line's own per-unit-length parameters. "
  "For their worked example &mdash; a 100&nbsp;&#937; differential stripline, six-mil "
  "traces, half-ounce copper, 0.6&nbsp;m of FR-4 &mdash; the boundaries computed here "
  "are as follows.")

FIGURE("regions",
       "Figure 1.1 &mdash; The propagation regions of Johnson and Graham's worked "
       "100&nbsp;&#937; differential stripline. The skin-effect and dielectric-loss "
       "regions are separated by a factor of only %.0f, so neither ever appears in "
       "isolation and the loss never settles into a clean square-root slope."
       % (r1['f_diel'] / r1['f_skin']), 150)

P("The narrowness of that separation is the practical point. Between 27&nbsp;MHz and "
  "about a gigahertz the two mechanisms are mushed together and the loss slope climbs "
  "gradually from one half to one. Anyone fitting a measured channel to a single power "
  "law is fitting the blend rather than either mechanism, which is the subject of "
  "chapter 3.")

H2("1.1&nbsp;&nbsp;Where fifty ohms comes from")

c = D[1]['coax']['air']
P("Fifty ohms is so universal that it is easy to assume it was derived. It was "
  "negotiated. Hold the outer radius of a coaxial line fixed &mdash; the connector shell "
  "and the bulkhead hole decide it &mdash; and vary the inner conductor. Conductor loss "
  "per unit length is proportional to $(x+1)/\\ln x$ with $x = b/a$, which has a single "
  "minimum. Power handling, limited by breakdown at the inner conductor where the field "
  "is strongest, is proportional to $\\ln x / x^2$, which has a single maximum. Neither "
  "is at fifty ohms and they are a factor of %.2f apart."
  % (c['z_min_atten'] / c['z_max_power']))

FIGURE("coax",
       "Figure 1.2 &mdash; The two optima of a coaxial line in air. Minimum attenuation "
       "at $b/a = %.3f$, giving %.1f&nbsp;&#937;; maximum power at $b/a = \\sqrt{e} = "
       "%.4f$, giving %.1f&nbsp;&#937;. Their geometric mean is %.1f&nbsp;&#937;. The "
       "optimum ratios do not depend on the dielectric; only the impedances they "
       "correspond to do."
       % (c['x_min_atten'], c['z_min_atten'], c['x_max_power'],
          c['z_max_power'], c['z_geometric_mean']), 116)

P("Seventy-five ohms is not a second compromise but one of the optima taken neat: a "
  "cable with a mostly-air dielectric has its minimum attenuation within a whisker of "
  "it, which is why the impedance that carries television down long runs is the "
  "lowest-loss one and the impedance that carries laboratory signals is the one that "
  "also handles power.")

P("None of this reasoning applies to a circuit board. There is no breakdown limit near "
  "the operating voltage, the geometry is not free because the stackup sets the layer "
  "thicknesses, and minimum loss would want a trace wider than the package escape "
  "allows. Boards settled near fifty ohms single-ended largely because the instruments "
  "and connectors already were, and what high-speed digital design actually "
  "standardised on is a differential impedance &mdash; 85, 90 or 100 ohms &mdash; chosen "
  "by standards bodies rather than by physics.")

H2("1.2&nbsp;&nbsp;Reading a channel with time-domain reflectometry")

P("Time-domain reflectometry launches a step and records what returns. Because a "
  "reflection arrives at a time set by distance and with an amplitude set by severity, "
  "the returned waveform can be redrawn as impedance against position. The conversion "
  "uses $Z = Z_0(1+\\rho)/(1-\\rho)$ sample by sample, and that relation is exact only "
  "for the first discontinuity &mdash; everything past it is being probed by a wave that "
  "has already been partly reflected.")

FIGURE("tdr",
       "Figure 1.3 &mdash; Left: synthesised TDR of two channels, one with a single "
       "0.4&nbsp;in section at 38&nbsp;&#937; and one with two discontinuities in "
       "series, where the second is reported as less severe than it is. Right: the same "
       "38&nbsp;&#937; section at varying length, probed with a 20&nbsp;ps edge. Below "
       "about 0.2&nbsp;in the instrument reports a shallower, wider feature than the "
       "reality.", 150)

res = [r for r in D[1]['tdr_resolution'] if r['reads_ohm']]
short, long_ = res[0], res[-1]
P("A feature shorter than the spatial extent of the edge is not reported at its true "
  "impedance, because the reflections from its start and end overlap and partly cancel. "
  "A %.2f&nbsp;inch section of 38&nbsp;&#937; line reads %.1f&nbsp;&#937; where a "
  "%.0f&nbsp;inch one reads %.1f. A via, which is a few tens of thousandths of "
  "discontinuity, is well inside the optimistic region for any realistic instrument, "
  "which is why vias are characterised in the frequency domain instead."
  % (short['length_in'], short['reads_ohm'], long_['length_in'], long_['reads_ohm']))

CHAP()

# ============================================================== chapter 2 ===
H1("2&nbsp;&nbsp;Return Paths and Reference Planes")

P("Charge is conserved, so current flows in loops. A driver pushing current down a trace "
  "is pulling an identical current back through something, and on a circuit board that "
  "something is the plane the trace is routed over. This is not a subtlety: the "
  "inductance and capacitance per unit length that chapter 1 rests on are properties of "
  "the loop, not of the trace.")

f2 = D[2]['fraction']
P("Above the frequency at which inductance rather than resistance decides the path "
  "&mdash; a few hundred kilohertz, far below anything a high-speed designer thinks "
  "about &mdash; the return current arranges itself to minimise loop inductance, which "
  "puts it in a narrow band directly under the trace with a Lorentzian profile "
  "$J(x) = (I/\\pi h)\\,[1+(x/h)^2]^{-1}$. Its width is set by the height above the "
  "plane and by nothing else: not by the trace width, not by the frequency, not by the "
  "current.")

FIGURE("return",
       "Figure 2.1 &mdash; Left: the analytic return-current profile against the charge "
       "distribution computed independently by the field solver, with the &plusmn;3h "
       "band shaded. Right: the integrated fraction. Three trace heights either side "
       "captures %.1f per cent, which is the origin of the eighty-per-cent rule; ninety "
       "per cent needs %.1f heights and ninety-nine per cent needs %.0f, because the "
       "distribution has algebraic rather than exponential tails."
       % (100 * f2['at_3h'], f2['half_width_for_90pct'],
          f2['half_width_for_99pct']), 150)

H2("2.1&nbsp;&nbsp;What a gap costs")

s20 = D[2]['slots'].get('20 mm slot') or list(D[2]['slots'].values())[2]
P("A slot in the reference plane forces the return current to run to the end of the slot "
  "and back. That detour is a loop, and its inductance appears in series with the "
  "signal, giving a low-pass transfer function $S_{21} = 1/(1 + j\\omega L/2Z_0)$. A "
  "20&nbsp;mm slot has a loop inductance of %.1f&nbsp;nH against %.2f&nbsp;nH for the "
  "intact plane &mdash; a factor of %.0f &mdash; and the reactance at the signal's knee "
  "frequency reaches %.0f&nbsp;&#937;, comparable with or larger than the line "
  "impedance. The line is effectively open at those frequencies rather than merely "
  "degraded."
  % (s20['l_gap_nh'], s20['l_intact_nh'], s20['ratio'], s20['xl_at_knee_ohm']))

FIGURE("slot",
       "Figure 2.2 &mdash; Left: insertion loss of a trace crossing plane slots of "
       "various lengths. Right: the impedance between a 150&nbsp;&times;&nbsp;100&nbsp;mm "
       "plane pair, behaving as a capacitor until the first cavity mode at "
       "%.2f&nbsp;GHz and as a resonator thereafter."
       % D[2]['plane_z']['f_first_mode_ghz'], 150)

st = D[2]['stitch']
TABLE([["Distance to the return via", "One return via", "Two", "Four"]] +
      [["%.1f mm" % r['distance_mm'], "%.3f nH" % r['n1'],
        "%.3f nH" % r['n2'], "%.3f nH" % r['n4']] for r in st],
      [46, 38, 38, 36],
      "Table 2.1 &mdash; Loop inductance added when a signal changes reference plane, "
      "for one, two and four stitching vias. The dependence is logarithmic, so moving "
      "the return via closer is worth more than adding more of them further away.")

CO("A power plane works exactly as well as a ground plane as a return path, because at "
   "signal frequencies the two are tied together by the decoupling capacitance and are "
   "the same conductor as far as the wave is concerned. What matters is continuity, not "
   "name. Chapter 7 concerns the frequencies at which that tying-together stops working.")

CHAP()

# ============================================================== chapter 3 ===
H1("3&nbsp;&nbsp;Materials, Loss and Causality")

P("A signal loses energy on a board in two separate ways, and keeping them apart is the "
  "most useful distinction in this chapter because they scale differently and are fixed "
  "by different purchases. Conductor loss is ohmic heating in the copper; it grows as "
  "the square root of frequency, because current crowds into a surface layer whose depth "
  "falls as $1/\\sqrt{f}$. Dielectric loss is energy absorbed by the laminate as it is "
  "polarised and re-polarised; it grows roughly in proportion to frequency.")

P("Those exponents mean the mix changes with data rate. At a gigahertz a typical "
  "stripline is conductor-dominated and a wider trace is the cheap fix. Past about ten "
  "gigahertz on most laminates the dielectric term has overtaken, and no amount of "
  "copper helps.")

H2("3.1&nbsp;&nbsp;Roughness, and where the simple model fails")

P("Copper foil is deliberately roughened so that the resin grips it, and the teeth are "
  "on the same scale as the skin depth at the frequencies that matter. Hammerstad's "
  "model fits Morgan's corrugated-surface results to an arctangent; it is in every field "
  "solver and it is bounded, unable to predict a factor greater than two however rough "
  "the copper. Huray's replaces the tooth structure with a cluster of spheres and "
  "computes the power each scatters; it has no ceiling.")

FIGURE("rough",
       "Figure 3.1 &mdash; The two roughness models on three copper profiles. Below "
       "about five gigahertz they agree; above it Hammerstad flattens against its "
       "ceiling of two while Huray keeps climbing, and it is Huray that tracks "
       "measurement on rough foil.", 116)

rc = D[3]['roughness_check']
TABLE([["Quantity", "This model", "Hall &amp; Heck", "Difference"]] +
      [[k.replace('_', ' '),
        "%.4g" % rc[k]['ours'], "%.4g" % rc[k]['published'],
        "%+.2f %%" % rc[k]['err_pct']] for k in rc],
      [62, 32, 32, 32],
      "Table 3.1 &mdash; Both roughness implementations checked against the worked "
      "examples in Hall and Heck, chapter 5, whose values come from measured "
      "transmission lines.")

FIGURE("laminates",
       "Figure 3.2 &mdash; Left: total loss per inch for four laminate generations. "
       "Right: the same loss for Megtron 6 split into its conductor and dielectric "
       "parts, with the crossover marked &mdash; the frequency above which better copper "
       "stops being the answer.", 150)

H2("3.2&nbsp;&nbsp;Why a constant dielectric constant cannot exist")

ca = D[3]['causality']
P("The obvious way to model a laminate is to take the datasheet Dk and Df and hold both "
  "fixed. A great many channel models do this and it is wrong in a way that matters, "
  "because it describes a material that violates causality. The Kramers&ndash;Kronig "
  "relations tie the real and imaginary parts of any causal response together, so a "
  "medium with loss is obliged to have a Dk that falls as frequency rises. Holding it "
  "flat while admitting a nonzero loss tangent asserts an impossibility.")

P("The consequence is not abstract. Over ten inches of Megtron 6 the constant-Dk model "
  "delivers detectable energy %.0f&nbsp;picoseconds before the wave could physically "
  "have arrived &mdash; about %.1f unit intervals at 28&nbsp;GBd. A simulator handed "
  "such a channel reports the result without complaint."
  % (ca['precursor_ps'], ca['precursor_ps'] / 35.71))

FIGURE("causal",
       "Figure 3.3 &mdash; Left: the impulse response of ten inches of laminate modelled "
       "two ways. The constant-Dk curve begins before the time of flight. Right: the "
       "causal Djordjevi&#263;&ndash;Sarkar alternative, whose loss tangent is flat "
       "across the band while its Dk falls logarithmically. The two are not independent "
       "choices; fixing one fixes the other.", 150)

kk = D[3]['kk']
P("The claim can be tested rather than asserted. Reconstructing the real part of each "
  "model's permittivity from its imaginary part by the Kramers&ndash;Kronig integral "
  "leaves a residual of %.3f per cent of Dk for the causal model and %.3f per cent for "
  "the constant one &mdash; a factor of %.0f. The reconstruction is a finite-band "
  "numerical integral, so even a perfect model leaves something; it is the contrast that "
  "carries the argument."
  % (kk['causal']['rel_err_pct'], kk['flat']['rel_err_pct'],
     kk['flat']['rms_err'] / kk['causal']['rms_err']))

H2("3.3&nbsp;&nbsp;The glass weave")

wv = D[3]['weave_check']
P("A laminate is not a uniform dielectric but woven glass yarn, with a relative "
  "permittivity near six, in resin near three. The windows between bundles are wide "
  "enough that one leg of a differential pair can sit over glass while the other sits "
  "over resin. What matters is the spread in <i>effective</i> permittivity seen by the "
  "trace rather than the raw material contrast, because the field spans several yarn "
  "pitches and several plies. That spread has been measured &mdash; 0.23 across "
  "sixty-four parallel microstrips on 2116 cloth &mdash; and that measurement anchors "
  "the model here, giving %.2f&nbsp;ps per inch and predicting full "
  "differential-to-common conversion at %.1f&nbsp;GHz over ten inches against a "
  "published %.0f."
  % (wv['skew_ps_per_in'], wv['ten_inch_ghz']['ours'],
     wv['ten_inch_ghz']['published']))

FIGURE("weave",
       "Figure 3.4 &mdash; Left: intra-pair skew by glass style. Right: the effect of "
       "routing at an angle to the weave, which averages the modulation down by roughly "
       "$1/\\pi N$ where $N$ is the number of yarn pitches crossed. A few degrees over a "
       "few inches is worth more than an order of magnitude.", 150)

CHAP()

# ============================================================== chapter 4 ===
H1("4&nbsp;&nbsp;Vias, Connectors and Discontinuities")

P("Everything else in a channel is defined photographically, to a few micrometres, in "
  "two dimensions. A via is a hole, drilled mechanically, plated, and possibly drilled "
  "again from the other side to remove part of what was just plated. Its tolerances are "
  "an order of magnitude looser than anything else on the board and it is the only "
  "feature that goes vertically, through every plane in the stackup.")

pv = D[4]['params']
P("It is simultaneously a capacitor, an inductor and, if the signal enters at the top "
  "and leaves part-way down, a resonator. Which description applies depends on "
  "frequency. It is also worth saying plainly that a via does not <i>have</i> an "
  "inductance: the handbook expression gives %.2f&nbsp;nH for a 120-mil barrel, and that "
  "figure assumes the return current is far away. With ground vias half a millimetre "
  "away the same barrel is worth a few tenths of a nanohenry. Inductance is a property "
  "of a loop, and a via does not have one until its return path is named."
  % pv['l_isolated'])

H2("4.1&nbsp;&nbsp;The stub")

nt = [r for r in D[4]['stub_notch'] if r['mil'] == 110]
P("A through-hole via is drilled through the whole board whether the signal needs to "
  "travel that far or not. A signal entering on layer two and leaving on layer four "
  "leaves most of the barrel connected at one end and nothing at the other: an "
  "open-circuited stub, which a quarter of a wavelength long presents a short circuit at "
  "its base. A 110-mil stub resonates at %.1f&nbsp;GHz, within a few per cent of the "
  "Nyquist frequency of a 28&nbsp;GBd lane. That is not a coincidence of this example; "
  "it is why back-drilling became mandatory at exactly the rates it did."
  % (nt[0]['ghz'] if nt else 13.9))

P("The distinction that matters is between attenuation and a notch. Attenuation removes "
  "amplitude and an equaliser can put it back, at the cost of amplifying noise with it. "
  "A notch removes the information at those frequencies altogether, and nothing recovers "
  "it.")

FIGURE("stub",
       "Figure 4.1 &mdash; Left: excess loss at 14&nbsp;GHz against how much stub "
       "back-drilling leaves behind. The curve is steep at the top and shallow at the "
       "bottom, so back-drilling is worth specifying and not worth over-specifying. "
       "Right: return loss of the same via modelled as a short coaxial transmission "
       "line, for four antipad diameters.", 150)

H2("4.2&nbsp;&nbsp;Designing the whole transition")

op = list(D[4]['optimise'].values())[1]
P("Here is the result that changes how a via is designed. A barrel whose own impedance "
  "equals the channel impedance is <i>not</i> the best via. The launch &mdash; the pad, "
  "the clearance in the signal layer, the short run of trace reaching the barrel &mdash; "
  "is capacitive, and a barrel slightly below the channel impedance reflects with the "
  "opposite sign in a way that partly cancels it. Optimising the two together rather "
  "than separately is worth %.1f&nbsp;dB of return loss at Nyquist on this geometry."
  % op['gain_db'])

FIGURE("viaopt",
       "Figure 4.2 &mdash; Return loss at 14&nbsp;GHz against antipad diameter, for "
       "three launch capacitances. The optimum is well below the diameter that matches "
       "the barrel to the channel, and the cancellation is narrowband: the antipad "
       "giving the widest usable bandwidth is a different one again.", 116)

CO("Every antipad is a hole in a reference plane. A dense connector footprint or a large "
   "ball-grid array perforates the planes so thoroughly that the return paths of chapter "
   "2 are obstructed and the plane pair of chapter 7 stops behaving like one. Via design "
   "is not a local optimisation: the antipad that makes one transition transparent can "
   "be the antipad that ruins the power delivery.")

CHAP()

# ============================================================== chapter 5 ===
H1("5&nbsp;&nbsp;Differential Signalling")

P("Every fast link is differential and the reasons usually given are a mixture of the "
  "real and the overstated. The genuinely large benefit, after chapter 2, is a defined "
  "return current: the two conductors carry equal and opposite currents, so each is the "
  "other's return and the loop is small, known and local. The second is a rejection of "
  "what is common to both, which is a finite number rather than a property. The third is "
  "six decibels of signal, because the receiver sees the difference.")

P("What is overstated is immunity to crosstalk. A pair rejects an aggressor only to the "
  "extent that the aggressor couples equally to both conductors, and a neighbouring "
  "trace is closer to one than the other.")

H2("5.1&nbsp;&nbsp;Two modes, and what tight coupling costs")

P("A coupled pair has two characteristic impedances. Driving both conductors together "
  "gives the even mode; driving them oppositely gives the odd mode. The differential "
  "impedance a receiver terminates is twice the odd-mode impedance, and the common-mode "
  "impedance is half the even-mode impedance.")

cc = D[5]['coupling_cost']['rows']
tight, loose = cc[0], cc[-1]
P("There is a persistent belief that a pair should be coupled as tightly as the "
  "technology allows. Testing it requires holding the differential impedance constant, "
  "because otherwise one is comparing geometries that are not alternatives. Doing so "
  "changes the question: tightening the pair lowers the odd-mode impedance, so the "
  "traces must be made narrower to bring it back, and narrower traces have more "
  "conductor loss. Going from %.2f&nbsp;mm to %.2f&nbsp;mm spacing raises the coupling "
  "from %.2f to %.1f per cent, forces the traces from %.3f to %.3f&nbsp;mm wide, and "
  "costs %.2f&nbsp;dB over ten inches at 14&nbsp;GHz."
  % (loose['s_mm'], tight['s_mm'], loose['coupling_pct'], tight['coupling_pct'],
     loose['w_mm'], tight['w_mm'], tight['extra_loss_db']))

FIGURE("coupling",
       "Figure 5.1 &mdash; Left: the loss penalty of tight coupling, at constant "
       "differential impedance. Right: what real copper thickness does to a "
       "100&nbsp;&#937; pair. Every closed-form stripline expression assumes zero "
       "thickness; half-ounce copper lowers the impedance by about ten per cent, which "
       "is the whole of a typical tolerance.", 150)

P("Tight coupling is right when routing density forces it, and when a pair has to "
  "survive a broken reference plane, because a tightly coupled pair carries more of its "
  "own return. Both are real reasons. Neither is that tighter coupling is better signal "
  "integrity, which the loss column contradicts.")

H2("5.2&nbsp;&nbsp;How symmetry is lost")

P("The benefit of differential signalling degrades with anything that breaks the "
  "symmetry, and the dominant asymmetry is intra-pair skew. Its effect is to move energy "
  "out of the differential mode and into the common mode as $|S_{cd21}| = "
  "|\\sin(\\pi f \\tau)|$ &mdash; a transfer rather than a loss, into a mode the "
  "receiver ignores and the chassis radiates.")

FIGURE("skewconv",
       "Figure 5.2 &mdash; Differential-to-common conversion against frequency for five "
       "values of intra-pair skew, with 14&nbsp;GHz marked. Conversion is complete when "
       "the skew reaches half a period.", 116)

mv = D[5]['mode_velocity']
P("There is also a source that survives perfect length matching. In a uniform dielectric "
  "the even and odd modes travel at the same speed; on an outer layer they do not, "
  "because the odd mode keeps more of its field in the laminate and the even mode more "
  "of it in air. A perfectly symmetric, perfectly matched microstrip pair therefore "
  "still converts, purely because it is microstrip: a two per cent velocity difference "
  "over ten inches is equivalent to %.1f&nbsp;ps of skew. In stripline the mechanism "
  "vanishes identically."
  % mv['effective_skew_ps'])

TABLE([["Source of skew", "Typical size", "Visible to the layout tool?"],
       ["Routed length mismatch", "a few picoseconds", "yes &mdash; the only term it reports"],
       ["Bends and serpentines", "sub-picosecond, but they accumulate", "partly"],
       ["Glass weave", "up to about 5 ps per inch worst case", "no"],
       ["A via on one leg only", "tens of picoseconds", "no"],
       ["Package and connector", "often the largest single term", "no &mdash; it is in a datasheet"],
       ["Modal velocity difference", "present on every microstrip pair", "no"]],
       [50, 56, 52],
       "Table 5.1 &mdash; Where intra-pair skew comes from. The term every tool measures "
       "and every reviewer checks is among the smallest.")

CHAP()

# ============================================================== chapter 6 ===
H1("6&nbsp;&nbsp;Crosstalk")

P("Loss and reflection are deterministic functions of the victim's own data, so a filter "
  "designed against its pulse response can subtract them. Crosstalk is driven by a "
  "different lane's data, which the victim's receiver has never seen. To that receiver "
  "it is indistinguishable from noise, so it enters the budget as a variance rather than "
  "as a tap, and the only places to fix it are the geometry and the routing.")

sc, mc = D[6]['stripline_coeff'], D[6]['microstrip_coeff']
P("Two lines are coupled both capacitively and inductively. Both inject current into the "
  "victim; the difference is direction. Towards the near end the two add, towards the "
  "far end they subtract:")

P("$$K_b = \\tfrac{1}{4}\\left(L_m/L + C_m/C\\right), \\qquad "
  "K_f = -\\tfrac{1}{2}\\left(L_m/L - C_m/C\\right).$$")

P("Everything distinctive about crosstalk follows from that one sign. The near-end "
  "coefficient is a sum of two positive quantities and cannot vanish. The far-end "
  "coefficient is a difference, and it vanishes whenever the two ratios are equal "
  "&mdash; which happens whenever the dielectric is uniform.")

TABLE([["Quantity", "Stripline (uniform laminate)", "Microstrip (laminate and air)"],
       ["$L_m/L$", "%.6f" % sc['lm_over_l'], "%.6f" % mc['lm_over_l']],
       ["$C_m/C$", "%.6f" % sc['cm_over_c'], "%.6f" % mc['cm_over_c']],
       ["difference", "%.2e" % (sc['lm_over_l'] - sc['cm_over_c']),
        "%.6f" % (mc['lm_over_l'] - mc['cm_over_c'])],
       ["near-end $K_b$", "%.5f" % sc['kb'], "%.5f" % mc['kb']],
       ["far-end $K_f$", "%.6f" % sc['kf'], "%.5f" % mc['kf']]],
       [46, 56, 56],
       "Table 6.1 &mdash; The field solver is given two cross-sections differing only in "
       "what is above the traces. In the stripline the two ratios agree to six decimal "
       "places and the far-end coefficient is zero to within numerical noise; in the "
       "microstrip the inductive ratio is %.2f times the capacitive one."
       % (mc['lm_over_l'] / mc['cm_over_c']))

P("This is a consequence of the medium rather than of the geometry. In a homogeneous "
  "medium every mode travels at $c/\\sqrt{\\varepsilon_r}$, which forces $LC = "
  "\\mu\\varepsilon$ as matrices and locks the mutual and self terms in the same ratio. "
  "It therefore survives any spacing, any trace width and any asymmetry.")

FIGURE("xtalk",
       "Figure 6.1 &mdash; Left: crosstalk against coupled length. Near-end coupling "
       "saturates once the section is longer than the edge covers in half its rise time. "
       "Far-end coupling grows linearly only while the modal delay difference is smaller "
       "than the rise time, then saturates at half the swing; the dotted line is the "
       "first-order formula, which diverges. Right: near-end crosstalk against spacing.",
       150)

sp = D[6]['spacing']
three = [r for r in sp['rows'] if abs(r['spacing_w'] - 3) < 0.01]
P("Layout guidelines are usually written as a multiple of the trace width. That is the "
  "wrong variable: what sets the coupling is the spacing relative to the dielectric "
  "height, and the two move independently whenever the stackup changes. On this stackup "
  "three trace widths is %.1f dielectric heights and leaves %.3f per cent near-end "
  "crosstalk &mdash; the rule is not wrong here, but it is right by coincidence."
  % (three[0]['s_over_h'] if three else 0, three[0]['next_pct'] if three else 0))

g = D[6]['guard']
if 'no guard' in g and 'grounded guard' in g:
    P("A grounded trace between two signals is an appealing idea and a frequently "
      "disappointing one. Solving all three conductors rather than treating the guard as "
      "a wall gives %.4f per cent near-end coupling with no guard, %.4f with a properly "
      "grounded one and %.4f with a floating one. A guard works only if it is stitched "
      "to the planes along its length; grounded at its two ends and nowhere else it is a "
      "resonator, and near its resonances it is a path rather than a barrier."
      % (g['no guard']['next_pct'], g['grounded guard']['next_pct'],
         g['floating guard']['next_pct']))

CO("<font name='DejaVu-Bold'>How far to trust the microstrip column.</font> The "
   "stripline result is exact in the sense that matters: the ratios are equal because "
   "the medium is uniform, and the solver confirms it to six decimal places. The "
   "microstrip <i>magnitudes</i> deserve caution. An open microstrip has fields "
   "extending indefinitely into the air above it and this solver encloses its "
   "cross-section in a grounded box, which perturbs the air-side field and overstates "
   "the difference between the modal velocities. The sign, the mechanism and the "
   "contrast with stripline are sound; the far-end coupling in decibels is not a number "
   "to budget from, which is why the budget below is built from the near-end term on an "
   "inner layer.")

bg = D[6]['budget']
ig = D[6]['icn_geometry']
icn = D[6]['icn']
P("Because crosstalk adds in quadrature with the other noise terms and cannot be "
  "equalised, its effect on the budget is direct. The arrangement costed here is the "
  "one this report works against: a stripline lane with four neighbours at %.0f trace "
  "widths, each coupling %.3f per cent of a %.0f&nbsp;mV swing, which combine in power "
  "to %.2f&nbsp;mV rms. Against a cursor of 44.5&nbsp;mV and 4&nbsp;mV of other noise "
  "that costs %.2f&nbsp;dB of margin. For comparison, <i>Equalisation in High-Speed "
  "Serial Links</i> found that five more decision-feedback taps on that channel bought "
  "between a quarter and half a decibel and that changing the board bought one and a "
  "half to two and a half. This crosstalk sits between the two, and it is fixed with "
  "spacing rather than with transistors."
  % (ig['spacing_w'], ig['next_pct'], 1000 * ig['swing_v'], icn['icn_mv'],
     bg['margin_lost_db']))

CHAP()

# ============================================================== chapter 7 ===
H1("7&nbsp;&nbsp;Jitter: What It Is, and Why It Is Decomposed")

P("The four chapters that follow treat timing noise on its own, because it is the "
  "quantity a serial link is finally judged on and because almost every mistake made "
  "with it is a mistake about statistics rather than about circuits. The organising "
  "text is Ransom Stephens's, whose five rules of jitter analysis are the spine of this "
  "chapter; each is stated and then computed, because several of them are the kind of "
  "claim that sounds like advice until the arithmetic makes it a constraint.")

rules = D[7]['rules']
TABLE([["", "Stephens's rules of jitter analysis"]] +
      [["%d" % (i + 1), r] for i, r in enumerate(rules)],
      [10, 148],
      "Table 7.1 &mdash; The first and the last are the same rule. That is deliberate: "
      "everything between them is machinery for predicting an error ratio that cannot "
      "be measured directly, and the machinery is only ever as good as that prediction.")

P("Jitter is the deviation of a transition from where it should have been, and the "
  "definition covers mechanisms with quite different statistics. They are separated "
  "because they combine differently &mdash; bounded quantities add arithmetically, "
  "unbounded ones in quadrature &mdash; and because the separation says what to buy. A "
  "term removed by equalisation and a term removed by a better oscillator are the same "
  "number of picoseconds and entirely different purchase orders.")

tax = D[7]['taxonomy']
TABLE([["", "Component", "Bounded", "Correlated with the data", "Removed by"]] +
      [[r['acronym'], r['name'], "yes" if r['bounded'] else "no",
        r['correlated'], r['fixed_by']] for r in tax],
      [13, 44, 22, 43, 36],
      "Table 7.2 &mdash; The taxonomy, with the column that matters on the right. Only "
      "the first row is unbounded, and only the first row is multiplied by Q when the "
      "error ratio is tightened.")

H2("7.1&nbsp;&nbsp;Rule one, computed")

b28 = {r['ber']: r for r in D[7]['bert_28']}
b25 = {r['ber']: r for r in D[7]['bert']}
P("The first rule says that jitter analysis is about the bit error ratio and nothing "
  "else. It is worth making that quantitative, because the consequence is a hard limit "
  "on what can be observed. Confirming an error ratio means collecting enough errors "
  "for the estimate to mean something; ten errors is the usual minimum. At "
  "28&nbsp;Gb/s that takes %.1f&nbsp;s at $10^{-12}$, which is a coffee break, and "
  "%.0f&nbsp;days at $10^{-15}$, which is not. At 2.5&nbsp;Gb/s the same two "
  "measurements take %.0f&nbsp;s and %.0f&nbsp;days."
  % (b28[1e-12]['seconds'], b28[1e-15]['days'],
     b25[1e-12]['seconds'], b25[1e-15]['days']))

FIGURE("bert",
       "Figure 7.1 &mdash; Left: the time to confirm an error ratio, at two rates. "
       "Right: the zero-crossing positions produced by every history of the preceding "
       "bits on the unequalised backplane channel. The second panel is the reason the "
       "first matters: the distribution the extrapolation has to model is not two "
       "impulses, and not a Gaussian either.", 150)

ddj = D[7]['ddj']
P("That is the whole case for extrapolation, and the whole difficulty with it. Nobody "
  "measures $10^{-15}$; everybody measures somewhere around $10^{-6}$ to $10^{-9}$ and "
  "fits a model. The right-hand panel above shows what the model has to describe. "
  "Enumerating all %d histories of the preceding bits on the unequalised channel spreads "
  "the crossing over %.2f&nbsp;UI &mdash; %.1f&nbsp;ps, with a standard deviation of "
  "%.1f&nbsp;ps &mdash; in a distribution with structure, gaps and no resemblance to "
  "either of the two shapes the reporting convention allows."
  % (ddj['n'], ddj['pp_ui'], ddj['pp_ps'], ddj['std_ps']))

CO("<font name='DejaVu-Bold'>A collision of notation.</font> The Q in these chapters is "
   "the argument of the error function &mdash; a signal-to-noise ratio in standard "
   "deviations, typically between three and eight. It is not the Q of a resonator, which "
   "is energy stored over energy dissipated per radian and is typically in the hundreds. "
   "The two meet: the tank Q of an oscillator sets its phase noise, which becomes the "
   "random jitter, which is part of the noise in the denominator of the communications "
   "Q. A sentence about a high-Q tank improving Q is not nonsense, but it needs both "
   "words defined.")

CHAP()

# ============================================================== chapter 8 ===
H1("8&nbsp;&nbsp;The Dual-Dirac Model and What It Costs")

P("The reporting convention replaces the deterministic distribution with two impulses "
  "separated by a quantity called $\\mathrm{DJ}(\\delta\\delta)$, each convolved with "
  "the Gaussian random part, giving $\\mathrm{TJ} = \\mathrm{DJ}(\\delta\\delta) + "
  "2Q\\,\\mathrm{RJ}_{rms}$. The deterministic term enters once whatever the error "
  "ratio; the random term is multiplied by a factor that grows with the confidence "
  "demanded. A design dominated by one behaves quite differently under a tightened "
  "specification from one dominated by the other, which is the reason to separate them "
  "at all.")

qt = {r['ber']: r for r in D[8]['q_table']}
TABLE([["Error ratio"] + ["$10^{-%d}$" % e for e in (10, 12, 15)],
       ["Q"] + ["%.2f" % qt[10.0 ** -e]['q'] for e in (10, 12, 15)],
       ["Multiplier on RJ"] + ["%.2f" % qt[10.0 ** -e]['two_q'] for e in (10, 12, 15)]],
      [50, 36, 36, 36],
      "Table 8.1 &mdash; Three decades of error ratio cost only 25 per cent more random "
      "jitter. That weak dependence is why extrapolation is tempting, and why a model "
      "error in the deterministic term is so much more damaging than one in the random "
      "term.")

P("Five assumptions are buried in that formula, and it is worth writing them down "
  "before testing them: that jitter separates into a random and a deterministic "
  "category; that the random part is Gaussian and described by one number; that the "
  "deterministic part is bounded; that it can be represented by two impulses; and that "
  "the process is stationary. Chapter 7 has already shown the fourth to be false on a "
  "real channel. This chapter prices that.")

H2("8.1&nbsp;&nbsp;$\\mathrm{DJ}(\\delta\\delta)$ is not the peak-to-peak value")

FIGURE("dualdirac",
       "Figure 8.1 &mdash; Left: the computed bathtub on a Q-scale, where the "
       "dual-Dirac model is a straight line by construction. The data curve, so the "
       "straight line fitted over the measurable region is not the data. Right: what "
       "the fit returns, against the truth it is fitting.", 150)

dd = D[8]['dd_vs_true']
TABLE([["True random jitter", "$\\mathrm{DJ}(\\delta\\delta)$",
        "True peak-to-peak DJ", "Ratio", "Fitted RJ", "Inflation"]] +
      [["%.1f %% UI" % (100 * r['rj_true_ui']),
        "%.3f UI" % r['dj_dd_ui'], "%.3f UI" % r['dj_pp_ui'],
        "%.2f" % r['dj_ratio'], "%.3f UI" % r['rj_fitted_ui'],
        "%.2f&times;" % r['rj_inflation']] for r in dd],
      [30, 30, 30, 18, 26, 22],
      "Table 8.2 &mdash; The same channel, three amounts of genuine random jitter. "
      "$\\mathrm{DJ}(\\delta\\delta)$ is consistently <i>smaller</i> than the real "
      "peak-to-peak deterministic spread, and the fitted random jitter consistently "
      "larger than the real one.")

r0 = dd[1]
P("The two errors are the same error. A fit over a region where the deterministic "
  "distribution still has width cannot tell that width apart from Gaussian tails, so it "
  "assigns some of it to the random term: here the fitted random jitter is "
  "%.2f&nbsp;times the truth, and in exchange the deterministic term comes back at "
  "%.0f per cent of the real peak-to-peak spread. Neither number is the physical "
  "quantity its name suggests. They are two fitting parameters that happen to "
  "reconstruct the tail of the distribution, which is all they were ever asked to do, "
  "and the total at $10^{-12}$ comes out %.1f per cent from the truth &mdash; better "
  "than either part."
  % (r0['rj_inflation'], 100 * r0['dj_ratio'], abs(r0['tj_err_pct'])))

CO("This is the practical form of the warning: $\\mathrm{DJ}(\\delta\\delta)$ from one "
   "instrument and a peak-to-peak deterministic figure from another are not comparable, "
   "and a specification that does not say which it means has not specified anything. "
   "The same applies to random jitter: the fitted value depends on the region fitted "
   "over, so two instruments fitting different regions of the same signal will disagree "
   "and both will be right about what they measured.")

H2("8.2&nbsp;&nbsp;What the shape of the deterministic part does")

cont = D[8]['contamination']
TABLE([["Shape of the deterministic distribution", "RJ inflation",
        "$\\mathrm{DJ}(\\delta\\delta)$ as % of peak-to-peak",
        "Total jitter error"]] +
      [[{'dual_dirac': 'two impulses (the assumption)',
         'uniform': 'uniform &mdash; a spread of equal weight',
         'gaussian_like': 'smooth and centrally peaked'}.get(
            r['dj_shape'], r['dj_shape']),
        "%.2f&times;" % r['rj_inflation'], "%.0f %%" % (100 * r['dj_ratio']),
        "%+.1f %%" % r['tj_err_pct']] for r in cont],
      [64, 28, 40, 26],
      "Table 8.3 &mdash; With the deterministic part shaped exactly as the model "
      "assumes, the fit recovers it. As the shape becomes smoother the fit moves more "
      "and more of it into the random term.")

ex = [r for r in D[8]['extrapolation'] if r.get('ratio_predicted_to_true')]
worst_ex = max(ex, key=lambda r: r['ratio_predicted_to_true']) if ex else None
if worst_ex:
    clean = D[8]['extrapolation'][0]
    P("The fifth assumption, stationarity, fails in a different and more dangerous way. "
      "If a second, rarer Gaussian exists &mdash; an intermittent aggressor, a marginal "
      "supply, a thermal cycle &mdash; a measurement at $10^{-6}$ cannot see it and the "
      "extrapolation cannot include it. With a second Gaussian of weight %.0e and "
      "standard deviation %.1f&nbsp;ps present, the fitted random jitter is "
      "%.3f&nbsp;ps against %.3f&nbsp;ps for perfectly clean data &mdash; identical to "
      "three decimal places. The extrapolation predicts %.2f&nbsp;ps of eye; the true "
      "opening at $10^{-12}$ is %.2f&nbsp;ps. It is wrong by a factor of %.1f and there "
      "is nothing in the measurement to say so."
      % (worst_ex['weight2'], worst_ex['rj2_true_ps'], worst_ex['rj_fitted_ps'],
         clean['rj_fitted_ps'], worst_ex['opening_predicted_ps'],
         worst_ex['opening_true_ps'], worst_ex['ratio_predicted_to_true']))

CHAP()

# ============================================================== chapter 9 ===
H1("9&nbsp;&nbsp;Clock Recovery, Transfer and Tolerance")

P("A serial link carries no clock, so the receiver builds one from the data and tracks "
  "it. That loop decides which jitter matters: anything slow enough for the loop to "
  "follow moves the sampling instant along with the data and costs nothing, and "
  "anything too fast for it to follow lands directly in the eye. The loop is therefore "
  "not a defence against jitter in general but a high-pass filter applied to it, and "
  "the same loop appears in three different documents under three different names.")

FIGURE("cdr",
       "Figure 9.1 &mdash; Left: the same loop described twice. Jitter transfer is what "
       "reaches the recovered clock, error response what remains between clock and "
       "data; they sum to unity at every frequency, which is why a wider loop is not "
       "simply better. Right: jitter tolerance masks for three loop bandwidths. The "
       "mask is the error response turned upside down and written as a test.", 150)

jt = D[9]['jtol']
P("The third name is the tolerance mask. A standard specifies how much sinusoidal "
  "jitter a receiver must survive at each frequency, and the shape of that specification "
  "&mdash; very large at low frequency, falling at twenty decibels per decade, flat "
  "above the loop bandwidth at roughly the residual eye budget &mdash; is not an "
  "empirical shape. It is the reciprocal of the error response, scaled by the budget "
  "the standard allows. A mask with a %.0f&nbsp;MHz corner is a mask that assumes a "
  "%.0f&nbsp;MHz loop, and a receiver whose loop is narrower will fail it while being "
  "perfectly serviceable in a system that never applies that jitter."
  % (jt['bw_hz'] / 1e6, jt['bw_hz'] / 1e6))

H2("9.1&nbsp;&nbsp;Phase noise, and the band it is quoted over")

pn = D[9]['phase_noise']['rows']
TABLE([["Integration band", "From", "To", "Random jitter, rms"]] +
      [[r['band'], "%.0f kHz" % (r['f_lo'] / 1e3) if r['f_lo'] < 1e6
        else "%.0f MHz" % (r['f_lo'] / 1e6),
        "%.0f MHz" % (r['f_hi'] / 1e6) if r['f_hi'] < 1e9
        else "%.0f GHz" % (r['f_hi'] / 1e9),
        "%.1f fs" % r['jitter_rms_fs']] for r in pn],
      [66, 28, 28, 36],
      "Table 9.1 &mdash; The same oscillator on a 14&nbsp;GHz carrier, integrated over "
      "different bands. A jitter figure quoted without its integration band does not "
      "constrain anything; the limits belong to the receiver's loop, not to the "
      "oscillator.")

pmax = max(r['jitter_rms_fs'] for r in pn)
pmin = min(r['jitter_rms_fs'] for r in pn)
P("The spread between the widest and narrowest band is a factor of %.0f, from the same "
  "measured phase-noise curve. That is not a subtlety to be aware of; it is the "
  "difference between a part that closes the budget and one that does not, decided "
  "entirely by an integration limit that belongs to the receiver rather than to the "
  "oscillator being sold." % (pmax / pmin))

d9 = D[9]['ddj']
if d9.get('ok'):
    P("It is worth ending the chapter by putting the loop in proportion. The "
      "data-dependent term on this channel changes from symbol to symbol, which places "
      "it at the very top of the jitter frequency range, where the loop has no effect "
      "whatever: %.2f&nbsp;UI of spread that no clock-recovery bandwidth can reduce. "
      "The loop is the answer to wander, to spread-spectrum modulation and to supply "
      "tones. It is not the answer to the channel." % d9['spread_ui'])

CHAP()

# ============================================================= chapter 10 ===
H1("10&nbsp;&nbsp;Jitter and the Channel")

P("Stephens's fourth rule is that timing noise and amplitude noise are not really "
  "separable, though the industry separates them anyway. The mechanism is simple: a "
  "receiver decides by comparing a voltage with a threshold, so a disturbance in "
  "voltage displaces the crossing in time by that voltage divided by the slew rate. The "
  "consequences are not simple at all, and this chapter computes them on the same "
  "backplane channel the rest of the report uses.")

sl = D[10]['slew']
a2j = D[10]['amp_to_jitter']
one = a2j[0]
P("After equalisation the channel delivers an edge with a slew rate of "
  "%.2f&nbsp;mV/ps, which is a 20 to 80 per cent rise time of %.0f&nbsp;ps against a "
  "%.1f&nbsp;ps unit interval. At that slope one millivolt of amplitude disturbance is "
  "%.3f&nbsp;ps of jitter, or %.2f per cent of a unit interval. Crosstalk, supply "
  "ripple and receiver noise all arrive as voltages and all convert at that exchange "
  "rate."
  % (sl['slew_mv_per_ps'], sl['rise_time_ps'], D[10]['ui_ps'],
     one['jitter_ps'], 100 * one['jitter_ui']))

xt = D[10]['xt_jitter']
P("Applied to the crosstalk of chapter 6, %.2f&nbsp;mV rms of aggressor coupling "
  "becomes %.3f&nbsp;ps rms of timing noise, or %.2f&nbsp;ps peak-to-peak at the "
  "%.0f-sigma equivalent of $10^{-12}$ &mdash; %.1f per cent of the unit interval, "
  "arriving in the jitter budget from a mechanism that appears nowhere in the jitter "
  "chapter's taxonomy except as the single line marked BUJ."
  % (xt['xt_mv_rms'], xt['jitter_rms_ps'], xt['jitter_pp_ps'], xt['n_sigma'],
     100 * xt['jitter_pp_ui']))

H2("10.1&nbsp;&nbsp;Why the exchange rate got worse")

FIGURE("sep",
       "Figure 10.1 &mdash; Left: the rise time the channel delivers, against the unit "
       "interval, as the rate is raised on unchanged copper. Right: what a fixed "
       "amplitude noise is worth in timing as a result. The separation of amplitude and "
       "timing noise was a good approximation once and is not one now.", 150)

sep = D[10]['separability']['rows']
lo, hi = sep[0], sep[-1]
P("The left-hand panel is the whole argument. On unchanged copper, raising the rate "
  "from %.0f to %.0f&nbsp;Gb/s shortens the unit interval by a factor of %.0f but "
  "shortens the received rise time by only %.1f, because past a few gigabits the edge "
  "is set by the channel's bandwidth and not by the transmitter. The rise time "
  "therefore grows from %.2f to %.2f of a unit interval, and a fixed %.0f&nbsp;mV rms "
  "of noise that was worth %.2f per cent of a unit interval becomes worth %.1f per "
  "cent &mdash; a factor of %.0f, from nothing but the ratio of two timescales."
  % (lo['rate_gbps'], hi['rate_gbps'], hi['ui_ps'] and lo['ui_ps'] / hi['ui_ps'],
     lo['rise_time_ps'] / hi['rise_time_ps'],
     lo['rise_time_ui'], hi['rise_time_ui'],
     D[10]['separability']['noise_mv_rms'],
     100 * lo['jitter_pp_ui_at_1e12'], 100 * hi['jitter_pp_ui_at_1e12'],
     hi['relative_to_slowest']))

knee = min(sep, key=lambda r: abs(r['rise_time_ui'] - 0.5))
P("The crossover &mdash; where the received rise time reaches half a unit interval, and "
  "with it the point past which an amplitude disturbance is comparable to a timing one "
  "&mdash; falls at about %.0f&nbsp;Gb/s on this channel. Stephens put the transition "
  "in the same region from quite different reasoning, which is the sort of agreement "
  "worth noticing: the rule of thumb and the computation are describing the same "
  "physics." % knee['rate_gbps'])

CO("The practical consequence is that a voltage-noise budget and a timing budget on a "
   "modern link are not two budgets. Spending margin in one spends it in the other at a "
   "rate the channel sets, and a design that optimises them separately will "
   "double-count some terms and miss others. The exchange rate &mdash; millivolts per "
   "picosecond at the receiver &mdash; is worth computing early and carrying through.")

CHAP()

# ============================================================= chapter 11 ===
H1("11&nbsp;&nbsp;The Power Delivery Network and Its Impedance")

P("The four chapters that follow treat power integrity as a subject in its own right "
  "and then return it to the signal. The organising text here is Smith and Bogatin's, "
  "and their central move is to stop thinking of a power delivery network as a supply "
  "and start thinking of it as an impedance: a network whose job is to keep the "
  "impedance seen by the load below some value across a band, and whose failures are "
  "always failures of impedance rather than of current.")

tg = D[11]['target']
P("The specification follows in one line. If a load draws a transient of "
  "%.0f&nbsp;A and the rail may move by %.0f per cent of %.2f&nbsp;V, the network must "
  "present no more than %.2f&nbsp;m&#937; at every frequency the transient contains. "
  "That is the target impedance, and it is the only specification in this report that "
  "is a bound on a whole curve rather than on a single number."
  % (tg['i_transient'], tg['ripple_pct'], tg['v_rail'], 1000 * tg['z_target']))

tgs = D[11]['targets']
TABLE([["Rail", "Transient current", "Ripple allowed", "Target impedance"]] +
      [["%.2f V" % r['v_rail'], "%.0f A" % r['i_transient'],
        "%.0f %%" % r['ripple_pct'],
        ("%.0f m&#937;" % (1000 * r['z_target'])) if r['z_target'] > 1e-3
        else ("%.0f &#181;&#937;" % (1e6 * r['z_target']))]
       for r in tgs],
      [30, 40, 34, 44],
      "Table 11.1 &mdash; Target impedance across four generations of core rail. The "
      "quantity falls by more than three orders of magnitude, because the voltage falls "
      "while the current rises and both act in the same direction. Nothing else in "
      "high-speed design has tightened this fast.")

CO("<font name='DejaVu-Bold'>What the target impedance is not.</font> It is a "
   "single-number stand-in for a spectrum, and it assumes the transient contains "
   "content at the frequency where the impedance peaks. A network can meet its target "
   "everywhere and still fail against a load whose spectrum is concentrated at the one "
   "frequency where it does not, and can miss its target at a frequency the load never "
   "excites and work perfectly. It is a good first specification and a poor final one, "
   "which is the same relationship insertion loss has to a channel.")

pk = D[11]['peaks'][0] if D[11]['peaks'] else None
if pk:
    P("The network modelled here meets its target across most of the band and fails at "
      "%.0f&nbsp;kHz, where two adjacent tiers resonate and the impedance reaches "
      "%.0f&nbsp;m&#937; &mdash; %.0f times the target. Every capacitor is inductive "
      "above its own series resonance, so every pair of adjacent values has a frequency "
      "at which one is inductive and the other still capacitive, and that is where they "
      "resonate against each other. The peaks are not a defect of this particular "
      "network; they are what a ladder of capacitors is."
      % (pk['f_hz'] / 1e3, 1000 * pk['z_ohm'], pk['z_ohm'] / tg['z_target']))

FIGURE("pdn",
       "Figure 11.1 &mdash; Left: the impedance of a complete decoupling ladder, with "
       "the individual tiers in grey and the anti-resonant peaks marked. Right: what "
       "happens as more capacitors of one value are added. The impedance in the band "
       "where that value is capacitive falls, as intended; the worst anti-resonant peak "
       "does not improve.", 150)

mcz = D[11]['more_caps']
P("That second panel is the result worth computing rather than asserting. The intuitive "
  "response to a network that misses its target is to add capacitors. Going from %d to "
  "%d parts of the same value lowers the impedance at 100&nbsp;MHz from %.1f to "
  "%.1f&nbsp;m&#937;, and moves the worst anti-resonant peak from %.0f to "
  "%.0f&nbsp;m&#937;. Sixteen times the parts, and the number that decides the design "
  "has gone the wrong way."
  % (mcz[0]['count'], mcz[-1]['count'], 1000 * mcz[0]['z_at_100mhz'],
     1000 * mcz[-1]['z_at_100mhz'], 1000 * mcz[0]['worst_peak_ohm'],
     1000 * mcz[-1]['worst_peak_ohm']))

H2("11.1&nbsp;&nbsp;What actually sets the number of capacitors")

fd = D[11]['fdtim']
P("Smith's frequency-domain target-impedance method answers the question a designer "
  "actually asks &mdash; how many capacitors, and of what &mdash; and its answer is not "
  "the one the intuition above expects. Above its series resonance a capacitor is an "
  "inductor of value equal to its mounting inductance, and near the top of the band "
  "every capacitor in the network is in that state. What the parallel combination "
  "presents there is the mounting inductance divided by the number of parts, so the "
  "count required is fixed by $2\\pi f_{max} L_{mount} / Z_{target}$ and the "
  "capacitance does not enter.")

P("For the rail modelled here &mdash; %.0f&nbsp;m&#937; to be held to %.0f&nbsp;GHz "
  "with %.0f&nbsp;pH of mounting inductance per part &mdash; that is %d capacitors. "
  "A single capacitor would have to be mounted with %.1f&nbsp;pH to do the job alone, "
  "which is roughly the inductance of the via barrel and nothing else."
  % (fd['z_target_mohm'], fd['f_max_hz'] / 1e9, fd['l_mount_ph'],
     int(fd['n_min']), fd['l_for_one_cap_ph']))

FIGURE("fdtim",
       "Figure 11.2 &mdash; Left: the number of capacitors against mounting inductance, "
       "at a fixed target. The relationship is exactly linear, because it is the same "
       "equation rearranged. Right: the number against the target impedance itself. "
       "Neither axis mentions capacitance.", 150)

mt = D[11]['mounting']
TABLE([["Via pairs per capacitor"] + ["%d" % r['vias'] for r in mt],
       ["Mounting inductance"] + ["%.0f pH" % r['l_ph'] for r in mt]],
      [50, 26, 26, 26, 26],
      "Table 11.2 &mdash; Mounting inductance against the number of via pairs. This, "
      "not the part number, is the design variable: doubling the vias halves the "
      "inductance and therefore halves the number of capacitors required.")

CO("The practical reading is that a decoupling problem is a layout problem wearing a "
   "component's clothes. Choosing a capacitor with a better self-resonance changes "
   "where one tier sits; shortening the loop from pad to plane changes how many tiers "
   "are needed at all. The first is a purchasing decision and the second is a stack-up "
   "decision, and only the second scales.")

CHAP()

# ============================================================= chapter 12 ===
H1("12&nbsp;&nbsp;Planes, Packages and the PDN Ecology")

P("The ladder of the previous chapter is a lumped model, and it stops describing "
  "reality at the frequency where the distance from the capacitor to the load becomes "
  "electrically significant. Above that, three things matter that no component list "
  "contains: the inductance of spreading current through a plane pair, the resonances "
  "of the plane pair considered as a cavity, and the antiresonance between the "
  "capacitance on the die and the inductance of the package that connects it to "
  "everything else.")

sn = D[12]['spreading_note']
P("Spreading inductance is the first of these and the easiest to overlook, because it "
  "is not in any component. Current flowing outwards from a via through a plane pair "
  "has inductance proportional to the plate separation and logarithmic in distance: "
  "%.0f&nbsp;pH for a load %.0f&nbsp;mm from its capacitor across a %.0f&nbsp;&#181;m "
  "dielectric. That is comparable to the mounting inductance of the capacitor itself, "
  "which means a capacitor ten millimetres away has roughly half the effect of the same "
  "capacitor mounted next to the load, and no amount of specifying the part improves "
  "it." % (sn['l_ph'], sn['d_mm'], sn['h_um']))

FIGURE("spread",
       "Figure 12.1 &mdash; Left: spreading inductance against distance, for four plate "
       "separations. Right: the rail's response to a current step, computed by "
       "transforming the impedance profile rather than by assembling a response by "
       "hand.", 150)

pr = D[12]['probe']
worst_probe = max(pr, key=lambda k: pr[k]['z_max_band'])
best_probe = min(pr, key=lambda k: pr[k]['z_max_band'])
P("The second is that a plane pair is a resonant cavity, and its impedance depends on "
  "where it is probed. Measuring the same %d by %d millimetre cavity from its centre "
  "gives a worst-case impedance of %.2f&nbsp;&#937; in band, and from one corner to the "
  "opposite corner %.2f&nbsp;&#937; &mdash; a factor of %.1f from nothing but the "
  "positions of two probes, because a corner sits at an antinode of every mode while "
  "the centre sits at a node of half of them. A plane-pair impedance quoted without a "
  "probe position is not a measurement of the board."
  % (150, 100, pr[best_probe]['z_max_band'], pr[worst_probe]['z_max_band'],
     pr[worst_probe]['z_max_band'] / pr[best_probe]['z_max_band']))

H2("12.1&nbsp;&nbsp;The Bandini Mountain")

bm = D[12]['bandini']
P("The third is the one Smith named, and the name has stuck because the feature "
  "deserves it. On-die capacitance and package inductance form a parallel resonance "
  "that no board component can reach, because every board component sits on the far "
  "side of the very inductance that causes it. With %.0f&nbsp;nF on the die and "
  "%.0f&nbsp;pH of package, the resonance is at %.0f&nbsp;MHz and the impedance there "
  "is %.1f&nbsp;m&#937; &mdash; squarely in the band where a processor core changes its "
  "activity, and %.0f times the %.2f&nbsp;m&#937; the rail is supposed to hold."
  % (bm['c_die_nf'], bm['l_pkg_ph'], bm['f_peak_hz'] / 1e6,
     1000 * bm['z_peak_ohm'],
     bm['z_peak_ohm'] / D[11]['target']['z_target'],
     1000 * D[11]['target']['z_target']))

FIGURE("bandini",
       "Figure 12.2 &mdash; Left: the impedance of the full ecology, with the "
       "antiresonance marked. Right: the height of that peak against the series "
       "resistance in the package path. The minimum sits at the characteristic "
       "impedance of the resonance, and both more and less resistance are worse.", 150)

dmp = D[12]['bandini_damping']
best = min(dmp['rows'], key=lambda r: r['z_peak_mohm'])
P("The right-hand panel above is the design rule, and it is not the one instinct "
  "supplies. The peak is minimised by a series resistance of about "
  "%.0f&nbsp;m&#937; &mdash; the characteristic impedance $\\sqrt{L/C}$ of the "
  "resonance, which for this package and die is %.1f&nbsp;m&#937;. Less resistance "
  "makes the resonance sharper and the peak higher; more resistance raises the "
  "impedance everywhere. An engineer specifying the lowest-resistance parts available "
  "is optimising the wrong quantity, and the same argument applies to the "
  "controlled-resistance capacitors sold for exactly this purpose."
  % (best['r_mohm'], dmp['z_bm_mohm']))

vc = D[12]['bandini_vs_cdie']
TABLE([["On-die capacitance"] + ["%.0f nF" % r['c_die_nf'] for r in vc],
       ["Resonant frequency"] + ["%.0f MHz" % r['f_bm_mhz'] for r in vc],
       ["Peak impedance"] + ["%.1f m&#937;" % r['z_peak_mohm'] for r in vc]],
      [38, 24, 24, 24, 24, 24],
      "Table 12.1 &mdash; What moves the mountain. Quadrupling the on-die capacitance "
      "halves the frequency and roughly halves the peak &mdash; a die change, not a "
      "board change, which is why this feature is usually somebody else's problem and "
      "always the board designer's symptom.")

H2("12.2&nbsp;&nbsp;The same event in the time domain")

tr = D[12]['transient']
P("A designer sees all of this on an oscilloscope as a sequence of droops, and it is "
  "worth connecting the two pictures because they are the same computation. A "
  "%.0f&nbsp;A step with a %.0f&nbsp;ps edge produces a deepest excursion of "
  "%.0f&nbsp;mV at %.1f&nbsp;ns. Divided by the step current that is "
  "%.1f&nbsp;m&#937;, against a peak impedance of %.1f&nbsp;m&#937; read off the "
  "frequency plot: %.1f per cent apart, which is as close as a single-frequency reading "
  "of a broadband event has any right to be. The peak of the impedance is not a proxy "
  "for the droop; it <i>is</i> the droop."
  % (tr['i_step_a'], tr['rise_ps'], abs(tr['worst_mv']), tr['worst_at_ns'],
     tr['worst_as_impedance_mohm'], tr['z_peak_mohm'],
     abs(tr['droop_vs_zpeak_err_pct'])))

P("The first droop, before anything off the die can respond, is usually described as "
  "the charge drawn divided by the on-die capacitance. That term is real and here it is "
  "%.2f&nbsp;mV. But the same current crosses that capacitance's own series resistance "
  "at the same instant, and that term is %.0f&nbsp;mV &mdash; %.0f times larger, "
  "independent of how much capacitance there is, and the reason a design that doubles "
  "on-die capacitance to fix a first-droop problem so often finds nothing changes. "
  "Smith's ordering is right: the die draws from itself first and the droop is what "
  "pulls current in from the board. The arithmetic adds that the resistive half is the "
  "one to attack."
  % (tr['first_droop_charge_mv'], tr['first_droop_esr_mv'],
     tr['first_droop_esr_mv'] / tr['first_droop_charge_mv']))

P("A last observation from the same computation: a microsecond after the step the rail "
  "is still %.0f&nbsp;mV low, and the level it will eventually settle to is only "
  "%.0f&nbsp;mV low. The bulk capacitance and the regulator are doing their job, but on "
  "a timescale the core never experiences. Nothing in the first microsecond is a "
  "regulator problem."
  % (abs(tr['at_end_mv']), tr['i_step_a'] * tr['r_dc_mohm']))

CHAP()

# ============================================================= chapter 13 ===
H1("13&nbsp;&nbsp;Measuring an Impedance Too Small to Measure")

P("A power delivery network has to be verified, and the quantity to be verified is a "
  "few milliohms. That is four orders of magnitude below the fifty ohms a network "
  "analyser is built around, and the gap is large enough that the usual instrument in "
  "its usual configuration cannot see the quantity at all. This chapter computes why, "
  "and what the alternative costs.")

sens = D[13]['sensitivity']
P("A one-port reflection measurement fails first, and it fails for a reason that has "
  "nothing to do with noise. A milliohm across a fifty-ohm port reflects essentially "
  "all of the incident wave: the reflection coefficient differs from that of a perfect "
  "short by %.0e, and an instrument with %.0f&nbsp;dB of directivity cannot distinguish "
  "a departure smaller than about %.0f&nbsp;m&#937;. Improving the calibration does not "
  "help, because directivity is a property of the bridge and not of the calibration."
  % (sens['rows'][1]['s11_departure_from_short'], sens['directivity_db'],
     sens['reflection_floor_mohm']))

s40, s50 = D[13]['sensitivity_40'], D[13]['sensitivity_50']
P("Ten more decibels of directivity &mdash; which is a great deal, and expensive "
  "&mdash; moves the floor from %.0f&nbsp;m&#937; to %.0f&nbsp;m&#937;. That is still "
  "two orders of magnitude above the quantity of interest, which is the point: this is "
  "not an instrument that needs improving but a method that needs replacing."
  % (s40['reflection_floor_mohm'], s50['reflection_floor_mohm']))

FIGURE("shunt",
       "Figure 13.1 &mdash; The two methods against the impedance under test. "
       "Reflection is flat and useless below an ohm; transmission through the device as "
       "a shunt falls at twenty decibels per decade and stays measurable into the "
       "microhms.", 130)

rt = D[13]['roundtrip']
one_m = [r for r in rt if abs(r['z_mohm'] - 1.0) < 1e-9]
P("The two-port shunt-through method connects the device between the two ports as a "
  "shunt, so that $S_{21} = 2Z/(2Z + Z_0)$ and a small impedance produces a small "
  "transmitted signal rather than an indistinguishable reflected one. A "
  "milliohm transmits %.1f&nbsp;dB, which is a large number an instrument measures "
  "easily and accurately; the impedance is then recovered by inverting the formula. "
  "The recovery is exact to the precision of the arithmetic across the whole range of "
  "interest, which is the property that makes the method worth the extra cable."
  % (one_m[0]['s21_db'] if one_m else rt[1]['s21_db']))

TABLE([["Impedance under test"] + ["%g m&#937;" % r['z_mohm'] for r in rt],
       ["Transmitted $S_{21}$"] + ["%.1f dB" % r['s21_db'] for r in rt],
       ["Recovered"] + ["%g m&#937;" % round(r['recovered_mohm'], 3) for r in rt]],
      [32, 21, 21, 21, 21, 21, 21],
      "Table 13.1 &mdash; Forward and back through the shunt-through formula. The "
      "method's usefulness is that the measured quantity stays large while the "
      "quantity of interest becomes small.")

gl = D[13]['ground_loop']
P("It has one classic failure, and it is worth stating because the error it produces is "
  "always in the same direction. The two cable braids form a loop in parallel with the "
  "device, and the instrument measures the parallel combination. With a "
  "%.0f&nbsp;m&#937; braid across a %.0f&nbsp;m&#937; device the reading is "
  "%.3f&nbsp;m&#937; &mdash; %.1f per cent <i>low</i>. A measurement error that always "
  "flatters the design is the most dangerous kind, and the fix &mdash; a common-mode "
  "choke or an isolated port &mdash; is a component, not a calibration."
  % (gl[0]['z_shield_mohm'], gl[0]['z_true_mohm'], gl[0]['z_apparent_mohm'],
     abs(gl[0]['error_pct'])))

CO("The general lesson travels beyond power integrity. When a quantity of interest sits "
   "far from an instrument's natural range, the answer is rarely a better instrument; "
   "it is a measurement configuration that maps the quantity onto something the "
   "instrument is good at. Shunt-through does that with a factor of $Z_0/2Z$, and the "
   "de-embedding of chapter 16 does the same thing in a different direction.")

CHAP()

# ============================================================= chapter 14 ===
H1("14&nbsp;&nbsp;Where Power Integrity Meets Signal Integrity")

P("The two subjects are usually taught apart and are not separate. A disturbance on a "
  "rail reaches a receiver's decision by four distinct routes, and the useful "
  "observation &mdash; useful because it changes who fixes the problem &mdash; is that "
  "two of the four are not power problems at all. They are return-path problems that "
  "happen to be visible on the supply.")

TABLE([["Route", "Arrives at the receiver as", "Enters which budget"],
       ["Through the transmitter",
        "amplitude modulation of the swing",
        "voltage noise, and its jitter equivalent via the slew rate"],
       ["Through the oscillator",
        "periodic jitter at the ripple frequency",
        "deterministic jitter, bounded"],
       ["Through the return path",
        "a series impedance in the signal's own return",
        "insertion loss and reflection &mdash; the channel itself"],
       ["Through the plane cavity",
        "crosstalk uncorrelated with the victim",
        "bounded uncorrelated jitter, and the crosstalk variance"]],
      [40, 56, 62],
      "Table 14.1 &mdash; Four routes. The third and fourth are chapters 2 and 12 "
      "wearing a different label; a designer who treats them as decoupling problems "
      "will add capacitors to a problem that needs copper.")

ssn = D[14]['ssn']
P("The first route to compute is the oldest. Simultaneous switching noise is the "
  "voltage developed across the inductance shared by a group of drivers and their "
  "return: %.0f&nbsp;mV for one driver on %.0f&nbsp;pH, and %.1f&nbsp;V for "
  "%d&nbsp;switching in step, because the rate of change adds while the inductance does "
  "not. The scaling with the number of simultaneously switching outputs, rather than "
  "the value of any one number, is why wide parallel interfaces stopped scaling before "
  "their signal integrity ran out."
  % (ssn[0]['v_noise_mv'], ssn[0]['l_loop_ph'], ssn[-1]['v_noise'],
     ssn[-1]['n_drivers']))

rp = D[14]['ripple']
P("The second route is the oscillator, and it repays being computed because the usual "
  "rule of thumb is right for a reason most statements of it leave out. A tone on the "
  "supply modulates the oscillator's frequency; frequency modulation integrates to "
  "phase modulation, so the phase deviation falls as the reciprocal of the modulation "
  "frequency. The loop rejects the disturbance, and how steeply it rejects decides "
  "everything: a first-order loop rejects in proportion to frequency, which cancels the "
  "falling modulation index exactly and leaves the jitter <i>flat</i> at "
  "%.1f&nbsp;ps from the lowest frequencies to the loop bandwidth. A second-order loop "
  "rejects as the square, the square wins, and there is a genuine peak."
  % rp['order1_plateau_ps'])

FIGURE("ripple",
       "Figure 14.1 &mdash; Left: ground bounce against the number of drivers switching "
       "together. Right: jitter from a 20&nbsp;mV supply tone against the rejection at "
       "the oscillator. Both are linear relationships being used as design rules.", 150)

P("Real synthesis and clock-recovery loops are second order, so the familiar advice "
  "survives &mdash; but in a sharper form than it is usually given. The peak is at "
  "%.2f times the loop bandwidth, which is to say <i>at</i> it rather than above it, "
  "and the response is symmetric about that point at twenty decibels per decade on "
  "either side. A tone placed a decade away in either direction is twenty decibels "
  "cheaper; the same tone at the peak is %.0f&nbsp;dB worse than one at a kilohertz. "
  "A switching regulator's fundamental is a number somebody chooses, and this is the "
  "calculation that should choose it."
  % (rp['worst_over_bw'], rp['peak_over_low_f_db']))

psrr = D[14]['psrr']
TABLE([["Supply rejection at the oscillator"] +
       ["%d dB" % r['psrr_db'] for r in psrr],
       ["Jitter from a 20 mV tone"] +
       ["%.2f ps" % r['jitter_pp_ps'] for r in psrr]],
      [58, 24, 24, 24, 24],
      "Table 14.2 &mdash; Ten decibels of rejection is worth a factor of about three in "
      "jitter, which makes the on-die regulator between the rail and the oscillator one "
      "of the highest-leverage components on the die.")

dcb = D[14]['dc_blocking']
P("The last connection is the most often missed, and it is a signal-integrity problem "
  "that looks like a power one. A high-speed link is nearly always AC-coupled, so the "
  "series capacitor carries the signal's return current as well as its forward current. "
  "One capacitor's mounting inductance presents %.1f&nbsp;&#937; at 1&nbsp;GHz; "
  "%d&nbsp;in parallel present %.2f&nbsp;&#937;. The capacitor's capacitance is "
  "irrelevant to this; its mounting is not, and the same stack-up decision that fixed "
  "the decoupling fixes this."
  % (dcb[0]['z_at_1ghz'], dcb[-1]['n_caps'], dcb[-1]['z_at_1ghz']))

CO("<font name='DejaVu-Bold'>Where this leaves the two disciplines.</font> Of the four "
   "routes, one belongs to the power team, one to whoever specifies the oscillator and "
   "its regulator, and two to whoever draws the reference planes. A review that assigns "
   "all four to the power team will fix the wrong two, and the symptom &mdash; an eye "
   "that closes when a nearby rail is loaded &mdash; looks identical in all four cases.")

CHAP()

# ============================================================== chapter 15 ===
H1("15&nbsp;&nbsp;Timing, Flight Time and the Budget")

fl = D[15]['flight']
good, bad = fl[1], fl[-1]
P("Propagation delay is a property of the line. Flight time is the interval between the "
  "driver crossing its own switching threshold and the receiver crossing its, and on a "
  "badly matched net the two differ considerably. A driver whose impedance is below the "
  "line's launches more than half the swing and the open receiver doubles it, so the "
  "threshold is crossed on the first incident wave. A driver well above it launches too "
  "little, and the receiver waits for a round trip. Eight inches of line has a "
  "propagation delay of %.0f&nbsp;ps; a %d&nbsp;&#937; driver gives a flight time of "
  "%.0f&nbsp;ps and a %d&nbsp;&#937; driver %.0f&nbsp;ps, on the same copper."
  % (good['tpd_ps'], good['z_source'], good['flight_time_ps'],
     bad['z_source'], bad['flight_time_ps']))

P("Setup and hold are not symmetric, and the asymmetry is the most useful thing to know "
  "about timing closure. Setup has the clock period in it and hold does not, so a hold "
  "violation cannot be fixed by slowing the clock down. A hold violation also gets worse "
  "when a trace is <i>shortened</i> &mdash; the one case in this whole report where more "
  "copper is the fix.")

H2("15.1&nbsp;&nbsp;Worst case against statistical")

st15 = D[15]['stat']
TABLE([["Independent terms", "Worst-case sum", "One sigma",
        "Statistical at 3&sigma;", "Statistical at $10^{-12}$"]] +
      [[k, "%.1f ps" % st15[k]['worst_case_ps'], "%.2f ps" % st15[k]['sigma_ps'],
        "%.1f ps  (saves %.0f %%)" % (st15[k]['statistical_3sigma_ps'],
                                      100 * (1 - st15[k]['ratio_3sigma'])),
        "%.1f ps  (saves %.0f %%)" % (st15[k]['statistical_ps'],
                                      100 * (1 - st15[k]['ratio']))]
       for k in st15],
      [28, 28, 22, 40, 40],
      "Table 15.1 &mdash; A budget added two ways, at two confidence levels. Conventional "
      "statistical timing closure works at three sigma, where the saving is large. A "
      "serial link has to work at an error ratio of $10^{-12}$, which is past seven "
      "sigma, and at that confidence the same quadrature sum buys very much less.")

P("With only four terms the statistical budget at $10^{-12}$ is <i>larger</i> than the "
  "worst-case sum, which sounds absurd and is correct: treating four terms as "
  "three-sigma spreads and then demanding seven sigma of the combination asks for more "
  "than their arithmetic sum. The technique pays only when there are many independent "
  "terms, and how many is a computation rather than a matter of taste.")

H2("15.2&nbsp;&nbsp;Why the wide parallel bus ended")

b15 = D[15]['bus']
P("The historical argument can be written as arithmetic. A common-clock bus spends the "
  "whole flight time and all of the clock skew out of one cycle. A source-synchronous "
  "bus forwards its clock with the data, cancelling most of the flight time, and is then "
  "limited by lane-to-lane matching. An embedded-clock link recovers timing per lane, so "
  "neither flight time nor lane skew appears in its budget at all.")

FIGURE("bus",
       "Figure 15.1 &mdash; Timing margin against rate per pin for three clocking "
       "schemes on an 8-inch board. The model gives limits of %.1f, %.1f and beyond "
       "%.1f&nbsp;Gb/s respectively."
       % (b15['max_rate_common_clock'], b15['max_rate_source_sync'],
          b15['max_rate_serial']), 120)

TABLE([["Scheme", "This model predicts", "What shipped", "Example"],
       ["common clock", "%.1f Gb/s" % b15['max_rate_common_clock'], "0.133 Gb/s",
        "PCI at 33 MHz, PCI-X at 133 MHz"],
       ["source synchronous", "%.1f Gb/s" % b15['max_rate_source_sync'], "6.4 Gb/s",
        "DDR4 at 3.2 Gb/s per pin, DDR5 at 6.4"],
       ["embedded clock", "%.1f Gb/s" % b15['max_rate_serial'], "32 Gb/s",
        "PCIe Gen5 at 32 GT/s per lane"]],
       [34, 36, 30, 58],
       "Table 15.2 &mdash; The model against history. With one board length, one set of "
       "device timings and no technology scaling, agreement within a factor of two or "
       "three across two orders of magnitude is as much as it can claim; what it "
       "reproduces is the ordering and the spacing.")

CHAP()

# ============================================================= chapter 16 ===
H1("16&nbsp;&nbsp;Measurement, De-embedding and Correlation")

P("A channel model is only as good as the scattering parameters it is built from, and "
  "those arrive with defects. They are band-limited because the instrument stops "
  "somewhere. They are undefined at direct current, because a network analyser cannot "
  "measure there. They frequently violate passivity or causality by small amounts, "
  "because they have been through a de-embedding step that subtracted something slightly "
  "wrong. Each defect is applied here to the actual backplane channel, and the "
  "equaliser is redesigned against each damaged version &mdash; the honest comparison, "
  "since a real receiver adapts to whatever it is given.")

qc = D[16]['qc']
TABLE([["Case", "Max power", "Precursor energy", "Min-phase departure",
        "Equalised eye", "Error"]] +
      [[r['case'], "%.4f" % r['max_power'],
        "%.1f dB" % r['precursor_energy_db'],
        "%.2f&deg;" % r['rms_phase_err_deg'],
        "%.4f V" % r['eye_v'], "%+.2f %%" % r['eye_err_pct']] for r in qc],
       [46, 22, 26, 28, 22, 18],
       "Table 16.1 &mdash; Four defects priced in eye height. The passivity violation is "
       "the only one that makes the channel look <i>better</i> than it is, which is what "
       "makes it dangerous. Moving the reference plane by 15&nbsp;ps costs essentially "
       "nothing, as it should: a pure delay is perfectly causal, and a check that "
       "flagged it would train its users to ignore it.")

dc = D[16]['dc']['rows']
zero = [r for r in dc if r['dc_mode'] == 'zero']
if zero:
    P("The single highest-leverage number in an S-parameter file is the one nobody "
      "measures. The value at direct current sets the baseline the whole time-domain "
      "response sits on, because it is the integral of the impulse response. Assuming it "
      "is zero &mdash; which some tools do by default, on the reasonable-sounding "
      "grounds that no data means no signal &mdash; costs %.1f per cent of the eye, from "
      "one missing point at one end of a sweep with sixteen thousand of them."
      % abs(zero[0]['eye_err_pct']))

FIGURE("echo",
       "Figure 16.1 &mdash; Left: the backplane channel this report works against. "
       "Right: the eye error produced by an identical internal reflection placed at "
       "different delays. Every case agrees with the truth on insertion loss to within "
       "a few thousandths of a decibel; the eye error ranges over several per cent.",
       150)

ec = D[16]['echo']['rows']
ilmin = min(r['il_rms_err_db'] for r in ec)
ilmax = max(r['il_rms_err_db'] for r in ec)
emin = min(r['eye_err_pct'] for r in ec)
emax = max(r['eye_err_pct'] for r in ec)
P("That figure is the uncomfortable result of this chapter. Correlation between a model "
  "and a measurement is almost always judged on insertion loss, because insertion loss "
  "is one curve and easy to overlay. Every row above agrees on insertion loss to between "
  "%.3f and %.3f&nbsp;dB rms &mdash; a spread of %.3f&nbsp;dB, which no reviewer would "
  "notice. The eye error ranges from %+.1f to %+.1f per cent, and the only thing that "
  "differs is where in time the reflection arrives: within the reach of the "
  "decision-feedback taps the receiver subtracts it, and beyond their span nothing does."
  % (ilmin, ilmax, ilmax - ilmin, emax, emin))

CO("Correlate on the pulse response, or on something derived from it &mdash; the cursor, "
   "the residual intersymbol interference after a defined equaliser, the eye height, or "
   "the channel operating margin of chapter 17. All of those are sensitive to where in "
   "time the energy lands, which is what the receiver is sensitive to. Insertion loss is "
   "a useful first check and a poor final one.")

CHAP()

# ============================================================= chapter 17 ===
H1("17&nbsp;&nbsp;Channel Operating Margin and Compliance")

P("A standards body has to publish a test deciding whether a channel is legal. It cannot "
  "simulate the receiver that will eventually be plugged in, because that receiver is "
  "proprietary and may not yet be designed. Nor can it simply limit insertion loss, "
  "because chapter 16 has just shown that insertion loss does not determine the eye. The "
  "resolution is to define a reference receiver &mdash; specific, published and "
  "deliberately unambitious &mdash; run it against the measured scattering parameters, "
  "and report a single number.")

CO("<font name='DejaVu-Bold'>What is implemented here.</font> A three-tap transmit "
   "equaliser from a grid of presets; a continuous-time equaliser from a grid, "
   "normalised at Nyquist so the grid trades shape rather than gain; a limited "
   "decision-feedback section; optimisation over sampling phase; and noise terms for "
   "residual intersymbol interference, crosstalk, jitter and receiver noise, with the "
   "residual interference treated statistically. Not implemented: explicit convolution "
   "of probability distributions, the published transmitter and package models, the full "
   "mask set, or the numerical constants of any one standard. This is not a "
   "certification tool; what survives the simplification is the structure of the "
   "argument.")

cm, it = D[17]['com'], D[17]['interpret']
P("Run against the backplane channel, back-drilled, the reference receiver takes the "
  "deepest continuous-time setting available, %.0f&nbsp;dB, which is what a channel "
  "losing 33&nbsp;dB at Nyquist demands. After it, residual intersymbol interference at "
  "%.1f&nbsp;mV still dominates the noise, with crosstalk at %.1f and receiver noise at "
  "%.1f. The margin is %.2f&nbsp;dB."
  % (cm['ctle_db'], cm['isi_mv'], cm['xt_mv'], cm['rx_mv'], cm['com_db']))

hb = D[17]['hand_budget']
TABLE([["Question asked", "Method", "Result", "Verdict"],
       ["Is this channel compliant?",
        "reference receiver, against a 3 dB threshold",
        "%.2f dB" % it['com_db'], it['verdict'].upper()],
       ["What error ratio does that imply at the slicer?",
        "the same calculation, read as a detector error ratio",
        "%.2e" % it['detector_error_ratio'], "before any coding"],
       ["Would it reach $10^{-12}$ uncoded?",
        "same reference receiver, uncoded target",
        "Q = %.2f against %.2f" % (it['q_equivalent'], it['q_for_1e12']),
        "%s, short by %.2f dB" % (it['uncoded_1e12_verdict'].upper(),
                                  it['shortfall_to_1e12_db'])],
       ["And with a full receive equaliser?",
        "the hand budget in <i>Equalisation in High-Speed Serial Links</i>",
        "Q = %.2f" % hb['q'], "short by %.2f dB" % hb['shortfall_db']]],
       [44, 46, 34, 34],
       "Table 17.1 &mdash; Four questions, one channel, four answers.")

P("The reconciliation is the most useful thing in this report to understand about "
  "compliance. A margin above three decibels is a pass because the threshold is "
  "calibrated against a <i>detector</i> error ratio in the region of one in ten thousand "
  "to one in a hundred thousand &mdash; the error rate at the slicer, before forward "
  "error correction. Every standard using this method also mandates coding, and the "
  "coding carries the link from there to $10^{-12}$ and beyond. The hand budget asked "
  "for $10^{-12}$ uncoded. Two different questions.")

P("Back-drilling, which chapter 4 argued for on physical grounds, is worth "
  "%.2f&nbsp;dB of margin on this channel &mdash; the largest single item any "
  "calculation in this report has identified, and a drilling operation rather than a "
  "design change."
  % D[17]['backdrill_gain_db'])

FIGURE("com",
       "Figure 17.1 &mdash; The verdict under variations in the reference receiver, on "
       "an unchanging channel. Whoever sets the crosstalk figure in the reference model "
       "has more influence over the outcome than the receiver architecture does.", 140)

FIGURE("ild",
       "Figure 17.2 &mdash; Insertion loss, the smooth curve fitted to it, and the "
       "deviation between them. The standards limit the deviation rather than the loss, "
       "because the smooth part is what the equaliser removes and the wiggle is caused "
       "by reflections, which it may not reach.", 120)

P("A compliance verdict is therefore a joint statement about a channel and a reference "
  "receiver, and reading it as a property of the channel alone is a mistake that shows "
  "up as an interoperability argument. It also says nothing about <i>why</i>: a single "
  "number cannot tell a designer which of the seventeen mechanisms in this report is "
  "responsible, which is what the preceding chapters are for, and why a failing margin "
  "should send an engineer back to the pulse response rather than to a bigger equaliser.")

CHAP()

# =============================================================== appendix ===
H1("Appendix A&nbsp;&nbsp;Checks")

P("A model that agrees only with itself is not worth much. Every cross-check this series "
  "makes against an independently published result is listed below, with the "
  "disagreement, followed by the places where two computations inside the series have to "
  "agree with each other. These are generated from the same file the decks read, so the "
  "table cannot drift from the models.")

rows = [(k, v) for k, v in sorted(VER.items())
        if isinstance(v, dict) and 'err_pct' in v]
rows.sort(key=lambda kv: (str(kv[1].get('source', '')).startswith('internal'), kv[0]))


def fnum(x):
    a = abs(x)
    return ("%.4g" % x) if (a >= 1e9 or (0 < a < 1e-3)) else ("%.5g" % x)


TABLE([["Quantity", "This series", "Reference value", "Difference", "Source"]] +
      [[k.split('/')[-1].replace('_', ' '), fnum(v['ours']), fnum(v['published']),
        "%+.2f %%" % v['err_pct'], v['source']] for k, v in rows],
      [40, 24, 24, 22, 48],
      "Table A.1 &mdash; Worst disagreement against published work: %.2f per cent. The "
      "rows whose source begins <i>internal</i> are consistency checks between two "
      "computations in this series rather than against anybody else, and are excluded "
      "from that figure."
      % max(abs(v['err_pct']) for _, v in rows
            if not str(v.get('source', '')).startswith('internal')))

H1("Appendix B&nbsp;&nbsp;The models")

P("Each chapter is backed by one module, and all of them share a two-dimensional "
  "electrostatic field solver used wherever a closed form does not exist &mdash; coupled "
  "pairs beside guard traces, microstrip with air above it, conductors with real "
  "thickness. The solver obtains capacitance matrices by relaxation and the inductance "
  "matrix from the identity $L = \\mu_0\\varepsilon_0\\,C_{\\text{air}}^{-1}$, which is "
  "exact for a transverse electromagnetic wave. It is validated against Cohn's exact "
  "coupled-stripline result to better than half a per cent, and that agreement is what "
  "licenses using it on the cross-sections Cohn does not cover.")

TABLE([["Module", "Chapter", "What it computes"],
       ["fdm2d.py", "shared", "the field solver, and the closed forms it is checked against"],
       ["tline.py", "1", "propagation regions, coaxial optima, reflections, TDR"],
       ["retpath.py", "2", "return-current distribution, slots, stitching, cavity modes"],
       ["materials.py", "3", "skin effect, roughness, causal permittivity, fibre weave"],
       ["via.py", "4", "via parameters, stub resonance, back-drilling, launch optimisation"],
       ["diffpair.py", "5", "modal impedances, coupling cost, mode conversion"],
       ["xtalk.py", "6", "NEXT and FEXT, spacing, guard traces, integrated crosstalk noise"],
       ["pdn.py", "7", "decoupling ladder, anti-resonance, supply noise to jitter"],
       ["jitter.py", "8", "dual-Dirac, bathtub, phase noise, clock recovery"],
       ["timing.py", "9", "flight time, setup and hold, statistical budgets, bus comparison"],
       ["sparam_qc.py", "10", "passivity, causality, truncation, de-embedding, correlation"],
       ["com.py", "11", "channel operating margin and the compliance masks"]],
       [30, 18, 110],
       "Table B.1 &mdash; The modules, all in the Matrix_Articles repository.")

H1("References")

for i, r in enumerate([
    "Howard Johnson and Martin Graham, <i>High-Speed Digital Design: A Handbook of "
    "Black Magic</i>, Prentice Hall, 1993; and <i>High-Speed Signal Propagation: "
    "Advanced Black Magic</i>, Prentice Hall, 2003. The propagation-region table of "
    "section 3.10, the via models of section 5.5, and the return-path and clock-jitter "
    "material.",
    "Stephen H. Hall and Howard L. Heck, <i>Advanced Signal Integrity for High-Speed "
    "Digital Designs</i>, Wiley, 2009. Chapter 5 for the roughness models and chapters "
    "6 and 7 for causal dielectrics and the fibre-weave effect.",
    "Eric Bogatin, <i>Signal and Power Integrity &mdash; Simplified</i>, 2nd ed., "
    "Prentice Hall, 2010. Return paths, differential pairs and power integrity.",
    "Peter J. Pupalaikis, <i>S-Parameters for Signal Integrity</i>, Cambridge "
    "University Press, 2020. De-embedding, passivity and causality enforcement.",
    "Greg Edlund, <i>Timing Analysis and Simulation for Signal Integrity Engineers</i>, "
    "Prentice Hall, 2007.",
    "Mark Horowitz, <i>High-Speed Electrical Signalling: Overview and Limitations</i>.",
    "Seymour B. Cohn, 'Shielded Coupled-Strip Transmission Line', IRE Transactions on "
    "Microwave Theory and Techniques, 1955. The exact result the field solver is "
    "validated against.",
    "E. O. Hammerstad, 'Equations for Microstrip Circuit Design', European Microwave "
    "Conference, 1975; and S. P. Morgan, 'Effect of Surface Roughness on Eddy Current "
    "Losses at Microwave Frequencies', Journal of Applied Physics, 1949.",
    "A. R. Djordjevi&#263;, R. M. Biljic, V. D. Likar-Smiljanic and T. K. Sarkar, "
    "'Wideband Frequency-Domain Characterization of FR-4 and Time-Domain Causality', "
    "IEEE Transactions on Electromagnetic Compatibility, 2001.",
    "IEEE Std 802.3, Annex 93A, <i>Channel Operating Margin</i>, and its descendants in "
    "the 100G, 400G and 800G clauses.",
    "Eric Bogatin's Signal Integrity Journal columns; Yuriy Shlepnev's Simberian "
    "application notes on causal material models, conductor roughness and via design; "
    "Donald Telian's published work on serial-link simulation and correlation; and the "
    "Signal Integrity Journal Fundamentals blog.",
    "Laminate parameters from manufacturers' datasheets: Isola (370HR, I-Speed), "
    "Panasonic (Megtron 6 and 7), Rogers (RO4350B, RO3003). Dk and Df vary with "
    "frequency, resin content and glass style; treat quoted figures as class indicators.",
], 1):
    A(Paragraph(M("[%d]&nbsp; %s" % (i, r)), S["ref"]))

# ------------------------------------------------------------------ build ---
OUT = "/home/brendan/Downloads/Signal Integrity and High-Speed Digital Design.pdf"
doc = BaseDocTemplate(OUT, pagesize=A4,
                      leftMargin=26 * mm, rightMargin=26 * mm,
                      topMargin=20 * mm, bottomMargin=22 * mm,
                      title="Signal Integrity and High-Speed Digital Design",
                      author="Brendan Lynskey")
frame = Frame(doc.leftMargin, doc.bottomMargin, CW,
              A4[1] - doc.topMargin - doc.bottomMargin, id="body")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                   onPage=page_furniture(
                                       "Signal Integrity & High-Speed Digital Design"))])
doc.build(story)
print("wrote", OUT)
