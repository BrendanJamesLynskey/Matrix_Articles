"""Jitter -- the model behind deck 08.

Jitter is the part of the budget where the vocabulary does the most damage.
The same word covers a bounded effect that is a deterministic function of the
data, an unbounded effect that is Gaussian and never stops growing, and a
periodic effect that comes from somewhere else on the board entirely; they are
added in different ways, they are measured differently, and confusing them
produces a budget that passes on the bench and fails in the field.

A terminology collision worth flagging before it bites: the Q in this deck is
the argument of the error function, a signal-to-noise ratio in units of
standard deviations, and it has nothing to do with the Q of a resonator, which
is a ratio of stored to dissipated energy. The two meet -- the tank Q of an
oscillator sets its phase noise, which becomes the random jitter, which sets
the communications Q -- and an engineer working across both will meet them in
the same sentence. They are different quantities with the same letter.

The deck's central computed claim is that extrapolating a bathtub curve
measured at an error ratio of 1e-6 out to 1e-12 is safe only if the jitter
really is the sum of one Gaussian and one bounded term. When it is not --
when there are two Gaussians of different width, which is what a crosstalk
aggressor or a marginal supply produces -- the extrapolation understates the
true eye closure, and `extrapolation_error()` measures by how much.
"""

import numpy as np


def erfc(x):
    """Abramowitz and Stegun 7.1.26, adequate for a bit-error-ratio readout."""
    x = np.asarray(x, float)
    z = np.abs(x)
    t = 1.0 / (1.0 + 0.5 * z)
    y = t * np.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196
        + t * (0.09678418 + t * (-0.18628806 + t * (0.27886807
        + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223
        + t * 0.17087277))))))))) 
    return np.where(x >= 0, y, 2.0 - y)


def q_from_ber(ber):
    """Invert 0.5 erfc(Q/sqrt2) = BER by bisection."""
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 0.5 * erfc(mid / np.sqrt(2)) > ber:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ber_from_q(q):
    return 0.5 * erfc(np.asarray(q, float) / np.sqrt(2))


# ------------------------------------------------------------ dual-Dirac ----

def dual_dirac(rj_rms_ps, dj_pp_ps, ber=1e-12):
    """Total jitter at a specified error ratio, by the dual-Dirac convention.

        TJ(BER) = DJ_pp + 2 Q(BER) RJ_rms

    The model replaces whatever the deterministic distribution really is with
    two impulses separated by DJ_pp, each convolved with the Gaussian. It is a
    convention for reporting, not a description of the physics, and it is exact
    only in the tails -- which is, admittedly, where the budget lives.
    """
    q = q_from_ber(ber)
    return dict(q=float(q), rj_rms_ps=rj_rms_ps, dj_pp_ps=dj_pp_ps,
                tj_pp_ps=float(dj_pp_ps + 2 * q * rj_rms_ps),
                ber=ber,
                rj_part_ps=float(2 * q * rj_rms_ps))


def bathtub(rj_rms_ps, dj_pp_ps, ui_ps, n=600, rj2_rms_ps=None, w2=0.0):
    """Bit-error ratio against sampling position across the unit interval.

    With one Gaussian the curve is a pair of complementary error functions and
    its tails are straight on a logarithmic axis. Mixing in a second, wider
    Gaussian with weight w2 -- which is what an intermittent aggressor looks
    like -- leaves the curve almost unchanged near the middle and bends it
    upward far out, which is exactly where a measurement cannot reach.
    """
    t = np.linspace(0, ui_ps, n)
    left_edge = dj_pp_ps / 2.0
    right_edge = ui_ps - dj_pp_ps / 2.0

    def side(d):
        a = 0.5 * erfc(d / (rj_rms_ps * np.sqrt(2)))
        if rj2_rms_ps and w2 > 0:
            b = 0.5 * erfc(d / (rj2_rms_ps * np.sqrt(2)))
            return (1 - w2) * a + w2 * b
        return a

    ber = 0.5 * (side(t - left_edge) + side(right_edge - t))
    ber = np.clip(ber, 1e-30, 0.5)
    return dict(t_ps=t.tolist(), ber=ber.tolist(), ui_ps=ui_ps)


