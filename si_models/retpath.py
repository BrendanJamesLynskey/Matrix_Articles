"""Return paths and reference planes -- the model behind deck 02.

Every signal current is a loop. The trace is the half of the loop that appears
on the schematic; the other half flows in the reference plane, and almost
every surprise in a high-speed board comes from designers attending to the
first half and assuming the second will look after itself.

Three results here carry the deck.

`return_fraction()` computes where the return current actually is. Above the
frequency at which inductance rather than resistance decides the path, the
current arranges itself to minimise loop inductance, which puts it in a narrow
band directly under the trace with a Lorentzian profile. Integrating that
profile says 79.5 per cent of it lies within three trace heights either side,
which is the origin of the eighty-per-cent rule of thumb quoted by both
Johnson and Hall and Heck -- and `verify_against_solver()` checks the profile
itself against the charge distribution the field solver computes.

`slot_inductance()` prices the classic mistake: a trace crossing a gap in its
reference plane. The return current cannot follow, so it goes around, and the
loop it is forced into adds series inductance. The deck turns that inductance
into a reflection and an insertion-loss figure rather than leaving it as a
warning.

`cavity_modes()` is where this deck hands over to power integrity: a pair of
planes is a resonant cavity, and the frequencies at which it rings are set by
its outline, not by anything on the schematic.
"""

import numpy as np

MU0 = 4.0e-7 * np.pi
C0 = 299792458.0
EPS0 = 1.0 / (MU0 * C0 * C0)
INCH = 0.0254


# ------------------------------------------- where the return current flows ---

def return_current_density(x_over_h):
    """Normalised return-current density at lateral distance x, height h.

    For a filamentary conductor at height h above a perfectly conducting
    plane, the image solution gives a Lorentzian profile,

        J(x) = (I / pi h) * 1 / (1 + (x/h)^2),

    normalised so that the integral over the whole plane returns the full
    current. It is the same function as the surface charge distribution,
    because both come from the same two-dimensional potential problem.
    """
    x = np.asarray(x_over_h, float)
    return 1.0 / (np.pi * (1.0 + x * x))


def return_fraction(k):
    """Fraction of the return current within +/- k trace heights of centre."""
    return float(2.0 / np.pi * np.arctan(k))


def verify_return_fraction():
    """The origin of the eighty-per-cent rule, and the width it really implies."""
    out = {k: return_fraction(k) for k in (0.5, 1, 2, 3, 5, 10, 20)}
    return dict(fractions=out,
                at_3h=out[3], published_rule=0.80,
                err_pct=100 * (out[3] / 0.80 - 1),
                half_width_for_50pct=1.0,      # tan(pi/4)
                half_width_for_90pct=float(np.tan(0.9 * np.pi / 2)),
                half_width_for_99pct=float(np.tan(0.99 * np.pi / 2)))


def verify_against_solver(h_mm=0.20, w_mm=0.20, er=4.0, cell=0.005, box=24):
    """Check the Lorentzian against the field solver's own charge profile.

    The solver knows nothing about images or Lorentzians -- it relaxes a
    potential on a grid -- so agreement between the two is a real check on
    both.
    """
    from .fdm2d import CrossSection, EPS0 as E0
    W = box * h_mm
    HT = 12 * h_mm
    cs = CrossSection(W, HT, cell)
    cs.dielectric(0, W, 0, h_mm, er)
    cs.ground_plane(0, cell)
    cs.conductor(W / 2 - w_mm / 2, W / 2 + w_mm / 2, h_mm, h_mm + 0.018, 1)
    phi = cs._relax(cs.eps, 1)

    # surface charge on the plane is eps * E_normal, one cell above the metal
    j = int(round(cell / cell))
    row = cs.cond[j + 1, :] == 0
    e_norm = (phi[j + 1, :] - phi[j, :]) / cs.h
    sigma = cs.eps[j + 1, :] * e_norm
    sigma = np.where(row, sigma, 0.0)
    x = (np.arange(cs.nx) - cs.nx / 2.0) * cell / h_mm
    sigma = np.abs(sigma)
    if sigma.sum() <= 0:
        return dict(ok=False)
    prof = sigma / np.trapezoid(sigma, x)
    lor = return_current_density(x)

    def frac(p):
        m = np.abs(x) <= 3.0
        return float(np.trapezoid(p[m], x[m]) / np.trapezoid(p, x))
    return dict(x_over_h=x.tolist(), solver=prof.tolist(), lorentzian=lor.tolist(),
                frac_3h_solver=frac(prof), frac_3h_lorentzian=frac(lor),
                peak_ratio=float(prof.max() / lor.max()))


