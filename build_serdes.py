"""Builds 'Equalisation in High-Speed Serial Links'.

Third article in the Matrix Methods pair, extending the network-parameter and
digital-filter companions into a worked link design. Every number quoted below
is pulled from _serdes_results.json, which serdes_model.py computes.
"""

import json
import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageTemplate, Paragraph, Spacer)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docstyle import (callout, datatable, page_furniture, register_fonts,  # noqa: E402
                      styles)

register_fonts()
S = styles()
FIG = os.path.join(HERE, "figs")
CW = 158 * mm
R = json.load(open(os.path.join(HERE, "_serdes_results.json")))
RM = json.load(open(os.path.join(HERE, "_serdes_remedies.json")))


def n(key, fmt="%.1f"):
    return fmt % R[key]


ST = R['stages']


def sv(i, key, fmt="%.2f"):
    return fmt % ST[i][key]


def snorm(i, key, fmt="%.3f"):
    return fmt % (ST[i][key] / ST[i]['sig'])


def img(name, width_mm):
    from PIL import Image as PILImage
    p = os.path.join(FIG, name)
    w, h = PILImage.open(p).size
    W = width_mm * mm
    return Image(p, width=W, height=W * h / w)


def fig(name, width_mm, caption):
    return KeepTogether([img(name, width_mm), Paragraph(caption, S["caption"])])


def P(t):
    return Paragraph(t, S["body"])


def CO(t):
    return callout(t, S, CW)


def H1(t):
    return Paragraph(t, S["h1"])


def H2(t):
    return Paragraph(t, S["h2"])


story = []
A = story.append

# ------------------------------------------------------------------ front ---
A(Paragraph("EQUALISATION IN HIGH-SPEED SERIAL LINKS", S["title"]))
A(Paragraph("From a measured channel to a closed link budget — characterisation, "
            "transmit and receive equalisation, and the road to 224 Gb/s", S["deck"]))
A(Paragraph("September 2026  •  Prepared for Brendan Lynskey", S["byline"]))

A(CO(
    "<b>What this report is about, in plain terms.</b> A serial link is a filter you did not "
    "design and cannot change, followed by a filter you did design and can. This report takes "
    "one concrete channel — 28.8 inches of differential stripline across two line cards and a "
    "backplane, carrying 28 GBd — and works it all the way through: what the S-parameters "
    "say, what the pulse response says, why the eye is completely shut before any "
    "equalisation, what each equaliser block can and cannot fix, and what the noise budget "
    "looks like once they are all in place. The answer, for this channel, is that the link "
    "lands " + n('margin_db', '%.2f').lstrip('-') + " dB short of a 10<super>−12</super> "
    "error rate, so the report also works through which of the available remedies actually "
    "recovers that margin — and which, despite being the obvious thing to reach for, does "
    "not. It is a companion to 'Matrix Methods in Network Parameters' and 'Matrix Concepts "
    "in Digital Filter Design': the channel is described by the mixed-mode S-parameters of "
    "the first, and every equaliser in it is an instance of the optimal-tap problem of the "
    "second."))
A(Spacer(1, 7))

A(datatable([
    ["If you want…", "Turn to…", "What you will find"],
    ["The short version of why links need equalisers at all", "§1",
     "Loss that rises with frequency, reflections, crosstalk, and what each does to a pulse"],
    ["What the names mean", "§2.1",
     "IEEE 802.3 against OIF CEI, how 10GBASE-KR decodes, why XAUI is not a network port, "
     "and what the reach classes are"],
    ["How the industry got here", "§2.3",
     "The machines that forced each generation, from the parallel bus running out of road "
     "to accelerator racks running out of copper"],
    ["The channel, characterised", "§3",
     "Stackup, laminates and what a digital board has to do that an RF board does not; "
     "insertion and return loss; a 110 mil via stub putting a notch exactly at Nyquist"],
    ["Why the pulse response is the thing you equalise", "§4",
     "Cursor, pre-cursors and post-cursors, and the closed eye written in numbers"],
    ["What each equaliser block actually does", "§5",
     "CTLE, transmit FFE, DFE — and the receive FFE that a modern part would add"],
    ["The worked design, stage by stage", "§6 and §7",
     "Tap values, eye diagrams and a noise budget that adds up"],
    ["What to do when it does not close", "§8",
     "Seven candidate fixes, priced in dB of margin"],
    ["Why PAM4 is not free", "§9",
     "The same channel at twice the bit rate, and where the 9.5 dB goes"],
], [46 * mm, 18 * mm, 94 * mm], S))
A(Spacer(1, 8))

A(P("<b>The channel, in one line.</b> 28 GBd NRZ, so a unit interval of 35.7 ps and a "
    "Nyquist frequency of 14 GHz. 28.8 inches of 100 Ω differential stripline on Dk 3.7 "
    "laminate at 163 ps per inch, split across a transmit package, a 6-inch line card, an "
    "18-inch backplane, a 4-inch line card and a receive package, with two backplane "
    "connectors and the vias that go with them."))

# ------------------------------------------------------------------- §1 -----
A(H1("1&nbsp;&nbsp; What closes an eye"))

A(P("A transmitter launches a clean rectangular symbol and a receiver, twenty-nine inches "
    "later, sees something that barely resembles it. Four mechanisms are responsible, and it "
    "is worth separating them because each is fixed by a different block."))

A(P("The first and largest is <b>frequency-dependent loss</b>. Copper loss rises as the "
    "square root of frequency because current crowds into an ever thinner skin, and "
    "dielectric loss rises roughly linearly because the laminate's molecules absorb more "
    "energy the faster you ask them to reorient. For the laminate used here the two together "
    "come to " + n('loss_per_inch_nyq', '%.2f') + " dB per inch at 14 GHz. A square pulse is "
    "a wide band of frequencies, so a channel that attenuates the high ones and passes the "
    "low ones does not merely shrink the pulse — it smears it across many symbol periods. "
    "That smearing is <b>intersymbol interference</b>, and it is the dominant impairment in "
    "every channel in this report."))

A(P("The second is <b>reflection</b>. Every impedance discontinuity — a via, a connector "
    "footprint, a package ball — sends part of the wave back, and part of that returns "
    "again from the next discontinuity. The result is energy arriving late, which is ISI "
    "with a longer memory and a less predictable shape than loss-induced smearing. The third "
    "is <b>crosstalk</b> from neighbouring lanes, which unlike the first two is not "
    "correlated with your own data and therefore behaves as noise rather than as ISI. The "
    "fourth is <b>jitter</b>, which moves the sampling instant rather than the level, and "
    "which converts into amplitude error in proportion to the slope of the signal at the "
    "moment you sample it."))

A(CO(
    "<b>Why not just send less far, or use better laminate?</b> Both help, and §8 prices "
    "them. But the economics of a backplane system are set by the chassis, the connector and "
    "the laminate cost, all of which are decided long before the SerDes is chosen, and none "
    "of which scale with each doubling of data rate. Equalisation is the part of the problem "
    "that lives on silicon, which is the only part that gets cheaper every generation. That "
    "is why every rate increase for twenty years has been paid for with more equalisation "
    "rather than with better copper."))
A(Spacer(1, 8))

# ------------------------------------------------------------------- §2 -----
A(H1("2&nbsp;&nbsp; A short history"))

A(H2("2.1&nbsp;&nbsp; The names, decoded"))
A(P("The names in this section come from three different bodies producing three different "
    "kinds of document, and the distinction is worth having before the history starts. It is "
    "a common assumption that they are all flavours of Ethernet. Some are; several of the "
    "most frequently cited are not. The sensible place to begin is the one every engineer has "
    "physically handled."))

A(P("<b>PCI Express</b> is published by PCI-SIG, an industry consortium, and it is a complete "
    "interconnect specification — electrical layer, link layer, transaction layer, "
    "configuration model and the mechanical form factors — rather than only a physical layer. "
    "Its naming is the simplest of the three. A link is identified by a <i>generation</i> and "
    "a <i>width</i>: 'Gen4 ×16' means sixteen lanes running at the Gen4 rate of 16 GT/s. The "
    "rate is quoted in <b>gigatransfers per second</b>, which is the raw signalling rate "
    "before coding overhead is removed, so it is always a little higher than the payload "
    "throughput. Each lane is full duplex and carries a differential pair in each direction, "
    "which means a ×16 slot is thirty-two pairs — sixty-four conductors — all of which have "
    "to escape the processor package and cross the board together."))

A(datatable([
    ["Generation", "Rate per lane", "Coding", "Payload, ×16 link", "Nyquist"],
    ["1.0 (2003)", "2.5 GT/s", "8b/10b", "4 GB/s each way", "1.25 GHz"],
    ["2.0 (2007)", "5 GT/s", "8b/10b", "8 GB/s", "2.5 GHz"],
    ["3.0 (2010)", "8 GT/s", "128b/130b", "≈15.8 GB/s", "4 GHz"],
    ["4.0 (2017)", "16 GT/s", "128b/130b", "≈31.5 GB/s", "8 GHz"],
    ["5.0 (2019)", "32 GT/s", "128b/130b", "≈63 GB/s", "16 GHz"],
    ["6.0 (2022)", "64 GT/s, PAM4", "FLIT + FEC", "≈121 GB/s", "16 GHz"],
    ["7.0 (draft)", "128 GT/s, PAM4", "FLIT + FEC", "≈242 GB/s", "32 GHz"],
], [26 * mm, 28 * mm, 26 * mm, 36 * mm, 22 * mm], S))
A(Spacer(1, 6))

A(CO(
    "<b>The row worth staring at.</b> Generation 6 doubles the throughput of generation 5 "
    "while leaving the Nyquist frequency exactly where it was, at 16 GHz, because it moves "
    "from two-level to four-level signalling and so halves the symbol rate for a given bit "
    "rate. That is precisely the trade §9 works through for Ethernet — the same channel, "
    "twice the data, and a 9.5 dB signal-to-noise penalty to pay for it. PCIe reached the "
    "same conclusion as Ethernet did, four years later and for the same reason: there was no "
    "more bandwidth to be had from the copper."))
A(Spacer(1, 6))

A(P("Where you meet it matters as much as what it is called, because the channel a PCIe link "
    "has to cross is shaped quite differently from a backplane. The commonest instances are "
    "a graphics or accelerator card in a ×16 slot; an NVMe solid-state drive, which is simply "
    "a PCIe device in an M.2, U.2 or EDSFF package rather than a storage interface in its own "
    "right; a network adapter at ×8 or ×16; the link from processor to chipset; and, since "
    "2019, CXL memory and accelerator devices, which run their own protocol over the PCIe "
    "electrical layer and inherit its channel problems wholesale. Thunderbolt and USB4 "
    "tunnel PCIe as well, which is how an external enclosure can hold a graphics card."))

A(P("Those channels are short — a few inches of motherboard to a slot, or a riser card and "
    "then a slot — but they are unusually rich in connectors and unusually strict about "
    "interoperability. A generation 5 slot has to work with a generation 1 card and with a "
    "card from any vendor, which is why the equalisation is negotiated from a published table "
    "of presets rather than adapted freely, and why so much of the PCIe channel budget is "
    "spent on reflections and crosstalk rather than on the loss that dominates a backplane. "
    "When the budget runs out, the standard's answer is a <b>retimer</b>: a device that "
    "fully recovers the clock and data and retransmits them, resetting the loss budget at the "
    "cost of latency and power. It is worth distinguishing from a <b>redriver</b>, which is an "
    "analogue amplifier and equaliser with no clock recovery — a redriver improves a channel, "
    "a retimer replaces it with two shorter ones."))

A(P("With that in hand, the two families of names that this report leans on more heavily."))

A(P("<b>IEEE 802.3</b> is Ethernet itself, and it specifies complete physical layers — the "
    "coding, the electrical interface, the medium and the compliance tests, as one package. "
    "Its names are systematic once you know the grammar. In <b>10GBASE-KR</b>, the 10G is the "
    "data rate, BASE means baseband signalling rather than modulation onto a carrier, the K "
    "says the medium is a backplane, and the R says the coding is 64b/66b. A trailing digit, "
    "where present, counts lanes: 100GBASE-KR4 is a hundred gigabits over a backplane on four "
    "of them. Revisions of the standard arrive as lettered amendments, which is where 802.3ap, "
    "802.3bj, 802.3ck and the rest come from."))