def eye_opening(bath, ber_target=1e-12):
    """Horizontal opening at a target error ratio, in picoseconds and in UI."""
    t = np.asarray(bath['t_ps']); b = np.asarray(bath['ber'])
    ok = t[b <= ber_target]
    if ok.size == 0:
        return dict(opening_ps=0.0, opening_ui=0.0, closed=True)
    op = float(ok.max() - ok.min())
    return dict(opening_ps=op, opening_ui=float(op / bath['ui_ps']),
                closed=False)


def extrapolation_error(rj_rms_ps=0.8, dj_pp_ps=12.0, ui_ps=35.7,
                        rj2_rms_ps=3.0, w2=1e-8, ber_meas=1e-6,
                        ber_target=1e-12):
    """What a dual-Dirac fit at a measurable error ratio misses.

    The instrument can only reach an error ratio it has time to observe. The
    standard practice is to fit the dual-Dirac model there and extrapolate. If
    the real distribution has a second, rarer Gaussian component, the fit sees
    almost none of it and the extrapolation is optimistic.
    """
    true_b = bathtub(rj_rms_ps, dj_pp_ps, ui_ps, 2000, rj2_rms_ps, w2)
    t = np.asarray(true_b['t_ps']); b = np.asarray(true_b['ber'])

    # fit a single-Gaussian dual-Dirac to the left flank at the measurable level
    left = t < ui_ps / 2
    tl, bl = t[left], b[left]
    # Fit only over the range an instrument can actually reach in a sane
    # observation time. Fitting down to error ratios nobody measured would
    # quietly give the model the very information the experiment cannot have,
    # which is the whole point at issue.
    pts = [(ti, bi) for ti, bi in zip(tl, bl) if ber_meas <= bi < 1e-4]
    if len(pts) < 5:
        return dict(ok=False)
    xs = np.array([q_from_ber(p[1]) for p in pts])
    ys = np.array([p[0] for p in pts])
    a, c = np.polyfit(xs, ys, 1)        # t = a*Q + c  ->  a is -RJ
    rj_fit = abs(a)
    q_t = q_from_ber(ber_target)
    pred_left = c - rj_fit * q_t if a < 0 else c + rj_fit * q_t
    pred_open = ui_ps - 2 * abs(pred_left)

    meas = eye_opening(true_b, ber_meas)
    truth = eye_opening(true_b, ber_target)
    true_open = truth['opening_ps']
    closed = true_open <= 1e-9
    return dict(true_eye_closed=bool(closed),
                ratio_predicted_to_true=(None if closed else
                                         float(max(pred_open, 0.0) / true_open)),
                rj_fitted_ps=float(rj_fit), rj_true_ps=rj_rms_ps,
                rj2_true_ps=rj2_rms_ps, weight2=w2,
                opening_at_meas_ps=meas['opening_ps'],
                opening_true_ps=truth['opening_ps'],
                opening_predicted_ps=float(max(pred_open, 0.0)),
                overestimate_ps=float(max(pred_open, 0.0) - truth['opening_ps']),
                overestimate_pct=(None if closed else
                                  float(100 * (max(pred_open, 0.0) - true_open)
                                        / true_open)),
                ber_meas=ber_meas, ber_target=ber_target)


# ------------------------------------------------------- phase noise --------

def phase_noise_profile(f, f_corner=200e3, l_white_dbc=-140.0,
                        f_offset_ref=1e6, l_ref_dbc=-120.0, spur=None):
    """A simple oscillator phase-noise profile in dBc/Hz.

    One region falling at 30 dB per decade from flicker noise, one at 20 dB per
    decade from the white noise of the resonator, and a floor. A spur may be
    added, because in practice the tone from the switching regulator is often
    the largest single contributor.
    """
    f = np.asarray(f, float)
    l20 = l_ref_dbc + 20 * np.log10(f_offset_ref / f)
    l30 = l_ref_dbc + 20 * np.log10(f_offset_ref / f_corner) \
        + 30 * np.log10(f_corner / f)
    l = np.where(f < f_corner, l30, l20)
    l = np.maximum(l, l_white_dbc)
    if spur:
        for fs, amp in spur:
            i = int(np.argmin(np.abs(f - fs)))
            l[i] = max(l[i], amp)
    return l


