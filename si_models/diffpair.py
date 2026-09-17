"""Differential signalling -- the model behind deck 05.

Everything in SerDes_Equalisation is written in terms of S_dd21 and every
channel in this series is a differential pair, but neither says why. This deck
does, and it computes the answer rather than reciting the usual list of
advantages.

Two claims here are worth more than the rest.

The first is that a differential pair is not two coupled lines that happen to
be near each other; the coupling is almost incidental. `coupling_cost()`
computes what tight coupling actually buys and what it costs, and finds that
holding the differential impedance constant while bringing the traces together
forces the traces narrower, which raises conductor loss -- so tight coupling is
paid for in decibels at Nyquist. Bogatin has argued this for years; here it is
as a number.

The second is that the benefit of differential signalling is a rejection
figure, not a binary property, and it degrades with anything that breaks the
symmetry. `skew_conversion()` turns intra-pair skew into the mode conversion
that follows from it, which is what the fibre-weave result in deck 03 feeds
into and what shows up as radiated emissions in a real system.
"""

import numpy as np

MU0 = 4.0e-7 * np.pi
C0 = 299792458.0
INCH = 0.0254


def pair_from_geometry(w_mm, s_mm, b_mm, er=3.7, cell=0.005, box=9,
                       t_mm=0.018):
    """Solve an edge-coupled stripline pair and return its modal parameters."""
    from .fdm2d import CrossSection, rlgc, modal
    W = box * b_mm
    cs = CrossSection(W, b_mm, cell)
    cs.dielectric(0, W, 0, b_mm, er)
    yc = b_mm / 2.0
    t = t_mm
    cs.conductor(W / 2 - s_mm / 2 - w_mm, W / 2 - s_mm / 2, yc, yc + t, 1)
    cs.conductor(W / 2 + s_mm / 2, W / 2 + s_mm / 2 + w_mm, yc, yc + t, 2)
    C, L = rlgc(cs)
    m = modal(C, L)
    m['w_mm'], m['s_mm'], m['b_mm'] = w_mm, s_mm, b_mm
    m['perimeter_m'] = 2 * (w_mm + t) * 1e-3
    return m


def pair_from_cohn(w_mm, s_mm, b_mm, er=3.7):
    """Modal parameters of an edge-coupled stripline from Cohn's exact result.

    For a homogeneous dielectric the even and odd modes travel at the same
    speed, so every per-unit-length quantity follows from the two modal
    impedances and that one velocity -- and in particular

        Lm / L = Cm / C = (Z0e - Z0o) / (Z0e + Z0o),

    which is exactly the condition that makes far-end crosstalk vanish in
    stripline. The field solver reproduces these to better than half a per
    cent (`verify_against_solver`), so the closed form is used for sweeps and
    the solver is kept for the geometries Cohn does not cover.
    """
    from .fdm2d import cohn_coupled_stripline
    z0e, z0o = cohn_coupled_stripline(w_mm, s_mm, b_mm, er)
    v = C0 / np.sqrt(er)
    Ls = (z0e + z0o) / (2 * v)
    Lm = (z0e - z0o) / (2 * v)
    Cs = (1.0 / z0e + 1.0 / z0o) / (2 * v)
    Cm = (1.0 / z0o - 1.0 / z0e) / (2 * v)
    return dict(z0e=z0e, z0o=z0o, zdiff=2 * z0o, zcomm=z0e / 2,
                k=(z0e - z0o) / (z0e + z0o), Ls=Ls, Lm=Lm, Cs=Cs, Cm=Cm,
                v_even=v, v_odd=v, w_mm=w_mm, s_mm=s_mm, b_mm=b_mm)


def solve_for_zdiff(s_mm, b_mm, er=3.7, z_target=100.0, cell=0.005,
                    lo=0.02, hi=1.2, iters=60, use_solver=False):
    """Find the trace width giving a target differential impedance.

    This is the question a stackup engineer actually asks -- not 'what
    impedance does this geometry give' but 'what geometry gives this
    impedance' -- so it is answered by bisection rather than by a table.
    """
    # Cohn first: it is exact, instant, and lands within about ten per cent of
    # the answer. Only then is the solver asked, in a bracket around that
    # width, because each solver evaluation costs four field relaxations.
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if pair_from_cohn(mid, s_mm, b_mm, er)['zdiff'] > z_target:
            lo = mid
        else:
            hi = mid
    w = 0.5 * (lo + hi)
    if use_solver:
        lo2, hi2 = 0.55 * w, 1.15 * w
        for _ in range(7):
            mid = 0.5 * (lo2 + hi2)
            if pair_from_geometry(mid, s_mm, b_mm, er, cell)['zdiff'] > z_target:
                lo2 = mid
            else:
                hi2 = mid
        w = 0.5 * (lo2 + hi2)
    m = (pair_from_geometry(w, s_mm, b_mm, er, cell) if use_solver
         else pair_from_cohn(w, s_mm, b_mm, er))
    m['w_solved_mm'] = w
    return m


