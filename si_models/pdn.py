"""Power integrity as a signal-integrity problem -- the model behind deck 07.

This deck does not try to design a power delivery network. It asks a narrower
question: by what route does a disturbance on the supply end up as an error at
the receiver, and how much of the link's budget does it consume?

The route has three stages, and each is computed here. A current step drawn by
the switching logic meets the network's impedance and becomes a voltage
ripple; the ripple reaches the transmitter and the phase-locked loop, which are
not perfectly immune to it, and becomes jitter and amplitude modulation; and
that jitter lands in the same budget as everything else.

The impedance stage is where the interesting behaviour is. A decoupling
capacitor is an inductor above its series resonance, so every capacitor helps
over a band and hurts above it, and two capacitors of different value put an
anti-resonant peak between them where the inductive branch of one meets the
capacitive branch of the other. Adding capacitors can therefore make the
network worse at the frequency that matters, which is the result most worth
computing rather than asserting.
"""

import numpy as np

MU0 = 4.0e-7 * np.pi


# Representative small capacitor data: capacitance, equivalent series
# resistance and equivalent series inductance of the part itself. Mounting
# inductance is added separately because it belongs to the board, not the part,
# and usually dominates.
CAP_LIBRARY = {
    '100 uF bulk (tantalum)': dict(c=100e-6, esr=0.050, esl=2.5e-9),
    '10 uF 0805':             dict(c=10e-6,  esr=0.010, esl=1.0e-9),
    '1 uF 0603':              dict(c=1e-6,   esr=0.015, esl=0.7e-9),
    '100 nF 0402':            dict(c=100e-9, esr=0.025, esl=0.4e-9),
    '10 nF 0402':             dict(c=10e-9,  esr=0.040, esl=0.4e-9),
    '1 nF 0201':              dict(c=1e-9,   esr=0.070, esl=0.25e-9),
}


def mounting_inductance(via_len_mm=0.8, pad_span_mm=1.6, n_via_pairs=1):
    """Inductance of the loop from a capacitor's pads down to the planes.

    The capacitor's own series inductance is a property of the part; this is a
    property of the layout, and above a few hundred megahertz it is almost
    always the larger of the two. Doubling the number of via pairs halves it,
    which is usually cheaper than buying a better capacitor.
    """
    l = MU0 / (2 * np.pi) * (2 * via_len_mm * 1e-3) * np.log(pad_span_mm / 0.15)
    return float(l / max(n_via_pairs, 1))


def cap_impedance(f, c, esr, esl, l_mount=0.0, n=1):
    """Impedance of n identical capacitors in parallel."""
    w = 2 * np.pi * np.asarray(f, float)
    z = esr + 1j * (w * (esl + l_mount) - 1.0 / (w * c))
    return z / max(n, 1)


def series_resonance(c, esl, l_mount=0.0):
    return float(1.0 / (2 * np.pi * np.sqrt(c * (esl + l_mount))))


def pdn_impedance(f=None, tiers=None, vrm_r=0.002, vrm_l=500e-9,
                  plane_c=20e-9, plane_r=0.001, die_c=200e-9, die_r=0.020,
                  die_l=8e-12):
    """Impedance of a decoupling ladder from the regulator to the die.

    Every branch is put in parallel: the regulator with its output inductance,
    each tier of discrete capacitors with its mounting inductance, the plane
    capacitance, and the on-die capacitance behind the package inductance.
    """
    if f is None:
        f = np.logspace(3, 10, 1400)
    f = np.asarray(f, float)
    w = 2 * np.pi * f
    if tiers is None:
        tiers = [('100 uF bulk (tantalum)', 4, 1.2e-9),
                 ('10 uF 0805', 10, 0.9e-9),
                 ('100 nF 0402', 40, 0.6e-9),
                 ('10 nF 0402', 20, 0.5e-9)]

    y = 1.0 / (vrm_r + 1j * w * vrm_l)
    parts = {}
    for name, count, lm in tiers:
        p = CAP_LIBRARY[name]
        z = cap_impedance(f, p['c'], p['esr'], p['esl'], lm, count)
        parts[name] = np.abs(z)
        y = y + 1.0 / z
    z_plane = plane_r + 1.0 / (1j * w * plane_c)
    y = y + 1.0 / z_plane
    z_die = die_r + 1j * w * die_l + 1.0 / (1j * w * die_c)
    y = y + 1.0 / z_die
    z = 1.0 / y
    return dict(f=f, z=np.abs(z), parts=parts,
                z_plane=np.abs(z_plane), z_die=np.abs(z_die))


