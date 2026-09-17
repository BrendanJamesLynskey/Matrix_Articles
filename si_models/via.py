"""Vias, stubs and discontinuities -- the model behind deck 04.

A via is the only part of a channel that is manufactured by drilling, and it
behaves unlike anything else on the board. It is simultaneously a capacitor
(the pad and barrel facing the antipad in every plane it passes), an inductor
(a thin vertical conductor whose return current has to find its way between
planes), and, if it carries the signal only part of the way down, a resonant
open-circuited stub that can put a null straight through the band.

Which of those three descriptions is the right one depends on frequency, and
`model_comparison()` computes where each stops being adequate rather than
asserting a rule.

The stub is the part that kills links. `backdrill_sweep()` prices it: an
un-backdrilled stub in a thick backplane puts its quarter-wave null near the
Nyquist frequency of a modern lane, and no equaliser recovers a null, because
the information at those frequencies has been removed rather than attenuated.
"""

import numpy as np

MU0 = 4.0e-7 * np.pi
C0 = 299792458.0
EPS0 = 1.0 / (MU0 * C0 * C0)
INCH = 0.0254


# ------------------------------------------------- incremental parameters ---

def via_capacitance(t_board_in, d_pad_in, d_anti_in, er=4.0):
    """Shunt capacitance of a via barrel and pad inside its antipad.

    The standard estimate treats the barrel-plus-pad and the antipad edge as a
    short coaxial capacitor:

        C [pF] = 1.41 * er * T * D_pad / (D_anti - D_pad)

    with every length in inches. It is a first-order figure; Johnson is
    emphatic that via capacitance is not separable from the capacitance of the
    traces attached to it, so this is a starting point for a budget rather than
    a substitute for a three-dimensional solve.
    """
    d = max(d_anti_in - d_pad_in, 1e-6)
    return 1.41 * er * t_board_in * d_pad_in / d      # pF


def via_inductance(h_in, d_in):
    """Series inductance of a via barrel of length h and diameter d, in nH.

    This is the isolated-via figure, and it assumes the return current is far
    away. That assumption is almost never true and almost always pessimistic:
    on a real board the return flows in ground vias a few tens of thousandths
    away, and `retpath.stitching_via` gives inductances several times smaller.

    The discrepancy is not an error in either formula. Inductance is a property
    of a loop, not of a piece of metal, so a via does not have an inductance
    until its return path is named. Quoting one without the other is the single
    most common way to get a via budget wrong.
    """
    return 5.08 * h_in * (np.log(4.0 * h_in / d_in) + 1.0)


def via_coax_impedance(d_barrel_in, d_anti_in, er=4.0):
    """The via seen as a length of coaxial line through the plane stack.

    Between planes the barrel really is the inner conductor of a coax whose
    outer conductor is the antipad edge, so it has a characteristic impedance.
    Designing the antipad so that this is near the channel impedance is what
    turns a via from a lumped discontinuity into a length of transmission line,
    which is the whole idea behind a well-designed high-speed via.
    """
    return 60.0 / np.sqrt(er) * np.log(d_anti_in / d_barrel_in)


def antipad_sweep(d_barrel_in=0.010, t_board_in=0.120, er=4.0,
                  d_pad_in=0.018, n=60, z_target=100.0):
    """Impedance and capacitance against antipad diameter.

    Opening the antipad raises the coaxial impedance and cuts the capacitance,
    which is why high-speed vias have large clearances -- and why the plane
    stack ends up perforated, which is where deck 02's return-path argument and
    deck 07's power-integrity argument both come back.
    """
    d_anti = np.linspace(d_pad_in * 1.2, d_pad_in * 5.0, n)
    z = np.array([via_coax_impedance(d_barrel_in, d, er) for d in d_anti])
    c = np.array([via_capacitance(t_board_in, d_pad_in, d, er) for d in d_anti])
    i = int(np.argmin(np.abs(2 * z - z_target)))
    return dict(d_anti_mil=(d_anti * 1000).tolist(), z_single=z.tolist(),
                z_diff=(2 * z).tolist(), c_pf=c.tolist(),
                d_anti_for_target_mil=float(d_anti[i] * 1000),
                c_at_target_pf=float(c[i]))