def crossover_frequency(w_mm, h_mm, sigma=5.8e7):
    """Where the return path stops being resistive and starts being inductive.

    At low frequency the current spreads out to minimise resistance; at high
    frequency it bunches under the trace to minimise inductance. The changeover
    is where the plane's sheet resistance over the effective return width
    matches the reactance of the loop inductance.
    """
    w_eff = 6.0 * h_mm * 1e-3          # the +/-3h band
    l_loop = MU0 * h_mm * 1e-3 / w_eff  # per metre, parallel-plate estimate
    t_plane = 35e-6
    r_sheet = 1.0 / (sigma * t_plane * w_eff)
    return dict(f_hz=float(r_sheet / (2 * np.pi * l_loop)),
                l_loop_h_per_m=float(l_loop), r_per_m=float(r_sheet))


# ----------------------------------------------------- gaps and detours ------

def rect_loop_inductance(a_m, b_m, r_m=50e-6):
    """Self-inductance of a rectangular loop of sides a and b (Grover)."""
    a, b, r = a_m, b_m, r_m
    d = np.sqrt(a * a + b * b)
    return (MU0 / np.pi) * (a * np.log(2 * a * b / (r * (a + d)))
                            + b * np.log(2 * a * b / (r * (b + d)))
                            + 2 * d - 1.75 * (a + b))


def slot_crossing(slot_len_mm=20.0, gap_mm=1.0, h_mm=0.2, z0=50.0,
                  f_ghz=None, tr_ps=30.0):
    """A trace crossing a slot in its reference plane.

    The return current cannot cross the slot, so it runs to the end of the slot
    and back. That detour is a loop of roughly half the slot length by the gap
    width, and its inductance appears in series with the signal. A series
    inductance L in a line of impedance Z0 gives

        S21 = 1 / (1 + j w L / 2 Z0),

    so the model reports the reflection and the loss rather than only the
    inductance, and reports what the same trace would see with the plane
    intact for comparison.
    """
    a = 0.5 * slot_len_mm * 1e-3
    b = max(gap_mm, 2 * h_mm) * 1e-3
    l_gap = rect_loop_inductance(a, b)
    l_intact = MU0 * (gap_mm * 1e-3) * (h_mm * 1e-3) / (6 * h_mm * 1e-3)

    f = np.logspace(7, 10.7, 400) if f_ghz is None else np.atleast_1d(f_ghz) * 1e9
    w = 2 * np.pi * f
    x = 1j * w * l_gap / (2 * z0)
    s21 = 1.0 / (1.0 + x)
    s11 = x / (1.0 + x)
    f_knee = 0.35 / (tr_ps * 1e-12)
    xk = 2 * np.pi * f_knee * l_gap / (2 * z0)
    return dict(l_gap_nh=float(l_gap * 1e9), l_intact_nh=float(l_intact * 1e9),
                ratio=float(l_gap / max(l_intact, 1e-18)),
                f_ghz=(f / 1e9).tolist(),
                s21_db=(20 * np.log10(np.abs(s21))).tolist(),
                s11_db=(20 * np.log10(np.abs(s11) + 1e-15)).tolist(),
                f_knee_ghz=float(f_knee / 1e9),
                s11_at_knee_db=float(20 * np.log10(abs(xk / (1 + xk)))),
                # The series reactance at the knee. Quoting an 'apparent
                # impedance' here would be misleading: once it is comparable
                # with Z0 the discontinuity is far outside the small-reflection
                # regime and the line is simply open at those frequencies.
                xl_at_knee_ohm=float(2 * np.pi * f_knee * l_gap))