def antiresonances(f, z, f_lo=1e4, f_hi=5e9):
    """Locate the peaks where two adjacent branches fight each other."""
    m = (f >= f_lo) & (f <= f_hi)
    fz, zz = f[m], z[m]
    peaks = []
    for i in range(1, len(zz) - 1):
        if zz[i] > zz[i - 1] and zz[i] >= zz[i + 1]:
            peaks.append(dict(f_hz=float(fz[i]), z_ohm=float(zz[i])))
    peaks.sort(key=lambda d: -d['z_ohm'])
    return peaks[:8]


def target_impedance(v_rail=0.9, ripple_pct=5.0, i_transient=20.0):
    """The usual target-impedance rule, and what it is actually worth.

    Z_target = (V * ripple) / I. It is a flat number applied to a network whose
    impedance is anything but flat, driven by a current whose spectrum is
    anything but white, so meeting it everywhere is neither necessary nor
    sufficient. It is useful as a first cut and misleading as a sign-off
    criterion, and the deck says so.
    """
    return dict(z_target=float(v_rail * ripple_pct / 100.0 / i_transient),
                v_rail=v_rail, ripple_pct=ripple_pct, i_transient=i_transient)


def ssn(n_drivers=32, i_per_driver=0.020, tr_ps=25.0, l_loop_ph=60.0):
    """Simultaneous switching noise from many drivers sharing a return.

    Every driver that switches at once drives its current through the shared
    inductance of the power and ground path, and the voltage that develops is
    L times the total rate of change. It scales with the number of drivers,
    which is why a wide interface switching in step is so much worse than the
    same drivers switching at random.
    """
    di_dt = n_drivers * i_per_driver / (tr_ps * 1e-12)
    v = l_loop_ph * 1e-12 * di_dt
    return dict(v_noise=float(v), v_noise_mv=float(v * 1000),
                di_dt_a_per_ns=float(di_dt / 1e9),
                n_drivers=n_drivers, l_loop_ph=l_loop_ph)


def supply_noise_to_jitter(v_ripple_mv, f_ripple_hz, psrr_db=-20.0,
                           kvco_hz_per_v=2e9, pll_bw_hz=4e6, f_carrier=14e9):
    """Convert a supply tone into periodic jitter at the transmitter.

    A tone on the supply reaches the oscillator's control node attenuated by
    the regulator and the loop's own rejection, and modulates its frequency.
    Frequency modulation integrates to phase modulation, so the phase deviation
    is the frequency deviation divided by the modulation frequency, and the
    resulting jitter is that phase divided by the carrier's angular frequency.

    The loop itself filters: inside the loop bandwidth the feedback corrects
    the disturbance, and outside it the oscillator is on its own. That is why
    supply tones just above the loop bandwidth are the dangerous ones, and why
    a switching regulator's fundamental is worth placing deliberately.
    """
    v = v_ripple_mv * 1e-3 * 10 ** (psrr_db / 20.0)
    df = kvco_hz_per_v * v
    loop_rej = np.abs(1j * (f_ripple_hz / pll_bw_hz)
                      / (1 + 1j * (f_ripple_hz / pll_bw_hz)))
    df_eff = df * loop_rej
    phase_rad = df_eff / max(f_ripple_hz, 1.0)
    jitter_s = phase_rad / (2 * np.pi * f_carrier)
    return dict(v_at_vco_mv=float(v * 1000), df_hz=float(df_eff),
                phase_rad=float(phase_rad),
                jitter_ps=float(jitter_s * 1e12),
                jitter_pp_ps=float(2 * jitter_s * 1e12),
                loop_rejection=float(loop_rej),
                f_ripple_hz=f_ripple_hz)


def ripple_sweep(v_ripple_mv=20.0, psrr_db=-20.0, pll_bw_hz=4e6,
                 f_carrier=14e9, n=200):
    """Jitter against where in frequency the supply tone sits."""
    f = np.logspace(3, 9, n)
    j = [supply_noise_to_jitter(v_ripple_mv, fi, psrr_db,
                                pll_bw_hz=pll_bw_hz,
                                f_carrier=f_carrier)['jitter_pp_ps'] for fi in f]
    j = np.array(j)
    i = int(np.argmax(j))
    return dict(f_hz=f.tolist(), jitter_pp_ps=j.tolist(),
                worst_f_hz=float(f[i]), worst_jitter_pp_ps=float(j[i]),
                pll_bw_hz=pll_bw_hz)