A(datatable([
    ["Position", "Letter", "Means"],
    ["Medium", "T / K / C",
     "Twisted pair / backplane / twinax copper cable"],
    ["Medium", "S / L / E / F",
     "Short-wavelength multimode fibre / long-wavelength single mode / extra-long / fibre "
     "generally"],
    ["Coding", "X / R",
     "8b/10b (25% overhead) / 64b/66b (about 3%)"],
    ["Lane count", "trailing digit",
     "Number of lanes; absent means one. 100GBASE-KR4 is four lanes of 25 Gb/s"],
], [22 * mm, 26 * mm, 110 * mm], S))
A(Spacer(1, 6))

A(P("<b>XAUI is the odd one out</b>, and it is the term most often misread. It is not a "
    "physical layer over a medium at all: it is a <i>chip-to-chip</i> interface, defined so "
    "that the internal bus of a 10 Gigabit Ethernet MAC can be carried a few inches across a "
    "printed circuit board to a separate physical-layer chip. The name is 'ten gigabit "
    "attachment unit interface' — X is the Roman numeral, and AUI is a term inherited from "
    "the original Ethernet of the 1980s. It carries 10 Gb/s of payload as four lanes of "
    "3.125 gigabaud, the extra rate being the 8b/10b coding overhead. Its descendants XLAUI, "
    "CAUI and the later AUI variants do the same job at 40, 100 and 400 gigabits. When this "
    "report says a generation 'ran XAUI', it means chips talking to each other on a board, "
    "not a cable between two machines."))

A(P("<b>OIF CEI</b> is the other family, and it is not Ethernet at all. The Optical "
    "Internetworking Forum publishes <i>Implementation Agreements</i> rather than standards, "
    "and its Common Electrical I/O series specifies the electrical interface alone — the "
    "signalling, the channel, the transmitter and receiver compliance — with no reference to "
    "what protocol runs over it. That is the point of them. CEI-28G is the electrical layer "
    "that a 28 gigabit lane sits on whether it is carrying Ethernet, Fibre Channel, "
    "InfiniBand or optical transport, and it is reused by all of them rather than belonging "
    "to any. Each generation is subdivided by reach, which is the part that matters for this "
    "report because reach is what sets the channel loss."))

A(datatable([
    ["Class", "Stands for", "Roughly", "Typical use"],
    ["XSR", "Extremely short reach", "a few centimetres",
     "Die to die, or chip to an optical engine in the same package"],
    ["VSR", "Very short reach", "about 10 cm",
     "Chip to a front-panel pluggable module"],
    ["MR", "Medium reach", "about 50 cm",
     "Chip to chip across a board, or across a mezzanine"],
    ["LR", "Long reach", "about 100 cm",
     "Backplane — two connectors and the worked example of this report"],
], [18 * mm, 34 * mm, 26 * mm, 80 * mm], S))
A(Spacer(1, 6))

A(CO(
    "<b>How the two fit together, and one more name.</b> IEEE defines the network and its "
    "ports; OIF defines the electrical interfaces that connect chips to one another and to "
    "optical modules. They are developed in step — CEI-112G and IEEE 802.3ck arrived together "
    "and are aligned on rate and channel — so a lane can legitimately be described either "
    "way depending on which layer you are discussing. One other name recurs below. "
    "<b>KP4 FEC</b> is the Reed–Solomon code RS(544,514), named after the 100GBASE-KP4 "
    "physical layer it was first specified for and now used far beyond it."))
A(Spacer(1, 8))

A(H2("2.2&nbsp;&nbsp; From fixed de-emphasis to adaptive equalisation"))
A(P("The first serial links worth the name ran at a few gigabits per second over channels "
    "that were, by later standards, almost transparent. XAUI in 2002 ran 3.125 GBd over a "
    "channel with perhaps 6 dB of loss at Nyquist, and a fixed two-tap transmit "
    "de-emphasis — implemented as a switchable current in the output driver — was enough. "
    "There was nothing adaptive about it; a board designer chose a setting from a table."))

A(P("The step that made modern links possible was 10GBASE-KR in 2007, which standardised "
    "three things at once: a three-tap transmit feed-forward equaliser, a receive "
    "decision-feedback equaliser, and — most importantly — a <b>training protocol</b> by "
    "which the receiver tells the transmitter which way to move its taps. Until then "
    "equalisation had been open-loop and set by hand. After it, a link could negotiate its "
    "own settings at start-up, and channels with 20 dB of loss became routine."))

A(P("CEI-28G, from around 2011, added the continuous-time linear equaliser as a standard "
    "receive block and pushed decision feedback from one or two taps to a dozen or more. "
    "This is the generation the worked example in this report belongs to, and it is the last "
    "one in which a designer can reasonably follow every block by hand. What came next "
    "changed the character of the problem: 400 Gigabit Ethernet and CEI-56G, standardised "
    "from 2017, moved from two-level signalling to four-level PAM4 and made forward error "
    "correction mandatory rather than optional. The 9.5 dB that PAM4 gives away (§9) is "
    "simply not recoverable by equalisation, so the industry stopped trying to reach "
    "10<super>−12</super> raw and started budgeting to a pre-correction error rate of a few "
    "times 10<super>−4</super> instead."))

A(P("IEEE 802.3ck and CEI-112G, from 2022, completed the transition by replacing the "
    "analogue slicer with an analogue-to-digital converter and doing the equalisation in the "
    "digital domain. Once the waveform is in a register file, the number of taps stops being "
    "a question of silicon area per tap and becomes a question of digital power, and "
    "algorithms that were impractical in analogue — long feed-forward filters, "
    "maximum-likelihood sequence estimation — become available. The 224 Gb/s generation now "
    "being standardised as 802.3dj continues in that direction."))

A(fig("sd_history.png", 152,
      "Figure 1 — Twenty-four years of Ethernet and OIF serial links. Each generation bought "
      "its rate increase with more equalisation on silicon, not with better copper."))

A(H2("2.3&nbsp;&nbsp; The systems that needed them"))

A(P("Standards do not appear because someone wants a faster number. Each of the generations "
    "above was forced by a class of machine that had run out of road, and the shape of the "
    "channel changed as much as the rate did. It is worth following the machines, because "
    "they explain why equalisation went from an afterthought to the largest analogue block "
    "on the die."))

A(P("<b>The parallel bus, and why it ran out.</b> Until the early 2000s almost everything "
    "inside a computer was a wide, slowly clocked, multi-drop parallel bus: PCI at 33 and "
    "then 66 MHz, PCI-X at 133, parallel ATA for disks, parallel SCSI on servers, and a "
    "front-side bus between processor and chipset. The attraction was simplicity — a common "
    "clock, and every receiver samples on the same edge. The problem is that the timing "
    "budget does not scale. Sixty-four data lines must all arrive within a fraction of a "
    "clock period, so the <b>skew</b> between them — from trace-length mismatch, from "
    "crosstalk, from the clock's own jitter — has to shrink in proportion to the clock, "
    "while the physical causes of that skew do not shrink at all. Worse, a multi-drop bus has "
    "a stub at every load, and every stub is a reflection. Ultra-320 SCSI needed heroic "
    "measures to work; Ultra-640 was specified and essentially never shipped. The bus had "
    "stopped being a bus and had become a distributed microwave problem that nobody wanted."))

A(P("The escape was to serialise: one differential pair instead of sixty-four single-ended "
    "lines, the clock embedded in the data rather than distributed alongside it, and "
    "point-to-point rather than multi-drop. That trades pin count for rate, and it removes "
    "skew between bits and stubs at loads in one move — at the cost of needing a clock "
    "recovery loop in every receiver, and of putting the whole timing budget on a single "
    "channel whose loss you now have to fight."))

A(P("<b>First-generation serial, 2000 to 2005.</b> The replacements arrived in a rush: PCI "
    "Express for the expansion bus, Serial ATA for consumer disks, Serial Attached SCSI for "
    "enterprise storage, InfiniBand for high-performance computing clusters, and XAUI inside "
    "the routers and switches being built out for the internet boom. Channels were short and "
    "lossy by only six decibels or so, and a fixed de-emphasis setting chosen from a table "
    "was enough. The hard problems of that era were not equalisation but connector design, "
    "the discipline of routing differential pairs, and the novelty of a clock recovery loop "
    "per lane."))

A(P("<b>The chassis era, 2005 to 2012 — where adaptive equalisation was forced.</b> The "
    "machines that broke fixed equalisation were chassis systems: carrier-grade telecom "
    "shelves built to the ATCA standard, core routers such as the Cisco CRS-1 and Juniper's "
    "T-series, and blade servers from IBM and HP. All of them share an architecture — a "
    "passive backplane or midplane, with line cards or blades plugged into it — and that "
    "architecture creates a problem fixed settings cannot solve. <i>The same line card must "
    "work in every slot.</i> Slot one might be six inches from the switch card and slot "
    "sixteen thirty-six inches, through two connectors either way, and no factory setting is "
    "right for both. The receiver has to discover the channel it has been given, which is "
    "exactly what the training protocol of 10GBASE-KR provides."))

A(P("A second constraint made it worse and made equalisation more valuable still. A chassis "
    "is a ten-year investment and its backplane is passive and unserviceable, while the line "
    "cards are replaced every few years. A backplane etched in 2005 therefore had to carry "
    "the SerDes of 2012, which is precisely why the industry poured its money into "
    "equalisation rather than into new copper. The limiting impairment in those years turned "
    "out to be crosstalk rather than loss, because a backplane connector carries dozens of "
    "pairs through one shroud; that drove a generation of connector redesign around better "
    "shielding, and eventually drove chassis architectures that deleted the midplane "
    "altogether by plugging line cards directly into fabric cards at right angles."))

A(P("<b>The data centre, 2012 to 2020 — the backplane dies.</b> Hyperscale operators "
    "replaced the big chassis router with large numbers of small fixed-configuration "
    "switches wired into a Clos fabric, and the channel changed shape completely. Instead of "
    "thirty inches of backplane there were six to twelve inches from the switch package to a "
    "front-panel cage holding a pluggable optical module or a direct-attach copper cable. "
    "That should have made life easier, and it did not, because the rate went from 10 to 25 "
    "to 50 gigabits per lane over the same period. What did change was the bottleneck: "
    "switch silicon radix grew roughly sixteen-fold in a decade, so a package that once had "
    "dozens of lanes now had hundreds, and getting them out of the package and across the "
    "board became as hard as getting them down the channel. In the same years PCI Express "
    "became a storage interface through NVMe and a memory interface through CXL, which "
    "pushed its channel budgets from a comfortable afterthought into genuine difficulty and "
    "made retimers an ordinary part of a server design."))

A(P("<b>Accelerators and the reach crisis, 2020 onwards.</b> Training large models turned "
    "interconnect into the defining problem of a machine rather than a detail of it, and at "
    "112 gigabits per lane the reach an equaliser can rescue has fallen to a handful of "
    "inches of ordinary laminate. Four responses are visible at once. Cabled backplanes route "
    "twinax assemblies from the package over the top of the board to the front panel, using "
    "the PCB for power and cooling and declining to use it for signals. Co-packaged and "
    "near-package optics move the conversion into the module. Linear-drive optics delete the "
    "module's own retimer so the host SerDes drives the optical engine directly. And chiplet "
    "interfaces such as UCIe keep the fastest links inside the package where the channel is "
    "millimetres of silicon. The largest accelerator racks now carry thousands of copper "
    "cables in a scale-up domain precisely because optics at that density would cost more "
    "power than the copper does."))

A(datatable([
    ["Era", "Machines", "The channel", "What limited it"],
    ["to ~2003", "PCI and PCI-X slots, parallel ATA and SCSI, front-side buses",
     "Wide multi-drop parallel bus, common clock",
     "Skew between bits and stub reflections; neither scales with the clock"],
    ["2000–2005", "PCIe 1.0, SATA, SAS, InfiniBand, XAUI in early routers",
     "Short point-to-point differential pairs, about 6 dB",
     "Connectors, pair routing discipline, and a clock recovery loop per lane"],
    ["2005–2012", "ATCA shelves, core routers, blade servers",
     "20 to 40 inches of backplane through two connectors",
     "The same card must work in every slot, so equalisation had to adapt; then "
     "connector crosstalk"],
    ["2012–2020", "Fixed-configuration switches in Clos fabrics; NVMe and CXL servers",
     "6 to 12 inches, package to front-panel cage",
     "Rate rising faster than reach falling; package and board escape for hundreds of lanes"],
    ["2020–", "Accelerator clusters, 400G and 800G optics",
     "A handful of inches, or no PCB at all",
     "Reach, power per bit, and the cost of converting to light"],
], [22 * mm, 34 * mm, 42 * mm, 60 * mm], S))
A(Spacer(1, 6))

