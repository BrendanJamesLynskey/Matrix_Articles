"""Measurement, de-embedding and correlation -- the model behind deck 10.

A channel model is only as good as the S-parameters it is built from, and
S-parameter files arrive with defects. They are band-limited, because the
instrument stops somewhere. They are not defined at direct current, because a
vector network analyser cannot measure there. They are sampled, so the
transform back to the time domain is periodic whether the engineer wants it to
be or not. They frequently violate passivity or causality by small amounts,
because they have been through a de-embedding step that subtracted something
slightly wrong.

None of these are theoretical worries. Each one is applied here to the actual
channel from SerDes_Equalisation -- imported, not re-fitted, so the published
results of that article are untouched -- and each is measured in the only
currency that matters, which is the error it produces in the pulse response
and therefore in the eye.

The uncomfortable result is the last one. `correlation_study()` shows that a
model can agree with measurement to a fraction of a decibel in insertion loss
across the whole band and still get the eye height wrong, because insertion
loss discards the phase that decides where the energy lands in time.
"""

import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def reference_channel(stub_len=0.0):
    """The SerDes_Equalisation channel, imported read-only.

    `serdes_model` writes its JSON only from `main()`, so importing the module
    and calling `build_channel` recomputes nothing that the article quotes.
    """
    import serdes_model as SM
    f = SM.FREQ.copy()
    s11, s21 = SM.build_channel(f, stub_len=stub_len)
    return dict(f=f, s11=s11, s21=s21, M=SM.M, NFFT=SM.NFFT, UI=SM.UI,
                fnyq=SM.FNYQ, fb=SM.FB, sm=SM)


def pulse_from_s21(s21, M, NFFT):
    """Pulse response for one symbol, by the same route the article uses."""
    full = np.concatenate([s21, np.conj(s21[-2:0:-1])])
    imp = np.real(np.fft.ifft(full))
    return np.convolve(imp, np.ones(M))[:NFFT]


def cursors(pulse, M, n_pre=6, n_post=30):
    best = (-1, 0, 0)
    for phase in range(M):
        v = pulse[phase::M]
        k = int(np.argmax(v))
        if v[k] > best[0]:
            best = (v[k], phase, k)
    _, phase, k = best
    v = pulse[phase::M]
    return v[k - n_pre:k + n_post + 1].copy(), n_pre


def eye(taps, cur):
    """Unequalised peak-distortion eye, plus the two terms it is made of.

    On a channel this lossy the unequalised eye is closed -- the article's
    whole point -- so the opening comes out negative and is useless as a
    sensitivity metric. The cursor and the intersymbol-interference sum are
    reported separately because they stay meaningful, and `equalised_eye`
    gives the number a reader actually cares about.
    """
    h0 = taps[cur]
    isi = np.sum(np.abs(taps)) - abs(h0)
    return dict(cursor=float(h0), isi=float(isi),
                eye_height=float(2 * (abs(h0) - isi)))


def equalised_eye(s21, ch, nf=9, nb=5, sigma_n=0.0015):
    """Eye opening after the article's own receive equaliser is designed to it.

    Designing the equaliser against each damaged channel, rather than reusing
    the taps from the clean one, is the honest comparison: a real receiver
    adapts to whatever it is given, so the question is not how much the
    waveform changed but how much margin survives after adaptation.
    """
    SM = ch['sm']
    p = pulse_from_s21(s21, ch['M'], ch['NFFT'])
    taps, cur = cursors(p, ch['M'])
    h = taps / max(abs(taps[cur]), 1e-30)
    w, c, d = SM.mmse_ffe_dfe(h, cur, nf=nf, nb=nb, sigma_n=sigma_n)
    keep = set([d]) | set(range(d + 1, d + 1 + nb))
    resid = float(np.sum(np.abs([c[k] for k in range(len(c)) if k not in keep])))
    cursor_v = float(abs(taps[cur]))
    return dict(cursor_v=cursor_v,
                residual_isi=resid,
                noise_gain=float(np.linalg.norm(w)),
                eye_norm=float(2 * (1.0 - resid)),
                eye_v=float(2 * (1.0 - resid) * cursor_v))