# ------------------------------------------------------------ the stub -----

def stub_notch_ghz(stub_len_in, er=3.7):
    """Quarter-wave resonance of an open-circuited stub."""
    tpd = np.sqrt(er) / C0 * INCH            # s per inch
    return 1.0 / (4.0 * tpd * stub_len_in) / 1e9


def stub_admittance(f, stub_len_in, z_stub=35.0, er=3.7,
                    ac=1.0, ad=0.2):
    """Shunt admittance of a lossy open-circuited stub, Y = tanh(gamma l)/Z."""
    f = np.asarray(f, float)
    tpd = np.sqrt(er) / C0 * INCH
    a_db = (ac * np.sqrt(f / 1e9) + ad * (f / 1e9)) * stub_len_in
    alpha = a_db / 8.686
    beta = 2 * np.pi * f * tpd * stub_len_in
    return np.tanh(alpha + 1j * beta) / z_stub


def backdrill_sweep(t_board_in=0.120, exit_layer_frac=0.25, f_nyq_ghz=14.0,
                    z0=100.0, z_stub=35.0, er=3.7, n=50):
    """Excess loss at Nyquist against how much stub is left behind.

    Back-drilling removes the unused barrel, but not all of it: the drill has
    to stop short of the signal layer by a manufacturing allowance, so a
    residual stub always remains. The sweep shows how quickly the penalty
    collapses once the stub is short enough to move its null well above the
    band -- and how little of the benefit depends on removing the last few
    thousandths.
    """
    full_stub = t_board_in * (1.0 - exit_layer_frac)
    res = np.linspace(0.0, full_stub, n)
    out = []
    for r in res:
        if r <= 1e-4:
            out.append(dict(stub_mil=float(r * 1000), notch_ghz=float('inf'),
                            excess_db=0.0))
            continue
        y = stub_admittance(f_nyq_ghz * 1e9, r, z_stub, er)
        excess = 20 * np.log10(np.abs(1.0 + y * z0 / 2.0))
        out.append(dict(stub_mil=float(r * 1000),
                        notch_ghz=float(stub_notch_ghz(r, er)),
                        excess_db=float(excess)))
    return dict(full_stub_mil=float(full_stub * 1000), sweep=out,
                f_nyq_ghz=f_nyq_ghz)


# ------------------------------------------------- the via as a two-port ----

def _abcd_series(z):
    n = np.size(z)
    m = np.zeros((2, 2, n), dtype=complex)
    m[0, 0] = 1; m[1, 1] = 1; m[0, 1] = z
    return m


def _abcd_shunt(y):
    n = np.size(y)
    m = np.zeros((2, 2, n), dtype=complex)
    m[0, 0] = 1; m[1, 1] = 1; m[1, 0] = y
    return m


