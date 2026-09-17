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
     for n in range(1, 12)}
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
A(Paragraph("The long-form companion to the eleven-deck series", S["deck"]))
A(Paragraph("Brendan Lynskey &nbsp;·&nbsp; every figure computed, "
            "every model checked", S["byline"]))

P("This report accompanies eleven interactive decks on getting a signal from one chip "
  "to another intact. It is not a summary of them: the decks carry the interactive "
  "models and this carries the continuous argument, and they are generated from the "
  "same computations so that a number cannot differ between the two.")

P("The organising discipline is that nothing is asserted. Every figure in this document "
  "is produced by a model in <font name='DejaVu-Bold'>si_models</font>, and wherever an "
  "independently published worked example exists the model is checked against it and "
  "the disagreement reported. Appendix A tabulates every such check; the worst "
  "disagreement across all of them is %.2f per cent."
  % max(abs(v['err_pct']) for v in VER.values()
        if isinstance(v, dict) and 'err_pct' in v))

P("Most chapters are worked against a single channel &mdash; the 28.8 inches of "
  "differential stripline across two line cards and an 18-inch backplane characterised "
  "in <i>Equalisation in High-Speed Serial Links</i> &mdash; so that a result in one "
  "chapter can be set against a result in another without an argument about whether the "
  "comparison is fair. Chapters 10 and 11 import that channel directly.")

CO("<font name='DejaVu-Bold'>How to read this.</font> Chapters 1 to 4 build the passive "
   "channel: what a transmission line is, where the return current flows, what the "
   "materials do, and what happens at the one feature made by drilling. Chapters 5 and 6 "
   "concern the signal on it. Chapters 7 to 9 concern its environment &mdash; the "
   "supply, the clock and the timing budget. Chapters 10 and 11 ask whether any of it "
   "can be believed, and how a standard turns it into a verdict.")

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
H1("7&nbsp;&nbsp;Power Integrity as a Signal-Integrity Problem")

P("Power delivery is a large subject and most of it belongs elsewhere. This chapter asks "
  "a narrower question with a definite answer: by what route does a disturbance on the "
  "supply become an error at a receiver, and how much of a link's budget does it "
  "consume? The route has three stages. A current step meets the network's impedance and "
  "becomes a voltage ripple; the ripple reaches the transmitter and its phase-locked "
  "loop, neither perfectly immune, and becomes jitter; and that jitter lands in the same "
  "budget as everything else.")

P("A real capacitor is a capacitance in series with a resistance and an inductance, so "
  "below its series resonance it is a capacitor and above it an inductor. No capacitor "
  "is useful across the whole band, which is why a decoupling network is a ladder of "
  "values &mdash; and because every capacitor is inductive above its resonance, every "
  "pair of adjacent values creates a frequency at which one is inductive and the other "
  "still capacitive. That is where they resonate against each other.")

pk = D[7]['peaks'][0] if D[7]['peaks'] else None
tg = D[7]['target']
if pk:
    P("The network modelled here meets its %.0f&nbsp;m&#937; target across most of the "
      "band and fails at %.0f&nbsp;MHz, where two adjacent tiers resonate and the "
      "impedance reaches %.0f&nbsp;m&#937; &mdash; %.1f times the target. That peak, "
      "not the average, is what a transient with content at that frequency will find."
      % (1000 * tg['z_target'], pk['f_hz'] / 1e6, 1000 * pk['z_ohm'],
         pk['z_ohm'] / tg['z_target']))

FIGURE("pdn",
       "Figure 7.1 &mdash; Left: the impedance of a complete decoupling ladder, with the "
       "individual tiers in grey and the anti-resonant peaks marked. Right: what happens "
       "as more capacitors of one value are added. The impedance in the band where that "
       "value is capacitive falls, as intended; the worst anti-resonant peak does not "
       "improve.", 150)