# -------------------------------------------------------- quality checks ----

def passivity(s11, s21, s12=None, s22=None):
    """A passive network cannot deliver more power than it is given.

    For a reciprocal, symmetric two-port the condition reduces to
    |S11|^2 + |S21|^2 <= 1 at every frequency. The amount by which a data set
    exceeds one is the amount of energy the model would manufacture, and a
    time-domain simulator handed such a file can oscillate.
    """
    s12 = s21 if s12 is None else s12
    s22 = s11 if s22 is None else s22
    p = np.abs(s11) ** 2 + np.abs(s21) ** 2
    return dict(max_power=float(np.max(p)),
                violates=bool(np.max(p) > 1.0 + 1e-9),
                excess=float(max(0.0, np.max(p) - 1.0)),
                n_violating=int(np.sum(p > 1.0 + 1e-9)))


def reciprocity(s21, s12):
    d = np.abs(s21 - s12)
    return dict(max_abs=float(np.max(d)),
                max_rel=float(np.max(d / (np.abs(s21) + 1e-15))))


def causality_time_domain(s21, M, NFFT, guard_frac=0.02):
    """Energy appearing before the signal could possibly have arrived.

    Transform the response to the time domain and look at the samples ahead of
    the first arrival. A causal network puts nothing there. The ratio of that
    energy to the total is a direct, interpretable measure of how non-causal a
    data set is, and it needs no Hilbert transform to compute.
    """
    full = np.concatenate([s21, np.conj(s21[-2:0:-1])])
    imp = np.real(np.fft.ifft(full))
    n = len(imp)
    pk = int(np.argmax(np.abs(imp)))
    guard = max(1, int(guard_frac * n))
    pre = imp[max(0, pk - n // 2):max(0, pk - guard)]
    e_pre = float(np.sum(pre ** 2))
    e_tot = float(np.sum(imp ** 2))
    return dict(precursor_energy_ratio=e_pre / max(e_tot, 1e-30),
                precursor_energy_db=float(10 * np.log10(max(e_pre / max(e_tot, 1e-30), 1e-30))),
                peak_index=pk)


def causality_minimum_phase(s21, f, band_ghz=40.0):
    """Test the phase against the one the magnitude implies.

    For a causal, minimum-phase response the phase is not free: it is the
    Hilbert transform of the log-magnitude, which is the Kramers-Kronig
    relation written for a transfer function instead of a permittivity. A data
    set whose magnitude has been edited without the matching dispersion fails
    this test even though nothing about it looks wrong on a magnitude plot.

    A pure time delay is subtracted before comparing, because a delay is a
    linear phase term that a minimum-phase reconstruction cannot know about and
    that is in any case perfectly causal -- moving the reference plane is not a
    violation, and a test that flagged it would be useless.

    The residual does not go to zero for a real channel and should not be
    expected to. Every internal reflection -- between a via and a connector,
    say -- contributes an all-pass factor, and an all-pass factor is causal but
    emphatically not minimum phase. The baseline this returns for a healthy
    channel is therefore a property of that channel's own discontinuities, and
    the metric is useful as a relative indicator: a file that reads a few
    degrees worse than its peers deserves a look, and one that reads two orders
    of magnitude worse has been cut off at the band edge.
    """
    # The reconstruction must see the whole measured spectrum. Cutting it to
    # the band of interest first would put a step in the log-magnitude at the
    # cut, and the transform would report that step rather than the data.
    mag = np.abs(s21) + 1e-300

    # Minimum phase by the cepstral method. Build a Hermitian double-sided
    # log-magnitude spectrum, take its real cepstrum, fold the non-causal half
    # onto the causal one, and transform back: the imaginary part is the phase
    # a minimum-phase system with this magnitude is obliged to have.
    lm = np.log(mag)
    full = np.concatenate([lm, lm[-2:0:-1]])
    c = np.real(np.fft.ifft(full))
    n = len(c)
    fold = np.zeros(n)
    fold[0] = c[0]
    half = n // 2
    fold[1:half] = 2 * c[1:half]
    if n % 2 == 0:
        fold[half] = c[half]
    phi_min = np.imag(np.fft.fft(fold))[:len(lm)]

    # only now restrict to the band the answer is wanted over
    m = (f > 0) & (f <= band_ghz * 1e9)
    fb = f[m]
    phi_min = phi_min[m]
    phi = np.unwrap(np.angle(s21))[m]
    # A pure delay is a linear phase term that a minimum-phase reconstruction
    # cannot know about and that is perfectly causal in any case, so it is
    # fitted out of the difference rather than counted as a violation.
    diff = phi - phi_min
    coef = np.polyfit(fb, diff, 1)
    resid = diff - np.polyval(coef, fb)
    return dict(rms_phase_err_rad=float(np.sqrt(np.mean(resid ** 2))),
                rms_phase_err_deg=float(np.degrees(np.sqrt(np.mean(resid ** 2)))),
                max_phase_err_deg=float(np.degrees(np.max(np.abs(resid)))),
                implied_delay_ps=float(-coef[0] / (2 * np.pi) * 1e12))


def truncate_band(ch, f_max_ghz, dc_mode='extrapolate'):
    """Cut the data off at f_max and rebuild the pulse response.

    Three things go wrong at once, and the deck separates them. Removing the
    high frequencies removes real signal content. Cutting abruptly is
    multiplication by a rectangle, whose transform rings. And whatever is done
    about the missing direct-current point sets the baseline the whole response
    sits on.
    """
    f, s21 = ch['f'], ch['s21'].copy()
    keep = f <= f_max_ghz * 1e9
    s = np.zeros_like(s21)
    s[keep] = s21[keep]
    if dc_mode == 'extrapolate':
        s[0] = np.abs(s21[1])                     # real, magnitude-continued
    elif dc_mode == 'zero':
        s[0] = 0.0
    elif dc_mode == 'unity':
        s[0] = 1.0
    return s


def truncation_study(ch, bands_ghz=(20, 30, 40, 50, 70), ref_band_ghz=None):
    """Eye height against where the measurement was stopped."""
    ref_s = ch['s21'] if ref_band_ghz is None else truncate_band(ch, ref_band_ghz)
    ref_p = pulse_from_s21(ref_s, ch['M'], ch['NFFT'])
    rt, rc = cursors(ref_p, ch['M'])
    ref = eye(rt, rc)
    rows = []
    for b in bands_ghz:
        s = truncate_band(ch, b)
        p = pulse_from_s21(s, ch['M'], ch['NFFT'])
        t, c = cursors(p, ch['M'])
        e = eye(t, c)
        rows.append(dict(band_ghz=b, cursor=e['cursor'], isi=e['isi'],
                         eye_height=e['eye_height'],
                         cursor_err_pct=100 * (e['cursor'] / ref['cursor'] - 1),
                         eye_err_pct=100 * (e['eye_height'] / ref['eye_height'] - 1)))
    return dict(reference=ref, rows=rows)


def dc_study(ch, f_max_ghz=40.0):
    """The same band limit with three different guesses at direct current."""
    ref_p = pulse_from_s21(ch['s21'], ch['M'], ch['NFFT'])
    rt, rc = cursors(ref_p, ch['M'])
    ref = eye(rt, rc)
    out = []
    for mode in ('extrapolate', 'zero', 'unity'):
        s = truncate_band(ch, f_max_ghz, mode)
        p = pulse_from_s21(s, ch['M'], ch['NFFT'])
        t, c = cursors(p, ch['M'])
        e = eye(t, c)
        tail = float(np.mean(p[-ch['NFFT'] // 8:]))
        out.append(dict(dc_mode=mode, cursor=e['cursor'],
                        eye_height=e['eye_height'], baseline_drift=tail,
                        eye_err_pct=100 * (e['eye_height'] / ref['eye_height'] - 1)))
    return dict(reference=ref, rows=out, f_max_ghz=f_max_ghz)


def inject_passivity_violation(s21, excess=0.02):
    """Scale the transmission up slightly, as a bad de-embedding would."""
    return s21 * (1.0 + excess)


def inject_noncausal_phase(ch, ps=15.0):
    """A pure phase advance -- included to show that it is *not* a violation.

    Multiplying by exp(+j w t) shifts the response earlier in time. That looks
    alarming and is harmless: a time shift is still a causal system, merely one
    with a different reference plane, which is exactly what de-embedding is for.
    The check has to distinguish this from a real violation, and it does.
    """
    return ch['s21'] * np.exp(1j * 2 * np.pi * ch['f'] * ps * 1e-12)


def inject_magnitude_only_error(ch, depth_db=2.0, f0_ghz=18.0, bw_ghz=6.0):
    """A genuine causality violation: change the magnitude, keep the phase.

    Magnitude and phase are not independent. Kramers and Kronig tie them
    together for any causal response, so a notch put into the magnitude without
    the dispersion that must accompany it describes a network that cannot
    exist. This is what a careless fit, a badly stitched pair of measurement
    bands, or a magnitude-only 'correction' produces, and unlike a time shift
    it does put energy before the arrival.
    """
    f = ch['f']
    shape = depth_db * np.exp(-((f - f0_ghz * 1e9) / (bw_ghz * 1e9)) ** 2)
    return ch['s21'] * 10 ** (-shape / 20.0)


def qc_summary(ch):
    """Run every check on the clean channel and on three damaged copies."""
    cases = {
        'as modelled': ch['s21'],
        'passivity violated by 2%': inject_passivity_violation(ch['s21'], 0.02),
        'reference plane moved 15 ps': inject_noncausal_phase(ch, 15.0),
        'magnitude notch, phase untouched':
            inject_magnitude_only_error(ch, depth_db=4.0),
        'truncated at 20 GHz': truncate_band(ch, 20.0),
    }
    rows = []
    for name, s in cases.items():
        p = pulse_from_s21(s, ch['M'], ch['NFFT'])
        t, c = cursors(p, ch['M'])
        e = eye(t, c)
        q = equalised_eye(s, ch)
        rows.append(dict(case=name,
                         **passivity(ch['s11'], s),
                         **causality_time_domain(s, ch['M'], ch['NFFT']),
                         **causality_minimum_phase(s, ch['f']),
                         cursor=e['cursor'], isi=e['isi'],
                         eye_v=q['eye_v'], noise_gain=q['noise_gain']))
    base = rows[0]
    for r in rows:
        r['eye_err_pct'] = 100 * (r['eye_v'] / base['eye_v'] - 1)
    return rows


# ------------------------------------------------------------ de-embedding --

def fixture_abcd(f, length_in=1.2, z0=100.0, z_fix=85.0, er=3.7,
                 ac=0.4, ad=0.15):
    """A test fixture: a launch, a length of line at the wrong impedance."""
    from .via import _abcd_shunt
    C0 = 299792458.0
    INCH = 0.0254
    tpd = np.sqrt(er) / C0 * INCH
    a_db = (ac * np.sqrt(f / 1e9) + ad * f / 1e9) * length_in
    g = a_db / 8.686 + 1j * 2 * np.pi * f * tpd * length_in
    ch_, sh = np.cosh(g), np.sinh(g)
    m = np.zeros((2, 2, f.size), dtype=complex)
    m[0, 0] = ch_; m[0, 1] = z_fix * sh
    m[1, 0] = sh / z_fix; m[1, 1] = ch_
    launch = _abcd_shunt(1j * 2 * np.pi * f * 0.12e-12)
    return np.einsum('ijf,jkf->ikf', launch, m)


def deembed_study(ch, z_fix_true=85.0, z_fix_assumed=100.0):
    """De-embed a fixture correctly and incorrectly, and price the difference.

    Fixture removal inverts a model of the fixture. If that model has the wrong
    impedance -- which is the usual case, because the fixture is built to the
    same tolerance as everything else -- the inversion leaves a residue behind,
    and the residue is a reflection that was never in the device under test.
    """
    from .via import _to_s
    f = ch['f']
    A = fixture_abcd(f, z_fix=z_fix_true)
    # embed: fixture, device, reversed fixture
    dut = ch['s21']
    # build the DUT's ABCD from its S (assume symmetric, reciprocal)
    s11, s21 = ch['s11'], dut
    d = (1 + s11) * (1 - s11) + s21 * s21
    z0 = 100.0
    Ad = ((1 + s11) * (1 - s11) + s21 * s21) / (2 * s21)
    Bd = z0 * ((1 + s11) * (1 + s11) - s21 * s21) / (2 * s21)
    Cd = ((1 - s11) * (1 - s11) - s21 * s21) / (2 * s21 * z0)
    Dd = Ad
    D_abcd = np.zeros((2, 2, f.size), dtype=complex)
    D_abcd[0, 0] = Ad; D_abcd[0, 1] = Bd; D_abcd[1, 0] = Cd; D_abcd[1, 1] = Dd
    Arev = np.zeros_like(A)
    Arev[0, 0] = A[1, 1]; Arev[0, 1] = A[0, 1]
    Arev[1, 0] = A[1, 0]; Arev[1, 1] = A[0, 0]
    meas = np.einsum('ijf,jkf->ikf', np.einsum('ijf,jkf->ikf', A, D_abcd), Arev)

    def invert(M):
        det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
        out = np.zeros_like(M)
        out[0, 0] = M[1, 1] / det; out[0, 1] = -M[0, 1] / det
        out[1, 0] = -M[1, 0] / det; out[1, 1] = M[0, 0] / det
        return out

    res = {}
    for label, zf in (('correct fixture model', z_fix_true),
                      ('fixture impedance wrong by %.0f ohm'
                       % (z_fix_assumed - z_fix_true), z_fix_assumed)):
        B = fixture_abcd(f, z_fix=zf)
        Brev = np.zeros_like(B)
        Brev[0, 0] = B[1, 1]; Brev[0, 1] = B[0, 1]
        Brev[1, 0] = B[1, 0]; Brev[1, 1] = B[0, 0]
        rec = np.einsum('ijf,jkf->ikf',
                        np.einsum('ijf,jkf->ikf', invert(B), meas), invert(Brev))
        s = _to_s(rec, z0)
        p = pulse_from_s21(s['s21'], ch['M'], ch['NFFT'])
        t, c = cursors(p, ch['M'])
        e = eye(t, c)
        il_err = np.abs(20 * np.log10(np.abs(s['s21']) + 1e-15)
                        - 20 * np.log10(np.abs(dut) + 1e-15))
        band = f <= 40e9
        res[label] = dict(eye_height=e['eye_height'], cursor=e['cursor'],
                          il_rms_err_db=float(np.sqrt(np.mean(il_err[band] ** 2))),
                          rl_max_db=float(np.max(20 * np.log10(
                              np.abs(s['s11'][band]) + 1e-15))))
    ref_p = pulse_from_s21(dut, ch['M'], ch['NFFT'])
    rt, rc = cursors(ref_p, ch['M'])
    res['truth'] = eye(rt, rc)
    for k, v in res.items():
        if k != 'truth':
            v['eye_err_pct'] = 100 * (v['eye_height'] / res['truth']['eye_height'] - 1)
    return res


def correlation_study(ch, rho=0.16, echo_delay_ps=140.0):
    """A model that matches insertion loss and still gets the eye wrong.

    Give the channel a small internal reflection: an echo of amplitude rho
    squared arriving a few symbols late, as an unnoticed impedance step
    anywhere along the line would produce. Its effect on the magnitude of the
    transfer function is second order in rho and hides inside the ripple
    everyone tolerates when they declare a model correlated.

    Its effect on the pulse response is first order in where the energy lands,
    and it lands several symbols after the cursor, where the decision-feedback
    taps have already run out. Insertion loss agrees; the eye does not.
    """
    f = ch['f']
    echo = 1.0 + rho * rho * np.exp(-1j * 2 * np.pi * f * echo_delay_ps * 1e-12)
    s = ch['s21'] * echo
    base_p = pulse_from_s21(ch['s21'], ch['M'], ch['NFFT'])
    bt, bc = cursors(base_p, ch['M'])
    be = eye(bt, bc)
    p = pulse_from_s21(s, ch['M'], ch['NFFT'])
    t, c = cursors(p, ch['M'])
    e = eye(t, c)
    band = f <= 40e9
    il_err = np.abs(20 * np.log10(np.abs(s) + 1e-15)
                    - 20 * np.log10(np.abs(ch['s21']) + 1e-15))
    qa = equalised_eye(ch['s21'], ch)
    qb = equalised_eye(s, ch)
    return dict(il_rms_err_db=float(np.sqrt(np.mean(il_err[band] ** 2))),
                il_max_err_db=float(np.max(il_err[band])),
                eye_ref_v=qa['eye_v'], eye_model_v=qb['eye_v'],
                eye_err_pct=float(100 * (qb['eye_v'] / qa['eye_v'] - 1)),
                residual_isi_ref=qa['residual_isi'],
                residual_isi_model=qb['residual_isi'],
                cursor_err_pct=float(100 * (e['cursor'] / be['cursor'] - 1)),
                rho=rho, echo_delay_ps=echo_delay_ps)


def echo_placement_study(ch, rho=0.16, delays_ps=(35, 70, 140, 280, 500)):
    """The same frequency-domain error, landing in different places in time.

    Every case here has an identical reflection magnitude, so every case has
    essentially the same insertion-loss agreement with the truth. What differs
    is when the echo arrives relative to the cursor, and therefore whether the
    decision-feedback taps can reach it. Within their span the receiver simply
    subtracts it; beyond their span it is residual intersymbol interference
    that nothing removes.

    This is why correlating a model against a measurement on insertion loss
    alone is not enough, and why the comparison has to be made on the pulse
    response or on something derived from it.
    """
    f = ch['f']
    base = equalised_eye(ch['s21'], ch)
    ui_ps = ch['UI'] * 1e12
    rows = []
    for d in delays_ps:
        s = ch['s21'] * (1.0 + rho * rho
                         * np.exp(-1j * 2 * np.pi * f * d * 1e-12))
        band = f <= 40e9
        il = np.abs(20 * np.log10(np.abs(s) + 1e-15)
                    - 20 * np.log10(np.abs(ch['s21']) + 1e-15))
        q = equalised_eye(s, ch)
        rows.append(dict(delay_ps=d, delay_ui=float(d / ui_ps),
                         il_rms_err_db=float(np.sqrt(np.mean(il[band] ** 2))),
                         eye_v=q['eye_v'],
                         eye_err_pct=float(100 * (q['eye_v'] / base['eye_v'] - 1)),
                         residual_isi=q['residual_isi']))
    return dict(reference=base, rows=rows, rho=rho, ui_ps=ui_ps)


def separability_from_channel(ch, rates_gbps=(1, 2.5, 5, 10, 14, 28, 56),
                              noise_mv_rms=6.0, amp_mv=400.0):
    """Received amplitude and slew rate against symbol rate, on a real channel.

    For each rate the pulse response is rebuilt with that symbol period -- the
    channel's transfer function does not change, but the boxcar that turns an
    impulse response into a symbol response does -- and the cursor amplitude
    and the slope at the preceding zero crossing are measured from it.

    A fixed receiver voltage noise is then converted to timing noise through
    that slope, which is the conversion Stephens's fourth rule rests on.
    """
    from .jitter import q_from_ber
    f = ch['f']
    NFFT = ch['NFFT']
    fs = f[-1] * 2.0
    rows = []
    for r in rates_gbps:
        ui = 1e-9 / r
        m = max(4, int(round(ui * fs / NFFT * NFFT)))
        m = max(4, int(round(ui * (NFFT * (f[1] - f[0]) * 2) / 1.0)))
        # samples per UI on the existing time grid
        dt = 1.0 / (2.0 * f[-1])
        m = max(4, int(round(ui / dt)))
        full = np.concatenate([ch['s21'], np.conj(ch['s21'][-2:0:-1])])
        imp = np.real(np.fft.ifft(full))
        pulse = np.convolve(imp, np.ones(m))[:NFFT]
        pk = int(np.argmax(np.abs(pulse)))
        cursor = float(abs(pulse[pk]))
        dt_ps = dt * 1e12
        # Slew from the 20-80 per cent rise of the leading edge. Taking the
        # derivative at 'the last zero crossing before the peak' fails on a
        # low-loss pulse, which has almost no precursor undershoot, so the
        # crossing lands in a flat region and the slope comes out near zero.
        sgn = 1.0 if pulse[pk] >= 0 else -1.0
        y = sgn * pulse[:pk + 1]
        ypk = y[pk]

        def _cross(frac):
            lvl = frac * ypk
            i = pk
            while i > 1 and y[i] > lvl:
                i -= 1
            if i >= pk:
                return float(pk)
            y0, y1 = y[i], y[i + 1]
            return i + ((lvl - y0) / (y1 - y0) if y1 != y0 else 0.0)

        i20, i80 = _cross(0.2), _cross(0.8)
        tr_samples = max(i80 - i20, 1e-9)
        slope_norm = 0.6 * ypk / (tr_samples * dt_ps)
        i0 = int(_cross(0.5))
        # scale so the transmitted swing is amp_mv
        scale = amp_mv
        cursor_mv = cursor * scale
        slew = slope_norm * scale
        j_rms = noise_mv_rms / slew if slew > 0 else float('nan')
        rows.append(dict(rate_gbps=r, ui_ps=float(ui * 1e12),
                         samples_per_ui=int(m),
                         rise_time_ps=float(tr_samples * dt_ps),
                         rise_time_ui=float(tr_samples * dt_ps / (ui * 1e12)),
                         cursor_mv=float(cursor_mv),
                         slew_mv_per_ps=float(slew),
                         jitter_rms_ps=float(j_rms),
                         jitter_rms_ui=float(j_rms / (ui * 1e12)),
                         jitter_pp_ui_at_1e12=float(
                             2 * q_from_ber(1e-12) * j_rms / (ui * 1e12))))
    return dict(rows=rows, noise_mv_rms=noise_mv_rms, amp_mv=amp_mv)


def equalised_pulse(ch, nf=9, nb=5, sigma_n=0.0015):
    """The pulse response a sampler actually sees, after the receive equaliser.

    The dual-Dirac model and every jitter measurement are applied at the
    slicer, not at the connector, so the data-dependent jitter that matters is
    the residual left after equalisation. On a channel losing thirty decibels
    the unequalised crossings spread over about two unit intervals and the eye
    never opens at all, which makes the unequalised distribution useless for
    testing a model whose whole purpose is to describe an open eye.
    """
    SM = ch['sm']
    p = pulse_from_s21(ch['s21'], ch['M'], ch['NFFT'])
    taps, cur = cursors(p, ch['M'])
    h = taps / max(abs(taps[cur]), 1e-30)
    w, c, dpos = SM.mmse_ffe_dfe(h, cur, nf=nf, nb=nb, sigma_n=sigma_n)
    # apply the same feed-forward filter to the oversampled pulse, so the
    # crossing can be located to better than a symbol
    m = ch['M']
    up = np.zeros((len(w) - 1) * m + 1)
    up[::m] = w
    peq = np.convolve(p, up)[:len(p)]
    return dict(pulse=peq, taps=c, cursor_index_taps=dpos,
                w=w, M=m, n_dfe=nb)
