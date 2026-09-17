"""Transmission lines and the physical channel -- the model behind deck 01.

The deck argues three things and this file computes all three.

First, that a trace becomes a transmission line not at some fixed length but
when the signal's rise time becomes short compared with the round trip, and
that the behaviour then divides into the regions Johnson and Graham set out --
lumped, RC, LC, skin-effect, dielectric-loss and waveguide. `regions()`
reproduces their worked 100-ohm differential stripline example, which is close
enough to the SerDes_Equalisation channel to be a useful check on both.

Second, that fifty ohms is a convention rather than a law. `coax_optimum()`
derives the two impedances a coaxial cable actually wants to have -- the one
that minimises attenuation and the one that maximises power handling -- shows
that they are nowhere near each other, and lands on their geometric mean.

Third, that reflections are the arithmetic of a mismatch repeated. `bounce()`
sums the series explicitly and `tdr()` turns a cascade of mismatched segments
into the reflected waveform an instrument would actually show.
"""

import numpy as np

C0 = 299792458.0
MU0 = 4.0e-7 * np.pi
EPS0 = 1.0 / (MU0 * C0 * C0)
ETA0 = MU0 * C0                      # 376.730... ohms
INCH = 0.0254


# ------------------------------------------------------------ why 50 ohms ---

def coax_optimum(er=1.0, n=400):
    """The two impedances a coaxial line wants, and the compromise between them.

    Hold the outer radius b fixed -- it is what the connector shell and the
    hole in the bulkhead decide -- and vary the inner radius a. Write x = b/a.

    Attenuation. The conductor loss per unit length goes as the surface
    resistance divided by the perimeter, summed over both conductors and
    divided by the impedance, which makes it proportional to (x + 1) / ln(x).
    That has a single minimum.

    Power handling. Breakdown happens first at the inner conductor, where the
    field is strongest, so fix E_max and ask how much power the line carries.
    With V = E_max * a * ln(x) and P = V^2 / 2 Z0, the power is proportional to
    ln(x) / x^2, which peaks where ln(x) = 1/2.

    Neither optimum is at fifty ohms, and they are a factor of two and a half
    apart, so the familiar number is a compromise rather than a derivation.
    """
    x = np.linspace(1.05, 12.0, n)
    z = ETA0 / (2 * np.pi * np.sqrt(er)) * np.log(x)
    atten = (x + 1.0) / np.log(x)              # arbitrary scale
    power = np.log(x) / x ** 2                 # arbitrary scale
    i_lo = int(np.argmin(atten))
    i_hi = int(np.argmax(power))

    # refine both by golden-section on the analytic expressions
    def golden(f, lo, hi, sign=1.0):
        gr = (np.sqrt(5) - 1) / 2
        c, d = hi - gr * (hi - lo), lo + gr * (hi - lo)
        for _ in range(200):
            if sign * f(c) < sign * f(d):
                hi = d
            else:
                lo = c
            c, d = hi - gr * (hi - lo), lo + gr * (hi - lo)
        return 0.5 * (lo + hi)

    x_att = golden(lambda t: (t + 1) / np.log(t), 1.5, 8.0, +1.0)
    x_pow = golden(lambda t: np.log(t) / t ** 2, 1.1, 5.0, -1.0)
    z_att = ETA0 / (2 * np.pi * np.sqrt(er)) * np.log(x_att)
    z_pow = ETA0 / (2 * np.pi * np.sqrt(er)) * np.log(x_pow)
    return dict(x=x.tolist(), z=z.tolist(),
                atten=(atten / atten[i_lo]).tolist(),
                power=(power / power[i_hi]).tolist(),
                x_min_atten=float(x_att), z_min_atten=float(z_att),
                x_max_power=float(x_pow), z_max_power=float(z_pow),
                z_geometric_mean=float(np.sqrt(z_att * z_pow)),
                er=er)


# -------------------------------------------------- per-unit-length models ---