A(CO(
    "<b>The pattern worth taking away.</b> Every era solved its channel problem by moving the "
    "difficulty somewhere cheaper. The parallel bus moved it from pin count to rate. The "
    "backplane era moved it from copper to silicon, because silicon got cheaper every year "
    "and a ten-year chassis did not. The data-centre era moved it from the chassis to the "
    "fabric topology, replacing one enormous channel with many short ones. And the current "
    "era is moving it off the board entirely, into cable and into light. Equalisation is "
    "what made each of those moves survivable while the next one was being worked out."))
A(Spacer(1, 6))

A(H2("2.4&nbsp;&nbsp; The same problem, solved again on every other bus"))
A(P("Ethernet and the OIF agreements are only one branch of the family. PCI Express is the "
    "other one most engineers meet, and it is worth tracing because it faces the same physics "
    "under quite different commercial constraints. Where a backplane Ethernet link is a "
    "point-to-point connection between two devices chosen by the same system architect, a "
    "PCIe link crosses a socket, a connector and an add-in card from a different vendor, and "
    "has to interoperate with parts designed a decade apart. It cannot simply let both ends "
    "adapt freely and hope."))

A(P("Its answer, introduced with PCIe 3.0 in 2010, is a negotiated <b>preset</b> table. "
    "Rather than requesting arbitrary tap movements, the receiver asks the far-end "
    "transmitter for one of eleven predefined combinations of de-emphasis and pre-shoot, and "
    "the link equalisation procedure walks through four phases to agree on them. It is a more "
    "constrained mechanism than the continuous tap negotiation of 10GBASE-KR, and "
    "deliberately so: a finite, published set of transmitter behaviours is what makes "
    "cross-vendor interoperability testable."))

A(datatable([
    ["Generation", "Rate per lane", "Year", "What was added"],
    ["PCIe 1.0 / 2.0", "2.5 and 5.0 GT/s", "2003, 2007",
     "8b/10b coding; fixed de-emphasis chosen by the platform"],
    ["PCIe 3.0", "8 GT/s", "2010",
     "128b/130b coding, transmitter presets and the four-phase link equalisation procedure "
     "— the point at which PCIe became an equalised link"],
    ["PCIe 4.0 / 5.0", "16 and 32 GT/s", "2017, 2019",
     "Tighter channel budgets, retimers become common, and connector and card loss start to "
     "dominate the budget"],
    ["PCIe 6.0", "64 GT/s", "2022",
     "PAM4, FLIT-based framing, and a deliberately <i>lightweight</i> forward error "
     "correction backed by link-level retry"],
    ["PCIe 7.0", "128 GT/s", "2025 (draft)",
     "PAM4 at 64 GBd; the reach question becomes acute and optical options enter the "
     "specification discussion"],
], [28 * mm, 26 * mm, 22 * mm, 82 * mm], S))
A(Spacer(1, 6))

A(CO(
    "<b>Why PCIe chose a weaker code than Ethernet.</b> Both moved to PAM4 and both had to "
    "add forward error correction to survive it, but they made opposite trades. Ethernet "
    "tolerates the hundred nanoseconds or so that a Reed–Solomon KP4 decoder costs, because "
    "a hundred nanoseconds is nothing beside the latency of the network it sits in. PCIe is a "
    "load-store fabric where a processor may be stalled waiting for the answer, so latency is "
    "part of the contract. PCIe 6.0 therefore pairs a much lighter FEC — one that corrects "
    "only a modest number of symbols — with a cyclic redundancy check and a link-level retry "
    "for whatever the FEC misses. Same physics, same constellation, different answer, because "
    "the cost function is different."))
A(Spacer(1, 6))

A(P("The pattern repeats across the other serial buses, and the interesting axis to compare "
    "them on is reach rather than rate. USB grew from 5 Gb/s in 2008 to 20 Gb/s per lane with "
    "USB4, and then to 80 Gb/s in USB4 version 2 by adopting three-level PAM3 signalling — a "
    "compromise that buys throughput with less of a signal-to-noise penalty than PAM4 while "
    "still needing careful equalisation over a consumer-grade cable. SAS reached 22.5 Gb/s, "
    "InfiniBand went from 25 Gb/s NRZ at EDR to 50 and then 100 Gb/s per lane in PAM4 at HDR "
    "and NDR, and DisplayPort and HDMI carry comparable rates over cables with no ground "
    "reference to speak of."))

A(P("At the far end of the axis sits UCIe, the die-to-die interface standardised from 2022. "
    "Its channel is a couple of millimetres of silicon interposer rather than tens of inches "
    "of laminate, and at that reach the loss is negligible, the equalisation is nearly "
    "nothing, and the design problem becomes one of parallelism and power per bit. That is "
    "the direction every one of these standards is being pushed: as the rate climbs, the "
    "reach that equalisation can rescue falls, and the answer is either to shorten the copper "
    "or to stop using it."))

# ------------------------------------------------------------------- §3 -----
A(H1("3&nbsp;&nbsp; The channel: layout, and what the S-parameters say"))

A(H2("3.1&nbsp;&nbsp; The physical channel"))
A(P("The channel is a conventional two-card backplane topology. A transmitter drives out "
    "through its package escape, across six inches of line-card stripline, down through a "
    "via into a backplane connector, along eighteen inches of backplane, up through a second "
    "connector, across four inches on the receiving line card, and into the receiver's "
    "package. Twenty-eight point eight inches of copper in total, on a laminate with a "
    "dielectric constant of 3.7, which gives 163 picoseconds of delay per inch and a "
    "total flight time of 4.7 nanoseconds — a hundred and thirty-one unit "
    "intervals. There are always more than a hundred symbols in flight at once, which is "
    "worth remembering when reasoning about what a reflection does."))

A(fig("sd_topology.png", 152,
      "Figure 2 — The channel. Two connectors, four via transitions and one of them left "
      "un-backdrilled."))

A(H2("3.2&nbsp;&nbsp; What the laminate is, and why it matters more each generation"))
A(P("A dielectric constant of 3.7 and a loss tangent of "
    + n('df_baseline', '%.4f') + " are not arbitrary numbers: they identify a class of "
    "material. Dielectric loss is, to a good approximation, α<sub>d</sub> ≈ 2.3 f √Dk · Df "
    "decibels per inch with f in gigahertz, so the loss tangent Df sets the slope of the "
    "channel directly while the dielectric constant Dk sets the propagation delay and, "
    "through it, how much copper you need for a given reach. The baseline here is a mid-loss "
    "laminate of the kind that was standard for 10 Gb/s work and is now marginal."))

A(datatable([
    ["Laminate", "Dk", "Df", "Dielectric loss at 14 GHz",
     "Typically used for"],
    ["Standard FR-4", "≈4.3", "≈0.022", "1.47 dB/inch",
     "Up to a few Gb/s — PCIe 1.0 and 2.0, USB 3.0, XAUI"],
    ["Isola FR408HR", "3.65", "0.0092", "0.57 dB/inch",
     "8 to 10 Gb/s — PCIe 3.0, 10GBASE-KR"],
    ["<i>This report's channel</i>", "3.70",
     n('df_baseline', '%.4f'), "0.49 dB/inch",
     "Mid-loss; adequate at 10 Gb/s, marginal at 28"],
    ["Isola I-Speed", "3.53", "0.0060", "0.36 dB/inch",
     "16 to 28 Gb/s — PCIe 4.0 and 5.0, CEI-28G"],
    ["Panasonic Megtron 6", "3.55", "0.0045", "0.27 dB/inch",
     "25 to 28 Gb/s backplanes; the low-loss remedy of §8"],
    ["Rogers RO4350B", "3.48", "0.0037", "0.22 dB/inch",
     "RF and mixed-signal boards where Dk stability matters most"],
    ["Isola Tachyon 100G", "3.02", "0.0021", "0.12 dB/inch",
     "56 Gb/s PAM4 and above — CEI-56G, PCIe 6.0"],
    ["Panasonic Megtron 7", "3.35", "0.0020", "0.12 dB/inch",
     "112 Gb/s per lane — 802.3ck, CEI-112G"],
], [30 * mm, 13 * mm, 17 * mm, 26 * mm, 72 * mm], S))
A(Spacer(1, 6))

A(P("Two things that do not appear in a datasheet Dk and Df often matter as much as the "
    "resin does. The first is <b>copper roughness</b>. A foil is deliberately roughened so "
    "that it adheres to the laminate, and at microwave frequencies the current follows that "
    "roughened surface rather than cutting across it, lengthening the path and raising the "
    "conductor loss. Standard foil with a profile of five to seven micrometres can add half "
    "again to the smooth-conductor loss at 14 GHz; reverse-treated foil brings that down, "
    "very-low-profile foil further, and the hyper-VLP grades used above 50 GBd further still. "
    "A board built on excellent resin with ordinary foil can easily lose to one built on "
    "worse resin with better copper."))

A(P("The second is the <b>glass weave</b>. Laminate is resin reinforced with woven glass "
    "cloth, and glass and resin have different dielectric constants — roughly 6 against 3. A "
    "differential pair whose two conductors happen to run one over the glass bundles and the "
    "other over the resin therefore sees two different propagation velocities, which is "
    "intra-pair skew, which is mode conversion by §9 of the companion report. It accumulates "
    "with length and it is the reason long pairs are routed at a small angle to the weave, or "
    "on the flattened, spread-glass styles such as 1078 and 3313 that even out the "
    "difference."))

A(CO(
    "<b>Why the RF laminates are not the answer.</b> The one genuinely surprising row in the "
    "table is Rogers RO4350B, which at 0.22 dB per inch is lower loss than the Megtron 6 that "
    "§8 recommends — and yet nobody builds a backplane out of it. The reasons are all about "
    "system fit rather than decibels. It is engineered for <i>Dk stability</i>, ±0.05 over "
    "temperature and lot, which matters when the dielectric constant sets a filter passband "
    "or an antenna length and is of no use whatever to a serial link. Its Dk of 3.48 is also "
    "too <i>high</i>: digital laminates chase low Dk deliberately, because a lower dielectric "
    "constant allows wider traces at the same 100 Ω differential impedance, and conductor "
    "loss falls roughly as trace width rises. And the conductor term is not a detail at these "
    "frequencies — it is comparable to the dielectric term, and it is dominated by foil "
    "roughness, where differences of 0.1 to 0.2 dB per inch between grades are typical. The "
    "0.05 dB per inch that RO4350B gains on Megtron 6 in the dielectric is smaller than the "
    "foil advantage it does not come packaged with, because the digital vendors sell core, "
    "prepreg, glass style and foil profile as one qualified system and the RF vendors offer a "
    "narrower range."))
A(Spacer(1, 6))

A(P("Two more practical objections finish the case. RF laminates are not offered in the "
    "spread-glass constructions that control intra-pair skew, because a single-ended RF line "
    "does not care about weave and a differential pair very much does. And the bondply system "
    "and the reliability qualification behind a material such as RO4350B target thin, "
    "low-layer-count boards, not a forty-layer backplane built by sequential lamination with "
    "tens of thousands of plated through-holes to survive thermal cycling — on top of which "
    "the ceramic filler is abrasive enough to matter to drill life, and the laminate costs "
    "several times as much per square foot over a large panel. Where these materials do "
    "appear in a high-speed digital product is as an RF island hybrid-laminated into an "
    "otherwise digital stackup, which is the sensible way to use them. The PTFE-based "
    "laminates take every one of these trade-offs further in the wrong direction: lower loss "
    "again, but poorer dimensional stability, special processing for adhesion, and worse "
    "through-hole reliability in a thick board."))