def verify_against_solver(b_mm=0.4, er=4.0, cases=((0.15, 0.15), (0.15, 0.30),
                                                   (0.20, 0.20)),
                          t_mm=0.005):
    """Check the closed form against the field solver at matched assumptions.

    Cohn's result is exact for a conductor of zero thickness, so the check is
    run with the thinnest conductor the grid can represent. Agreement is then
    better than half a per cent, which is the real accuracy of the solver;
    `thickness_effect` separately reports what happens when the copper is given
    its actual thickness, which is a physical change rather than an error.
    """
    out = []
    for w, s in cases:
        a = pair_from_cohn(w, s, b_mm, er)
        c = pair_from_geometry(w, s, b_mm, er, 0.005, t_mm=t_mm)
        out.append(dict(w_mm=w, s_mm=s,
                        zdiff_cohn=float(a['zdiff']), zdiff_solver=float(c['zdiff']),
                        err_pct=float(100 * (c['zdiff'] / a['zdiff'] - 1)),
                        k_cohn=float(a['k']), k_solver=float(c['k'])))
    return out


def thickness_effect(w_mm=0.15, s_mm=0.15, b_mm=0.4, er=4.0,
                     thicknesses_mm=(0.005, 0.012, 0.018, 0.035, 0.070)):
    """What finite copper thickness does to a stripline pair.

    Every closed-form stripline result in the literature, Cohn's included,
    assumes an infinitely thin conductor. Real copper is between twelve and
    seventy micrometres thick, and the extra metal adds capacitance to the
    plates and to the neighbouring trace. The impedance falls accordingly, by
    an amount too large to ignore in a stackup that has to hold ten per cent.
    """
    ref = pair_from_cohn(w_mm, s_mm, b_mm, er)
    rows = []
    for t in thicknesses_mm:
        m = pair_from_geometry(w_mm, s_mm, b_mm, er, 0.005, t_mm=t)
        rows.append(dict(t_um=float(t * 1000), t_oz=float(t / 0.0348),
                         zdiff=float(m['zdiff']), k=float(m['k']),
                         delta_pct=float(100 * (m['zdiff'] / ref['zdiff'] - 1))))
    return dict(cohn_zdiff=float(ref['zdiff']), rows=rows,
                w_mm=w_mm, s_mm=s_mm, b_mm=b_mm)


def coupling_cost(b_mm=0.4, er=3.7, z_target=100.0, spacings=None,
                  f_nyq_ghz=14.0, length_in=10.0, rms_um=0.4,
                  sigma=5.8e7, cell=0.005, use_solver=True):
    """What tight coupling buys, and what it costs in loss.

    For each spacing the trace width is re-solved to hold the differential
    impedance at its target, so the comparison is between real, buildable
    stackups rather than between geometries with different impedances.

    Tight coupling does buy something: the pair is less sensitive to a
    neighbour, and the return current is more nearly confined between the two
    traces. It costs trace width, and conductor loss scales inversely with
    width, so the decibels lost at Nyquist are the price.
    """
    from .materials import hammerstad
    if spacings is None:
        spacings = [0.10, 0.15, 0.20, 0.30, 0.45, 0.70, 1.00]
    rows = []
    for s in spacings:
        m = solve_for_zdiff(s, b_mm, er, z_target, cell, use_solver=use_solver)
        w = m['w_solved_mm']
        perim = 2 * (w + 0.018) * 1e-3
        f = f_nyq_ghz * 1e9
        r_ac = 1.0 / perim * np.sqrt(2 * np.pi * f * MU0 / (2 * sigma))
        r_ac *= hammerstad(f, rms_um, sigma)
        # differential loop resistance is twice the per-conductor value
        alpha_db_in = 2 * r_ac / (2 * m['zdiff']) * 8.686 * INCH
        rows.append(dict(s_mm=s, w_mm=float(w), zdiff=float(m['zdiff']),
                         k=float(m['k']), lm_over_l=float(m['Lm'] / m['Ls']),
                         cm_over_c=float(m['Cm'] / m['Cs']),
                         alpha_db_per_in=float(alpha_db_in),
                         loss_db=float(alpha_db_in * length_in)))
    base = rows[-1]
    for r in rows:
        r['extra_loss_db'] = float(r['loss_db'] - base['loss_db'])
        r['coupling_pct'] = float(100 * r['k'])
    return dict(rows=rows, f_nyq_ghz=f_nyq_ghz, length_in=length_in,
                z_target=z_target, b_mm=b_mm)


