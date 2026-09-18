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
C0 = 299792458.0
EPS0 = 1.0 / (MU0 * C0 * C0)


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
                           kvco_hz_per_v=2e9, pll_bw_hz=4e6, f_carrier=14e9,
                           order=2, zeta=0.707):
    """Convert a supply tone into periodic jitter at the transmitter.

    A tone on the supply reaches the oscillator's control node attenuated by
    the regulator and the loop's own rejection, and modulates its frequency.
    Frequency modulation integrates to phase modulation, so the phase deviation
    is the frequency deviation divided by the modulation frequency, and the
    resulting jitter is that phase divided by the carrier's angular frequency.

    The loop itself filters, and the order of the loop decides the shape of
    the answer. Against a disturbance injected at the oscillator the loop's
    error response is high-pass: a first-order (type I) loop rejects as f,
    a second-order (type II) loop as f squared.

    That distinction matters more than it looks, because the modulation index
    already falls as 1/f. In a first-order loop the rising rejection and the
    falling modulation index cancel exactly, and the jitter is flat from DC to
    the loop bandwidth before rolling off - so there is no worst frequency
    below the bandwidth, only a plateau. In a second-order loop the f-squared
    rejection wins, the response rises, and there is a genuine peak near the
    natural frequency. The common statement that the dangerous tone sits just
    above the loop bandwidth is a statement about type-II loops; applied to a
    first-order model it is wrong, and this function computes both so the
    difference is visible rather than asserted.
    """
    v = v_ripple_mv * 1e-3 * 10 ** (psrr_db / 20.0)
    df = kvco_hz_per_v * v
    x = f_ripple_hz / pll_bw_hz
    if order == 1:
        loop_rej = np.abs(1j * x / (1 + 1j * x))
    else:
        loop_rej = np.abs(-(x ** 2) / (1 - x ** 2 + 2j * zeta * x))
    df_eff = df * loop_rej
    phase_rad = df_eff / max(f_ripple_hz, 1.0)
    jitter_s = phase_rad / (2 * np.pi * f_carrier)
    return dict(v_at_vco_mv=float(v * 1000), df_hz=float(df_eff),
                phase_rad=float(phase_rad),
                jitter_ps=float(jitter_s * 1e12),
                jitter_pp_ps=float(2 * jitter_s * 1e12),
                loop_rejection=float(loop_rej),
                order=order, zeta=zeta,
                f_ripple_hz=f_ripple_hz)


def ripple_sweep(v_ripple_mv=20.0, psrr_db=-20.0, pll_bw_hz=4e6,
                 f_carrier=14e9, n=200, order=2, zeta=0.707):
    """Jitter against where in frequency the supply tone sits.

    Both loop orders are returned. The second-order curve is the headline
    because real clock-recovery and synthesis loops are type II; the
    first-order curve is kept alongside it because it is flat below the loop
    bandwidth, and that flatness is the reason the usual rule of thumb needs
    the loop order stated before it means anything.
    """
    f = np.logspace(3, 9, n)

    def sweep(o):
        return np.array([supply_noise_to_jitter(
            v_ripple_mv, fi, psrr_db, pll_bw_hz=pll_bw_hz,
            f_carrier=f_carrier, order=o, zeta=zeta)['jitter_pp_ps']
            for fi in f])

    j = sweep(order)
    j1 = sweep(1)
    i = int(np.argmax(j))
    # How sharply the peak stands above the low-frequency behaviour, which is
    # the part of the rule of thumb worth keeping.
    lo = float(j[0])
    return dict(f_hz=f.tolist(), jitter_pp_ps=j.tolist(),
                jitter_pp_ps_order1=j1.tolist(),
                worst_f_hz=float(f[i]), worst_jitter_pp_ps=float(j[i]),
                worst_over_bw=float(f[i] / pll_bw_hz),
                jitter_at_1khz_ps=lo,
                peak_over_low_f_db=float(20 * np.log10(j[i] / lo))
                if lo > 0 else float('inf'),
                order1_plateau_ps=float(j1[0]),
                order1_at_bw_ps=float(j1[int(np.argmin(abs(f - pll_bw_hz)))]),
                order=order, zeta=zeta,
                pll_bw_hz=pll_bw_hz)


