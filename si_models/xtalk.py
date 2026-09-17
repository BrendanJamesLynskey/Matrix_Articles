"""Crosstalk -- the model behind deck 06.

Crosstalk is the impairment an equaliser cannot touch. Loss and reflection are
both correlated with the data on the victim lane, so a filter designed against
the victim's own pulse response can subtract them; crosstalk is driven by
somebody else's data, and to the victim's receiver it is simply noise. That is
why it enters the link budget as a variance rather than as a tap, and why the
only place to fix it is the board.

The coupling itself comes out of the same two matrices as everything else. If
the mutual inductance and mutual capacitance are in the same ratio to their
self terms, the two contributions to forward coupling cancel exactly and there
is no far-end crosstalk at all. That happens whenever the dielectric is
uniform, which is to say in stripline, and it is why the near-end and far-end
pictures look so different on inner and outer layers.
"""

import numpy as np

C0 = 299792458.0
INCH = 0.0254


def coefficients(modal):
    """Backward and forward coupling coefficients from the modal parameters.

        Kb = (1/4) (Lm/L + Cm/C)        near end, saturating
        Kf = -(1/2) (Lm/L - Cm/C)       far end, per unit of delay

    The near-end coefficient adds the two couplings and the far-end one
    subtracts them, which is the whole story: uniform dielectric means the
    difference vanishes and stripline has no far-end crosstalk.
    """
    lm, ls = modal['Lm'], modal['Ls']
    cm, cs = modal['Cm'], modal['Cs']
    kb = 0.25 * (lm / ls + cm / cs)
    kf = -0.5 * (lm / ls - cm / cs)
    return dict(kb=float(kb), kf=float(kf),
                lm_over_l=float(lm / ls), cm_over_c=float(cm / cs))


def next_fext(modal, length_in, tr_ps, er=3.7, v_swing=1.0):
    """Near- and far-end crosstalk amplitudes for a given coupled length.

    Near-end crosstalk saturates: once the coupled section is long enough that
    the backward wave from the far end is still arriving when the edge finishes,
    making it longer adds nothing. The saturation length is the distance the
    edge covers in half its own rise time.

    Far-end crosstalk does not saturate. It grows in proportion to length and
    in inverse proportion to rise time, so it is the one that gets worse as
    edges get faster.
    """
    c = coefficients(modal)
    v = C0 / np.sqrt(er)
    tpd = INCH / v
    tr = tr_ps * 1e-12
    l_sat_in = tr * v / 2.0 / INCH
    next_amp = c['kb'] * v_swing
    if length_in < l_sat_in:
        next_amp *= length_in / l_sat_in
    fext_amp = c['kf'] * (length_in * tpd) / tr * v_swing
    return dict(next_v=float(next_amp), fext_v=float(fext_amp),
                next_pct=float(100 * next_amp / v_swing),
                fext_pct=float(100 * fext_amp / v_swing),
                saturation_length_in=float(l_sat_in),
                saturated=bool(length_in >= l_sat_in),
                next_duration_ps=float(2 * length_in * tpd * 1e12),
                **c)


def spacing_sweep(b_mm=0.4, er=3.7, z_target=100.0, w_over_s=None,
                  length_in=6.0, tr_ps=20.0, use_solver=False):
    """Test the three-widths rule against the arithmetic.

    Layout guidelines are usually stated as a multiple of the trace width --
    keep neighbours three widths away, or five. The rule is worth testing,
    because what actually sets the coupling is the spacing relative to the
    dielectric height, not relative to the trace width, and the two differ as
    soon as the stackup changes.
    """
    from .diffpair import solve_for_zdiff, pair_from_cohn
    base = solve_for_zdiff(0.60, b_mm, er, z_target, use_solver=use_solver)
    w = base['w_solved_mm']
    if w_over_s is None:
        w_over_s = [1, 1.5, 2, 3, 4, 5, 6, 8]
    rows = []
    for k in w_over_s:
        s = k * w
        m = (pair_from_cohn(w, s, b_mm, er) if not use_solver
             else None)
        if m is None:
            from .diffpair import pair_from_geometry
            m = pair_from_geometry(w, s, b_mm, er)
        nf = next_fext(m, length_in, tr_ps, er)
        rows.append(dict(spacing_w=float(k), s_mm=float(s),
                         s_over_h=float(s / (b_mm / 2)),
                         next_pct=nf['next_pct'], fext_pct=nf['fext_pct'],
                         next_db=float(20 * np.log10(max(nf['next_pct'] / 100, 1e-12))),
                         kb=nf['kb'], kf=nf['kf']))
    return dict(trace_w_mm=float(w), b_mm=b_mm, rows=rows,
                length_in=length_in, tr_ps=tr_ps)