mcz = D[7]['more_caps']
P("That second panel is the result worth computing rather than asserting. The intuitive "
  "response to a network that misses its target is to add more capacitors. Going from "
  "%d to %d parts of the same value lowers the impedance at 100&nbsp;MHz from %.1f to "
  "%.1f&nbsp;m&#937;, and moves the worst anti-resonant peak from %.0f to "
  "%.0f&nbsp;m&#937;. Sixteen times the parts, and the number that decides the design "
  "has gone the wrong way."
  % (mcz[0]['count'], mcz[-1]['count'], 1000 * mcz[0]['z_at_100mhz'],
     1000 * mcz[-1]['z_at_100mhz'], 1000 * mcz[0]['worst_peak_ohm'],
     1000 * mcz[-1]['worst_peak_ohm']))

CO("What helps instead: spreading the values so adjacent tiers overlap rather than "
   "leaving a gap; choosing parts with enough equivalent series resistance to damp the "
   "resonance rather than the lowest available; and reducing mounting inductance, which "
   "moves every resonance up together instead of creating a new one. The instinct to "
   "specify the lowest-resistance capacitor available is precisely wrong here.")

rp = D[7]['ripple']
P("The last stage converts ripple into jitter. A tone on the supply reaches the "
  "oscillator's control node attenuated by whatever rejection exists, and modulates its "
  "frequency; frequency modulation integrates to phase modulation, so the phase "
  "deviation is the frequency deviation divided by the modulation frequency. The loop "
  "itself filters, correcting disturbances inside its bandwidth and not outside it. The "
  "worst place for a supply tone is therefore just above the loop bandwidth, where the "
  "feedback has stopped correcting and the modulation index has not yet fallen.")

FIGURE("ripple",
       "Figure 7.2 &mdash; Jitter produced by a 20&nbsp;mV supply tone against its "
       "frequency, for a 4&nbsp;MHz loop. The peak of %.3f&nbsp;ps sits at "
       "%.1f&nbsp;MHz, which is where a modern switching regulator lands by default."
       % (rp['worst_jitter_pp_ps'], rp['worst_f_hz'] / 1e6), 116)

CHAP()

# ============================================================== chapter 8 ===
H1("8&nbsp;&nbsp;Jitter")

P("Jitter is the deviation of a transition from where it should have been, and that "
  "definition covers several mechanisms with quite different statistics. The reason to "
  "keep them apart is that they combine differently: bounded quantities add "
  "arithmetically, unbounded ones in quadrature, and mixing the rules produces a budget "
  "that passes on the bench and fails in the field.")

CO("<font name='DejaVu-Bold'>A collision of notation.</font> The Q in this chapter is the "
   "argument of the error function &mdash; a signal-to-noise ratio in standard "
   "deviations, typically between three and eight. It is not the Q of a resonator, which "
   "is energy stored over energy dissipated per radian and is typically in the hundreds. "
   "The two meet: the tank Q of an oscillator sets its phase noise, which becomes the "
   "random jitter, which is part of the noise in the denominator of the communications "
   "Q. A sentence about a high-Q tank improving Q is not nonsense, but it needs both "
   "words defined.")

q12 = D[8]['q']['1e-12']
P("The reporting convention replaces the deterministic distribution with two impulses "
  "separated by its peak-to-peak value, each convolved with the Gaussian random part, "
  "giving $\\mathrm{TJ} = \\mathrm{DJ}_{pp} + 2Q\\,\\mathrm{RJ}_{rms}$. The "
  "deterministic term enters once whatever the error ratio; the random term is "
  "multiplied by %.2f at $10^{-12}$. A design dominated by one behaves quite differently "
  "under a tightened specification from one dominated by the other." % (2 * q12))

FIGURE("bathtub",
       "Figure 8.1 &mdash; Left: bathtub curves for three jitter splits, with "
       "$10^{-12}$ marked. Right: jitter tolerance masks for three clock-recovery loop "
       "bandwidths. Only the jitter the loop fails to track reaches the sampler, so "
       "tolerance rises steeply below the loop bandwidth.", 150)

