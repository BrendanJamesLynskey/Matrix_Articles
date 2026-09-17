"""Conductor loss, dielectric loss and causality -- the model behind deck 03.

Two independent mechanisms attenuate a signal on a board and they scale
differently, which is the whole reason the deck exists: conductor loss rises
roughly as the square root of frequency and dielectric loss roughly in
proportion to it, so the mix changes as the data rate rises and the right
thing to spend money on changes with it.

Three things here are easy to get wrong and are therefore checked against
published worked examples rather than asserted.

`hammerstad()` and `huray()` are the two standard roughness corrections.
Hammerstad fits Morgan's 1949 corrugated-surface results to an arctangent and
saturates at a factor of two however rough the copper gets; Huray treats the
tooth structure as a cluster of spheres and does not saturate, which is why it
survives above about 5 GHz where Hammerstad stops tracking measurement. Both
reproduce the worked examples in Hall and Heck, chapter 5.

`djordjevic_sarkar()` builds a causal permittivity. A constant Dk with a
constant loss tangent, which is what a datasheet quotes and what a careless
model implements, violates the Kramers-Kronig relations -- and a non-causal
channel model produces a pulse response that begins before the pulse does.
`causality_error()` measures that, in picoseconds and in millivolts.
"""

import numpy as np

MU0 = 4.0e-7 * np.pi
C0 = 299792458.0
EPS0 = 1.0 / (MU0 * C0 * C0)
SIGMA_CU = 5.8e7
INCH = 0.0254


# --------------------------------------------------------------- laminates ---
# Dk and Df as published by the laminate suppliers, quoted at 10 GHz unless
# the datasheet only characterises a lower frequency. These are nominal design
# values; a real stackup varies with resin content, glass style and direction.
LAMINATES = {
    'FR-4 (generic)':      dict(dk=4.30, df=0.0200, f_ref=1e9,  era='1990s'),
    'Isola 370HR':         dict(dk=4.04, df=0.0210, f_ref=1e9,  era='mainstream'),
    'Isola I-Speed':       dict(dk=3.56, df=0.0060, f_ref=10e9, era='mid-loss'),
    'Panasonic Megtron 6': dict(dk=3.40, df=0.0040, f_ref=12e9, era='low-loss'),
    'Panasonic Megtron 7': dict(dk=3.35, df=0.0020, f_ref=12e9, era='ultra-low-loss'),
    'Rogers RO4350B':      dict(dk=3.48, df=0.0037, f_ref=10e9, era='RF laminate'),
    'Rogers RO3003':       dict(dk=3.00, df=0.0010, f_ref=10e9, era='PTFE'),
}

# Copper foil profiles, RMS tooth height in micrometres.
FOILS = {
    'standard (STD)':        1.80,
    'reverse-treat (RTF)':   1.20,
    'very low profile (VLP)': 0.70,
    'hyper very low (HVLP)': 0.40,
    'ultra low (HVLP2)':     0.25,
}


def skin_depth(f, sigma=SIGMA_CU, mu=MU0):
    return np.sqrt(2.0 / (2 * np.pi * np.asarray(f, float) * mu * sigma))


def hammerstad(f, rms_um, sigma=SIGMA_CU):
    """Hammerstad-Jensen roughness correction factor.

    K = 1 + (2/pi) arctan(1.4 (delta_rms / skin_depth)^2).

    The arctangent is bounded by pi/2, so K cannot exceed 2 no matter how rough
    the copper is. That ceiling is the model's well-known defect: measured
    losses on rough foil go well past twice the smooth value.
    """
    d = skin_depth(f, sigma)
    r = (rms_um * 1e-6) / d
    return 1.0 + (2.0 / np.pi) * np.arctan(1.4 * r * r)