# ==========================================================================
# The material below follows Smith and Bogatin's treatment. Their organising
# claim is that a power delivery network is not a lumped ladder but an
# ecology: on-die capacitance, package lead inductance, the board cavity and
# the regulator each dominate a band, and the interesting behaviour lives in
# the interactions between them rather than in any one element.
#
# Their second claim, which inverts the usual intuition, is about the forcing
# function. It is not that a current step drives di/dt through an inductor;
# it is that charge drawn out of the on-die capacitance makes the die voltage
# droop, and that droop is what pulls current through the package inductance.
# `transient_droop` is written that way round.
# ==========================================================================

def bandini_mountain(c_die_nf=200.0, l_pkg_ph=30.0, r_die_mohm=5.0,
                     r_board_mohm=None, f=None, c_board_uf=100.0,
                     l_board_ph=50.0, r_bulk_mohm=5.0, c_bulk_uf=2000.0,
                     l_bulk_nh=5.0, r_vrm_mohm=1.0, l_vrm_nh=500.0):
    """The antiresonance between on-die capacitance and package inductance.

    Seen from the die, the on-die decoupling capacitance is in parallel with
    everything beyond the package, and everything beyond the package is behind
    the package's lead inductance. Those two resonate, and because the die
    capacitance is large and the package inductance small the resonance lands
    in the high hundreds of megahertz -- exactly where core logic switches.

    Steve Weir named the resulting peak the Bandini Mountain. It is usually the
    largest feature in a real impedance profile and it cannot be decoupled away
    from the board, because the board is on the far side of the inductance that
    causes it. The only remedies are on the die or in the package.

    Its characteristic impedance is sqrt(L_pkg / C_die), and the series
    resistance needed to damp it is of that order -- which is the useful design
    number, because it says how much loss the path has to have.
    """
    if f is None:
        f = np.logspace(5, 10, 1600)
    w = 2 * np.pi * f
    c_die = c_die_nf * 1e-9
    l_pkg = l_pkg_ph * 1e-12
    r_die = r_die_mohm * 1e-3
    r_board = (r_board_mohm * 1e-3) if r_board_mohm is not None \
        else np.sqrt((l_pkg + l_board_ph * 1e-12) / c_die)

    # The board has to be modelled as a bank of mounted capacitors, not as a
    # single series RLC. A one-nanohenry board branch swamps a thirty-
    # picohenry package lead, and the antiresonance then sits where the board
    # puts it rather than where the package does -- which is the wrong answer
    # and, worse, a plausible-looking one.
    z_dieC = r_die + 1.0 / (1j * w * c_die)
    z_mlcc = r_board + 1j * w * l_board_ph * 1e-12 \
        + 1.0 / (1j * w * c_board_uf * 1e-6)
    z_bulk = r_bulk_mohm * 1e-3 + 1j * w * l_bulk_nh * 1e-9 \
        + 1.0 / (1j * w * c_bulk_uf * 1e-6)
    z_vrm = r_vrm_mohm * 1e-3 + 1j * w * l_vrm_nh * 1e-9
    z_board = 1.0 / (1.0 / z_mlcc + 1.0 / z_bulk + 1.0 / z_vrm)
    z_beyond = 1j * w * l_pkg + z_board
    z = 1.0 / (1.0 / z_dieC + 1.0 / z_beyond)

    # the loop the die capacitance actually resonates against includes the
    # inductance of the board bank as well as the package lead
    l_eff = l_pkg + l_board_ph * 1e-12
    f_bm = 1.0 / (2 * np.pi * np.sqrt(l_eff * c_die))
    z_bm = np.sqrt(l_eff / c_die)
    band = (f > 0.25 * f_bm) & (f < 4 * f_bm)
    j = int(np.arange(len(f))[band][int(np.argmax(np.abs(z[band])))])
    return dict(f=f, z=np.abs(z),
                f_bm_hz=float(f_bm), z_bm_ohm=float(z_bm),
                f_peak_hz=float(f[j]), z_peak_ohm=float(np.abs(z[j])),
                q=float(z_bm / r_board) if r_board else None,
                r_board_mohm=float(r_board * 1e3),
                l_eff_ph=float(l_eff * 1e12),
                c_die_nf=c_die_nf, l_pkg_ph=l_pkg_ph)