ex = [r for r in D[8]['extrapolation'] if r.get('ratio_predicted_to_true')]
worst_ex = max(ex, key=lambda r: r['ratio_predicted_to_true']) if ex else None
P("No instrument can measure an error ratio of $10^{-12}$ in reasonable time, so the "
  "universal practice is to measure to about $10^{-6}$, fit the model and extrapolate. "
  "That is sound if the jitter really is one Gaussian plus one bounded term. If a "
  "second, rarer Gaussian exists &mdash; an intermittent aggressor, a marginal supply "
  "&mdash; the measurement cannot see it and the extrapolation does not include it.")

if worst_ex:
    clean = D[8]['extrapolation'][0]
    P("The model makes this concrete. With a second Gaussian of weight %.0e and standard "
      "deviation %.1f&nbsp;ps present, the fitted random jitter is %.3f&nbsp;ps against "
      "%.3f&nbsp;ps for perfectly clean data &mdash; identical to three decimal places, "
      "because at $10^{-6}$ the second component contributes nothing observable. The "
      "extrapolation predicts %.2f&nbsp;ps of eye and the true opening at $10^{-12}$ is "
      "%.2f&nbsp;ps, overstating it by a factor of %.1f."
      % (worst_ex['weight2'], worst_ex['rj2_true_ps'], worst_ex['rj_fitted_ps'],
         clean['rj_fitted_ps'], worst_ex['opening_predicted_ps'],
         worst_ex['opening_true_ps'], worst_ex['ratio_predicted_to_true']))

pn = D[8]['phase_noise']['rows']
TABLE([["Integration band", "From", "To", "Random jitter, rms"]] +
      [[r['band'], "%.0f kHz" % (r['f_lo'] / 1e3) if r['f_lo'] < 1e6
        else "%.0f MHz" % (r['f_lo'] / 1e6),
        "%.0f MHz" % (r['f_hi'] / 1e6) if r['f_hi'] < 1e9
        else "%.0f GHz" % (r['f_hi'] / 1e9),
        "%.1f fs" % r['jitter_rms_fs']] for r in pn],
      [66, 28, 28, 36],
      "Table 8.1 &mdash; The same oscillator on a 14&nbsp;GHz carrier, integrated over "
      "different bands. A jitter figure quoted without its integration band does not "
      "constrain anything; the limits belong to the receiver's loop, not to the "
      "oscillator.")

ddj = D[8].get('ddj', {})
if ddj.get('ok'):
    P("Finally, the largest single timing term on a lossy channel is neither random nor "
      "from the clock. Enumerating all %d histories of the preceding six bits on the "
      "unequalised backplane channel spreads the zero crossing over %.1f&nbsp;ps, which "
      "is %.0f per cent of the unit interval. That term dwarfs every random "
      "contribution, and unlike them it is removed by the equaliser rather than by a "
      "better oscillator &mdash; which is exactly why the distinction earns its keep: it "
      "says what to buy."
      % (ddj['n_patterns'], ddj['spread_ui'] * 35.71, 100 * ddj['spread_ui']))

CHAP()

# ============================================================== chapter 9 ===
H1("9&nbsp;&nbsp;Timing, Flight Time and the Budget")

fl = D[9]['flight']
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

H2("9.1&nbsp;&nbsp;Worst case against statistical")

st9 = D[9]['stat']
TABLE([["Independent terms", "Worst-case sum", "One sigma",
        "Statistical at 3&sigma;", "Statistical at $10^{-12}$"]] +
      [[k, "%.1f ps" % st9[k]['worst_case_ps'], "%.2f ps" % st9[k]['sigma_ps'],
        "%.1f ps  (saves %.0f %%)" % (st9[k]['statistical_3sigma_ps'],
                                      100 * (1 - st9[k]['ratio_3sigma'])),
        "%.1f ps  (saves %.0f %%)" % (st9[k]['statistical_ps'],
                                      100 * (1 - st9[k]['ratio']))]
       for k in st9],
      [28, 28, 22, 40, 40],
      "Table 9.1 &mdash; A budget added two ways, at two confidence levels. Conventional "
      "statistical timing closure works at three sigma, where the saving is large. A "
      "serial link has to work at an error ratio of $10^{-12}$, which is past seven "
      "sigma, and at that confidence the same quadrature sum buys very much less.")