def integrate_phase_noise(f, l_dbc, f_carrier, f_lo=1e4, f_hi=1e8):
    """Root-mean-square jitter from a phase-noise profile.

    The mean-square phase is twice the integral of the single-sideband noise
    over the offset band, and dividing by the carrier's angular frequency turns
    radians into seconds. The integration limits are a choice, not a property
    of the oscillator: a clock recovery loop tracks slow phase and rejects it,
    so the lower limit belongs to the receiver, not to the transmitter.
    """
    f = np.asarray(f, float)
    m = (f >= f_lo) & (f <= f_hi)
    lin = 10 ** (np.asarray(l_dbc, float)[m] / 10.0)
    phi2 = 2.0 * np.trapezoid(lin, f[m])
    phi_rms = np.sqrt(phi2)
    return dict(phi_rms_rad=float(phi_rms),
                jitter_rms_s=float(phi_rms / (2 * np.pi * f_carrier)),
                jitter_rms_fs=float(1e15 * phi_rms / (2 * np.pi * f_carrier)),
                f_lo=f_lo, f_hi=f_hi)


def integration_limits_matter(f_carrier=14e9):
    """The same oscillator, integrated over different bands."""
    f = np.logspace(3, 9, 3000)
    l = phase_noise_profile(f)
    out = []
    for lo, hi, name in ((1e3, 1e9, 'everything'),
                         (1e4, 1e8, 'the usual 10 kHz to 100 MHz'),
                         (1e5, 1e8, 'above a 100 kHz loop'),
                         (4e6, 1e9, 'above a 4 MHz clock recovery loop')):
        r = integrate_phase_noise(f, l, f_carrier, lo, hi)
        out.append(dict(band=name, f_lo=lo, f_hi=hi,
                        jitter_rms_fs=r['jitter_rms_fs']))
    return dict(rows=out, f_carrier=f_carrier,
                f_hz=f.tolist(), l_dbc=l.tolist())


# --------------------------------------------------- data-dependent jitter --

def ddj_from_pulse(pulse, samples_per_ui, cursor_index, depth=6, n_patterns=None):
    """Data-dependent jitter extracted from a channel's pulse response.

    Every pattern of preceding bits shifts the zero crossing by a different
    amount, because the tails of earlier pulses are still present when the
    current edge happens. Enumerating the patterns and finding the crossing for
    each gives the spread directly, and shows that this part of the jitter is
    not random at all -- it is a deterministic function of the data, which is
    why an equaliser removes it and a better oscillator does not.
    """
    p = np.asarray(pulse, float)
    m = samples_per_ui
    n = 2 ** depth if n_patterns is None else n_patterns
    crossings = []
    for k in range(n):
        bits = [(k >> i) & 1 for i in range(depth)]
        wave = np.zeros_like(p)
        for i, b in enumerate(bits):
            sh = (i + 1) * m
            s = (1 if b else -1)
            if sh < len(p):
                wave[sh:] += s * p[:len(p) - sh]
        wave = wave + p                       # the edge under test
        lo = max(cursor_index - 2 * m, 1)
        hi = min(cursor_index, len(wave) - 1)
        seg = wave[lo:hi]
        sgn = np.sign(seg)
        idx = np.nonzero(np.diff(sgn) != 0)[0]
        if idx.size:
            i0 = idx[-1]
            y0, y1 = seg[i0], seg[i0 + 1]
            frac = -y0 / (y1 - y0) if (y1 - y0) != 0 else 0.0
            crossings.append(lo + i0 + frac)
    if not crossings:
        return dict(ok=False)
    c = np.array(crossings)
    return dict(ok=True, n_patterns=len(c),
                spread_samples=float(c.max() - c.min()),
                spread_ui=float((c.max() - c.min()) / m),
                std_ui=float(np.std(c) / m))


# ------------------------------------------------------------ the CDR -------

def cdr_transfer(f, bw_hz=4e6, zeta=1.0):
    """Jitter transfer and error response of a second-order clock recovery loop.

    The recovered clock follows slow phase movement and ignores fast movement,
    so jitter transfer is a low-pass and the error -- what the sampler actually
    sees -- is its high-pass complement. Slow jitter is therefore harmless and
    fast jitter is not, which is why a jitter number quoted without the band it
    was measured over means very little.
    """
    f = np.asarray(f, float)
    wn = 2 * np.pi * bw_hz
    s = 1j * 2 * np.pi * f
    h = (2 * zeta * wn * s + wn ** 2) / (s ** 2 + 2 * zeta * wn * s + wn ** 2)
    return dict(f_hz=f.tolist(), jitter_transfer_db=(20 * np.log10(np.abs(h))).tolist(),
                error_db=(20 * np.log10(np.abs(1 - h) + 1e-18)).tolist())