def huray(f, a_um=0.8, n_spheres=20, tile_um=9.4, er=4.0, sigma=SIGMA_CU):
    """Huray 'snowball' roughness correction, by the scattering formulation.

    The tooth structure is replaced by N copper spheres of radius a sitting on
    a flat tile. The power a sphere absorbs from the tangential magnetic field
    follows from the first-order Mie scattering coefficient, and the correction
    factor is the ratio of total absorbed power (tile plus spheres) to the
    power the flat tile alone would absorb.

    Unlike Hammerstad this has no ceiling: enough spheres, or big enough ones,
    give an arbitrarily large factor, which is what measurement on rough foil
    actually shows.
    """
    f = np.asarray(f, float)
    w = 2 * np.pi * f
    d = skin_depth(f, sigma)
    a = a_um * 1e-6
    tile = (tile_um * 1e-6) ** 2
    eta = np.sqrt(MU0 / (EPS0 * er))
    k = w * np.sqrt(MU0 * EPS0 * er)

    num = 1.0 - (d / a) * (1 + 1j)
    den = 1.0 + (d / (2 * a)) * (1 + 1j)
    alpha1 = -(2j / 3.0) * (k * a) ** 3 * num / den

    p_flat = MU0 * w * d / 4.0 * tile
    p_sph = n_spheres * np.abs(np.real(0.5 * eta * (3 * np.pi / k ** 2) * alpha1))
    return 1.0 + p_sph / p_flat


def huray_sphere_count(h_tooth_um, b_base_um, a_um=0.8):
    """How many spheres replicate a hemispheroidal tooth of the measured size."""
    h, b = h_tooth_um, b_base_um
    # lateral area of a prolate hemispheroid of height h on a base of width b
    rt = np.sqrt(max(1e-12, 1.0 - (b / 2) ** 2 / h ** 2))
    a_lat = np.pi * (b / 2) * (h * np.arcsin(rt) / rt + b / 2)
    a_sphere = 4 * np.pi * a_um ** 2
    return dict(area_um2=float(a_lat), n=float(a_lat / a_sphere))


def verify_roughness():
    """Reproduce the worked roughness examples in Hall and Heck, chapter 5."""
    # Example 5-3: RMS tooth 1.8 um, the frequency where skin depth equals it
    fr = 2.0 / (2 * np.pi * SIGMA_CU * MU0 * (1.8e-6) ** 2)
    kh = hammerstad(2e9, 1.8)
    # Example 5-5: 20 spheres of 0.8 um radius on a 9.4 um tile at 5 GHz
    khu = huray(5e9, a_um=0.8, n_spheres=20, tile_um=9.4, er=4.0)
    cnt = huray_sphere_count(5.8, 9.4, 0.8)
    return dict(
        f_rough_onset=dict(ours=float(fr), published=1.34e9,
                           err_pct=float(100 * (fr / 1.34e9 - 1))),
        hammerstad_rac_ratio=dict(ours=float(kh), published=8.4 / 4.86,
                                  err_pct=float(100 * (kh / (8.4 / 4.86) - 1))),
        huray_factor=dict(ours=float(khu), published=1.95,
                          err_pct=float(100 * (khu / 1.95 - 1))),
        huray_sphere_area_um2=dict(ours=cnt['area_um2'], published=161.0,
                                   err_pct=float(100 * (cnt['area_um2'] / 161.0 - 1))),
    )


# ------------------------------------------------------- causal dielectric ---