def skin_resistance(f, perimeter, sigma=5.8e7, kp=1.0, r_dc=None):
    """Series resistance per metre, blending the DC and skin-limited values.

    Below the frequency where the skin depth exceeds the conductor thickness
    the resistance is simply the DC value; above it the current is confined to
    a layer of depth sqrt(2 / omega mu sigma) around the perimeter. The two are
    combined in quadrature, which is the usual smooth interpolation and is
    accurate to a few per cent through the knee.

    `kp` is Johnson's proximity factor: current does not spread uniformly
    around the perimeter, it crowds on the faces that look at the return
    conductor, and the factor is how much that raises the resistance above the
    uniform-perimeter estimate.
    """
    f = np.asarray(f, dtype=float)
    r_ac = kp / perimeter * np.sqrt(2 * np.pi * f * MU0 / (2 * sigma))
    if r_dc is None:
        return r_ac
    return np.sqrt(r_dc ** 2 + r_ac ** 2)


def dielectric_conductance(f, C, tand):
    """Shunt conductance per metre for a loss tangent tand: G = omega C tan(d)."""
    return 2 * np.pi * np.asarray(f, dtype=float) * C * tand


def gamma_z0(f, R, L, G, C):
    """Propagation constant and characteristic impedance from RLGC."""
    w = 2 * np.pi * np.asarray(f, dtype=float)
    Zs = R + 1j * w * L
    Yp = G + 1j * w * C
    g = np.sqrt(Zs * Yp)
    z0 = np.sqrt(Zs / Yp)
    g = np.where(g.real < 0, -g, g)
    return g, z0


# ------------------------------------------------- Johnson's region model ---

def regions(length_m=0.6, w=152e-6, t=17.4e-6, sigma=5.98e7, b=508e-6,
            z0=100.0, er_eff=4.3, tand=0.025, kp=3.2, f0=1e9):
    """Onset frequencies of the six propagation regions.

    Defaults are Johnson and Graham's worked example (Advanced Black Magic,
    section 3.10): a 100-ohm differential stripline 0.6 m long on FR-4. Our
    values are checked against their published table in `verify()`.
    """
    p = 2 * (w + t)
    v0 = C0 / np.sqrt(er_eff)
    L = z0 / v0
    C = 1.0 / (z0 * v0)
    r_dc = 2.0 / (sigma * w * t)          # two conductors in series
    w0 = 2 * np.pi * f0
    r0 = kp / p * np.sqrt(w0 * MU0 / (2 * sigma))

    w_lc = 0.25 / length_m / np.sqrt(L * C)
    w_skin = w0 * (r_dc / r0) ** 2
    w_diel = (1.0 / w0) * ((v0 * r0) / (z0 * tand)) ** 2
    w_wg = np.pi * v0 / b
    crit_len = (0.25 / r_dc) * np.sqrt(L / C)
    return dict(v0=v0, tpd_ps_per_in=1e12 * INCH / v0, L=L, C=C,
                r_dc=r_dc, r_ac_f0=r0, perimeter=p,
                f_lc=w_lc / 2 / np.pi, f_skin=w_skin / 2 / np.pi,
                f_diel=w_diel / 2 / np.pi, f_wg=w_wg / 2 / np.pi,
                critical_length_m=crit_len, length_m=length_m)


def verify_against_johnson():
    """Reproduce the published breakpoint table and report the error."""
    r = regions()
    published = dict(f_lc=9.58e6, f_skin=27.1e6, f_diel=498e6, f_wg=142e9,
                     v0=1.4457e8, L=691e-9, C=69.1e-12,
                     r_dc=12.64, r_ac_f0=76.74, critical_length_m=1.97)
    out = {}
    for k, ref in published.items():
        out[k] = dict(ours=float(r[k]), johnson=float(ref),
                      err_pct=float(100 * (r[k] / ref - 1)))
    out['worst_err_pct'] = float(max(abs(v['err_pct']) for v in out.values()
                                     if isinstance(v, dict)))
    return out


def electrically_short(tr_s, length_m, v0):
    """How many rise times fit in the round trip.

    The usual rule of thumb is that a line may be treated as lumped while the
    round-trip delay is below about a sixth of the rise time; the ratio is
    reported so a reader can apply whichever threshold their house style uses
    rather than inheriting ours.
    """
    tpd = length_m / v0
    return dict(one_way_delay_s=tpd, round_trip_s=2 * tpd,
                ratio_round_trip_to_tr=2 * tpd / tr_s,
                lumped_by_sixth_rule=bool(2 * tpd < tr_s / 6.0),
                critical_length_m=v0 * tr_s / 12.0)