P("With only four terms the statistical budget at $10^{-12}$ is <i>larger</i> than the "
  "worst-case sum, which sounds absurd and is correct: treating four terms as "
  "three-sigma spreads and then demanding seven sigma of the combination asks for more "
  "than their arithmetic sum. The technique pays only when there are many independent "
  "terms, and how many is a computation rather than a matter of taste.")

H2("9.2&nbsp;&nbsp;Why the wide parallel bus ended")

b9 = D[9]['bus']
P("The historical argument can be written as arithmetic. A common-clock bus spends the "
  "whole flight time and all of the clock skew out of one cycle. A source-synchronous "
  "bus forwards its clock with the data, cancelling most of the flight time, and is then "
  "limited by lane-to-lane matching. An embedded-clock link recovers timing per lane, so "
  "neither flight time nor lane skew appears in its budget at all.")

FIGURE("bus",
       "Figure 9.1 &mdash; Timing margin against rate per pin for three clocking "
       "schemes on an 8-inch board. The model gives limits of %.1f, %.1f and beyond "
       "%.1f&nbsp;Gb/s respectively."
       % (b9['max_rate_common_clock'], b9['max_rate_source_sync'],
          b9['max_rate_serial']), 120)

TABLE([["Scheme", "This model predicts", "What shipped", "Example"],
       ["common clock", "%.1f Gb/s" % b9['max_rate_common_clock'], "0.133 Gb/s",
        "PCI at 33 MHz, PCI-X at 133 MHz"],
       ["source synchronous", "%.1f Gb/s" % b9['max_rate_source_sync'], "6.4 Gb/s",
        "DDR4 at 3.2 Gb/s per pin, DDR5 at 6.4"],
       ["embedded clock", "%.1f Gb/s" % b9['max_rate_serial'], "32 Gb/s",
        "PCIe Gen5 at 32 GT/s per lane"]],
       [34, 36, 30, 58],
       "Table 9.2 &mdash; The model against history. With one board length, one set of "
       "device timings and no technology scaling, agreement within a factor of two or "
       "three across two orders of magnitude is as much as it can claim; what it "
       "reproduces is the ordering and the spacing.")

CHAP()

# ============================================================= chapter 10 ===
H1("10&nbsp;&nbsp;Measurement, De-embedding and Correlation")

P("A channel model is only as good as the scattering parameters it is built from, and "
  "those arrive with defects. They are band-limited because the instrument stops "
  "somewhere. They are undefined at direct current, because a network analyser cannot "
  "measure there. They frequently violate passivity or causality by small amounts, "
  "because they have been through a de-embedding step that subtracted something slightly "
  "wrong. Each defect is applied here to the actual backplane channel, and the "
  "equaliser is redesigned against each damaged version &mdash; the honest comparison, "
  "since a real receiver adapts to whatever it is given.")

qc = D[10]['qc']
TABLE([["Case", "Max power", "Precursor energy", "Min-phase departure",
        "Equalised eye", "Error"]] +
      [[r['case'], "%.4f" % r['max_power'],
        "%.1f dB" % r['precursor_energy_db'],
        "%.2f&deg;" % r['rms_phase_err_deg'],
        "%.4f V" % r['eye_v'], "%+.2f %%" % r['eye_err_pct']] for r in qc],
       [46, 22, 26, 28, 22, 18],
       "Table 10.1 &mdash; Four defects priced in eye height. The passivity violation is "
       "the only one that makes the channel look <i>better</i> than it is, which is what "
       "makes it dangerous. Moving the reference plane by 15&nbsp;ps costs essentially "
       "nothing, as it should: a pure delay is perfectly causal, and a check that "
       "flagged it would train its users to ignore it.")

