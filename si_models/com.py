"""Channel operating margin and compliance -- the model behind deck 11.

A standard has to decide whether a channel is legal without knowing which
transceiver will be plugged into it. It cannot simulate the real receiver,
because the real receiver is proprietary and has not been designed yet, so it
defines a *reference* receiver, runs it against the measured S-parameters and
reports a single number. That number is the channel operating margin, and this
file computes one.

What is implemented here is a scoped version, and the scope is stated rather
than glossed: a three-tap transmit equaliser chosen from a grid, a
continuous-time equaliser chosen from a grid, a decision-feedback section of
limited length and limited tap magnitude, optimisation over sampling phase, and
noise terms for residual intersymbol interference, crosstalk, jitter and the
receiver's own noise combined as a root sum of squares. The published method in
IEEE 802.3 annex 93A convolves probability distributions instead of adding
variances, includes explicit transmitter and package models, and applies a
detailed set of masks. The difference matters for a certification laboratory
and does not change the argument this deck is making.

The argument is that a compliance verdict is a function of the reference
receiver's assumptions as much as of the channel, and `sensitivity()` shows
how much the same channel's margin moves when those assumptions are varied
within the range real silicon actually spans.
"""

import numpy as np


def _lin(db):
    return 10 ** (np.asarray(db, float) / 20.0)


def ctle_response(f, fz_ghz, fp1_ghz, fp2_ghz, dc_gain_db, f_norm_ghz=None):
    """A one-zero two-pole continuous-time equaliser.

    The setting moves the zero and with it the amount of low-frequency
    attenuation; it does not change the overall level, because every real
    receiver follows its equaliser with a gain stage that restores the
    amplitude. The response is therefore normalised to unit gain at the
    normalising frequency -- Nyquist by default -- so that stepping through the
    settings trades shape against shape rather than quietly turning the signal
    down, which would make the flattest setting win on any signal-to-noise
    measure for the wrong reason.
    """
    f = np.asarray(f, float)
    s = 1j * 2 * np.pi * f
    wz = 2 * np.pi * fz_ghz * 1e9
    w1 = 2 * np.pi * fp1_ghz * 1e9
    w2 = 2 * np.pi * fp2_ghz * 1e9
    g = _lin(dc_gain_db)
    h = g * (1 + s / wz) / ((1 + s / w1) * (1 + s / w2))
    if f_norm_ghz:
        ref = np.interp(f_norm_ghz * 1e9, f, np.abs(h))
        if ref > 0:
            h = h / ref
    return h


def _pulse(s21, M, NFFT):
    full = np.concatenate([s21, np.conj(s21[-2:0:-1])])
    imp = np.real(np.fft.ifft(full))
    return np.convolve(imp, np.ones(M))[:NFFT]


def _sample(pulse, M, phase, n_pre=8, n_post=40):
    v = pulse[phase::M]
    k = int(np.argmax(np.abs(v)))
    lo, hi = max(k - n_pre, 0), min(k + n_post + 1, len(v))
    return v[lo:hi].copy(), k - lo


def apply_tx_ffe(taps, cursor, c):
    """Convolve a transmit feed-forward equaliser into the sampled response."""
    out = np.convolve(taps, c)
    return out, cursor + int(np.argmax(np.abs(c)))