def guard_trace(w_mm=0.18, s_mm=0.25, b_mm=0.4, er=3.7, guard_w_mm=0.18,
                cell=0.005, grounded=True):
    """A guard trace between two signals, solved rather than assumed.

    A grounded guard trace works only if it is actually grounded -- stitched to
    the reference planes often enough that it cannot support a standing wave of
    its own. A guard that is grounded at its two ends and nowhere else is a
    resonator, and between its resonances it couples the two signals together
    rather than isolating them.

    The solver is given three conductors, so the guard is treated as a
    conductor with its own charge rather than as a wall.
    """
    from .fdm2d import CrossSection, rlgc, modal
    W = 12 * b_mm
    cs = CrossSection(W, b_mm, cell)
    cs.dielectric(0, W, 0, b_mm, er)
    yc = b_mm / 2.0
    t = 0.018
    pitch = s_mm + w_mm
    x0 = W / 2 - pitch
    cs.conductor(x0 - w_mm / 2, x0 + w_mm / 2, yc, yc + t, 1)
    x2 = W / 2 + pitch
    cs.conductor(x2 - w_mm / 2, x2 + w_mm / 2, yc, yc + t, 2)
    if guard_w_mm > 0:
        if grounded:
            cs.conductor(W / 2 - guard_w_mm / 2, W / 2 + guard_w_mm / 2,
                         yc, yc + t, -1)      # tied to the planes
        else:
            cs.conductor(W / 2 - guard_w_mm / 2, W / 2 + guard_w_mm / 2,
                         yc, yc + t, 3)       # floating: its own conductor
    C, L = rlgc(cs)
    m = modal(C, L)
    return m


def guard_comparison(w_mm=0.18, s_mm=0.25, b_mm=0.4, er=3.7, length_in=6.0,
                     tr_ps=20.0):
    """Coupling with no guard, a grounded guard, and a floating guard."""
    from .diffpair import pair_from_geometry
    pitch = 2 * (s_mm + w_mm)
    out = {}
    none = pair_from_geometry(w_mm, pitch - w_mm, b_mm, er)
    out['no guard'] = next_fext(none, length_in, tr_ps, er)
    out['grounded guard'] = next_fext(
        guard_trace(w_mm, s_mm, b_mm, er, w_mm, grounded=True),
        length_in, tr_ps, er)
    out['floating guard'] = next_fext(
        guard_trace(w_mm, s_mm, b_mm, er, w_mm, grounded=False),
        length_in, tr_ps, er)
    return out


def power_sum(amplitudes):
    """Combine uncorrelated aggressors. Independent sources add in power."""
    a = np.asarray(amplitudes, float)
    return float(np.sqrt(np.sum(a * a)))


def icn(next_list, fext_list, v_swing=1.0):
    """Integrated crosstalk noise, as a root-sum-square of all aggressors.

    The standards define ICN as a weighted integral of the crosstalk transfer
    functions against the spectrum of the transmitted signal and the response
    of a reference receiver. The version here is the same idea reduced to its
    essentials: aggressors are uncorrelated with each other and with the
    victim, so their contributions add in power, and the result is a
    root-mean-square voltage that enters the noise budget beside receiver
    noise rather than beside intersymbol interference.
    """
    tot = power_sum(list(next_list) + list(fext_list))
    return dict(icn_v=float(tot), icn_mv=float(tot * 1000),
                icn_pct=float(100 * tot / v_swing),
                n_aggressors=len(next_list) + len(fext_list),
                next_part_mv=float(power_sum(next_list) * 1000),
                fext_part_mv=float(power_sum(fext_list) * 1000))


def budget_impact(icn_mv, sigma_other_mv, cursor_mv, target_q=7.035):
    """What the crosstalk costs the link budget, in decibels of margin.

    Crosstalk cannot be equalised, so it adds in quadrature to the other noise
    terms and shows up directly as a reduction in the ratio the budget is
    built on. Expressing it in decibels makes it comparable with the remedies
    priced in SerDes_Equalisation.
    """
    s_without = sigma_other_mv
    s_with = np.sqrt(sigma_other_mv ** 2 + icn_mv ** 2)
    q_without = cursor_mv / s_without
    q_with = cursor_mv / s_with
    return dict(q_without=float(q_without), q_with=float(q_with),
                margin_lost_db=float(20 * np.log10(q_without / q_with)),
                sigma_without_mv=float(s_without), sigma_with_mv=float(s_with),
                meets_target_without=bool(q_without >= target_q),
                meets_target_with=bool(q_with >= target_q))