def djordjevic_sarkar(f, dk_ref, df_ref, f_ref=1e10, f1=1e3, f2=1e12):
    """A causal wideband-Debye permittivity matched to a datasheet point.

    A real dielectric has a loss tangent that is nearly flat over many decades,
    which no single Debye relaxation produces. Djordjevic and Sarkar obtain it
    by superposing a continuum of relaxations between two frequency limits m1
    and m2, which integrates to a closed form:

        eps(w) = eps_inf + (d_eps / ln(m2/m1)) * ln((m2 + jw)/(m1 + jw))

    Between m1 and m2 the imaginary part is almost constant and the real part
    falls logarithmically. That downward slope in Dk is not an inconvenience to
    be flattened away -- it is exactly what causality demands of any medium
    with loss, and it is what the Kramers-Kronig relations tie to the loss.
    """
    f = np.asarray(f, float)
    w = 2 * np.pi * f
    m1, m2 = 2 * np.pi * f1, 2 * np.pi * f2
    L = np.log(m2 / m1)
    w_ref = 2 * np.pi * f_ref

    # Choose d_eps so the loss tangent hits df_ref at f_ref, then eps_inf so
    # the real part hits dk_ref there.
    imag_shape = (np.arctan(w_ref / m1) - np.arctan(w_ref / m2)) / L
    d_eps = df_ref * dk_ref / imag_shape
    real_shape = 0.5 * np.log((m2 ** 2 + w_ref ** 2) / (m1 ** 2 + w_ref ** 2)) / L
    eps_inf = dk_ref - d_eps * real_shape

    ep = eps_inf + d_eps * 0.5 * np.log((m2 ** 2 + w ** 2) / (m1 ** 2 + w ** 2)) / L
    epp = d_eps * (np.arctan(w / m1) - np.arctan(w / m2)) / L
    return dict(dk=ep, df=epp / ep, eps_r=ep - 1j * epp,
                eps_inf=float(eps_inf), d_eps=float(d_eps))