A(CO(
    "<b>How the generations map onto materials.</b> Up to a few gigabits per second, ordinary "
    "FR-4 and ordinary foil. At 8 to 10 Gb/s, an improved FR-4 with reverse-treated foil. At "
    "16 to 28 Gb/s, a genuine low-loss laminate, very-low-profile copper and spread glass. At "
    "56 and 112 Gb/s per lane, an ultra-low-loss resin with hyper-VLP foil — <i>and</i> a "
    "much shorter channel, because at those rates no material saves a backplane. That last "
    "clause is the important one: materials bought perhaps 15 dB of improvement across twenty "
    "years, while the loss at Nyquist of a fixed length of copper roughly tripled over the "
    "same period."))
A(Spacer(1, 6))

A(H2("3.3&nbsp;&nbsp; What the board has to do, and why that rules out most of the choices"))

A(P("The comparison with RF laminates is easier to see once the rest of the board is on the "
    "table, because almost nothing about a high-speed digital stackup is chosen for signal "
    "integrity alone. It is a compromise between routing density, power delivery, mechanical "
    "rigidity and manufacturing yield, and the signal integrity engineer arrives late and "
    "negotiates."))

A(P("<b>Layer count is set by escape routing.</b> A modern switch or accelerator package has "
    "thousands of balls on a one-millimetre or finer pitch, of which several hundred pairs "
    "are high-speed. Every pair has to leave the ball field, which means threading between "
    "the via antipads of the balls around it, and the number of traces that fit in that "
    "channel is small — often one or two. The only way to escape hundreds of pairs is to "
    "escape a few per layer and then use a great many layers. Twenty to forty layers is "
    "ordinary for a line card and more than that is not unusual, and the count is decided by "
    "the ball map, not by the dielectric."))

A(P("<b>Trace width is set by the same constraint, not by loss.</b> Conductor loss falls as "
    "the trace gets wider, so a signal integrity engineer left alone would use very wide "
    "traces. The escape channel forbids it: the width is whatever fits between the antipads, "
    "typically four to six mils where the loss calculation would prefer eight to twelve. This "
    "is the single sharpest difference from RF practice, where a line can be as wide as the "
    "substrate thickness allows because there are a few dozen nets on the board rather than "
    "a few thousand."))

A(P("<b>Board thickness is close to immovable.</b> It follows from the layer count and the "
    "dielectric thickness each layer needs, and it is then pinned in place from three other "
    "directions. Press-fit backplane connectors are qualified for a specific thickness range "
    "and the compliant pin will not seat properly outside it. A large card must be stiff "
    "enough not to sag in its guides or flex during insertion. And the plated through-hole "
    "has an aspect ratio limit — thickness divided by drill diameter — beyond which the "
    "plating chemistry will not reliably throw down the barrel, which for a thick board "
    "forces a larger drill, which enlarges the antipad, which takes away the routing channel "
    "you were trying to create. Everything is coupled."))

A(CO(
    "<b>Which is why back-drilling exists at all.</b> A thick board means long via barrels, "
    "and a signal that enters at layer three and leaves at layer six has left most of the "
    "barrel dangling as a stub. In RF you would simply use a thin substrate and the problem "
    "would not arise. Here the thickness is not available as a design variable, so the "
    "industry invented a second drilling operation to remove the unused copper afterwards — "
    "at extra cost, with its own tolerance, and leaving six to ten mils of residual stub "
    "behind. §3.4 shows what happens when that operation is skipped."))
A(Spacer(1, 6))

A(P("Set against RF practice the contrast is stark, and it explains the material choice "
    "better than any loss figure does."))

A(datatable([
    ["", "High-speed digital board", "RF board"],
    ["Layer count", "20 to 40, occasionally more; set by package escape",
     "2 to 8; often a single ground plane"],
    ["Thickness", "2.5 to 6 mm, fixed by layer count, connectors, stiffness and "
     "plating aspect ratio", "0.25 to 1.5 mm, chosen freely to set line width and radiation"],
    ["Trace width", "4 to 6 mil, set by the escape channel between antipads",
     "Tens of mils, set by impedance and loss"],
    ["Nets", "Thousands, all at one controlled impedance",
     "Tens, individually tuned"],
    ["Bandwidth", "DC to beyond Nyquist, broadband",
     "A band, often a narrow one"],
    ["Vias", "Tens of thousands; each an impairment to be back-drilled",
     "Few; often a deliberate design element"],
    ["What must be stable", "Loss slope and impedance across a huge board and a long "
     "production run", "Dk, tightly, over temperature and lot"],
    ["Shares the stackup with", "Dozens of power rails, plane splits and decoupling",
     "Little else"],
], [28 * mm, 66 * mm, 64 * mm], S))
A(Spacer(1, 6))

A(P("Read down that table and the earlier verdict on RO4350B becomes almost inevitable. A "
    "material whose distinguishing virtue is tightly controlled Dk, supplied in thin "
    "constructions for boards with a handful of layers, is answering a question the digital "
    "designer never asks, in a form he cannot use, at a price that scales with an area he "
    "cannot avoid."))

A(H2("3.4&nbsp;&nbsp; Insertion loss, and a via stub in exactly the wrong place"))
A(P("The differential insertion loss S<sub>dd21</sub> is the single number a link budget "
    "starts from. Here it is " + n('il_1g', '%.1f') + " dB at 1 GHz and "
    + n('il_nyq_bd', '%.1f') + " dB at the 14 GHz Nyquist frequency — a hard channel, at "
    "the limit of what 28 GBd NRZ is normally asked to cross, but not an unreasonable one."))

A(P("That figure assumes the vias have been back-drilled. If one of them is left with the "
    "unused barrel intact, the result is a 110 mil open-circuited stub hanging off the "
    "through path, and an open stub is a quarter-wave short at the frequency where its "
    "length equals a quarter wavelength. At 163 ps per inch that lands at "
    + n('stub_notch_ghz', '%.1f') + " GHz, which is within a percent of Nyquist. The stub "
    "adds " + n('stub_excess_at_nyq', '%.0f') + " dB of loss at exactly the frequency the "
    "link can least afford it, taking the channel from " + n('il_nyq_bd', '%.1f') + " dB to "
    + n('il_nyq_stub', '%.1f') + " dB. No amount of equalisation recovers that. Back-drilling "
    "is not an optimisation; on this channel it is the difference between a link and a "
    "brick."))

A(fig("sd_channel.png", 152,
      "Figure 3 — Differential insertion loss with and without the via stub, and the "
      "differential return loss. The stub notch sits within a percent of Nyquist."))

A(H2("3.5&nbsp;&nbsp; Return loss, crosstalk and mode conversion"))
A(P("Return loss matters less directly than insertion loss but is not ignorable. Here "
    "S<sub>dd11</sub> peaks at about " + n('rl_nyq', '%.0f') + " dB near Nyquist, and the "
    "ripple visible on the insertion-loss curve is the signature of energy bouncing between "
    "the two connector transitions. Each bounce is a delayed copy of the signal, and because "
    "the round trip between connectors is many unit intervals long, those copies land as "
    "isolated ISI terms far from the cursor — exactly where a decision-feedback equaliser "
    "with a handful of taps cannot reach them."))

A(P("Crosstalk does not appear in a two-port measurement at all, which is one reason "
    "characterisation is done on a multiport fixture. Near-end crosstalk from lanes driving "
    "in the opposite direction and far-end crosstalk from lanes driving alongside are "
    "aggregated into a single figure of merit, the integrated crosstalk noise, which is "
    "what enters the budget in §7 as " + n('sigma_xt', '%.1f') + " mV rms. And mode "
    "conversion, the S<sub>cd</sub> block of the companion report, matters here for a reason "
    "specific to equalisation: converted energy is energy the receiver never sees, so it "
    "reduces the cursor without appearing anywhere in the differential insertion loss."))

# ------------------------------------------------------------------- §4 -----
A(H1("4&nbsp;&nbsp; From S-parameters to a pulse response"))

A(P("Insertion loss tells you how much of a sine wave survives. It does not directly tell "
    "you what a receiver sees, because a receiver does not sample sine waves — it samples "
    "one symbol at a time, in the presence of all the others. The object that answers that "
    "question is the <b>pulse response</b>: the voltage waveform produced by sending a "
    "single one-unit-interval symbol and nothing else. Take the inverse Fourier transform of "
    "S<sub>dd21</sub> to get the impulse response, convolve with a one-UI rectangle, and you "
    "have it."))

A(P("Sample that waveform once per unit interval, at the phase that maximises the peak, and "
    "the resulting sequence of numbers is the whole story. The largest sample is the "
    "<b>cursor</b>: the part of the symbol that arrives when it is supposed to. Samples "
    "before it are <b>pre-cursors</b>, energy that has arrived early; samples after it are "
    "<b>post-cursors</b>, energy still arriving one, two, ten symbols later. Every one of "
    "them lands on top of a neighbouring symbol."))

A(fig("sd_pulse.png", 152,
      "Figure 4 — The single-bit response before and after the CTLE, and the same waveform "
      "sampled on the unit-interval grid. The circled sample is the cursor; everything else "
      "is interference."))

A(CO(
    "<b>The closed eye, in numbers.</b> For this channel the cursor is "
    + n('raw_cursor', '%.3f') + " of the transmitted amplitude, and the sum of the absolute "
    "values of every other tap is " + n('raw_isi', '%.3f') + " — nearly three times as "
    "large. The worst-case eye opening is twice the difference between the two, which comes "
    "out at " + n('raw_eye', '%.2f') + ". A negative eye opening is not a small eye; it "
    "means that for some patterns of neighbouring data the receiver sees the wrong sign "
    "entirely. The first post-cursor alone is " + n('raw_post1', '%.3f') + " and the first "
    "pre-cursor " + n('raw_pre1', '%.3f') + ", each comparable with the cursor itself. "
    "Nothing about this link works without equalisation."))
A(Spacer(1, 8))

# ------------------------------------------------------------------- §5 -----
A(H1("5&nbsp;&nbsp; The equalisers, one block at a time"))

A(H2("5.1&nbsp;&nbsp; The continuous-time linear equaliser"))
A(P("The CTLE is an analogue filter in the receiver front end, usually a degenerated "
    "differential pair whose source degeneration is bypassed by a capacitor so that gain "
    "rises with frequency. It is the cheapest equalisation there is: a handful of devices, "
    "no clock, no adaptation loop beyond selecting one of a dozen settings. What it does is "
    "approximately invert the channel's slope over the band of interest. What it cannot do "
    "is add gain — a CTLE with a boost of " + n('ctle_boost_db', '%.1f') + " dB achieves it "
    "by attenuating low frequencies, not by amplifying high ones, so the cursor shrinks "
    "along with the ISI. That is less damaging than it sounds, because the front-end noise "
    "and the crosstalk arriving alongside the signal are attenuated by the same filter: "
    "over the receiver's noise bandwidth this setting has a gain of "
    + n('ctle_noise_gain_db', '%.1f') + " dB, so what a CTLE really trades is signal "
    "against ISI rather than signal against noise."))

A(P("That is exactly what happens here. The CTLE brings the ISI sum down from "
    + n('raw_isi', '%.3f') + " to " + n('ctle_isi', '%.3f') + ", a real improvement, but the "
    "cursor falls from " + n('raw_cursor', '%.3f') + " to " + n('ctle_cursor', '%.3f') + " "
    "at the same time. The eye opening improves from " + n('raw_eye', '%.2f') + " to "
    + n('ctle_eye', '%.2f') + " — still negative, still shut. The CTLE has done useful work "
    "and has not, on its own, produced a link. The setting used here is the one a receiver's "
    "adaptation converges on — the best of the sixteen or so a real part offers, found by "
    "sweeping them and keeping whichever gives the highest signal-to-noise ratio at the "
    "slicer."))

A(fig("sd_ctle.png", 118,
      "Figure 5 — The CTLE family. More boost is bought by giving away more low-frequency "
      "gain. The dashed curve is the inverse channel, for scale: a single pole-zero pair "
      "cannot track it far."))

A(H2("5.2&nbsp;&nbsp; The transmit feed-forward equaliser"))
A(P("The transmitter can pre-distort. A feed-forward equaliser is a short FIR filter running "
    "at the symbol rate, and because it operates before the channel it shapes the signal "
    "without amplifying anything the channel or the neighbours add afterwards. That is its "
    "unique advantage, and it is the reason transmit equalisation survives even though "
    "receivers have become far more capable."))