# ------------------------------------------------------------ reflections ---

def bounce(zs, z0, zl, n=12):
    """The reflection series on a mismatched line, term by term.

    A source of impedance `zs` drives a line of impedance `z0` terminated in
    `zl`. The launched step is divided by the source divider, and thereafter
    each arrival at an end is multiplied by that end's reflection coefficient.
    Returning the terms rather than only the sum lets the deck show the
    staircase settling rather than assert that it does.
    """
    gl = (zl - z0) / (zl + z0)
    gs = (zs - z0) / (zs + z0)
    a0 = z0 / (z0 + zs)
    steps, v, amp = [], 0.0, a0
    for k in range(n):
        v += amp                       # incident arrives at the load
        steps.append(dict(t_units=2 * k + 1, v_load=v))
        amp *= gl                      # reflects off the load
        v += amp
        steps[-1]['v_load'] = v
        amp *= gs                      # and off the source
    return dict(gamma_load=float(gl), gamma_source=float(gs),
                v_final=float(zl / (zl + zs)), steps=steps)


def _abcd_tl(gamma, z0, length):
    gl = gamma * length
    ch, sh = np.cosh(gl), np.sinh(gl)
    return np.array([[ch, z0 * sh], [sh / z0, ch]], dtype=complex)


def tdr(segments, tr_ps=20.0, z_ref=50.0, fmax=60e9, nfft=8192, er=4.0,
        ac_db_in_sqrtghz=0.0, ad_db_in_ghz=0.0):
    """Synthesise a TDR trace for a cascade of transmission-line segments.

    Each segment is a dict with `z0` in ohms and `length_in` in inches. The
    cascade is built in the frequency domain as a product of ABCD matrices,
    converted to S11 against the reference impedance, multiplied by the
    spectrum of a step with a raised-cosine edge, and transformed back.

    The impedance profile is then read off the reflected wave using the
    single-reflection relation Z = Z0 (1 + rho) / (1 - rho). That relation is
    exact only for the first discontinuity, which is precisely why a real TDR
    misreads the impedance of a segment hiding behind an earlier mismatch --
    the deck makes that point with this function.
    """
    df = fmax / (nfft // 2)
    f = np.arange(nfft // 2 + 1) * df
    f[0] = df * 1e-6
    v0 = C0 / np.sqrt(er)
    tpd = INCH / v0

    s11 = np.zeros_like(f, dtype=complex)
    A = np.zeros((2, 2, f.size), dtype=complex)
    A[0, 0] = 1.0
    A[1, 1] = 1.0
    for seg in segments:
        ln = seg['length_in']
        a_db = (ac_db_in_sqrtghz * np.sqrt(f / 1e9) + ad_db_in_ghz * f / 1e9) * ln
        alpha = a_db / 8.686 / (ln * INCH) if ln > 0 else 0.0
        g = alpha + 1j * 2 * np.pi * f * tpd / INCH
        M = _abcd_tl(g, seg['z0'], ln * INCH)
        A = np.einsum('ijf,jkf->ikf', A, M)
    a, b_, c, d = A[0, 0], A[0, 1], A[1, 0], A[1, 1]
    den = a + b_ / z_ref + c * z_ref + d
    s11 = (a + b_ / z_ref - c * z_ref - d) / den

    # a step whose edge is a raised cosine of 10-90 rise time tr
    tr = tr_ps * 1e-12
    fknee = 0.35 / tr
    edge = np.exp(-(f / (1.6 * fknee)) ** 2)
    # The instrument launches a step, so the reflected wave is the running
    # integral of the impulse response. rho is then read directly, because the
    # incident step has unit height.
    h11 = np.fft.irfft(s11 * edge, n=nfft)
    refl = np.cumsum(h11)
    t = np.arange(nfft) / (2 * fmax)
    rho = np.clip(refl, -0.98, 0.98)
    z_prof = z_ref * (1 + rho) / (1 - rho)
    keep = t < 4e-9
    return dict(t_ns=(t[keep] * 1e9).tolist(),
                rho=rho[keep].tolist(),
                z_profile=z_prof[keep].tolist(),
                f_ghz=(f / 1e9).tolist(),
                s11_db=(20 * np.log10(np.abs(s11) + 1e-12)).tolist(),
                tpd_ps_per_in=tpd * 1e12)