def com(channel, fb=28e9, n_dfe=5, dfe_limit=0.5, tx_presets=None,
        ctle_grid=None, sigma_rx_mv=1.8, sigma_xt_mv=3.0, rj_fs=350.0,
        amp_mv=400.0, n_phase=8, a_dd=0.02):
    """Compute a channel operating margin for a two-port channel.

    The reference receiver is optimised over its own settings, because that is
    what a real receiver's adaptation does and a standard that assumed a fixed
    setting would fail channels that work. The margin reported is the ratio of
    the available signal to the total noise, in decibels.
    """
    f = channel['f']
    M, NFFT = channel['M'], channel['NFFT']
    ui = 1.0 / fb

    if tx_presets is None:
        tx_presets = [(0.0, 1.0, 0.0), (-0.05, 0.90, -0.05),
                      (-0.10, 0.80, -0.10), (-0.15, 0.75, -0.10),
                      (0.0, 0.85, -0.15), (0.0, 0.75, -0.25),
                      (-0.20, 0.70, -0.10)]
    if ctle_grid is None:
        ctle_grid = [(-db, 13.0, 24.0, db) for db in
                     (0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0)]

    best = None
    for gdc in ctle_grid:
        # a deeper setting pulls the zero down in frequency, which is what
        # attenuates the low frequencies the equaliser is trying to suppress
        boost = abs(gdc[3])
        fz = max(fb / 1e9 / 2.0 / (1.0 + boost / 2.0), 0.3)
        h_ct = ctle_response(f, fz, gdc[1], gdc[2], -boost,
                             f_norm_ghz=fb / 2e9)
        s_eq = channel['s21'] * h_ct
        p = _pulse(s_eq, M, NFFT)
        for phase in range(0, M, max(1, M // n_phase)):
            taps0, cur0 = _sample(p, M, phase)
            for pre, main, post in tx_presets:
                c = np.array([pre, main, post], float)
                taps, cur = apply_tx_ffe(taps0, cur0, c)
                if cur >= len(taps):
                    continue
                h0 = taps[cur]
                if abs(h0) < 1e-9:
                    continue
                fb_idx = set(range(cur + 1, min(cur + 1 + n_dfe, len(taps))))
                # Statistical, not worst case. The data is random, so each
                # residual tap contributes +v or -v with equal probability and
                # the variances add; summing magnitudes instead would price a
                # pattern that occurs once in 2^40 symbols as though it were
                # the normal case, which is what peak-distortion analysis does
                # and why it disagrees so violently with measurement.
                acc = 0.0
                for k in range(len(taps)):
                    if k == cur:
                        continue
                    v = taps[k]
                    if k in fb_idx:
                        v = v - np.clip(v, -dfe_limit * abs(h0),
                                        dfe_limit * abs(h0))
                    acc += v * v
                resid = np.sqrt(acc)
                slope = abs(taps[cur] - taps[max(cur - 1, 0)]) / ui
                sigma_j = slope * rj_fs * 1e-15
                sig = abs(h0) * amp_mv
                s_isi = resid * amp_mv
                s_j = sigma_j * amp_mv
                noise = np.sqrt(s_isi ** 2 + sigma_rx_mv ** 2
                                + sigma_xt_mv ** 2 + s_j ** 2
                                + (a_dd * sig) ** 2)
                margin = 20 * np.log10(sig / noise) if noise > 0 else -99
                ratio = sig / noise if noise > 0 else 0.0
                if best is None or margin > best['com_db']:
                    best = dict(com_db=float(margin),
                                signal_to_noise_ratio=float(ratio),
                                cursor_mv=float(sig),
                                isi_mv=float(s_isi), jitter_mv=float(s_j),
                                xt_mv=float(sigma_xt_mv),
                                rx_mv=float(sigma_rx_mv),
                                noise_mv=float(noise),
                                ctle_db=float(-abs(gdc[3])),
                                tx_preset=(float(pre), float(main), float(post)),
                                phase=int(phase), n_dfe=int(n_dfe))
    if best is not None:
        from .jitter import ber_from_q, q_from_ber
        r = best['signal_to_noise_ratio']
        best['detector_error_ratio'] = float(ber_from_q(r))
        best['q_equivalent'] = float(r)
        # what the same channel would need to reach 1e-12 with no coding
        best['q_for_1e12'] = float(q_from_ber(1e-12))
        best['shortfall_to_1e12_db'] = float(
            20 * np.log10(q_from_ber(1e-12) / r)) if r > 0 else 99.0
    return best


def interpret(best, com_threshold_db=3.0):
    """Say what the number means, and what it does not.

    A channel operating margin above three decibels is a pass, and it is easy
    to read that as 'this link will work'. It means something narrower. The
    threshold is calibrated against a detector error ratio in the region of one
    in ten thousand to one in a hundred thousand -- the error rate *before*
    forward error correction -- because every standard that uses this method
    also mandates coding. A budget written for an uncoded link at one error in
    a million million is asking a different question and will get a different
    answer on the same channel.

    Both numbers are reported here so the difference is visible rather than
    surprising.
    """
    return dict(
        com_db=best['com_db'],
        verdict='pass' if best['com_db'] >= com_threshold_db else 'fail',
        threshold_db=com_threshold_db,
        detector_error_ratio=best['detector_error_ratio'],
        q_equivalent=best['q_equivalent'],
        q_for_1e12=best['q_for_1e12'],
        shortfall_to_1e12_db=best['shortfall_to_1e12_db'],
        uncoded_1e12_verdict=('pass' if best['q_equivalent']
                              >= best['q_for_1e12'] else 'fail'))


def sensitivity(channel, base=None, **kw):
    """How much the verdict moves when the reference receiver is varied.

    The point is not that any one of these settings is the right one; it is
    that the channel has not changed between rows and the number has. A
    standard's verdict is a joint statement about a channel and a reference
    receiver, and reading it as a property of the channel alone is a mistake
    that shows up as an interoperability argument.
    """
    base = base or com(channel, **kw)
    rows = [dict(variant='reference receiver as defined', **base)]
    for n in (1, 3, 5, 8, 12, 16):
        r = com(channel, n_dfe=n, **kw)
        rows.append(dict(variant='%d decision-feedback taps' % n, **r))
    for xt in (0.0, 1.5, 3.0, 6.0):
        r = com(channel, sigma_xt_mv=xt, **kw)
        rows.append(dict(variant='crosstalk %.1f mV rms' % xt, **r))
    for rj in (150.0, 350.0, 700.0):
        r = com(channel, rj_fs=rj, **kw)
        rows.append(dict(variant='random jitter %.0f fs rms' % rj, **r))
    return dict(base=base, rows=rows)


# ------------------------------------------------------------ the masks ----

def insertion_loss_fit(f, s21, f_max_ghz=30.0, order=4):
    """Fit a smooth insertion loss and return the deviation from it.

    The standards do this because the smooth part of the loss is what the
    equaliser is designed to remove, while the wiggle on top of it -- the
    insertion-loss deviation -- is the part caused by reflections, and
    reflections are what the equaliser cannot handle. Separating the two is the
    same argument the deck on measurement makes about where in time the energy
    lands.
    """
    m = (f > 0) & (f <= f_max_ghz * 1e9)
    x = np.sqrt(f[m] / 1e9)
    y = 20 * np.log10(np.abs(s21[m]) + 1e-15)
    co = np.polyfit(x, y, order)
    fit = np.polyval(co, x)
    ild = y - fit
    return dict(f_ghz=(f[m] / 1e9).tolist(), il_db=y.tolist(),
                fit_db=fit.tolist(), ild_db=ild.tolist(),
                ild_rms_db=float(np.sqrt(np.mean(ild ** 2))),
                ild_max_db=float(np.max(np.abs(ild))))


def compliance_masks(channel, f_nyq_ghz=14.0, il_limit_db=-30.0,
                     rl_limit_db=-10.0, ild_limit_db=1.0):
    """The handful of frequency-domain limits a channel has to meet."""
    f, s21, s11 = channel['f'], channel['s21'], channel['s11']
    il_nyq = float(20 * np.log10(abs(np.interp(f_nyq_ghz * 1e9, f,
                                               np.abs(s21)))))
    band = (f > 0) & (f <= f_nyq_ghz * 1e9)
    rl_worst = float(np.max(20 * np.log10(np.abs(s11[band]) + 1e-15)))
    ild = insertion_loss_fit(f, s21, f_nyq_ghz * 2)
    return dict(
        il_at_nyquist_db=il_nyq, il_limit_db=il_limit_db,
        il_pass=bool(il_nyq >= il_limit_db),
        rl_worst_db=rl_worst, rl_limit_db=rl_limit_db,
        rl_pass=bool(rl_worst <= rl_limit_db),
        ild_rms_db=ild['ild_rms_db'], ild_max_db=ild['ild_max_db'],
        ild_limit_db=ild_limit_db,
        ild_pass=bool(ild['ild_max_db'] <= ild_limit_db))