def kramers_kronig_check(f, eps_r):
    """Recover the real part from the imaginary part and report the mismatch.

    The discrete Hilbert transform below is a finite-band approximation, so a
    perfect model will not give exactly zero; what matters is the contrast
    between a causal model and a constant-Dk one, which is orders of magnitude.
    """
    ep, epp = np.real(eps_r), -np.imag(eps_r)
    n = len(f)
    rec = np.zeros(n)
    for i in range(n):
        m = np.arange(n) != i
        integrand = f[m] * epp[m] / (f[m] ** 2 - f[i] ** 2)
        rec[i] = (2.0 / np.pi) * np.trapezoid(integrand, f[m])
    off = np.median(ep - rec)
    resid = ep - rec - off
    band = (f > f[n // 20]) & (f < f[-n // 20])
    return dict(rms_err=float(np.sqrt(np.mean(resid[band] ** 2))),
                rel_err_pct=float(100 * np.sqrt(np.mean(resid[band] ** 2))
                                  / np.mean(ep[band])))


def causality_error(length_in=10.0, dk=3.6, df=0.004, f_ref=1e10,
                    nfft=16384, fmax=100e9):
    """What a non-causal constant-Dk model does to a pulse response.

    Build the same line twice -- once with a flat Dk and flat loss tangent,
    once with the causal wideband-Debye fit that matches it at the reference
    frequency -- and transform both to the time domain. The constant-Dk line
    delivers energy before the causal one does, which is the signature of a
    model that cannot be realised by any physical medium.
    """
    df_step = fmax / (nfft // 2)
    f = np.arange(nfft // 2 + 1) * df_step
    f[0] = df_step * 1e-9
    ln = length_in * INCH

    def prop(dk_f, df_f):
        eps = dk_f * (1 - 1j * df_f)
        g = 1j * 2 * np.pi * f * np.sqrt(eps) / C0
        return np.exp(-g * ln)

    h_flat = prop(dk, df)
    ds = djordjevic_sarkar(f, dk, df, f_ref)
    h_caus = prop(ds['dk'], ds['df'])

    win = np.exp(-(f / (0.55 * fmax)) ** 4)
    t = np.arange(nfft) / (2 * fmax)
    y_flat = np.fft.irfft(h_flat * win, n=nfft)
    y_caus = np.fft.irfft(h_caus * win, n=nfft)

    def onset(y, frac=0.01):
        pk = np.max(np.abs(y))
        i = int(np.argmax(np.abs(y) > frac * pk))
        return t[i]

    t0_flat, t0_caus = onset(y_flat), onset(y_caus)
    tof = ln * np.sqrt(dk) / C0
    return dict(t_ns=(t[:nfft // 8] * 1e9).tolist(),
                y_flat=y_flat[:nfft // 8].tolist(),
                y_causal=y_caus[:nfft // 8].tolist(),
                onset_flat_ns=float(t0_flat * 1e9),
                onset_causal_ns=float(t0_caus * 1e9),
                time_of_flight_ns=float(tof * 1e9),
                precursor_ps=float((tof - t0_flat) * 1e12),
                dk_at_1ghz=float(np.interp(1e9, f, ds['dk'])),
                dk_at_40ghz=float(np.interp(40e9, f, ds['dk'])),
                dk_slope_per_decade=float(np.interp(1e9, f, ds['dk'])
                                          - np.interp(10e9, f, ds['dk'])))


# ------------------------------------------------------------- total loss ---

def loss_per_inch(f, dk, df, z0=50.0, w_um=150.0, t_um=17.4, rms_um=0.4,
                  kp=1.0, roughness='huray', sigma=SIGMA_CU, n_spheres=None):
    """Attenuation in dB per inch, split into its three contributions."""
    f = np.asarray(f, float)
    perim = 2 * (w_um + t_um) * 1e-6
    r_dc = 1.0 / (sigma * (w_um * 1e-6) * (t_um * 1e-6))
    r_ac = kp / perim * np.sqrt(2 * np.pi * f * MU0 / (2 * sigma))
    r_smooth = np.sqrt(r_dc ** 2 + r_ac ** 2)

    if roughness == 'hammerstad':
        k = hammerstad(f, rms_um, sigma)
    elif roughness == 'huray':
        n = n_spheres if n_spheres is not None else max(1.0, (rms_um / 0.4) ** 2 * 6.0)
        k = huray(f, a_um=max(0.25, rms_um), n_spheres=n,
                  tile_um=max(2.0, 5.0 * rms_um), er=dk)
    else:
        k = np.ones_like(f)
    r_rough = r_smooth * k

    a_c = r_rough / (2 * z0) * 8.686 * INCH               # dB/inch
    a_d = (np.pi * f * np.sqrt(dk) * df / C0) * 8.686 * INCH
    return dict(f=f, alpha_c=a_c, alpha_d=a_d,
                alpha_c_smooth=r_smooth / (2 * z0) * 8.686 * INCH,
                total=a_c + a_d, k_rough=k,
                crossover_ghz=float(np.interp(0.0, a_d - a_c, f) / 1e9)
                if np.any(a_d > a_c) and np.any(a_d < a_c) else float('nan'))


# ------------------------------------------------------------ fibre weave ---
# Weave styles, with the width of the resin window between yarn bundles
# relative to a dense reference, and the yarn pitch in millimetres. The
# anchor is 2116, for which Hall and Heck report a *measured* worst-case
# spread in effective permittivity of 0.23 on microstrip; the other styles are
# scaled by how open the weave is, which is a representative ordering rather
# than a measurement of any particular laminate.
WEAVES = {
    '106  (very open)':   dict(pitch_mm=0.55, openness=1.85),
    '1080 (open)':        dict(pitch_mm=0.60, openness=1.50),
    '2116 (measured)':    dict(pitch_mm=0.66, openness=1.00),
    '7628 (dense)':       dict(pitch_mm=0.74, openness=0.80),
    '3313 (flat)':        dict(pitch_mm=0.62, openness=0.55),
    'spread / mech. flat': dict(pitch_mm=0.60, openness=0.20),
}
DELTA_EREFF_2116 = 0.23      # Hall and Heck, fig. 6-15: 3.73 against 3.50


def fibre_weave(style='2116 (measured)', length_in=10.0, er_eff=3.60,
                angle_deg=0.0, f_ghz=None, delta_anchor=DELTA_EREFF_2116):
    """Intra-pair skew from the glass weave, and the mode conversion it causes.

    A woven laminate is not a uniform dielectric. The glass yarn has a
    permittivity near 6 and the resin around it near 3, and the windows between
    bundles are wide enough that one leg of a differential pair can sit over
    glass while the other sits over resin. The two legs then propagate at
    different speeds, and the pair arrives skewed.

    The quantity that matters is the spread in *effective* permittivity seen by
    the trace, not the contrast in the raw materials: the field of a trace
    spans several yarn pitches and several plies, so only a fraction of the
    material contrast survives the averaging. Hall and Heck measured that
    spread directly -- 0.23 across 64 parallel microstrips on 2116 cloth -- and
    that measurement is the anchor here rather than a mixing rule.

    Routing at an angle to the weave is the standard mitigation and the model
    computes rather than asserts it: a trace crossing N yarn pitches laterally
    averages a periodic modulation down by the sinc factor |sin(pi N)/(pi N)|,
    so a few degrees over a few inches is worth more than an order of
    magnitude.
    """
    w = WEAVES.get(style, WEAVES['2116 (measured)'])
    d_eff = delta_anchor * w['openness']

    # averaging from crossing the weave at an angle
    lat_mm = length_in * 25.4 * np.sin(np.deg2rad(angle_deg))
    n_periods = lat_mm / w['pitch_mm']
    if n_periods < 1e-9:
        avg = env = 1.0
    else:
        avg = abs(np.sin(np.pi * n_periods) / (np.pi * n_periods))
        env = min(1.0, 1.0 / (np.pi * n_periods))
    # The sinc has nulls, and at an exact null the model says the skew
    # vanishes. It does not: the weave is not a pure sinusoid, the angle is
    # not held to a fraction of a degree across a panel, and registration
    # shifts between layers. The envelope is therefore the number to design
    # to, and the sinc is reported only to show where the nulls sit.
    d_eff_routed = d_eff * env

    e1 = er_eff + d_eff_routed / 2.0
    e2 = er_eff - d_eff_routed / 2.0
    tpd1 = np.sqrt(e1) / C0 * INCH * 1e12
    tpd2 = np.sqrt(e2) / C0 * INCH * 1e12
    skew = (tpd1 - tpd2) * length_in

    out = dict(style=style, pitch_mm=w['pitch_mm'], angle_deg=angle_deg,
               delta_er_eff=float(d_eff), delta_er_eff_routed=float(d_eff_routed),
               averaging_factor=float(env), averaging_sinc=float(avg),
               n_weave_periods=float(n_periods),
               er_over_glass=float(e1), er_over_resin=float(e2),
               tpd_glass_ps_in=float(tpd1), tpd_resin_ps_in=float(tpd2),
               skew_ps=float(skew), skew_ps_per_in=float(skew / max(length_in, 1e-9)),
               # differential energy is converted to common mode as
               # |Scd21| = |sin(pi f tau)|, complete at half a period of skew
               f_full_conversion_ghz=float(1e3 / (2 * skew)) if skew > 1e-12 else float('inf'))
    if f_ghz is not None:
        c = abs(np.sin(np.pi * f_ghz * 1e9 * skew * 1e-12))
        out['scd21_db'] = float(20 * np.log10(max(c, 1e-12)))
        out['f_ghz'] = f_ghz
    return out


def verify_fibre_weave():
    """Reproduce Hall and Heck example 7-2: the frequency of full conversion."""
    a = fibre_weave('2116 (measured)', length_in=10.0, er_eff=3.615)
    b = fibre_weave('2116 (measured)', length_in=5.0, er_eff=3.615)
    return dict(
        ten_inch_ghz=dict(ours=a['f_full_conversion_ghz'], published=10.0,
                          err_pct=100 * (a['f_full_conversion_ghz'] / 10.0 - 1)),
        five_inch_ghz=dict(ours=b['f_full_conversion_ghz'], published=20.0,
                           err_pct=100 * (b['f_full_conversion_ghz'] / 20.0 - 1)),
        skew_ps_per_in=a['skew_ps_per_in'])