def bandini_damping(c_die_nf=200.0, l_pkg_ph=30.0,
                    r_list_mohm=(10, 20, 50, 71, 100, 200)):
    """Peak height against the series resistance damping it."""
    z_bm = bandini_mountain(c_die_nf, l_pkg_ph)['z_bm_ohm']
    rows = []
    for r in r_list_mohm:
        b = bandini_mountain(c_die_nf, l_pkg_ph, r_board_mohm=r)
        rows.append(dict(r_mohm=r, z_peak_mohm=float(1e3 * b['z_peak_ohm']),
                         f_peak_mhz=float(b['f_peak_hz'] / 1e6),
                         ratio_to_zbm=float(b['z_peak_ohm'] / z_bm)))
    return dict(z_bm_mohm=float(1e3 * z_bm), rows=rows,
                c_die_nf=c_die_nf, l_pkg_ph=l_pkg_ph)


def spreading_inductance(h_um=100.0, d_mm=10.0, r_via_mm=0.15):
    """Inductance of current spreading through a plane cavity.

    Between two points in a wide cavity the inductance does not depend on the
    area of the planes but on the logarithm of the separation divided by the
    contact radius, scaled by the plate spacing. Two consequences follow, and
    both are counter-intuitive.

    The first is that a thinner dielectric gives a lower inductance in direct
    proportion, which is why power and ground planes are placed on adjacent
    layers rather than merely somewhere in the stackup.

    The second is that impedance depends on *where* you probe. A capacitor is
    only as good as the spreading inductance between it and the load, so the
    same board measures differently at different points, and 'the PDN
    impedance' is not a single number.
    """
    h = h_um * 1e-6
    d = d_mm * 1e-3
    r = r_via_mm * 1e-3
    l = MU0 * h / (2 * np.pi) * np.log(max(d / r, 1.001))
    return dict(h_um=h_um, d_mm=d_mm, l_ph=float(l * 1e12),
                l_per_sq_ph=float(MU0 * h * 1e12))


def spreading_sweep(h_list_um=(50, 100, 200, 400), d_list_mm=(1, 2, 5, 10, 25)):
    rows = []
    for h in h_list_um:
        for d in d_list_mm:
            s = spreading_inductance(h, d)
            rows.append(dict(h_um=h, d_mm=d, l_ph=s['l_ph']))
    return rows


def cavity_impedance_at(x1, y1, x2, y2, w_mm=150.0, l_mm=100.0, h_um=100.0,
                        er=4.0, loss_tangent=0.02, f=None, n_modes=8):
    """Impedance between two points on a plane pair, by modal expansion.

    The cavity's modes each contribute in proportion to the product of the mode
    shape evaluated at the two contact points, so a probe sitting on a node of
    a mode does not see that mode at all. This is the formal statement of the
    previous function's second consequence: impedance is a property of a pair
    of points, not of a board.
    """
    if f is None:
        f = np.logspace(7, 10, 800)
    W, L, h = w_mm * 1e-3, l_mm * 1e-3, h_um * 1e-6
    w = 2 * np.pi * f
    c_plane = EPS0 * er * W * L / h
    z = 1.0 / (1j * w * c_plane * (1 + 1j * loss_tangent))
    C0_ = 299792458.0
    for m in range(n_modes):
        for n in range(n_modes):
            if m == 0 and n == 0:
                continue
            fmn = C0_ / (2 * np.sqrt(er)) * np.sqrt((m / W) ** 2 + (n / L) ** 2)
            if fmn > 3 * f[-1]:
                continue
            cm = (2 if m else 1) * (2 if n else 1)
            shape = (np.cos(m * np.pi * x1 / W) * np.cos(n * np.pi * y1 / L) *
                     np.cos(m * np.pi * x2 / W) * np.cos(n * np.pi * y2 / L))
            wmn = 2 * np.pi * fmn
            q = 1.0 / loss_tangent
            z = z + (cm * shape / (1j * w * c_plane)) * \
                (w ** 2) / ((wmn ** 2 - w ** 2) + 1j * w * wmn / q)
    return dict(f=f, z=np.abs(z), c_plane_nf=float(c_plane * 1e9))


