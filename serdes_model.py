"""Channel model and equaliser design for the SerDes equalisation article.

Everything quoted in the document comes out of this file: the channel is built
as an ABCD cascade of lossy differential transmission-line sections, vias,
connectors and an un-backdrilled via stub; the pulse response comes from an
IFFT of the resulting SDD21; and the CTLE, transmit FFE and decision-feedback
taps are designed against that pulse response rather than asserted.
"""

import json
import os

import numpy as np

# ------------------------------------------------------------------ setup ---
FB = 28.0e9                 # symbol rate, baud
UI = 1.0 / FB
FNYQ = FB / 2.0             # 14 GHz
M = 32                      # samples per UI
NFFT = 1 << 15
FS = FB * M                 # 896 GHz sample rate
DF = FS / NFFT
FREQ = np.arange(NFFT // 2 + 1) * DF

Z0D = 100.0                 # differential characteristic impedance
DK = 3.7
VP = 2.998e8 / np.sqrt(DK) / 0.0254      # inch/s
TPD = 1.0 / VP                            # s per inch  (~163 ps/inch)

A_C = 0.09      # dB / inch / sqrt(GHz)   conductor
A_D = 0.035     # dB / inch / GHz         dielectric
CTLE_DB = -12.0 # the setting the receiver's adaptation lands on; a real part
                # picks one of about sixteen, and this is the best of them
BP_LEN = 18.0   # backplane length, inches


def df_from_ad(ad, dk=DK):
    """Dielectric loss alpha_d [dB/inch] = 2.3 * f[GHz] * sqrt(Dk) * Df, so a
    loss coefficient in dB/inch/GHz implies a loss tangent."""
    return ad / (2.3 * np.sqrt(dk))


def gamma(f, ac=A_C, ad=A_D):
    """Propagation constant per inch."""
    fg = np.maximum(f, 1.0) / 1e9
    a_db = ac * np.sqrt(fg) + ad * fg
    alpha = a_db / 8.686
    beta = 2 * np.pi * f * TPD
    return alpha + 1j * beta


def abcd_tl(f, length, z0=Z0D, ac=A_C, ad=A_D):
    g = gamma(f, ac, ad) * length
    ch, sh = np.cosh(g), np.sinh(g)
    return np.array([[ch, z0 * sh], [sh / z0, ch]])


def abcd_shunt(y):
    one = np.ones_like(y)
    return np.array([[one, np.zeros_like(y)], [y, one]])


def abcd_series(z):
    one = np.ones_like(z)
    return np.array([[one, z], [np.zeros_like(z), one]])


def cascade(*mats):
    out = mats[0]
    for m in mats[1:]:
        out = np.einsum('ij...,jk...->ik...', out, m)
    return out


def to_s(abcd, z0=Z0D):
    A, B, C, D = abcd[0, 0], abcd[0, 1], abcd[1, 0], abcd[1, 1]
    den = A + B / z0 + C * z0 + D
    s21 = 2.0 / den
    s11 = (A + B / z0 - C * z0 - D) / den
    return s11, s21


def open_stub_y(f, length, z0_stub=35.0):
    """Admittance of an open-circuited via stub hanging off the through path."""
    g = gamma(f, ac=0.25, ad=0.05) * length
    return np.tanh(g) / z0_stub


def build_channel(f, stub_len=0.110, bp_len=BP_LEN):
    """Tx package -> line card -> connector -> backplane -> connector -> line
    card -> Rx package, with a via stub at the second backplane transition."""
    w = 2 * np.pi * f
    via = abcd_shunt(1j * w * 0.15e-12)          # 0.15 pF via pad capacitance
    conn = cascade(abcd_series(1j * w * 0.35e-9),  # 0.35 nH connector inductance
                   abcd_shunt(1j * w * 0.12e-12))
    stub = abcd_shunt(open_stub_y(f, stub_len)) if stub_len > 1e-4 else None

    parts = [abcd_tl(f, 0.4, ac=0.30, ad=0.12),   # Tx package escape, lossy
             abcd_tl(f, 6.0), via, conn, via,
             abcd_tl(f, bp_len)]
    if stub is not None:
        parts.append(stub)
    parts += [via, conn, via,
              abcd_tl(f, 4.0),
              abcd_tl(f, 0.4, ac=0.30, ad=0.12)]  # Rx package escape
    return to_s(cascade(*parts))


# ----------------------------------------------------- frequency -> time ----
def impulse_from_h(h_half):
    full = np.concatenate([h_half, np.conj(h_half[-2:0:-1])])
    imp = np.real(np.fft.ifft(full))
    return imp


def pulse_response(h_half):
    """Response to one NRZ symbol: impulse response boxcar-filtered over 1 UI."""
    imp = impulse_from_h(h_half)
    box = np.ones(M)
    return np.convolve(imp, box)[:NFFT]


def sample_cursors(pulse, n_pre=6, n_post=30):
    """Sample the pulse response on the UI grid at the phase that maximises the
    cursor, and return (cursor index, tap vector) with the cursor at n_pre."""
    best = (-1, 0, None)
    for phase in range(M):
        idx = np.arange(phase, NFFT, M)
        vals = pulse[idx]
        k = int(np.argmax(vals))
        if vals[k] > best[0]:
            best = (vals[k], phase, k)
    _, phase, k = best
    idx = np.arange(phase, NFFT, M)
    vals = pulse[idx]
    lo, hi = k - n_pre, k + n_post + 1
    return vals[lo:hi].copy(), n_pre


def eye_height(taps, cursor):
    """Worst-case (peak-distortion) inner eye opening, as a fraction of swing."""
    h0 = taps[cursor]
    isi = np.sum(np.abs(taps)) - abs(h0)
    return 2.0 * (abs(h0) - isi), h0, isi


# ------------------------------------------------------------- equalisers ---
def ctle(f, fp1=13.0e9, fp2=24.0e9, dc_att_db=-9.0):
    """Standard degenerated-pair CTLE. The setting moves the ZERO, not the
    overall gain: a deeper DC attenuation pulls the zero down in frequency and
    so buys more peaking. High-frequency gain stays near unity throughout,
    which is what makes a CTLE a shaping stage rather than an amplifier."""
    a = 10 ** (dc_att_db / 20.0)
    fz = fp1 * a
    s = 1j * 2 * np.pi * f
    return a * (1 + s / (2 * np.pi * fz)) / \
        ((1 + s / (2 * np.pi * fp1)) * (1 + s / (2 * np.pi * fp2)))


def tx_ffe_taps(taps, cursor):
    """3-tap transmit FFE with two pre-taps, zero-forcing the first two
    pre-cursors — the ISI a decision-feedback equaliser cannot touch. Normalised
    so the sum of tap magnitudes is 1, which is the transmitter's peak-power
    constraint and the source of the de-emphasis penalty.

    With c = [c_-2, c_-1, c_0] and c_0 = 1, requiring the output to vanish one
    and two symbols before the cursor gives a 2x2 system."""
    h = taps
    k = cursor
    Amat = np.array([[h[k + 1], h[k]],
                     [h[k],     h[k - 1]]])
    rhs = -np.array([h[k - 1], h[k - 2]])
    cm2, cm1 = np.linalg.solve(Amat, rhs)
    c = np.array([cm2, cm1, 1.0])
    return c / np.sum(np.abs(c))


def apply_ffe(taps, cursor, c):
    """c is indexed [c_-2, c_-1, c_0]; convolution delays by 2 taps."""
    out = np.convolve(taps, c)
    return out, cursor + 2


def mmse_ffe_dfe(h, cursor, nf=9, npre_w=6, nb=5, sigma_n=0.0015):
    """Joint MMSE design of a T-spaced receive FFE and a decision-feedback tail.

    Minimises noise power plus the residual ISI that neither the cursor nor the
    feedback taps can remove, subject to holding the cursor at unity:

        min_w  sigma_n^2 ||w||^2 + sum_{k in S} |c_k|^2   s.t.  c_d = 1

    where c = conv(h, w), S is every tap outside {cursor} and the nb feedback
    positions, and ||w|| is the noise enhancement the FFE costs."""
    L = len(h)
    # convolution matrix: c = H_mat @ w, with c of length L + nf - 1
    H_mat = np.zeros((L + nf - 1, nf))
    for i in range(nf):
        H_mat[i:i + L, i] = h
    d = cursor + npre_w                       # where the cursor lands in c
    keep = set([d]) | set(range(d + 1, d + 1 + nb))
    S = [k for k in range(L + nf - 1) if k not in keep]
    A = H_mat[S, :]
    b = H_mat[d, :]
    M = sigma_n ** 2 * np.eye(nf) + A.T @ A
    Minv_b = np.linalg.solve(M, b)
    w = Minv_b / (b @ Minv_b)
    c = H_mat @ w
    return w, c, d


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    R = {}

    # ---- channel, with and without the via stub ---------------------------
    s11, s21 = build_channel(FREQ, stub_len=0.110)
    s11b, s21b = build_channel(FREQ, stub_len=0.008)    # back-drilled
    R['il_nyq_stub'] = float(20 * np.log10(abs(np.interp(FNYQ, FREQ, abs(s21)))))
    R['il_nyq_bd'] = float(20 * np.log10(abs(np.interp(FNYQ, FREQ, abs(s21b)))))
    R['il_1g'] = float(20 * np.log10(abs(np.interp(1e9, FREQ, abs(s21b)))))
    R['rl_nyq'] = float(20 * np.log10(abs(np.interp(FNYQ, FREQ, abs(s11b)))))
    R['tpd_ps_in'] = float(TPD * 1e12)
    R['loss_per_inch_nyq'] = float(A_C * np.sqrt(FNYQ / 1e9) + A_D * FNYQ / 1e9)
    # stub resonance
    # isolate the stub by differencing against the back-drilled channel
    excess = 20 * np.log10(np.abs(s21b) + 1e-30) - 20 * np.log10(np.abs(s21) + 1e-30)
    band = (FREQ > 2e9) & (FREQ < 45e9)
    k = int(np.argmax(excess[band]))
    R['stub_notch_ghz'] = float(FREQ[band][k] / 1e9)
    R['stub_notch_depth'] = float(excess[band][k])
    R['stub_excess_at_nyq'] = float(np.interp(FNYQ, FREQ, excess))

    # ---- raw pulse response (back-drilled channel from here on) -----------
    # A lossless channel would give a pulse of unit height, so the tap values
    # below are already fractions of the transmitted amplitude.
    pr = pulse_response(s21b)
    taps, cur = sample_cursors(pr)
    eh, h0, isi = eye_height(taps, cur)
    R['raw_cursor'] = float(h0)
    R['raw_isi'] = float(isi)
    R['raw_eye'] = float(eh)
    R['raw_pre1'] = float(taps[cur - 1])
    R['raw_post1'] = float(taps[cur + 1])
    R['raw_post2'] = float(taps[cur + 2])

    # ---- CTLE --------------------------------------------------------------
    H = ctle(FREQ, dc_att_db=CTLE_DB)
    R['ctle_boost_db'] = float(20 * np.log10(abs(np.interp(FNYQ, FREQ, abs(H)) /
                                                np.interp(1e8, FREQ, abs(H)))))
    R['ctle_peak_db'] = float(20 * np.log10(np.max(np.abs(H)) /
                                            abs(np.interp(1e8, FREQ, abs(H)))))
    pr_c = pulse_response(s21b * H)
    taps_c, cur_c = sample_cursors(pr_c)
    eh_c, h0_c, isi_c = eye_height(taps_c, cur_c)
    R['ctle_cursor'] = float(h0_c)
    R['ctle_isi'] = float(isi_c)
    R['ctle_eye'] = float(eh_c)

    # ---- transmit FFE ------------------------------------------------------
    c = tx_ffe_taps(taps_c, cur_c)
    R['ffe_taps'] = [float(x) for x in c]
    taps_f, cur_f = apply_ffe(taps_c, cur_c, c)
    eh_f, h0_f, isi_f = eye_height(taps_f, cur_f)
    R['ffe_cursor'] = float(h0_f)
    R['ffe_isi'] = float(isi_f)
    R['ffe_eye'] = float(eh_f)

    # ---- decision feedback on the transmit-equalised response --------------
    # The headline chain is a CEI-28G-class analogue receiver: CTLE, transmit
    # FFE, DFE. A receive FFE is evaluated separately below and priced as one of
    # the remedies in section 8, because on this channel it is not the answer.
    NDFE = 5
    comb = taps_f / taps_f[cur_f]
    dcur = cur_f
    R['dfe_taps'] = [float(comb[dcur + k]) for k in range(1, NDFE + 1)]
    taps_d = comb.copy()
    taps_d[dcur + 1: dcur + 1 + NDFE] = 0.0
    eh_d, h0_d, isi_d = eye_height(taps_d, dcur)
    R['dfe_cursor'] = float(h0_d)
    R['dfe_isi'] = float(isi_d)
    R['dfe_eye'] = float(eh_d)
    R['resid_isi_rms'] = float(np.sqrt(max(np.sum(taps_d ** 2) - h0_d ** 2, 0.0)))

    # the receive-FFE variant, for section 5.3 and for the remedies table
    w, comb_f, dcur_f = mmse_ffe_dfe(taps_f, cur_f, nf=9, nb=NDFE)
    R['rxffe_taps'] = [float(x) for x in w]
    R['rxffe_noise_gain'] = float(np.linalg.norm(w))
    R['rxffe_noise_enh_db'] = float(
        20 * np.log10(float(np.linalg.norm(w)) * abs(taps_f[cur_f])))

    # ---- stage-by-stage signal, noise and ISI ------------------------------
    # Referred to a common point so the stages are comparable. The transmit FFE
    # scales the signal but not the receiver's noise; the CTLE scales both.
    AMP0, SRX, SXT, SJIT = 400.0, 1.8, 3.0, 0.10
    g_ctle = ctle_noise_gain(H)

    def stage(tp, cu, gn, name):
        sig = abs(tp[cu]) * AMP0
        isi_rms = float(np.sqrt(max(np.sum(tp ** 2) - tp[cu] ** 2, 0.0))) * AMP0
        isi_sum = (float(np.sum(np.abs(tp))) - abs(tp[cu])) * AMP0
        nn = float(np.sqrt((SRX * gn) ** 2 + (SXT * gn) ** 2 + SJIT ** 2))
        return dict(name=name, sig=sig, isi_rms=isi_rms, isi_sum=isi_sum,
                    noise=nn, eye=2 * (sig - isi_sum),
                    snr_n=float(20 * np.log10(sig / nn)),
                    snr_i=float(20 * np.log10(sig / max(isi_rms, 1e-9))),
                    q=float(sig / np.sqrt(nn ** 2 + isi_rms ** 2)),
                    gain=float(gn))

    dfe_zeroed = taps_f.copy()
    dfe_zeroed[cur_f + 1: cur_f + 1 + NDFE] = 0.0
    R['stages'] = [stage(taps, cur, 1.0, "Channel only"),
                   stage(taps_c, cur_c, g_ctle, "+ CTLE"),
                   stage(taps_f, cur_f, g_ctle, "+ transmit FFE"),
                   stage(dfe_zeroed, cur_f, g_ctle, "+ DFE, five taps")]
    R['df_baseline'] = float(df_from_ad(A_D))
    R['df_lowloss'] = float(df_from_ad(0.022))
    R['dk'] = DK

    from math import erfc, sqrt, log10
    SWING = 800.0                     # mV differential peak-to-peak at the Tx
    AMP = SWING / 2.0                 # amplitude of a +/-1 symbol

    # The MMSE design pins the cursor at 1, so the FFE carries an implicit AGC
    # gain. Refer everything back to the receiver input, where the numbers mean
    # something: the only thing the FFE really costs is noise ENHANCEMENT, the
    # ratio of its noise gain to its signal gain.
    R['ctle_noise_gain_db'] = float(20 * np.log10(ctle_noise_gain(H)))
    noise_enh = ctle_noise_gain(H)      # only the CTLE shapes the noise here
    R['noise_enh'] = float(noise_enh)
    R['noise_enh_db'] = float(20 * log10(noise_enh))

    sig_rx, sig_xt = 1.8, 3.0         # mV rms at the receiver input
    RJ = 350e-15                      # s rms random jitter
    slope = float(np.max(np.abs(np.diff(pr_c))) / (UI / M))
    sig_jit = slope * RJ * AMP

    signal_mv = abs(R['ffe_cursor']) * AMP                 # cursor at the input
    # resid_isi_rms is relative to the cursor, so scale it by the cursor itself
    sig_isi = R['resid_isi_rms'] * abs(R['ffe_cursor']) * AMP
    sig_rx_e, sig_xt_e = sig_rx * noise_enh, sig_xt * noise_enh
    sig_jit_e = sig_jit * noise_enh
    sig = float(sqrt(sig_rx_e ** 2 + sig_xt_e ** 2 + sig_jit_e ** 2 + sig_isi ** 2))

    R.update(swing_mv=SWING, sigma_rx=sig_rx, sigma_xt=sig_xt, rj_fs=RJ * 1e15,
             sigma_rx_eff=float(sig_rx_e), sigma_xt_eff=float(sig_xt_e),
             sigma_jit=float(sig_jit_e), sigma_isi=float(sig_isi),
             sigma_tot=sig, signal_mv=float(signal_mv))
    R['eye_mv'] = float(2 * signal_mv)
    R['eye_mv_worstcase'] = float(eh_d * abs(R['ffe_cursor']) * AMP)
    Q = signal_mv / sig
    R['Q'] = float(Q)
    R['ber_exp'] = float(log10(max(0.5 * erfc(Q / sqrt(2)), 1e-300)))
    R['margin_db'] = float(20 * log10(Q / 7.03))     # 7.03 is Q for BER 1e-12

    # ---- the same channel at 56 Gb/s PAM4 ---------------------------------
    Qp = Q / 3.0                       # three eyes, each a third of the amplitude
    ser = 1.5 * erfc(Qp / sqrt(2))
    R['pam4_Q'] = float(Qp)
    R['pam4_eye_mv'] = float(2 * signal_mv / 3.0)
    R['pam4_ber'] = float(ser / 2.0)
    R['pam4_ber_exp'] = float(log10(max(ser / 2.0, 1e-300)))
    R['pam4_penalty_db'] = float(20 * log10(3.0))
    # what Q would PAM4 need to sit under the KP4 FEC threshold of 2.4e-4?
    lo, hi = 1.0, 12.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 1.5 * erfc(mid / sqrt(2)) / 2.0 > 2.4e-4:
            lo = mid
        else:
            hi = mid
    R['pam4_Q_needed'] = float(hi)
    R['pam4_snr_short_db'] = float(20 * log10(hi / Qp))
    R['kp4_threshold'] = 2.4e-4

    np.save(os.path.join(here, '_serdes_arrays.npy'),
            {'freq': FREQ, 's21': s21, 's21b': s21b, 's11b': s11b,
             'H': H, 'pr': pr, 'pr_c': pr_c,
             'taps': taps, 'cur': cur, 'taps_c': taps_c, 'cur_c': cur_c,
             'taps_f': taps_f, 'cur_f': cur_f, 'taps_d': taps_d,
             'ffe': c, 'ndfe': NDFE, 'rxffe': w, 'comb': comb, 'dcur': dcur},
            allow_pickle=True)
    with open(os.path.join(here, '_serdes_results.json'), 'w') as fh:
        json.dump(R, fh, indent=1)
    for k, v in R.items():
        if k == 'stages':
            continue
        print("%-20s %s" % (k, np.round(v, 4) if not isinstance(v, (list, dict))
                            else v))
    return R




# ------------------------------------------------------- remedies sweep -----
def ctle_noise_gain(H, bw=1.2 * FNYQ):
    """Front-end noise and crosstalk pass through the CTLE along with the
    signal, so its attenuation is not a pure loss. For a roughly white input
    the noise gain is the rms of |H| over the receiver's noise bandwidth."""
    band = FREQ <= bw
    return float(np.sqrt(np.mean(np.abs(H[band]) ** 2)))


def run_case(bp_len=BP_LEN, ad=A_D, ac=A_C, sig_rx=1.8, sig_xt=3.0,
             rj=350e-15, ndfe=5, nf=9, pam4=False, stub=0.008,
             ctle_db=CTLE_DB, rxffe=False):
    """Re-run the whole chain with one or two parameters changed, and report
    the margin. Used to answer 'what would actually fix this link?'."""
    from math import erfc, sqrt, log10
    f = FREQ
    w = 2 * np.pi * f
    via = abcd_shunt(1j * w * 0.15e-12)
    conn = cascade(abcd_series(1j * w * 0.35e-9), abcd_shunt(1j * w * 0.12e-12))
    parts = [abcd_tl(f, 0.4, ac=0.30, ad=0.12), abcd_tl(f, 6.0, ac=ac, ad=ad),
             via, conn, via, abcd_tl(f, bp_len, ac=ac, ad=ad)]
    if stub > 1e-4:
        parts.append(abcd_shunt(open_stub_y(f, stub)))
    parts += [via, conn, via, abcd_tl(f, 4.0, ac=ac, ad=ad),
              abcd_tl(f, 0.4, ac=0.30, ad=0.12)]
    _, s21 = to_s(cascade(*parts))
    il = float(20 * np.log10(abs(np.interp(FNYQ, FREQ, abs(s21)))))

    H = ctle(f, dc_att_db=ctle_db)
    pr_c = pulse_response(s21 * H)
    taps_c, cur_c = sample_cursors(pr_c)
    c = tx_ffe_taps(taps_c, cur_c)
    taps_f, cur_f = apply_ffe(taps_c, cur_c, c)
    if rxffe:
        wv, comb, dcur = mmse_ffe_dfe(taps_f, cur_f, nf=nf, nb=ndfe)
        g_sig = 1.0 / abs(taps_f[cur_f])
        enh = float(np.linalg.norm(wv)) / g_sig
    else:
        comb, dcur = taps_f.copy(), cur_f
        comb = comb / comb[dcur]                 # normalise to the cursor
        g_sig = 1.0 / abs(taps_f[cur_f])
        enh = 1.0                                # no linear receive filter, no enhancement

    resid = comb.copy()
    resid[dcur + 1: dcur + 1 + ndfe] = 0.0
    isi_rms = float(np.sqrt(max(np.sum(resid ** 2) - 1.0, 0.0)))

    AMP = 400.0
    slope = float(np.max(np.abs(np.diff(pr_c))) / (UI / M))
    enh = enh * ctle_noise_gain(H)          # the CTLE shapes the noise too
    s_tot = sqrt((sig_rx * enh) ** 2 + (sig_xt * enh) ** 2 +
                 (slope * rj * AMP * enh) ** 2 + (isi_rms / g_sig * AMP) ** 2)
    sig_mv = abs(taps_f[cur_f]) * AMP
    Q = sig_mv / s_tot
    if pam4:
        Q = Q / 3.0
        ber = 1.5 * erfc(Q / sqrt(2)) / 2.0
        target = 2.4e-4                    # KP4 FEC input threshold
        margin = 20 * log10(Q / 3.5985)
    else:
        ber = 0.5 * erfc(Q / sqrt(2))
        target = 1e-12
        margin = 20 * log10(Q / 7.034)
    return dict(il=il, Q=float(Q), ber_exp=float(log10(max(ber, 1e-300))),
                margin=float(margin), target=target, sigma=float(s_tot),
                signal=float(sig_mv))


def remedies():
    cases = [
        ("As built", {}),
        ("Halve the crosstalk (connector + pair pitch)", dict(sig_xt=1.5)),
        ("Low-loss laminate (Df 0.0079 → 0.0050)", dict(ad=0.022)),
        ("Shorten the backplane 18\" → 13\"", dict(bp_len=13.0)),
        ("Ten DFE taps instead of five", dict(ndfe=10)),
        ("Add a 9-tap receive FFE (the ADC-DSP answer)", dict(rxffe=True)),
        ("Low-loss laminate + halved crosstalk", dict(ad=0.022, sig_xt=1.5)),
    ]
    out = []
    for name, kw in cases:
        r = run_case(**kw)
        out.append(dict(name=name, **r))
        print("%-46s IL %6.1f dB   Q %5.2f   BER 1e%-6.1f  margin %+5.2f dB"
              % (name, r['il'], r['Q'], r['ber_exp'], r['margin']))
    print()
    p4 = [("PAM4, as built", {}),
          ("PAM4 + low-loss laminate", dict(ad=0.022)),
          ("PAM4 + low-loss + 13\" backplane", dict(ad=0.022, bp_len=13.0)),
          ("PAM4 + all of the above, plus a receive FFE",
           dict(ad=0.022, bp_len=13.0, sig_xt=1.5, rxffe=True))]
    out4 = []
    for name, kw in p4:
        r = run_case(pam4=True, **kw)
        out4.append(dict(name=name, **r))
        print("%-46s IL %6.1f dB   Q %5.2f   BER 1e%-6.1f  margin %+5.2f dB"
              % (name, r['il'], r['Q'], r['ber_exp'], r['margin']))
    return out, out4

if __name__ == "__main__":
    main()