A(P("Its unique disadvantage is the peak-power constraint. A transmitter has a maximum "
    "output swing, so the tap magnitudes must sum to no more than one; every unit of "
    "correction is subtracted from the main cursor. The three-tap filter designed here, with "
    "two pre-taps set to zero-force the first two pre-cursors, comes out as ["
    + ", ".join("%.3f" % t for t in R['ffe_taps']) + "], and the price is visible "
    "immediately: the cursor falls again, from " + n('ctle_cursor', '%.3f') + " to "
    + n('ffe_cursor', '%.3f') + ". The eye opening finally turns positive, at "
    + n('ffe_eye', '%.3f') + ", but only just."))

A(CO(
    "<b>Why the transmitter is asked to handle pre-cursors specifically.</b> A "
    "decision-feedback equaliser works by subtracting the known contribution of symbols it "
    "has already decided. It therefore cannot touch pre-cursor ISI, which is caused by "
    "symbols it has not decided yet. A receive feed-forward filter can, at the cost of noise "
    "enhancement. A transmit FFE can, at the cost of swing. Splitting the work so that the "
    "transmitter handles the pre-cursors and the feedback path handles the post-cursors is "
    "not arbitrary — it puts each impairment where the cheapest remedy is."))
A(Spacer(1, 6))

A(H2("5.3&nbsp;&nbsp; The receive feed-forward equaliser: two effects, not one"))
A(P("The receiver can filter too, and a symbol-rate FIR there is the most flexible linear "
    "block available: it sees the signal after the channel has done its worst, it can have "
    "many taps, and in a digital receiver it adapts continuously. It is the block that "
    "distinguishes a modern ADC-DSP receiver from the analogue one this worked example is "
    "built around, and §8 prices exactly what adding it would be worth here."))

A(P("It is tempting — and wrong — to describe such a filter as a device that removes "
    "interference at the cost of amplifying noise. It does two things at once, and they pull "
    "in opposite directions. Consider what happens when the filter forms a weighted sum of "
    "several successive samples of the received waveform. The <b>signal</b> contributions add "
    "<i>coherently</i>: the pre- and post-cursor samples are not noise, they are the same "
    "transmitted symbol arriving at the wrong time, so when the filter lines them up and adds "
    "them their amplitudes add directly. The <b>noise</b> contributions, being uncorrelated "
    "from sample to sample, add only in root-sum-square. Combine k samples carrying "
    "comparable signal and the signal grows roughly as k while the noise grows as √k, so the "
    "ratio improves."))

A(P("That is the same mechanism as a matched filter, and it has the same limit. The most any "
    "receiver can extract from a pulse is set by the total energy in that pulse: the "
    "<b>matched-filter bound</b>, SNR = 2E/N<sub>0</sub>, is what you would get from a filter "
    "that collects every scrap of the pulse response and worries about nothing else. A "
    "linear equaliser cannot beat that bound, and it usually falls short of it, because it is "
    "not free to collect energy wherever it likes — it must also drive the interference to "
    "zero, and on a channel with deep spectral nulls those two objectives conflict. The "
    "shortfall is what the literature means by <b>noise enhancement</b>."))

A(CO(
    "<b>What the number in this report actually measures.</b> The 'noise enhancement' quoted "
    "here is not the raw gain of the filter. The nine-tap minimum-mean-squared-error design "
    "on this channel has a Euclidean tap norm of about "
    + n('rxffe_noise_gain', '%.0f') + ", which would be an alarming figure if it were a noise "
    "penalty — but the same taps raise the cursor by a comparable factor, because they are "
    "collecting signal that the channel had scattered across a dozen symbol periods. The "
    "meaningful quantity is the <i>ratio</i> of the two, the noise gain divided by the signal "
    "gain, and that comes out at " + n('rxffe_noise_enh_db', '%.2f') + " dB. That is the net "
    "cost, already accounting for the coherent recovery. Quoting the tap norm alone would "
    "overstate the penalty by more than twenty decibels."))
A(Spacer(1, 6))

A(P("Two consequences follow. The first is that a linear equaliser is worth having even when "
    "the channel is benign, because energy collection is a gain and not merely a "
    "rearrangement. The second is the one that shapes real receivers: since the penalty is "
    "the <i>gap</i> between coherent signal gain and incoherent noise gain, any mechanism "
    "that removes interference without touching the noise at all is strictly better. That is "
    "precisely what the next block does, and it is why a decision-feedback tap is preferred "
    "to a feed-forward tap wherever a decision-feedback tap will do."))

A(H2("5.4&nbsp;&nbsp; The decision-feedback equaliser"))
A(P("The decision-feedback equaliser is the one block that removes interference without "
    "amplifying noise at all. Having decided a symbol, the receiver knows exactly what that "
    "symbol will contribute to the next few, and subtracts it. Because the subtraction is "
    "driven by a clean two-level decision rather than by the noisy waveform, no noise rides "
    "along with it. Where the feed-forward filter of §5.3 pays a gap between coherent signal "
    "gain and incoherent noise gain, the feedback path pays nothing: the decision is "
    "noiseless by construction."))

A(P("This is why the classical optimum has the structure it does. Forney's decomposition of "
    "the maximum-likelihood receiver puts a <i>whitened matched filter</i> at the front, "
    "whose job is exactly the energy collection of §5.3, and follows it with a detector "
    "that resolves the remaining causal interference. The minimum-mean-squared-error "
    "decision-feedback equaliser is the practical descendant of that structure: a "
    "feed-forward section that gathers the pulse energy and leaves a minimum-phase response, "
    "and a feedback section that cancels the causal tail of that response for free. It "
    "outperforms the best purely linear equaliser on every channel with significant loss, "
    "and the margin between them grows with the loss. What stops it reaching the "
    "matched-filter bound in practice is not the mathematics but the next paragraph."))

A(P("The five taps used here are ["
    + ", ".join("%.3f" % t for t in R['dfe_taps']) + "], and they reduce the residual ISI "
    "to " + n('dfe_isi', '%.3f') + " of the cursor. Two caveats come with them. The first is "
    "<b>error propagation</b>: a wrong decision is subtracted with the wrong sign, which "
    "makes the next decision more likely to be wrong. With a tap as large as "
    + "%.2f" % max(abs(t) for t in R['dfe_taps']) + " that is not a remote possibility, and "
    "it is one reason forward error correction and decision feedback are usually specified "
    "together. The second is that the feedback path must settle within one unit interval — "
    "35.7 ps here — which puts the first tap on the critical timing path of the whole "
    "receiver and is why it is often unrolled into a speculative, parallel form."))

A(datatable([
    ["Block", "Removes", "Cannot remove", "Costs"],
    ["CTLE", "Broadband slope, cheaply",
     "Anything with structure — reflections, isolated echoes",
     "Cursor amplitude; it attenuates rather than amplifies"],
    ["Transmit FFE", "Pre-cursor and near post-cursor ISI, before crosstalk is added",
     "Anything it cannot see; it has no knowledge of the receiver's noise",
     "Transmit swing, through the peak-power constraint"],
    ["Receive FFE", "Pre-cursor ISI and long tails, with many taps available",
     "Nothing in principle, but each tap costs noise",
     "Noise enhancement — here " + n('rxffe_noise_enh_db', '%.2f') + " dB"],
    ["DFE", "Post-cursor ISI exactly, with no noise penalty",
     "Pre-cursor ISI, ever; it acts only on decided symbols",
     "Error propagation, and a hard timing path on the first tap"],
], [24 * mm, 44 * mm, 46 * mm, 44 * mm], S))
A(Spacer(1, 8))

# ------------------------------------------------------------------- §6 -----
A(H1("6&nbsp;&nbsp; The worked design, stage by stage"))

A(P("Putting the blocks in series and tracking the pulse response through them gives the "
    "table below. It is set out twice on purpose. The left-hand group is in millivolts at the "
    "receiver input, which is where a budget has to be written; the right-hand group "
    "normalises each stage to its own cursor, which is where the shape of the response is "
    "visible without the scaling getting in the way."))

A(datatable([
    ["Stage", "Cursor", "ISI (rms)", "Non-ISI noise",
     "ISI ÷ cursor", "Eye ÷ cursor"],
    [ST[0]['name'], sv(0, 'sig') + " mV", sv(0, 'isi_rms') + " mV",
     sv(0, 'noise') + " mV", snorm(0, 'isi_sum'), snorm(0, 'eye')],
    [ST[1]['name'], sv(1, 'sig') + " mV", sv(1, 'isi_rms') + " mV",
     sv(1, 'noise') + " mV", snorm(1, 'isi_sum'), snorm(1, 'eye')],
    [ST[2]['name'], sv(2, 'sig') + " mV", sv(2, 'isi_rms') + " mV",
     sv(2, 'noise') + " mV", snorm(2, 'isi_sum'), snorm(2, 'eye')],
    [ST[3]['name'], sv(3, 'sig') + " mV", sv(3, 'isi_rms') + " mV",
     sv(3, 'noise') + " mV", snorm(3, 'isi_sum'), snorm(3, 'eye')],
], [30 * mm, 22 * mm, 22 * mm, 26 * mm, 24 * mm, 24 * mm], S))
A(Spacer(1, 6))

A(H2("6.1&nbsp;&nbsp; Which blocks must shrink the cursor, and which need not"))
A(P("The absolute column falls sharply, and it is worth being precise about why, because the "
    "four blocks are not alike and two of them are shrinking the cursor for quite different "
    "reasons."))

A(datatable([
    ["Block", "Does it scale the cursor?", "Why"],
    ["CTLE", "Yes, and it must",
     "It is a passive-shaped analogue filter with a fixed headroom. Its high-frequency gain "
     "is about unity, so the only way it can present a rising response is to attenuate "
     "everything below. <b>But it attenuates the incoming noise and crosstalk by nearly the "
     "same factor</b> — here " + n('ctle_noise_gain_db', '%.1f') + " dB over the noise "
     "bandwidth — so most of the cursor reduction is not a loss of signal-to-noise ratio"],
    ["Transmit FFE", "Yes, and it must",
     "The transmitter has a hard peak-power limit, so Σ|c<sub>i</sub>| ≤ 1 and every unit of "
     "correction is subtracted from the main tap. <b>The noise it fights is added downstream "
     "and does not scale with it</b>, so this attenuation is a real signal-to-noise loss — "
     "the most expensive decibels in the chain"],
    ["Receive FFE", "No, not meaningfully",
     "Its gain is arbitrary because a variable-gain amplifier and the slicer threshold follow "
     "it and scale together. Only the ratio of its signal gain to its noise gain matters "
     "(§5.3), which is why it is fair to normalise its output to unity"],
    ["DFE", "No",
     "It subtracts rather than scales. The cursor passes through untouched and the noise is "
     "untouched too, because the thing being subtracted is a decision rather than a waveform"],
], [26 * mm, 32 * mm, 100 * mm], S))
A(Spacer(1, 6))

A(H2("6.2&nbsp;&nbsp; What actually falls monotonically"))
A(P("It is often said that equalisation works by making the interference shrink faster than "
    "the signal does. That is a statement about the cursor, and the cursor is not a "
    "well-defined quantity: it depends on where you put the gain, and slide the automatic "
    "gain control and you can make it whatever you like. The invariant statement is about "
    "ratios, and it is this:"))

A(CO(
    "<b>Every linear block in the chain trades signal-to-noise ratio for signal-to-ISI "
    "ratio.</b> Measured against the noise that is <i>not</i> correlated with the data — "
    "thermal noise in the front end, crosstalk from the neighbours, quantisation in the "
    "converter, jitter converted to amplitude through the slope — the signal falls "
    "monotonically through the chain, from " + sv(0, 'snr_n', '%.1f') + " dB at the channel "
    "output to " + sv(2, 'snr_n', '%.1f') + " dB after the transmit FFE, and no linear "
    "operation can ever reverse that. What is bought in exchange is the other ratio: signal "
    "to residual ISI climbs from " + sv(0, 'snr_i', '%.1f') + " dB to "
    + sv(3, 'snr_i', '%.1f') + " dB. The link works when the two together are good enough, "
    "and both matter only over the bandwidth the signal actually occupies."))
A(Spacer(1, 6))

A(fig("sd_stages.png", 145,
      "Figure 6 — The scale-invariant picture. Signal to non-ISI noise (red) can only fall; "
      "signal to residual ISI (green) is what the equalisers buy. The decision-feedback "
      "stage is the only one that improves the second without spending any of the first."))