def probe_position_study(w_mm=150.0, l_mm=100.0, h_um=100.0, er=4.0):
    """The same plane pair measured at three pairs of points."""
    W, L = w_mm * 1e-3, l_mm * 1e-3
    cases = {
        'centre to centre': (W / 2, L / 2, W / 2, L / 2),
        'centre to a corner': (W / 2, L / 2, 0.05 * W, 0.05 * L),
        'corner to opposite corner': (0.05 * W, 0.05 * L, 0.95 * W, 0.95 * L),
    }
    out = {}
    for k, (x1, y1, x2, y2) in cases.items():
        r = cavity_impedance_at(x1, y1, x2, y2, w_mm, l_mm, h_um, er)
        f, z = r['f'], r['z']
        band = (f > 2e8) & (f < 5e9)
        out[k] = dict(f=f, z=z, z_max_band=float(z[band].max()),
                      f_at_max=float(f[band][int(np.argmax(z[band]))]))
    return out


def fdtim(z_target_mohm=45.0, f_max_hz=1e9, l_mount_ph=600.0,
          c_values_uf=(100.0, 10.0, 1.0, 0.1, 0.01), r_esr_mohm=20.0):
    """The frequency-domain target-impedance method, in its essential form.

    Smith and Bogatin's observation is that the number of capacitors a board
    needs is not set by how much capacitance is wanted but by mounting
    inductance. Above their resonances, N capacitors in parallel present
    L_mount / N, so meeting a target impedance at the highest frequency the
    discrete capacitors have to cover requires

        N >= 2 pi f_max L_mount / Z_target

    regardless of the values chosen. Capacitance decides where the coverage
    begins; inductance decides how many parts it takes. That is why halving
    the mounting inductance is worth more than any change of value, and why a
    design that misses its target cannot always be rescued by buying more
    capacitors of the same sort.
    """
    z_t = z_target_mohm * 1e-3
    l_m = l_mount_ph * 1e-12
    n_min = 2 * np.pi * f_max_hz * l_m / z_t
    rows = []
    for c in c_values_uf:
        cc = c * 1e-6
        srf = 1.0 / (2 * np.pi * np.sqrt(cc * l_m))
        f_lo = 1.0 / (2 * np.pi * cc * z_t)        # where C alone meets target
        rows.append(dict(c_uf=c, srf_hz=float(srf),
                         f_target_from_hz=float(f_lo),
                         decades=float(np.log10(max(srf / f_lo, 1.0)))))
    return dict(n_min=float(np.ceil(n_min)), n_min_exact=float(n_min),
                z_target_mohm=z_target_mohm, f_max_hz=f_max_hz,
                l_mount_ph=l_mount_ph, rows=rows,
                l_for_one_cap_ph=float(1e12 * z_t / (2 * np.pi * f_max_hz)))


def fdtim_sweep(z_target_mohm=45.0, f_max_hz=1e9,
                l_list_ph=(200, 400, 600, 1000, 2000)):
    return [dict(l_mount_ph=l,
                 n_min=fdtim(z_target_mohm, f_max_hz, l)['n_min'])
            for l in l_list_ph]