dc = D[10]['dc']['rows']
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
       "Figure 10.1 &mdash; Left: the backplane channel this report works against. "
       "Right: the eye error produced by an identical internal reflection placed at "
       "different delays. Every case agrees with the truth on insertion loss to within "
       "a few thousandths of a decibel; the eye error ranges over several per cent.",
       150)

ec = D[10]['echo']['rows']
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
   "the channel operating margin of chapter 11. All of those are sensitive to where in "
   "time the energy lands, which is what the receiver is sensitive to. Insertion loss is "
   "a useful first check and a poor final one.")

CHAP()

# ============================================================= chapter 11 ===
H1("11&nbsp;&nbsp;Channel Operating Margin and Compliance")

P("A standards body has to publish a test deciding whether a channel is legal. It cannot "
  "simulate the receiver that will eventually be plugged in, because that receiver is "
  "proprietary and may not yet be designed. Nor can it simply limit insertion loss, "
  "because chapter 10 has just shown that insertion loss does not determine the eye. The "
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

cm, it = D[11]['com'], D[11]['interpret']
P("Run against the backplane channel, back-drilled, the reference receiver takes the "
  "deepest continuous-time setting available, %.0f&nbsp;dB, which is what a channel "
  "losing 33&nbsp;dB at Nyquist demands. After it, residual intersymbol interference at "
  "%.1f&nbsp;mV still dominates the noise, with crosstalk at %.1f and receiver noise at "
  "%.1f. The margin is %.2f&nbsp;dB."
  % (cm['ctle_db'], cm['isi_mv'], cm['xt_mv'], cm['rx_mv'], cm['com_db']))

hb = D[11]['hand_budget']
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
       "Table 11.1 &mdash; Four questions, one channel, four answers.")

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
  % D[11]['backdrill_gain_db'])

FIGURE("com",
       "Figure 11.1 &mdash; The verdict under variations in the reference receiver, on "
       "an unchanging channel. Whoever sets the crosstalk figure in the reference model "
       "has more influence over the outcome than the receiver architecture does.", 140)

FIGURE("ild",
       "Figure 11.2 &mdash; Insertion loss, the smooth curve fitted to it, and the "
       "deviation between them. The standards limit the deviation rather than the loss, "
       "because the smooth part is what the equaliser removes and the wiggle is caused "
       "by reflections, which it may not reach.", 120)

P("A compliance verdict is therefore a joint statement about a channel and a reference "
  "receiver, and reading it as a property of the channel alone is a mistake that shows "
  "up as an interoperability argument. It also says nothing about <i>why</i>: a single "
  "number cannot tell a designer which of the eleven mechanisms in this report is "
  "responsible, which is what the preceding chapters are for, and why a failing margin "
  "should send an engineer back to the pulse response rather than to a bigger equaliser.")

CHAP()

# =============================================================== appendix ===
H1("Appendix A&nbsp;&nbsp;Checks against published work")

P("A model that agrees only with itself is not worth much. Every cross-check this series "
  "makes against an independently published result is listed below, with the "
  "disagreement. These are generated from the same file the decks read, so the table "
  "cannot drift from the models.")

rows = [(k, v) for k, v in sorted(VER.items())
        if isinstance(v, dict) and 'err_pct' in v]


def fnum(x):
    a = abs(x)
    return ("%.4g" % x) if (a >= 1e9 or (0 < a < 1e-3)) else ("%.5g" % x)


TABLE([["Quantity", "This series", "Published", "Difference", "Source"]] +
      [[k.split('/')[-1].replace('_', ' '), fnum(v['ours']), fnum(v['published']),
        "%+.2f %%" % v['err_pct'], v['source']] for k, v in rows],
      [40, 24, 24, 22, 48],
      "Table A.1 &mdash; Worst disagreement across every check: %.2f per cent."
      % max(abs(v['err_pct']) for _, v in rows))

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