A(P("The figure also shows why the division of labour of §5 is not merely tidy. The "
    "decision-feedback equaliser is the only block whose signal-to-noise line is flat: it "
    "improves the "
    "ISI ratio by "
    + "%.1f" % (ST[3]['snr_i'] - ST[2]['snr_i']) + " dB at no cost in signal-to-noise ratio "
    "whatsoever. Every other block pays. And the transmit FFE, judged on its own, looks like "
    "a poor bargain — it gives up "
    + "%.1f" % (ST[1]['snr_n'] - ST[2]['snr_n']) + " dB of signal-to-noise to buy only "
    + "%.1f" % (ST[2]['snr_i'] - ST[1]['snr_i']) + " dB of signal-to-ISI. Run the chain "
    "without it and the five feedback taps take Q only from 1.30 to 1.69, because what "
    "remains after the CTLE is dominated by pre-cursors that the feedback path cannot reach. "
    "The transmit FFE is not there to improve the eye by itself; it is there to clear the "
    "pre-cursors so that the block which <i>is</i> free can do its work. Together they take Q "
    "from 1.30 to " + n('Q', '%.2f') + "."))

A(fig("sd_taps.png", 152,
      "Figure 7 — The sampled pulse response at each stage. Note the vertical scales: the CTLE "
      "cuts the cursor to about a third while cutting the ISI sum by nearly five, which is "
      "why it is worth having. The final panel is normalised to its own cursor, with the "
      "five feedback positions shaded."))

A(fig("sd_eyes.png", 152,
      "Figure 8 — The same three stages as eye diagrams, built by driving four thousand random "
      "symbols through the modelled chain. The arrow marks the eye opening at the sampling "
      "instant in units of the cursor amplitude, so an ideal ISI-free eye would read 2.0 "
      "and the equalised eye at 1.11 is a little over half of that."))

# ------------------------------------------------------------------- §7 -----
A(H1("7&nbsp;&nbsp; The noise and jitter budget"))

A(P("An open eye is necessary but not sufficient. What decides the error rate is the ratio "
    "of the eye opening to everything that moves the received level around, and those "
    "contributions have to be referred to a common point. Referring them to the receiver "
    "input, where the cursor is " + n('signal_mv', '%.1f') + " mV out of a "
    + n('swing_mv', '%.0f') + " mV transmitted swing, gives the budget below."))

A(datatable([
    ["Contribution", "Value", "Where it comes from"],
    ["Receiver noise", n('sigma_rx_eff', '%.2f') + " mV rms",
     n('sigma_rx', '%.1f') + " mV of front-end noise, shaped by the CTLE, whose gain over the "
     "noise bandwidth is " + n('ctle_noise_gain_db', '%.1f') + " dB"],
    ["Crosstalk", n('sigma_xt_eff', '%.2f') + " mV rms",
     n('sigma_xt', '%.1f') + " mV of integrated crosstalk noise from neighbouring lanes, "
     "shaped by the same filter"],
    ["Jitter", n('sigma_jit', '%.2f') + " mV rms",
     n('rj_fs', '%.0f') + " fs rms of random jitter, converted to amplitude through the "
     "slope of the waveform at the sampling instant"],
    ["Residual ISI", n('sigma_isi', '%.2f') + " mV rms",
     "What the equalisers left behind, treated statistically rather than worst-case"],
    ["<b>Total</b>", "<b>" + n('sigma_tot', '%.2f') + " mV rms</b>",
     "Root-sum-square of the above"],
], [28 * mm, 26 * mm, 104 * mm], S))
A(Spacer(1, 6))

A(CO(
    "<b>A note on the letter Q, because it is badly overloaded.</b> The Q used here is the "
    "<i>Q-factor</i> of digital and optical communications, and it has nothing whatever to do "
    "with the quality factor of a resonator that appears in §5 of the companion report. It is "
    "named after the Gaussian tail function Q(x) = ∫<sub>x</sub><super>∞</super> φ(u) du, and "
    "it is defined as the separation of the two signal levels divided by the sum of their "
    "noise standard deviations, Q = (μ<sub>1</sub> − μ<sub>0</sub>)/(σ<sub>1</sub> + "
    "σ<sub>0</sub>), which for a symmetric binary signal is simply half the eye opening "
    "divided by the rms noise. The bit error rate follows as ½ erfc(Q/√2), so Q = 7.03 is "
    "10<super>−12</super> and Q = 6 is about 10<super>−9</super>. Optical work usually quotes "
    "it in decibels as 20 log Q, which invites a further confusion with electrical "
    "signal-to-noise ratio in power terms."))

A(P("The collision is worth naming because it genuinely bites anyone working across "
    "disciplines. In an atomic clock, for instance, the fractional frequency stability "
    "depends on the resonator Q <i>and</i> on the signal-to-noise ratio, and the two appear "
    "in the same expression — so an engineer who reads 'Q' in this report as the resonator "
    "quantity will get a sentence that is not merely wrong but wrong in a plausible-looking "
    "way. Where the ambiguity would matter, the safest course is to quote the error rate "
    "directly, or to use the IEEE 802.3 <b>channel operating margin</b>, which expresses the "
    "same judgement as a single number in decibels and is defined in the standard rather than "
    "by convention. This report keeps Q because it is what every SerDes datasheet and every "
    "optical link budget uses, but it means the communications Q-factor throughout and never "
    "the resonator one."))
A(Spacer(1, 6))

A(P("The cursor is " + n('signal_mv', '%.1f') + " mV and the total noise "
    + n('sigma_tot', '%.2f') + " mV rms, so the Q-factor is Q = " + n('Q', '%.2f')
    + ". That corresponds to a bit error rate of about 10<super>"
    + n('ber_exp', '%.0f') + "</super>. The conventional target for an uncorrected link is "
    "10<super>−12</super>, which needs Q = 7.03, so this link is <b>"
    + n('margin_db', '%.2f').lstrip('-') + " dB short</b>."))

A(fig("sd_budget.png", 152,
      "Figure 9 — Where the noise comes from, and what the resulting Q buys. Crosstalk dominates; "
      "residual ISI is close behind it, and receiver noise third."))

A(CO(
    "<b>Read the budget before choosing a fix.</b> The largest single contribution is "
    "crosstalk at " + n('sigma_xt_eff', '%.2f') + " mV, with residual ISI second at "
    + n('sigma_isi', '%.2f') + " mV and receiver noise third. That ordering matters, because "
    "it says the link is short of margin mostly because of its neighbours and only partly "
    "because of what the equalisers left behind. Removing every last scrap of residual ISI "
    "would take the total from " + n('sigma_tot', '%.2f') + " mV down to about 1.8 mV, worth "
    "roughly four tenths of a decibel — nothing like the shortfall. §8 checks that arithmetic "
    "against the alternatives."))
A(Spacer(1, 8))

# ------------------------------------------------------------------- §8 -----
A(H1("8&nbsp;&nbsp; It does not close: what would actually fix it"))

A(P("Seven candidate remedies, each re-run through the whole chain from the channel model "
    "outwards, so that the margin figures below are computed rather than estimated."))

A(datatable(
    [["What you change", "Loss at Nyquist", "Q", "Margin to 10<super>−12</super>"]] +
    [[c['name'], "%.1f dB" % c['il'], "%.2f" % c['Q'],
      "%+.2f dB" % c['margin']] for c in RM['nrz']],
    [66 * mm, 26 * mm, 18 * mm, 32 * mm], S))
A(Spacer(1, 6))

A(P("The table divides cleanly, and the division is the point. Everything that changes the "
    "<i>board</i> is worth between one and a half and two and a half decibels. A lower-loss "
    "laminate lifts the cursor by reducing the slope the equalisers have to undo; five inches "
    "off the backplane does much the same and is often cheaper if the mechanical design still "
    "has any freedom in it; halving the crosstalk attacks the largest single term in the "
    "budget directly. Any one of the three closes the link on its own."))

A(P("Everything that changes the <i>silicon</i> is worth a fraction of that. Doubling the "
    "decision-feedback taps from five to ten buys "
    + "%.2f" % (RM['nrz'][4]['margin'] - RM['nrz'][0]['margin']) + " dB. Adding a nine-tap "
    "receive feed-forward equaliser — the block that defines a modern ADC-DSP receiver, and "
    "the obvious thing to reach for — buys "
    + "%.2f" % (RM['nrz'][5]['margin'] - RM['nrz'][0]['margin']) + " dB, and still leaves the "
    "link short of target. Neither is useless, and on a channel dominated by intersymbol "
    "interference rather than by crosstalk both would look very different. But on "
    "<i>this</i> channel the budget said the problem was the neighbours, and the budget was "
    "right."))

A(CO(
    "<b>The general lesson.</b> The block that fixed the last problem is rarely the block "
    "that fixes the next one. A link short of margin is short for a reason, the budget names "
    "the reason, and the instinct to reach for more equalisation is the instinct to solve the "
    "problem you solved last time. Build the budget first: it costs an afternoon, and it "
    "tells you which of seven candidate fixes are worth the meeting."))
A(Spacer(1, 8))

# ------------------------------------------------------------------- §9 -----
A(H1("9&nbsp;&nbsp; The same channel at 56 Gb/s: PAM4 is not free"))

A(P("The obvious way to double throughput without doubling the Nyquist frequency is to send "
    "two bits per symbol. PAM4 does exactly that, with four amplitude levels instead of two, "
    "at the same 28 GBd and therefore across the same 14 GHz of channel. The channel does "
    "not get any worse. The signalling does."))

A(P("Four levels spread across the same peak-to-peak swing leave three eyes, each one third "
    "the height of the single NRZ eye. That is a loss of 20 log 3 = "
    + n('pam4_penalty_db', '%.1f') + " dB of signal-to-noise ratio before anything else is "
    "considered, and it is not recoverable by equalisation because it is a property of the "
    "constellation rather than of the channel. On this channel the Q of "
    + n('Q', '%.2f') + " becomes " + n('pam4_Q', '%.2f') + ", and the raw error rate rises "
    "from 10<super>" + n('ber_exp', '%.0f') + "</super> to about 10<super>"
    + n('pam4_ber_exp', '%.1f') + "</super>."))

A(fig("sd_pam4.png", 140,
      "Figure 10 — The same swing, divided two ways. Three eyes of one third the height cost "
      + n('pam4_penalty_db', '%.1f') + " dB before the channel is even considered."))

A(P("An error rate of one in thirty is not a link, which is why PAM4 generations made "
    "forward error correction mandatory rather than optional. The Reed–Solomon KP4 code, "
    "RS(544,514) over GF(2<super>10</super>), takes a pre-correction error rate of about "
    + "%.1e" % R['kp4_threshold'] + " down below 10<super>−15</super>, and PAM4 links are "
    "budgeted to that threshold instead of to 10<super>−12</super>. Even so, this channel "
    "does not reach it: the required Q is " + n('pam4_Q_needed', '%.2f') + " and the "
    "available Q is " + n('pam4_Q', '%.2f') + ", a shortfall of "
    + n('pam4_snr_short_db', '%.1f') + " dB."))

A(datatable(
    [["Channel change", "Loss at Nyquist", "Q", "Margin to the KP4 threshold"]] +
    [[c['name'], "%.1f dB" % c['il'], "%.2f" % c['Q'],
      "%+.2f dB" % c['margin']] for c in RM['pam4']],
    [66 * mm, 26 * mm, 18 * mm, 32 * mm], S))
A(Spacer(1, 6))

A(P("The lesson is the one the industry learned between 2015 and 2020. PAM4 does not let you "
    "run twice the data over the channel you already have; it lets you run twice the data "
    "over a channel roughly "
    + "%.0f" % abs(RM['pam4'][2]['il'] - RM['nrz'][0]['il']) + " dB better than the one you "
    "already have, in exchange for a coding layer, a larger latency budget and a "
    "considerably more complicated receiver."))

# ------------------------------------------------------------------ §10 -----
A(H1("10&nbsp;&nbsp; Adaptation and training"))

A(P("Nothing in §5 can be set from a datasheet. Manufacturing spread, temperature, the "
    "particular board and the particular connector all move the channel, so every tap in a "
    "modern link is adapted. The mechanism is the least-mean-squares algorithm of the "
    "companion report on digital filters, usually in its sign-sign form: take the sign of "
    "the error between the sampled level and the decided level, take the sign of the data in "
    "the relevant tap position, multiply, and accumulate. That requires no multiplier and no "
    "knowledge of the channel, and it converges to the same minimum of the same quadratic "
    "bowl that the Wiener–Hopf equations describe."))