def transient_droop(i_step_a=10.0, rise_ps=50.0, t_span_ns=200.0,
                    nfft=1 << 21, record_us=20.0, **pdn_kw):
    """Voltage droop in the time domain, obtained from the impedance itself.

    Rather than assembling a second-order response by hand, the current step is
    transformed, multiplied by the network's own impedance and transformed
    back, so every feature of the impedance profile appears in the time
    response without having to be put there. The three droops a designer sees
    on an oscilloscope are the three resonances of the ecology, in order of
    frequency.

    Two details decide whether the answer means anything, and both were got
    wrong here first time. The transform is circular, so a load that is still
    drawing current at the end of the record wraps round and contaminates t=0;
    and a record only as long as the plot resolves no frequency below its own
    reciprocal, which for a 200 ns window is 5 MHz - above everything the bulk
    capacitance and the regulator do. The fix for both is the damped transform:
    the network is evaluated at s = sigma + j.omega rather than on the
    imaginary axis, the current is weighted by exp(-sigma.t) before the
    transform and the result by exp(+sigma.t) after it, and the record is made
    far longer than the part reported. The wrap-around term is then suppressed
    by exp(-sigma.T), and the reported window is a genuine step response.

    Smith's framing is worth keeping in mind while reading the result. The die
    does not wait for the package; it draws charge out of its own capacitance
    immediately, and the voltage that develops is what pulls current through
    the package inductance afterwards. The first droop is therefore set by
    on-die capacitance alone, and nothing on the board can reduce it.
    """
    T = record_us * 1e-6
    fs = nfft / T
    k = np.arange(nfft // 2 + 1)
    sigma = 23.0 / T                      # exp(-sigma.T) is about 1e-10
    sv = sigma + 1j * 2 * np.pi * k / T
    Z = _bandini_complex(s=sv, **pdn_kw)

    t = np.arange(nfft) / fs
    tr = rise_ps * 1e-12
    i_t = i_step_a * np.clip(t / tr, 0.0, 1.0)
    v = -np.fft.irfft(np.fft.rfft(i_t * np.exp(-sigma * t)) * Z, n=nfft) \
        * np.exp(sigma * t)

    keep = t <= t_span_ns * 1e-9
    tt, vv = t[keep] * 1e9, v[keep] * 1e3
    # Two separate things happen during the edge, and the usual statement runs
    # them together. Charge comes out of the on-die capacitance, which is the
    # q/C term; and the same current crosses that capacitance's own series
    # resistance, which is an I.R term that appears instantly and does not
    # depend on how much capacitance there is.
    q = 0.5 * i_step_a * tr              # a linear ramp delivers half of i.tr
    first_charge = q / (pdn_kw.get('c_die_nf', 200.0) * 1e-9)
    first_esr = i_step_a * pdn_kw.get('r_die_mohm', 5.0) * 1e-3
    i_edge = int(np.argmin(np.abs(tt - 1e-3 * rise_ps)))
    worst = float(vv.min())
    z_peak = bandini_mountain(**pdn_kw)['z_peak_ohm']
    # Decimate for the deck: the edge needs picosecond steps, the plot does not.
    step = max(1, len(tt) // 1200)
    return dict(t_ns=tt[::step].tolist(), v_mv=vv[::step].tolist(),
                first_droop_charge_mv=float(first_charge * 1e3),
                first_droop_esr_mv=float(first_esr * 1e3),
                first_droop_mv=float((first_charge + first_esr) * 1e3),
                first_droop_computed_mv=float(-vv[i_edge]),
                worst_mv=worst,
                worst_at_ns=float(tt[int(np.argmin(vv))]),
                # The frequency and time domains checked against each other:
                # the deepest droop divided by the step current should be the
                # peak of the impedance profile, and it is.
                worst_as_impedance_mohm=float(-worst / i_step_a),
                z_peak_mohm=float(1e3 * z_peak),
                droop_vs_zpeak_err_pct=float(
                    100 * ((-worst * 1e-3 / i_step_a) - z_peak) / z_peak),
                at_end_mv=float(vv[-1]),
                r_dc_mohm=float(1e3 * abs(_bandini_complex(s=np.array([1e-3]),
                                                           **pdn_kw)[0])),
                record_us=record_us, t_span_ns=t_span_ns,
                i_step_a=i_step_a, rise_ps=rise_ps)


def _bandini_complex(f=None, c_die_nf=200.0, l_pkg_ph=30.0, r_die_mohm=5.0,
                     r_board_mohm=None, c_board_uf=100.0, l_board_ph=50.0,
                     r_bulk_mohm=5.0, c_bulk_uf=2000.0, l_bulk_nh=5.0,
                     r_vrm_mohm=1.0, l_vrm_nh=500.0, s=None):
    """The same network as `bandini_mountain`, returning complex impedance.

    Either a real frequency array `f`, or a complex Laplace variable `s`. The
    second form is what `transient_droop` needs: evaluating the network off the
    imaginary axis is what makes the numerical inverse transform behave.
    """
    sv = (1j * 2 * np.pi * np.asarray(f, float)) if s is None \
        else np.asarray(s, complex)
    c_die = c_die_nf * 1e-9
    l_pkg = l_pkg_ph * 1e-12
    r_board = (r_board_mohm * 1e-3) if r_board_mohm is not None \
        else np.sqrt((l_pkg + l_board_ph * 1e-12) / c_die)
    z_dieC = r_die_mohm * 1e-3 + 1.0 / (sv * c_die)
    z_mlcc = r_board + sv * l_board_ph * 1e-12 \
        + 1.0 / (sv * c_board_uf * 1e-6)
    z_bulk = r_bulk_mohm * 1e-3 + sv * l_bulk_nh * 1e-9 \
        + 1.0 / (sv * c_bulk_uf * 1e-6)
    z_vrm = r_vrm_mohm * 1e-3 + sv * l_vrm_nh * 1e-9
    z_board = 1.0 / (1.0 / z_mlcc + 1.0 / z_bulk + 1.0 / z_vrm)
    return 1.0 / (1.0 / z_dieC + 1.0 / (sv * l_pkg + z_board))


# ------------------------------------------------ measuring low impedance ---

def two_port_shunt(z_dut, z0=50.0):
    """Transmission through a shunt impedance, from its ABCD matrix.

    A shunt admittance Y between two ports has ABCD [[1,0],[Y,1]], so

        S21 = 2 / (2 + Z0/Z) = 2Z / (2Z + Z0),

    which inverts to Z = (Z0/2) S21 / (1 - S21).

    The important feature is that a small impedance produces a *small*
    transmitted signal, not a small deviation on a large one. A milliohm
    transmits about -88 dB, and a network analyser has well over a hundred
    decibels of dynamic range, so the measurement sits comfortably inside the
    instrument's capability. That is the whole reason the method exists.
    """
    z = np.asarray(z_dut, dtype=complex)
    return 2 * z / (2 * z + z0)


def two_port_shunt_invert(s21, z0=50.0):
    s21 = np.asarray(s21, dtype=complex)
    return (z0 / 2.0) * s21 / (1.0 - s21)


def measurement_sensitivity(z_list_mohm=(0.1, 1, 10, 100, 1000), z0=50.0,
                            directivity_db=40.0):
    """Why a one-port reflection measurement cannot reach a milliohm.

    Reflection: anything far below the reference impedance looks like a short,
    and the measured quantity is a tiny departure from a reflection of unity.
    How tiny it can be and still be believed is set by the analyser's
    directivity -- the leakage of the incident signal into the reflected
    channel -- which is typically forty decibels and puts a floor of around
    2*Z0*10^(-D/20) on the impedance that can be resolved. For a 50 ohm
    instrument with 40 dB directivity that floor is about an ohm.

    Transmission: the shunt transmits 2Z/(2Z+Z0), which for a milliohm is
    -88 dB. That is a small signal in a large dynamic range rather than a
    small difference between two large ones, and there is no directivity term
    at all.
    """
    floor = 2 * z0 * 10 ** (-directivity_db / 20.0)
    rows = []
    for zm in z_list_mohm:
        z = zm * 1e-3
        s11 = (z - z0) / (z + z0)
        s21 = 2 * z / (2 * z + z0)
        rows.append(dict(
            z_mohm=zm,
            s11_db=float(20 * np.log10(abs(s11))),
            s11_departure_from_short=float(abs(abs(s11) - 1.0)),
            s21_db=float(20 * np.log10(abs(s21))),
            resolvable_by_reflection=bool(z > floor)))
    return dict(rows=rows, directivity_db=directivity_db,
                reflection_floor_ohm=float(floor),
                reflection_floor_mohm=float(floor * 1e3))


def ground_loop_error(z_dut_mohm=1.0, z_shield_mohm=100.0, z0=50.0):
    """The error a cable-braid ground loop puts on a shunt-through measurement.

    The two ports share a ground through the cable braids, so some of the
    current intended for the device returns through the shields instead. At low
    frequency the braid impedance is comparable with a milliohm device and the
    measurement reads the parallel combination, which is why a shunt-through
    setup needs a common-mode isolator below a megahertz or so.
    """
    z = z_dut_mohm * 1e-3
    zs = z_shield_mohm * 1e-3
    z_meas = z + zs * 0.0 + (z * zs) / (z + zs) * 0.0 + z
    z_apparent = 1.0 / (1.0 / z + 1.0 / zs) if zs > 0 else z
    return dict(z_true_mohm=z_dut_mohm, z_shield_mohm=z_shield_mohm,
                z_apparent_mohm=float(z_apparent * 1e3),
                error_pct=float(100 * (z_apparent / z - 1)))