def skew_conversion(skew_ps, f_ghz=None):
    """Differential-to-common conversion caused by intra-pair skew.

    A skew tau between the two legs means the difference signal loses, and the
    common-mode signal gains, a term proportional to sin(pi f tau). The
    conversion is complete when the skew reaches half a period, and the
    differential loss that goes with it is the part that costs eye height.
    """
    if f_ghz is None:
        f_ghz = np.linspace(0.1, 50, 500)
    f = np.asarray(f_ghz, float) * 1e9
    tau = skew_ps * 1e-12
    scd = np.abs(np.sin(np.pi * f * tau))
    sdd = np.abs(np.cos(np.pi * f * tau))
    return dict(f_ghz=np.asarray(f_ghz, float).tolist(),
                scd21_db=(20 * np.log10(scd + 1e-12)).tolist(),
                sdd21_db=(20 * np.log10(sdd + 1e-12)).tolist(),
                skew_ps=skew_ps,
                f_full_conversion_ghz=float(1e3 / (2 * skew_ps))
                if skew_ps > 0 else float('inf'))


def mode_velocity_conversion(length_in=10.0, er=3.7, delta_v_pct=2.0,
                             f_ghz=None):
    """Conversion caused by the two modes travelling at different speeds.

    In a homogeneous dielectric -- stripline -- the even and odd modes travel
    at the same speed and a symmetric pair converts nothing. In microstrip they
    do not, because the odd mode keeps more of its field in the laminate and
    the even mode more of it in air. A pair can then convert differential to
    common mode with no skew, no asymmetry and no manufacturing defect at all,
    purely because it is on the outer layer.
    """
    if f_ghz is None:
        f_ghz = np.linspace(0.1, 50, 500)
    f = np.asarray(f_ghz, float) * 1e9
    v = C0 / np.sqrt(er)
    tau = length_in * INCH / v
    dtau = tau * delta_v_pct / 100.0
    conv = np.abs(np.sin(np.pi * f * dtau))
    return dict(f_ghz=np.asarray(f_ghz, float).tolist(),
                conversion_db=(20 * np.log10(conv + 1e-12)).tolist(),
                effective_skew_ps=float(dtau * 1e12),
                delta_v_pct=delta_v_pct)


def common_mode_rejection(noise_mv=50.0, imbalance_pct=2.0, gain_mismatch_db=0.2):
    """How much of a common-mode disturbance survives into the differential signal.

    The textbook claim is that differential signalling rejects common-mode
    noise completely. It rejects it to the extent that the two halves are
    identical, and they never are: the traces differ in length and width, the
    receiver's two input devices differ, and the terminations differ. The
    residual is what matters.
    """
    g = 10 ** (gain_mismatch_db / 20.0)
    a_imb = imbalance_pct / 100.0
    cmrr = abs((g - 1) / (g + 1)) + a_imb / 2.0
    return dict(cmrr_db=float(-20 * np.log10(max(cmrr, 1e-9))),
                residual_mv=float(noise_mv * cmrr),
                noise_mv=noise_mv, imbalance_pct=imbalance_pct,
                gain_mismatch_db=gain_mismatch_db)


def termination_options(zdiff=100.0, z0e=None):
    """The three ways to terminate a pair, and what each one loads.

    A single resistor across the pair terminates the differential mode and
    leaves the common mode completely unterminated -- which is why a pair that
    looks well behaved differentially can still ring badly in common mode and
    radiate. The tee network terminates both.
    """
    z0o = zdiff / 2.0
    z0e = z0e if z0e is not None else z0o * 1.25
    zcm = z0e / 2.0
    return dict(
        z_diff=zdiff, z_odd=z0o, z_even=float(z0e), z_common=float(zcm),
        single_resistor=dict(r_ohm=zdiff, terminates_diff=True,
                             terminates_common=False),
        two_resistor=dict(r_ohm=z0o, terminates_diff=True,
                          terminates_common=False,
                          note='to a floating midpoint'),
        tee=dict(r_series_ohm=z0o, r_shunt_ohm=float(zcm),
                 terminates_diff=True, terminates_common=True))