def _cascade(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = np.einsum('ijf,jkf->ikf', out, m)
    return out


def _to_s(abcd, z0):
    a, b, c, d = abcd[0, 0], abcd[0, 1], abcd[1, 0], abcd[1, 1]
    den = a + b / z0 + c * z0 + d
    return dict(s11=(a + b / z0 - c * z0 - d) / den, s21=2.0 / den)


def via_two_port(f, c_pf=0.55, l_nh=0.42, stub_in=0.0, z0=100.0,
                 z_stub=35.0, er=3.7, model='pi'):
    """S-parameters of a via, by one of the three usual models."""
    f = np.asarray(f, float)
    w = 2 * np.pi * f
    c = c_pf * 1e-12
    l = l_nh * 1e-9
    y_half = 1j * w * c / 2.0
    if stub_in > 0:
        y_half = y_half + stub_admittance(f, stub_in, z_stub, er) / 2.0
    if model == 'c':
        m = _abcd_shunt(2 * y_half)
    elif model == 'l':
        m = _abcd_series(1j * w * l)
    else:
        m = _cascade(_abcd_shunt(y_half), _abcd_series(1j * w * l),
                     _abcd_shunt(y_half))
    return _to_s(m, z0)


def model_comparison(c_pf=0.55, l_nh=0.42, z0=100.0, tol_lin=0.01):
    """Where each simplified via model stops agreeing with the pi model.

    Below the frequency at which the barrel inductance matters, a via is a
    capacitor; below the frequency at which the pad capacitance matters, it is
    an inductor; in between, only the pi model is right. The self-resonance of
    the pi model is where the two reactances cancel, and above it the via is a
    resonator rather than a discontinuity.
    """
    f = np.logspace(8, 11.2, 900)
    ref = via_two_port(f, c_pf, l_nh, z0=z0, model='pi')
    out = {}
    for m in ('c', 'l'):
        s = via_two_port(f, c_pf, l_nh, z0=z0, model=m)
        # Compare reflection coefficients linearly. Comparing them in decibels
        # would call a simplification wrong at low frequency where both models
        # predict a reflection too small to matter, which is the opposite of
        # what we want to know.
        err = np.abs(np.abs(s['s11']) - np.abs(ref['s11']))
        bad = np.nonzero(err >= tol_lin)[0]
        if bad.size == 0:
            v = float(f[-1] / 1e9)          # never breaks over the sweep
        elif bad[0] == 0:
            v = 0.0                         # already wrong at the bottom
        else:
            v = float(f[bad[0] - 1] / 1e9)
        out[m] = dict(valid_to_ghz=v)
    f_res = 1.0 / (2 * np.pi * np.sqrt(l_nh * 1e-9 * c_pf * 1e-12))
    z_via = float(np.sqrt((l_nh * 1e-9) / (c_pf * 1e-12)))
    return dict(
                dominant='inductive' if z_via > z0 else 'capacitive',
                tol_lin=tol_lin,f_ghz=(f / 1e9).tolist(),
                s11_pi_db=(20 * np.log10(np.abs(ref['s11']) + 1e-15)).tolist(),
                s21_pi_db=(20 * np.log10(np.abs(ref['s21']) + 1e-15)).tolist(),
                cap_model_valid_to_ghz=out['c']['valid_to_ghz'],
                ind_model_valid_to_ghz=out['l']['valid_to_ghz'],
                self_resonance_ghz=float(f_res / 1e9),
                z_via_ohm=float(np.sqrt((l_nh * 1e-9) / (c_pf * 1e-12))))


# -------------------------------------------------- via-to-via crosstalk ----

def via_crosstalk_inductance(h_in, s1_in, s2_in, s3_in, r_in):
    """Mutual inductance between two signal vias sharing a return via.

    Johnson's result: the shared return path, not the direct field between the
    two signal barrels, is what couples them, so the mutual inductance is

        Lm = 5.08 h ln(s1 s3 / (s2 r))  nH,

    where s1 and s3 are the distances from the shared return via to the two
    signal vias and s2 is the distance between the signal vias. Giving each
    signal via its own return via is what breaks the mechanism.
    """
    return 5.08 * h_in * np.log(max(s1_in * s3_in / (s2_in * r_in), 1.0 + 1e-9))


def via_as_tline(f, t_board_in=0.120, d_barrel_in=0.010, d_anti_in=0.030,
                 er=3.7, z0=100.0, stub_in=0.0, z_stub=35.0,
                 launch_c_pf=0.10):
    """The via modelled as a short length of coaxial line rather than a lump.

    This is the modern view and it is the one that makes 112G vias possible. A
    barrel passing through a stack of antipads is a coaxial transmission line;
    if its impedance is designed to match the channel, it is not a
    discontinuity at all, however long it is. What remains is the launch -- the
    transition from planar trace to barrel, which is genuinely lumped and
    genuinely capacitive -- and the stub, if any is left.

    Comparing this against `via_two_port` shows how badly the lumped picture
    misleads once the antipad has been opened up: the lumped model says the via
    gets worse with board thickness, the transmission-line model says it does
    not, and measurement agrees with the second.
    """
    f = np.asarray(f, float)
    w = 2 * np.pi * f
    z_via_diff = 2.0 * via_coax_impedance(d_barrel_in, d_anti_in, er)
    tpd = np.sqrt(er) / C0 * INCH
    beta = w * tpd * t_board_in
    alpha = (0.6 * np.sqrt(f / 1e9)) / 8.686 * t_board_in
    g = alpha + 1j * beta
    ch, sh = np.cosh(g), np.sinh(g)
    n = f.size
    m = np.zeros((2, 2, n), dtype=complex)
    m[0, 0] = ch; m[0, 1] = z_via_diff * sh
    m[1, 0] = sh / z_via_diff; m[1, 1] = ch

    y_l = 1j * w * launch_c_pf * 1e-12
    if stub_in > 0:
        y_l = y_l + stub_admittance(f, stub_in, z_stub, er)
    full = _cascade(_abcd_shunt(y_l), m, _abcd_shunt(y_l))
    s = _to_s(full, z0)
    return dict(z_via_diff=float(z_via_diff),
                s11_db=(20 * np.log10(np.abs(s['s11']) + 1e-15)).tolist(),
                s21_db=(20 * np.log10(np.abs(s['s21']) + 1e-15)).tolist(),
                f_ghz=(f / 1e9).tolist())


def optimise_via(t_board_in=0.120, d_barrel_in=0.010, er=3.7, z0=100.0,
                 launch_c_pf=0.08, f_nyq_ghz=14.0, f_max_ghz=30.0, n=80):
    """Find the antipad that makes the whole transition best, not the barrel.

    A barrel whose own impedance equals the channel impedance is *not* the best
    via. The launch -- the pad, the antipad in the signal layer and the stub of
    trace reaching the barrel -- is capacitive, and a barrel a little below the
    channel impedance reflects with the opposite sign to that capacitance, so
    the two partly cancel. Optimising them together rather than separately is
    the difference between a via that works at 28 GBd and one that does not.

    The objective is the reflection at the Nyquist frequency of the lane the
    via has to carry, which is the design point that matters; the frequency at
    which return loss crosses ten decibels is reported alongside it as the
    usable bandwidth of the transition. Optimising instead for the worst
    reflection anywhere in a wide sweep is not informative, because at the top
    of such a sweep the launch capacitance dominates whatever the barrel does.
    """
    f = np.linspace(0.2e9, f_max_ghz * 1e9, 400)
    d_anti = np.linspace(d_barrel_in * 1.6, d_barrel_in * 8.0, n)
    rows = []
    for d in d_anti:
        r = via_as_tline(f, t_board_in, d_barrel_in, d, er, z0,
                         launch_c_pf=launch_c_pf)
        fg = np.array(r['f_ghz']); s11 = np.array(r['s11_db'])
        under = fg[s11 < -10.0]
        # the first frequency at which the transition stops making 10 dB
        bad = np.nonzero(s11 >= -10.0)[0]
        bw = float(fg[bad[0]]) if bad.size else float(fg[-1])
        rows.append(dict(d_anti_mil=float(d * 1000),
                         z_diff=float(r['z_via_diff']),
                         s11_nyq_db=float(np.interp(f_nyq_ghz, fg, s11)),
                         bw_10db_ghz=bw))
    best = min(rows, key=lambda r: r['s11_nyq_db'])
    widest = max(rows, key=lambda r: r['bw_10db_ghz'])
    matched = min(rows, key=lambda r: abs(r['z_diff'] - z0))
    return dict(sweep=rows, best=best, widest=widest,
                impedance_matched=matched, launch_c_pf=launch_c_pf,
                f_nyq_ghz=f_nyq_ghz,
                gain_db=float(matched['s11_nyq_db'] - best['s11_nyq_db']))