A(P("Receive-side taps can be adapted continuously because the receiver has the error signal "
    "in hand. Transmit-side taps cannot, because the transmitter does not know what the "
    "receiver saw, so the standards define a <b>link training</b> phase: before data flows, "
    "the two ends exchange a control channel over which the receiver requests increment, "
    "decrement or hold on each transmit tap, and the transmitter reports what it did. "
    "10GBASE-KR introduced this and every backplane standard since has kept it. Training "
    "typically takes a few milliseconds and is re-run on every link-up."))

A(CO(
    "<b>Adaptation interacts with the clock.</b> The clock and data recovery loop chooses the "
    "sampling phase, and the equaliser adapts to whatever phase it is given, while the phase "
    "detector sees a waveform shaped by whatever the equaliser is currently doing. The two "
    "loops can and do fight, and a link that trains to a stable but poor setting — the "
    "wrong lock point, an eye centred half a unit interval away from the best one — is a "
    "common and deeply unpleasant failure. Bandwidth separation between the loops is the "
    "usual defence."))
A(Spacer(1, 8))

# ------------------------------------------------------------------ §11 -----
A(H1("11&nbsp;&nbsp; Where this is going"))

A(P("The 224 Gb/s per lane generation now in standardisation keeps PAM4 and doubles the "
    "symbol rate again, to around 112 GBd, which puts Nyquist at 56 GHz. Copper at that "
    "frequency is unforgiving, and the practical consequence is that the reach of an "
    "electrical channel keeps shrinking: a backplane of the kind modelled here is already "
    "out of the question, and even the few inches from a switch die to a front-panel cage "
    "have become a design problem rather than a piece of routing."))

A(H2("11.1&nbsp;&nbsp; Better receivers, stronger codes, shorter copper"))
A(P("Three responses are visible. The first is more sophisticated receivers: "
    "maximum-likelihood sequence estimation, which instead of equalising the channel and "
    "then slicing, searches for the most likely transmitted sequence given the known channel "
    "response, and which is worth a few dB over a decision-feedback equaliser at the cost of "
    "considerable digital power. The second is stronger coding, with concatenated and "
    "soft-decision schemes replacing the hard-decision Reed–Solomon codes that have served "
    "since 2017. The third, and the most consequential, is to stop sending electrical "
    "signals so far: co-packaged optics move the electrical-to-optical conversion into the "
    "switch package, and linear-drive pluggable optics remove the retimer from the module "
    "so that the host SerDes drives the optical engine directly. Both change the problem "
    "from equalising twenty inches of copper to equalising two."))

A(H2("11.2&nbsp;&nbsp; Chiplets: the limit case of shortening the copper"))
A(P("Take that third response to its conclusion and you arrive at the chiplet. If the "
    "expensive part of a link is the channel, the cheapest possible channel is a couple of "
    "millimetres of wiring on a silicon interposer or an embedded bridge, with bumps on a "
    "pitch measured in tens of micrometres. At that reach the loss is negligible across the "
    "whole band of interest, and something interesting happens to the design: you stop "
    "needing the apparatus this report is about. No continuous-time equaliser, no "
    "decision-feedback taps, no clock recovery loop per lane — a forwarded clock will do, "
    "because the lanes are short enough and matched enough that the skew between them is a "
    "few picoseconds. Often the signalling is not even differential, because there is no "
    "common-mode environment to reject."))

A(P("What you buy with the power you no longer spend on equalisation is <i>width</i>. A "
    "long-reach SerDes at 112 Gb/s costs several picojoules for every bit it moves; a "
    "die-to-die link over an advanced package costs a fraction of one. Spend the same power "
    "budget at a fortieth of the energy per bit and you can afford hundreds or thousands of "
    "lanes instead of dozens, which is why the figure of merit changes too. Nobody quotes "
    "gigabits per lane for a chiplet interface; they quote <b>bandwidth density</b>, "
    "terabits per second per millimetre of die edge, because the edge is the scarce "
    "resource. The whole design problem inverts, from 'how do I recover a signal that has "
    "crossed thirty inches' to 'how many wires can I fit along this shoreline and how little "
    "energy can I move a bit with'."))

A(datatable([
    ["", "Advanced package", "Standard package", "Board SerDes, for comparison"],
    ["Medium", "Silicon interposer, bridge or fine-pitch fanout",
     "Organic substrate", "Laminate, connectors, sometimes a backplane"],
    ["Bump or ball pitch", "Tens of micrometres", "Around 100 micrometres",
     "Hundreds of micrometres at the package ball"],
    ["Reach", "A couple of millimetres", "Up to a few tens of millimetres",
     "Inches to tens of inches"],
    ["Signalling", "Single-ended, forwarded clock, little or no equalisation",
     "Single-ended, some equalisation", "Differential, full equaliser chain, CDR per lane"],
    ["What is scarce", "Die edge and bump count", "Substrate routing",
     "Channel loss budget"],
], [30 * mm, 36 * mm, 32 * mm, 50 * mm], S))
A(Spacer(1, 6))

A(P("UCIe is the standardisation of this, with a specification covering both package classes "
    "so that dies from different vendors can in principle be assembled into one part, and "
    "the Open Compute Project's Bunch of Wires takes a similar line. The proprietary "
    "equivalents came first and are widely deployed: the on-package fabric linking the "
    "compute and I/O dies in AMD's processors, the die-to-die links between Intel's tiles, "
    "and the interconnects joining accelerator dies in the largest training parts. The "
    "motivation is not mainly signalling — it is that a reticle has a maximum size, that "
    "yield falls sharply with die area, and that analogue and I/O circuits do not benefit "
    "from a leading-edge process the way logic does, so building one enormous chip is both "
    "risky and wasteful. The signalling advantage is a consequence of the packaging decision "
    "rather than the reason for it, but it is a large consequence."))

A(CO(
    "<b>Where this leaves the equaliser.</b> Chiplets do not abolish the problem, they "
    "relocate it. Every bit that now crosses two millimetres of interposer still has to leave "
    "the package eventually, and the link that takes it out is a harder one than before, "
    "because the package is now denser and hotter and the rate has risen. The effect of "
    "chiplets on this report's subject is to concentrate the difficulty: fewer, faster, more "
    "aggressively equalised external links, surrounded by a great many nearly-free internal "
    "ones."))
A(Spacer(1, 6))

A(H2("11.3&nbsp;&nbsp; Memory: the last parallel bus"))
A(P("The interface between a processor and its main memory is the one place where the wide, "
    "single-ended, common-clock parallel bus of §2.3 never went away. DDR5 runs a "
    "sixty-four-bit data path, plus check bits, at several thousand megatransfers per second, "
    "and it is subject to every difficulty that killed the parallel bus everywhere else: skew "
    "between bits, stubs wherever more than one module hangs off a channel, and a pin count "
    "that has become one of the dominant constraints on processor packaging. A server "
    "processor with a dozen memory channels spends well over a thousand pins on memory alone, "
    "and those pins compete for the same package edge as everything else."))

A(P("It has survived by importing the serial world's toolkit rather than by avoiding the "
    "problem. Modern DRAM interfaces train per-bit timing and reference levels at "
    "initialisation, and DDR5 specifies a decision-feedback equaliser on the DRAM's data "
    "receivers — the same block as §5.4, in the least likely place. The rate still rises, but "
    "the number of modules a channel can carry falls as it does, which is the capacity-versus-"
    "bandwidth bind that memory system designers have been complaining about for a decade."))

A(P("Two escapes are being taken, and they are opposite in direction. The first is to "
    "<b>serialise</b>. A buffer chip on the module accepts a small number of high-rate serial "
    "lanes from the processor and drives conventional DRAM behind it, which collapses the pin "
    "count and removes the multi-drop stub problem at a stroke. IBM's Open Memory Interface "
    "has done exactly this in shipping POWER systems for several years, reaching hundreds of "
    "gigabytes per second per socket over a handful of lanes. More visibly, CXL-attached "
    "memory puts DRAM behind what is electrically a PCI Express link, which additionally "
    "allows capacity to be pooled across hosts and media of different kinds to be mixed "
    "behind one interface."))

A(CO(
    "<b>The precedent worth remembering, and the reason it matters here.</b> This has been "
    "tried before. Fully Buffered DIMMs put an advanced memory buffer on every module in the "
    "mid-2000s and were abandoned over power and, above all, <i>latency</i> — every hop "
    "through a buffer costs time that a processor stalled on a load cannot hide. That is the "
    "whole difficulty with serialising memory, and it is why CXL memory is deployed as a "
    "capacity tier rather than as a replacement for the direct channels: the round trip is "
    "roughly double a native DDR access. It also puts this report's subject somewhere "
    "uncomfortable. A memory link is a serial channel with all the impairments described "
    "here, but unlike a network link it is on the critical path of a stalled processor, so "
    "every nanosecond of forward error correction, every retimer hop and every retry is "
    "paid for directly in application performance. Equalisation choices that are free in a "
    "switch are not free here."))
A(Spacer(1, 6))

A(P("The second escape is the opposite of serialising: go <b>wider and shorter</b>, and put "
    "the memory in the package. High-bandwidth memory stacks DRAM dies and connects them "
    "over a thousand-odd wires running at single-digit gigabits each, across a couple of "
    "millimetres of interposer — which is to say, it is the chiplet answer of §11.2 applied "
    "to memory. It reaches bandwidths no pin-limited external interface can approach, and it "
    "pays for that in capacity, cost and the impossibility of upgrading it after manufacture. "
    "The likely settlement is that memory stops being one thing: a near tier in the package, "
    "wide and parallel and fast; a far tier behind a serial link, large and pooled and slower; "
    "and conventional modules squeezed between them. Both tiers are answers to the same "
    "question this report has been asking throughout — when the channel becomes the "
    "constraint, you either equalise harder or you change the channel — and memory is simply "
    "the last part of the machine to be asked it."))

A(H2("11.4&nbsp;&nbsp; CXL: when the physical layer lands on the critical path"))
A(P("The memory tier of §11.3 is one use of a broader thing, and it is worth separating the "
    "two because the broader thing changes what a physical layer is allowed to cost. Compute "
    "Express Link is not a new electrical interface at all — it runs on the PCI Express "
    "physical layer and reuses its link training, with the two ends negotiating into CXL mode "
    "during the same training sequence that would otherwise bring up an ordinary PCIe link. "
    "Everything in §2.1 about presets, retimers and channel budgets therefore applies to it "
    "unchanged. What is new is above the physical layer: three protocols multiplexed onto the "
    "one link, and a coherence model that lets a device and a host share memory rather than "
    "copy it."))

A(datatable([
    ["Sub-protocol", "What it carries", "Why it exists"],
    ["CXL.io", "Discovery, configuration, interrupts, bulk transfer",
     "Essentially PCI Express. Every CXL link has it, and a device falls back to it if "
     "CXL mode is not negotiated"],
    ["CXL.cache", "A device coherently caching the host's memory",
     "Lets an accelerator or a network adapter work on host data without an explicit copy "
     "and without software-managed coherence"],
    ["CXL.mem", "The host reading and writing memory attached to the device",
     "Lets memory live behind the link and still be addressed as memory — this is the "
     "capacity tier of §11.3"],
], [26 * mm, 52 * mm, 80 * mm], S))
A(Spacer(1, 6))

A(P("Devices are classified by which of the three they use. A type 1 device has a coherent "
    "cache but no memory of its own, which suits a smart network adapter. A type 2 device has "
    "both, which is the shape of an accelerator that wants the host to reach into its memory "
    "and vice versa. A type 3 device is a memory expander and uses CXL.mem alone. Successive "
    "revisions widened the topology around them: the second added switching and the pooling "
    "of memory across several hosts, and the third added multi-level fabrics, peer-to-peer "
    "traffic between devices and genuine sharing of a memory region between hosts with "
    "hardware coherence. The destination is a rack in which processors, memory and "
    "accelerators are separately provisioned rather than bolted together in fixed ratios at "
    "the time the server is built."))