def jitter_tolerance(f=None, bw_hz=4e6, zeta=1.0, budget_ui=0.15,
                     max_ui=15.0):
    """How much sinusoidal jitter the receiver survives at each frequency.

    Only the part of an applied jitter tone that the loop fails to track
    reaches the sampler, so the tolerance is the budget divided by the
    magnitude of the error response. Below the loop bandwidth that magnitude is
    small and the tolerance rises as the square of the period, which is the
    characteristic slope of every published tolerance mask.
    """
    if f is None:
        f = np.logspace(3, 9, 400)
    t = cdr_transfer(f, bw_hz, zeta)
    err = 10 ** (np.asarray(t['error_db']) / 20.0)
    tol = np.minimum(budget_ui / np.maximum(err, 1e-12), max_ui)
    return dict(f_hz=np.asarray(f).tolist(), tol_ui=tol.tolist(),
                bw_hz=bw_hz, budget_ui=budget_ui,
                corner_hz=float(bw_hz))


# ==========================================================================
# The material below follows Ransom Stephens's treatment, whose organising
# idea is that jitter analysis exists to predict a bit error ratio and that
# almost every practical difficulty comes from forgetting it. Four of his
# points are computed here rather than quoted: how long a real measurement
# takes, how far the dual-Dirac deterministic jitter sits from the actual
# peak-to-peak value, how readily deterministic jitter is mistaken for random
# jitter, and how amplitude noise becomes jitter through the slew rate.
# ==========================================================================

def bert_time(ber, rate_gbps, confidence_bits=10.0):
    """How long a bit error ratio tester needs to measure down to `ber`.

    Observing an error ratio requires seeing errors, and seeing enough of them
    to believe the number requires roughly `confidence_bits` divided by the
    ratio. That is the arithmetic behind Stephens's second rule: total jitter
    at a low error ratio can only be *measured* on a bit error ratio tester,
    and everything an oscilloscope reports is an estimate.
    """
    bits = confidence_bits / ber
    secs = bits / (rate_gbps * 1e9)
    return dict(ber=ber, rate_gbps=rate_gbps, bits=float(bits),
                seconds=float(secs), minutes=float(secs / 60),
                hours=float(secs / 3600), days=float(secs / 86400),
                one_error_every_s=float(1.0 / (ber * rate_gbps * 1e9)))


def ddj_crossings(pulse, samples_per_ui, cursor_index, depth=8):
    """Every zero crossing the data pattern can produce, in unit intervals.

    This is the true data-dependent jitter distribution for a pattern depth,
    computed from the channel's own pulse response rather than assumed. It is
    emphatically not two delta functions, which is what makes it the right
    thing to test the dual-Dirac model against.
    """
    p = np.asarray(pulse, float)
    m = samples_per_ui
    out = []
    for k in range(2 ** depth):
        bits = [(k >> i) & 1 for i in range(depth)]
        wave = p.copy()
        for i, b in enumerate(bits):
            sh = (i + 1) * m
            if sh < len(p):
                wave[sh:] += (1 if b else -1) * p[:len(p) - sh]
        lo = max(cursor_index - 2 * m, 1)
        hi = min(cursor_index, len(wave) - 1)
        seg = wave[lo:hi]
        idx = np.nonzero(np.diff(np.sign(seg)) != 0)[0]
        if idx.size:
            i0 = idx[-1]
            y0, y1 = seg[i0], seg[i0 + 1]
            frac = -y0 / (y1 - y0) if (y1 - y0) != 0 else 0.0
            out.append((lo + i0 + frac) / m)
    c = np.array(out)
    if c.size == 0:
        return dict(ok=False)
    c = c - np.mean(c)
    return dict(ok=True, crossings_ui=c, n=int(c.size),
                pp_ui=float(c.max() - c.min()), std_ui=float(np.std(c)))


def ber_from_distribution(crossings_ui, rj_rms_ui, ui_ps, n=1400,
                          span_ui=1.0):
    """Bit error ratio against sampling position, from a real jitter pdf.

    The deterministic crossings are treated as equally likely and each is
    convolved with the Gaussian random part, which is the honest calculation
    the dual-Dirac model approximates.
    """
    c = np.asarray(crossings_ui, float)
    t = np.linspace(-0.5 * span_ui, 0.5 * span_ui, n)
    left = np.zeros(n)
    right = np.zeros(n)
    for x in c:
        left += 0.5 * erfc((t - x) / (rj_rms_ui * np.sqrt(2)))
        right += 0.5 * erfc(((1.0 + x) - t) / (rj_rms_ui * np.sqrt(2)))
    left /= c.size
    right /= c.size
    ber = 0.5 * (left + right)
    return dict(t_ui=t, ber=np.clip(ber, 1e-30, 1.0),
                left=np.clip(left, 1e-30, 1.0),
                right=np.clip(right, 1e-30, 1.0), ui_ps=ui_ps)