def stitching_via(distance_mm=2.0, plane_gap_mm=0.2, via_d_mm=0.3, n_return=1):
    """Loop inductance added when a signal changes reference plane.

    A signal via that moves between layers referenced to different planes needs
    somewhere for its return current to follow. If the two planes are at the
    same potential a stitching via does it; the penalty is the inductance of
    the loop between signal via and stitching via, which grows as the log of
    their separation -- so the first stitching via matters enormously and the
    tenth hardly at all.

    For a single return via the loop inductance is mu0 h ln(s/r) / pi, which in
    Johnson's units is 5.08 h (2 ln(s/r)) nH with the dimensions in inches;
    the two expressions are the same number. He gives fitted forms for two and
    four return vias as well, and those are used here, because symmetric return
    paths cancel part of the flux rather than simply halving the inductance.
    """
    s_m = distance_mm * 1e-3
    h_m = plane_gap_mm * 1e-3
    r_m = via_d_mm * 1e-3 / 2
    h_in, s_in, r_in = h_m / INCH, s_m / INCH, r_m / INCH
    ln_sr = np.log(s_in / r_in)
    if n_return >= 4:
        l_nh = h_in * 5.08 * (1.25 * ln_sr - 0.347)
    elif n_return >= 2:
        l_nh = h_in * 5.08 * (1.50 * ln_sr - 0.347)
    else:
        l_nh = h_in * 5.08 * (2.00 * ln_sr)
    l_nh = max(l_nh, 0.0)
    return dict(distance_mm=distance_mm, n_return=n_return,
                l_nh=float(l_nh), l_si_check_nh=float(MU0 * h_m / np.pi
                                                      * ln_sr * 1e9),
                xl_at_10ghz=float(2 * np.pi * 10e9 * l_nh * 1e-9))


def stitching_capacitor(cap_nf=10.0, esl_ph=500.0, plane_gap_mm=0.2,
                        distance_mm=2.0):
    """The same transition where the planes are at different potentials.

    A stitching capacitor is the only route, and it brings its own mounting
    inductance, which above its series resonance is all the signal sees.
    """
    c = cap_nf * 1e-9
    l = esl_ph * 1e-12 + stitching_via(distance_mm, plane_gap_mm)['l_nh'] * 1e-9  # noqa
    f_res = 1.0 / (2 * np.pi * np.sqrt(l * c))
    return dict(f_series_res_mhz=float(f_res / 1e6), l_total_nh=float(l * 1e9),
                z_at_10ghz=float(2 * np.pi * 10e9 * l))


# ------------------------------------------------- the planes as a cavity ----

def cavity_modes(w_mm=150.0, l_mm=100.0, er=4.0, n=6):
    """Resonant frequencies of a rectangular plane pair.

    Two planes separated by a thin dielectric form a parallel-plate waveguide
    whose edges behave approximately as open circuits -- magnetic walls -- so
    the cavity resonates at

        f_mn = (c / 2 sqrt(er)) sqrt((m/W)^2 + (n/L)^2).

    These are the peaks a power-plane impedance measurement shows above a few
    hundred megahertz, and they are set by the board outline rather than by any
    component on it, which is why they cannot be decoupled away.
    """
    W, L = w_mm * 1e-3, l_mm * 1e-3
    out = []
    for m in range(n):
        for k in range(n):
            if m == 0 and k == 0:
                continue
            f = C0 / (2 * np.sqrt(er)) * np.sqrt((m / W) ** 2 + (k / L) ** 2)
            out.append(dict(m=m, n=k, f_ghz=float(f / 1e9)))
    out.sort(key=lambda d: d['f_ghz'])
    return out


def plane_impedance(w_mm=150.0, l_mm=100.0, h_um=100.0, er=4.0,
                    f=None, loss_tangent=0.02, n_modes=5):
    """Impedance between a plane pair, as a modal sum.

    Below the first cavity mode the pair is simply a capacitor; above it, the
    modes dominate and the impedance is a comb of peaks.
    """
    if f is None:
        f = np.logspace(6, 10, 600)
    W, L, h = w_mm * 1e-3, l_mm * 1e-3, h_um * 1e-6
    c_plane = EPS0 * er * W * L / h
    w = 2 * np.pi * f
    y = 1j * w * c_plane * (1 + 1j * loss_tangent)
    for m in range(n_modes):
        for k in range(n_modes):
            if m == 0 and k == 0:
                continue
            fmn = C0 / (2 * np.sqrt(er)) * np.sqrt((m / W) ** 2 + (k / L) ** 2)
            wmn = 2 * np.pi * fmn
            q = 1.0 / loss_tangent
            y += 1j * w * c_plane * 4.0 / ((1 - (w / wmn) ** 2) - 1j * (w / wmn) / q)
    z = 1.0 / y
    return dict(f_ghz=(f / 1e9).tolist(), z_ohm=np.abs(z).tolist(),
                c_plane_nf=float(c_plane * 1e9),
                f_first_mode_ghz=float(cavity_modes(w_mm, l_mm, er)[0]['f_ghz']))