A(CO(
    "<b>Why this belongs in a report about equalisation.</b> Because it moves a serial link "
    "onto the critical path of a load instruction, and in doing so it changes the currency "
    "the physical layer is paid in. A switch tolerates the hundred nanoseconds that a strong "
    "forward error correction code costs, because the packet is going to spend microseconds "
    "in the network anyway. A processor stalled on a cache miss cannot hide any of it. That "
    "single fact propagates all the way down: it is why PCI Express 6.0 pairs a deliberately "
    "weak FEC with a cyclic redundancy check and link-level retry rather than adopting the "
    "Reed–Solomon code Ethernet uses, why the flit framing exists at all, why the "
    "latency-optimised variant splits its check so the first part of a flit can be forwarded "
    "before the whole of it has been verified, and why the number of retimer hops permitted "
    "in a CXL topology is constrained in a way that a network path's is not."))
A(Spacer(1, 6))

A(P("It also puts the PAM4 decision in an uncomfortable light. The third revision moves to "
    "the 64 GT/s physical layer, which means four-level signalling, which means the 9.5 dB "
    "penalty of §9 — landing on a link where the usual way of buying that margin back is "
    "forbidden. You cannot spend latency here. The margin has to come from a shorter channel, "
    "a better board, fewer connectors or a lower-noise receiver: which is to say, from "
    "precisely the table in §8, read with one column deleted. Of all the links discussed in "
    "this report, a coherent memory link is the one where the budget has the least room to "
    "manoeuvre, and it is the one the industry is nonetheless pushing hardest."))

A(H2("11.5&nbsp;&nbsp; What does not change"))
A(P("For all of that, the structure of the problem has not changed since 10GBASE-KR. There "
    "is a channel you cannot alter, a pulse response that describes it completely, a set of "
    "filters whose taps are the solution of a quadratic minimisation, and a budget that "
    "decides whether the result works. Everything in this report transfers; only the "
    "numbers move."))

# ------------------------------------------------------------------ §12 -----
A(H1("12&nbsp;&nbsp; Cheat sheet"))

A(datatable([
    ["Quantity", "This channel", "What it tells you"],
    ["Insertion loss at Nyquist", n('il_nyq_bd', '%.1f') + " dB",
     "The headline difficulty. Above about −30 dB, NRZ needs everything in §5"],
    ["Cursor, unequalised", n('raw_cursor', '%.3f'),
     "Fraction of the transmitted amplitude arriving on time"],
    ["Worst-case eye, unequalised", n('raw_eye', '%.2f'),
     "Negative means some data patterns invert the decision"],
    ["Noise enhancement of the receive FFE", n('noise_enh_db', '%.2f') + " dB",
     "The price of each linear tap; compare with a DFE tap, which is free"],
    ["Cursor at the slicer", n('signal_mv', '%.1f') + " mV",
     "Out of " + n('swing_mv', '%.0f') + " mV launched"],
    ["Total noise", n('sigma_tot', '%.2f') + " mV rms",
     "Dominated by crosstalk, not by residual ISI"],
    ["Q and margin", n('Q', '%.2f') + ", " + n('margin_db', '%+.2f') + " dB",
     "Short of 10<super>−12</super>; see §8 for what recovers it"],
    ["PAM4 penalty", n('pam4_penalty_db', '%.1f') + " dB",
     "Structural, not recoverable by equalisation"],
], [48 * mm, 30 * mm, 80 * mm], S))
A(Spacer(1, 7))

A(CO(
    "<b>Working order for a new channel.</b> First, get the S-parameters and check them: "
    "passive, causal, reciprocal, correctly de-embedded, and with the mixed-mode port map "
    "the right way round. Second, look for structural damage — a via stub notch near "
    "Nyquist, a connector resonance, an unterminated branch — because no equaliser fixes a "
    "notch. Third, compute the pulse response and read the cursor and the first few "
    "pre- and post-cursors; that tells you which blocks you need before you design any of "
    "them. Fourth, build the budget and find out what actually dominates. Only then choose "
    "the equalisation, and re-check the budget afterwards, because the equaliser you added "
    "changed the noise as well as the signal."))
A(Spacer(1, 9))

# -------------------------------------------------------------- glossary ----
A(H1("Glossary"))
for term, defn in [
    ("AUI family", "Attachment unit interfaces — XAUI, XLAUI, CAUI and successors. "
     "Chip-to-chip or chip-to-module interfaces carrying an Ethernet MAC's internal bus "
     "across a board, not physical layers over a medium."),
    ("Redriver and retimer", "A redriver is an analogue amplifier and equaliser with no clock "
     "recovery — it improves a channel. A retimer fully recovers clock and data and "
     "retransmits, replacing one channel with two shorter ones at the cost of latency and "
     "power."),
    ("GT/s", "Gigatransfers per second: the raw signalling rate before coding overhead, used "
     "by PCI Express. PCIe 3.0 at 8 GT/s with 128b/130b delivers about 7.88 Gb/s of payload "
     "per lane."),
    ("CEI", "Common Electrical I/O: the OIF's protocol-agnostic electrical interface "
     "agreements — CEI-28G, CEI-56G, CEI-112G — subdivided by reach into XSR, VSR, MR and "
     "LR. Reused by Ethernet, Fibre Channel, InfiniBand and optical transport alike."),
    ("CXL", "Compute Express Link: a coherence and memory protocol carried on the PCI "
     "Express physical layer, negotiated during PCIe link training. CXL.io, CXL.cache and "
     "CXL.mem are multiplexed on one link; type 1, 2 and 3 devices use different "
     "combinations of them."),
    ("COM", "Channel operating margin: the statistical figure of merit IEEE 802.3 uses to "
     "decide whether a channel is compliant, computed from the S-parameters and a reference "
     "receiver."),
    ("CTLE", "Continuous-time linear equaliser. An analogue filter with rising gain, which "
     "flattens the channel by attenuating low frequencies."),
    ("Cursor", "The sample of the pulse response at the chosen sampling phase — the part of "
     "a symbol that arrives when it should. Everything else is ISI."),
    ("DFE", "Decision-feedback equaliser. Subtracts the known contribution of already-decided "
     "symbols, so it removes post-cursor ISI without amplifying noise."),
    ("FFE", "Feed-forward equaliser. A symbol-rate FIR filter, in the transmitter (limited by "
     "peak power) or the receiver (limited by noise enhancement)."),
    ("ICN", "Integrated crosstalk noise: near- and far-end crosstalk aggregated into a single "
     "rms voltage for the budget."),
    ("ISI", "Intersymbol interference. Energy from one symbol landing on another, caused by "
     "frequency-dependent loss and by reflections."),
    ("IEEE 802.3 names", "Rate, then BASE for baseband, then a medium letter (T twisted "
     "pair, K backplane, C twinax, S/L/E fibre), then a coding letter (X for 8b/10b, R for "
     "64b/66b), then a lane count. So 100GBASE-KR4 is 100 Gb/s over a backplane, 64b/66b "
     "coded, on four lanes."),
    ("KP4", "The RS(544,514) Reed–Solomon code, named after the 100GBASE-KP4 physical layer "
     "it was first specified for and now used far beyond it. Takes a pre-correction error "
     "rate of roughly 2×10<super>−4</super> below 10<super>−15</super>."),
    ("MLSE", "Maximum-likelihood sequence estimation. Searches for the most likely "
     "transmitted sequence rather than slicing symbol by symbol."),
    ("OIF", "Optical Internetworking Forum, publisher of the CEI implementation agreements. "
     "An industry forum rather than a standards body in the IEEE sense."),
    ("PAM4", "Four-level pulse amplitude modulation: two bits per symbol, three eyes, and a "
     "9.5 dB signal-to-noise penalty relative to NRZ at the same swing."),
    ("Pulse response", "The waveform produced by a single symbol. Sampled on the UI grid it "
     "gives the cursor and the ISI taps, which is everything an equaliser design needs."),
    ("Q-factor", "The communications Q, named after the Gaussian tail function and defined "
     "as (μ<sub>1</sub> − μ<sub>0</sub>)/(σ<sub>1</sub> + σ<sub>0</sub>) — half the eye "
     "opening over the rms noise for a symmetric binary signal. BER = ½ erfc(Q/√2), so "
     "Q = 7.03 gives 10<super>−12</super>. Unrelated to the resonator quality factor."),
    ("Matched-filter bound", "SNR = 2E/N<sub>0</sub>, the most any receiver can extract from "
     "a pulse of energy E. A linear equaliser approaches it by combining pulse-response "
     "samples coherently and falls short of it by the noise enhancement."),
    ("Noise enhancement", "The gap between a linear equaliser's coherent signal gain and its "
     "incoherent noise gain — the <i>net</i> penalty, not the raw tap norm."),
    ("Df, loss tangent", "The dielectric dissipation factor. Sets the slope of the channel "
     "directly: α<sub>d</sub> ≈ 2.3 f √Dk · Df dB per inch, with f in GHz."),
    ("Dk, dielectric constant", "Relative permittivity. Sets propagation delay, characteristic "
     "impedance and, through the glass-resin difference, fibre-weave skew."),
    ("Via stub", "The unused remainder of a plated through-hole. A quarter-wave resonator "
     "that puts a deep notch in the channel, removed by back-drilling."),
]:
    A(Paragraph("<b>%s.</b> %s" % (term, defn), S["gloss"]))

A(Spacer(1, 8))
A(H1("References"))
for i, r in enumerate([
    "Bogatin, <i>Signal and Power Integrity — Simplified</i>, 3rd ed., Prentice Hall, 2018.",
    "Hall and Heck, <i>Advanced Signal Integrity for High-Speed Digital Designs</i>, "
    "Wiley, 2009.",
    "Proakis and Salehi, <i>Digital Communications</i>, 5th ed., McGraw-Hill, 2007 — "
    "the MMSE decision-feedback equaliser and its analysis.",
    "IEEE Std 802.3-2022, Clause 93 (100GBASE-KR4) and the 100G-per-lane clauses added "
    "by 802.3ck — link training and the channel operating margin method.",
    "OIF CEI-56G and CEI-112G Implementation Agreements.",
    "CXL Consortium, <i>Compute Express Link Specification</i>, revisions 1.1 through 3.1 — "
    "protocol negotiation on the PCIe physical layer, flit framing and the latency budget.",
    "UCIe Consortium, <i>Universal Chiplet Interconnect Express Specification</i> — the "
    "advanced and standard package classes and their bandwidth-density targets.",
    "Gustavsen and Semlyen, 'Rational approximation of frequency domain responses by vector "
    "fitting', IEEE Trans. Power Delivery, 1999 — turning measured S-parameters into a "
    "simulatable model.",
    "Grivet-Talocia and Gustavsen, <i>Passive Macromodeling</i>, Wiley, 2016.",
    "Haykin, <i>Adaptive Filter Theory</i>, 5th ed., Pearson, 2013 — LMS and its sign-sign "
    "variants.",
    "Forney, 'Maximum-likelihood sequence estimation of digital sequences in the presence "
    "of intersymbol interference', IEEE Trans. Information Theory, 1972 — the whitened "
    "matched filter and why the MMSE-DFE has the structure it does.",
    "PCI-SIG, <i>PCI Express Base Specification</i>, revisions 3.0 (2010) through 6.0 "
    "(2022) — transmitter presets, the link equalisation procedure, and FLIT-mode FEC.",
    "Laminate parameters from the manufacturers' datasheets: Isola (FR408HR, I-Speed, "
    "Tachyon 100G), Panasonic (Megtron 6 and 7), Rogers (RO4350B). Dk and Df vary with "
    "frequency, resin content and glass style; treat quoted figures as class indicators.",
], 1):
    A(Paragraph("[%d]&nbsp; %s" % (i, r), S["ref"]))

# ------------------------------------------------------------------ build ---
OUT = "/home/brendan/Downloads/Equalisation in High-Speed Serial Links.pdf"
doc = BaseDocTemplate(OUT, pagesize=A4,
                      leftMargin=26 * mm, rightMargin=26 * mm,
                      topMargin=20 * mm, bottomMargin=22 * mm,
                      title="Equalisation in High-Speed Serial Links",
                      author="Brendan Lynskey")
frame = Frame(doc.leftMargin, doc.bottomMargin, CW,
              A4[1] - doc.topMargin - doc.bottomMargin, id="body")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                   onPage=page_furniture("SerDes Equalisation"))])
doc.build(story)
print("wrote", OUT)