def q_scale(t_ui, ber_side):
    """Convert one flank of a bathtub to the Q scale.

    Replacing log(BER) with Q(BER) on the vertical axis turns a pure Gaussian
    tail into a straight line, which is what makes the dual-Dirac fit a
    straight-line fit: the slope is the random jitter and the intercept is the
    model's deterministic jitter. It also makes a non-Gaussian tail obvious by
    inspection, which a logarithmic axis does not.
    """
    b = np.asarray(ber_side, float)
    m = (b > 1e-30) & (b < 0.4)
    q = np.array([q_from_ber(v) for v in b[m]])
    return np.asarray(t_ui)[m], q


def dual_dirac_vs_true(crossings_ui, rj_rms_ui, ui_ps, ber_fit=(1e-9, 1e-4),
                       ber_target=1e-12):
    """Fit the dual-Dirac model to a real jitter distribution and compare.

    The headline comparison of the model's limits. The deterministic jitter
    the dual-Dirac fit reports is a parameter of the fit, obtained by
    extrapolating the Gaussian tails back to where they would have come from
    if the deterministic distribution really were two impulses. The actual
    peak-to-peak spread of the deterministic distribution is a different
    quantity and is larger; Stephens writes them DJ(dd) and DJ(p-p) and is
    emphatic that confusing them is the commonest error in the field.
    """
    d = ber_from_distribution(crossings_ui, rj_rms_ui, ui_ps)
    t, left = d['t_ui'], d['left']
    m = (left >= ber_fit[0]) & (left <= ber_fit[1])
    if m.sum() < 5:
        return dict(ok=False)
    q = np.array([q_from_ber(v) for v in left[m]])
    # t = -sigma*Q + mu_L  on the left flank
    a, b0 = np.polyfit(q, t[m], 1)
    sigma_fit = abs(a)
    mu_l = b0
    dj_dd = 2.0 * abs(mu_l)          # symmetric distribution: |mu_L - mu_R|
    c = np.asarray(crossings_ui, float)
    dj_pp = float(c.max() - c.min())
    qt = q_from_ber(ber_target)
    tj_dd = dj_dd + 2 * qt * sigma_fit
    # true total jitter at the target, read off the computed curve
    ok = t[(d['ber'] <= ber_target)]
    tj_true = 1.0 - float(ok.max() - ok.min()) if ok.size else 1.0
    return dict(ok=True,
                rj_true_ui=float(rj_rms_ui), rj_fitted_ui=float(sigma_fit),
                rj_inflation=float(sigma_fit / rj_rms_ui),
                dj_dd_ui=float(dj_dd), dj_pp_ui=float(dj_pp),
                dj_ratio=float(dj_dd / dj_pp) if dj_pp else None,
                tj_dual_dirac_ui=float(tj_dd), tj_true_ui=float(tj_true),
                tj_err_pct=float(100 * (tj_dd / tj_true - 1)) if tj_true else None,
                ui_ps=ui_ps, ber_target=ber_target, ber_fit=list(ber_fit))


def rj_contamination(rj_rms_ui=0.02, dj_shape='uniform', dj_pp_ui=0.25,
                     ui_ps=35.71, ber_fit=(1e-9, 1e-4), n_dj=64):
    """How much a deterministic distribution inflates the fitted random jitter.

    A fit to the tails cannot tell whether width comes from the Gaussian or
    from a deterministic distribution that happens to be smooth. The more the
    deterministic part resembles a Gaussian, the more of it is counted as
    random -- and random jitter is multiplied by fourteen at an error ratio of
    1e-12 while deterministic jitter is not, so the mistake is expensive in
    exactly one direction.
    """
    if dj_shape == 'dual_dirac':
        c = np.array([-dj_pp_ui / 2, dj_pp_ui / 2])
    elif dj_shape == 'uniform':
        c = np.linspace(-dj_pp_ui / 2, dj_pp_ui / 2, n_dj)
    elif dj_shape == 'gaussian_like':
        u = np.linspace(-2.2, 2.2, n_dj)
        c = (dj_pp_ui / 2) * u / 2.2
        w = np.exp(-0.5 * u ** 2)
        c = np.repeat(c, np.maximum(1, (w * 12).astype(int)))
    else:
        c = np.array([0.0])
    r = dual_dirac_vs_true(c, rj_rms_ui, ui_ps, ber_fit)
    if not r.get('ok'):
        return dict(ok=False)
    r['dj_shape'] = dj_shape
    return r


# ------------------------------------------- rule four: the other dimension --

def amplitude_to_jitter(dv_mv, slew_mv_per_ps):
    """Timing error produced by a voltage disturbance, through the slew rate.

    Stephens's fourth rule is that timing noise and amplitude noise are not
    really separable. The conversion is geometric and immediate: a signal
    displaced vertically by dV crosses its threshold earlier or later by
    dV divided by the slope it crosses at.

    The consequence is that the separation gets worse as edges get faster in
    absolute terms but the unit interval shrinks faster still, which is why he
    puts the breakdown somewhere around ten gigabits per second.
    """
    if slew_mv_per_ps <= 0:
        return float('nan')
    return float(dv_mv / slew_mv_per_ps)


def slew_from_pulse(pulse, samples_per_ui, ui_ps, amp_mv=400.0):
    """Slew rate at the zero crossing of a channel's own pulse response."""
    p = np.asarray(pulse, float)
    m = samples_per_ui
    pk = int(np.argmax(np.abs(p)))
    lo = max(pk - 2 * m, 1)
    seg = p[lo:pk]
    idx = np.nonzero(np.diff(np.sign(seg)) != 0)[0]
    i0 = (lo + idx[-1]) if idx.size else max(pk - m, 1)
    dt_ps = ui_ps / m
    d = (p[i0 + 1] - p[i0 - 1]) / (2 * dt_ps)
    return dict(slew_mv_per_ps=float(abs(d) * amp_mv / max(abs(p[pk]), 1e-12)),
                crossing_index=int(i0),
                rise_time_ps=float(0.8 * amp_mv /
                                   max(abs(d) * amp_mv /
                                       max(abs(p[pk]), 1e-12), 1e-12)))


def crosstalk_jitter(xt_mv_rms, slew_mv_per_ps, ui_ps, n_sigma=7.0):
    """Crosstalk expressed as jitter rather than as voltage.

    Crosstalk is the canonical bounded uncorrelated jitter: it is not random,
    because it is a deterministic function of somebody else's data; it is not
    data-dependent, because that data is not the victim's; and it is bounded,
    because the aggressor's swing is. Converting it through the slew rate puts
    it on the same axis as everything else in the budget and shows why a
    crosstalk problem so often presents as a jitter problem.
    """
    rms_ps = amplitude_to_jitter(xt_mv_rms, slew_mv_per_ps)
    return dict(xt_mv_rms=xt_mv_rms, slew_mv_per_ps=slew_mv_per_ps,
                jitter_rms_ps=float(rms_ps),
                jitter_pp_ps=float(n_sigma * rms_ps),
                jitter_rms_ui=float(rms_ps / ui_ps),
                jitter_pp_ui=float(n_sigma * rms_ps / ui_ps),
                n_sigma=n_sigma)


def separability(rows):
    """Summarise where treating jitter and voltage noise separately fails.

    `rows` must come from `sparam_qc.separability_from_channel`, which measures
    the received amplitude and the slew rate at the crossing on a real channel
    for each symbol rate. Doing it that way matters: assuming instead that the
    edge is a fixed fraction of the unit interval makes the amplitude-induced
    jitter a constant fraction of the interval at every rate, which is both
    wrong and vacuous.

    What actually happens is that the channel, not the transmitter, sets the
    received edge. Its bandwidth does not improve because the data rate went
    up, so as the interval shrinks the edge occupies more of it and the
    received amplitude falls as well. The slew rate therefore stops improving
    and eventually worsens, while the interval keeps shrinking -- so the jitter
    a fixed receiver voltage noise produces grows as a fraction of the
    interval. That is the quantitative form of Stephens's fourth rule.
    """
    out = []
    for r in rows:
        out.append(dict(r))
    base = out[0]['jitter_rms_ui'] if out else 1.0
    for r in out:
        r['relative_to_slowest'] = float(r['jitter_rms_ui'] / base) if base else None
    return dict(rows=out)
