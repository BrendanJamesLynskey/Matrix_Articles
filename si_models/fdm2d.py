"""A two-dimensional electrostatic field solver for PCB cross-sections.

Closed-form impedance formulas exist for the simple cross-sections and we use
them as checks, but they do not extend to a coupled pair beside a guard trace,
or to a microstrip whose fields are partly in air and partly in laminate. Both
of those matter to this series, so the cross-sections are solved rather than
looked up.

The method is the standard one. Laplace's equation for a piecewise-uniform
dielectric,

    div( eps grad(phi) ) = 0,

is discretised on a uniform grid with the permittivity of each cell face taken
as the harmonic mean of the two cells it separates, which is the combination
that conserves normal flux across a dielectric boundary. Each conductor in turn
is raised to one volt with the others held at zero, the resulting potential is
relaxed by red-black successive over-relaxation, and the charge on every
conductor is recovered by summing the discrete flux through the faces that
bound it. That gives the Maxwell capacitance matrix directly.

Running the same cross-section twice -- once with the real laminate and once
with every dielectric replaced by vacuum -- gives C and C_air, and the
inductance matrix follows from the fact that a transverse electromagnetic wave
in a uniform medium must travel at the speed of light in that medium:

    L = mu0 * eps0 * inv(C_air).

That identity is exact and it is what lets an electrostatic solver produce the
inductive part of the problem, including the mutual inductance that crosstalk
depends on.
"""

import numpy as np

EPS0 = 8.8541878128e-12
MU0 = 4.0e-7 * np.pi
C0 = 299792458.0


class CrossSection:
    """A rectangular window on a PCB cross-section, in millimetres.

    The window edges are held at zero volts, so they behave as a grounded
    enclosure. They must be placed far enough from the conductors that the
    enclosure does not change the answer; `check_box_margin` reports how far
    the fields have decayed by the time they reach the wall.
    """

    def __init__(self, width_mm, height_mm, cell_mm=0.005):
        self.h = cell_mm * 1e-3
        self.nx = int(round(width_mm / cell_mm))
        self.ny = int(round(height_mm / cell_mm))
        self.eps = np.ones((self.ny, self.nx))
        self.cond = np.zeros((self.ny, self.nx), dtype=np.int16)
        self._n_cond = 0

    # -- geometry -----------------------------------------------------------
    def _idx(self, x0, x1, y0, y1, atleast1=False):
        c = self.h * 1e3
        j0, j1 = int(round(y0 / c)), int(round(y1 / c))
        i0, i1 = int(round(x0 / c)), int(round(x1 / c))
        if atleast1:            # a feature thinner than a cell still exists
            j1 = max(j1, j0 + 1)
            i1 = max(i1, i0 + 1)
        return (max(0, j0), min(self.ny, j1), max(0, i0), min(self.nx, i1))

    def dielectric(self, x0, x1, y0, y1, er):
        j0, j1, i0, i1 = self._idx(x0, x1, y0, y1)
        self.eps[j0:j1, i0:i1] = er
        return self

    def conductor(self, x0, x1, y0, y1, cid):
        """Add (part of) conductor `cid`. Ground is conductor 0 by convention
        and is tied to the enclosure, so signal conductors start at 1."""
        j0, j1, i0, i1 = self._idx(x0, x1, y0, y1, atleast1=True)
        self.cond[j0:j1, i0:i1] = cid
        self._n_cond = max(self._n_cond, cid)
        return self

    def ground_plane(self, y0, y1):
        j0, j1, i0, i1 = self._idx(0, self.nx * self.h * 1e3, y0, y1, atleast1=True)
        self.cond[j0:j1, i0:i1] = -1          # -1 marks held-at-zero metal
        return self

    # -- solve --------------------------------------------------------------
    def _face_eps(self, eps):
        """Harmonic-mean permittivity on the faces between adjacent cells."""
        ex = 2.0 * eps[:, :-1] * eps[:, 1:] / (eps[:, :-1] + eps[:, 1:])
        ey = 2.0 * eps[:-1, :] * eps[1:, :] / (eps[:-1, :] + eps[1:, :])
        return ex, ey

    def _stencil(self, eps):
        ny, nx = self.ny, self.nx
        return self._stencil_on(eps, ny, nx)

    @staticmethod
    def _stencil_on(eps, ny, nx):
        ex = 2.0 * eps[:, :-1] * eps[:, 1:] / (eps[:, :-1] + eps[:, 1:])
        ey = 2.0 * eps[:-1, :] * eps[1:, :] / (eps[:-1, :] + eps[1:, :])
        aW = np.zeros((ny, nx)); aW[:, 1:] = ex
        aE = np.zeros((ny, nx)); aE[:, :-1] = ex
        aS = np.zeros((ny, nx)); aS[1:, :] = ey
        aN = np.zeros((ny, nx)); aN[:-1, :] = ey
        diag = aW + aE + aS + aN
        diag[diag == 0] = 1.0
        return aW, aE, aS, aN, diag

    @staticmethod
    def _neighbour_sum(phi, aW, aE, aS, aN):
        nb = np.zeros_like(phi)
        nb[:, 1:] += aW[:, 1:] * phi[:, :-1]
        nb[:, :-1] += aE[:, :-1] * phi[:, 1:]
        nb[1:, :] += aS[1:, :] * phi[:-1, :]
        nb[:-1, :] += aN[:-1, :] * phi[1:, :]
        return nb

    @classmethod
    def _sor(cls, phi, cond, eps, driven, tol, itmax):
        """Red-black SOR on one grid level, starting from `phi`."""
        ny, nx = phi.shape
        aW, aE, aS, aN, diag = cls._stencil_on(eps, ny, nx)
        fixed = cond != 0
        phi = phi.copy()
        phi[fixed] = 0.0
        phi[cond == driven] = 1.0
        rj = 0.5 * (np.cos(np.pi / nx) + np.cos(np.pi / ny))
        omega = min(2.0 / (1.0 + np.sqrt(1.0 - rj * rj)), 1.995)
        jj, ii = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
        masks = []
        for par in (0, 1):
            m = ((ii + jj) % 2 == par) & ~fixed
            m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = False
            masks.append(m)
        it = 0
        for it in range(1, itmax + 1):
            for m in masks:
                new = cls._neighbour_sum(phi, aW, aE, aS, aN) / diag
                phi[m] += omega * (new[m] - phi[m])
            if it % 40 == 0:
                r = np.abs(cls._neighbour_sum(phi, aW, aE, aS, aN) - diag * phi)
                r[fixed] = 0.0
                r[0, :] = r[-1, :] = r[:, 0] = r[:, -1] = 0.0
                if r.max() < tol:
                    break
        return phi, it

    @staticmethod
    def _coarsen(a, how='mean'):
        ny, nx = a.shape
        ny -= ny % 2; nx -= nx % 2
        b = a[:ny, :nx].reshape(ny // 2, 2, nx // 2, 2)
        if how == 'mean':
            return b.mean(axis=(1, 3))
        # conductors: a 2x2 block belongs to any conductor it touches, so that
        # a trace one cell thick survives to the coarse grid instead of
        # evaporating and changing the problem being solved
        flat = b.transpose(0, 2, 1, 3).reshape(ny // 2, nx // 2, 4)
        out = np.zeros((ny // 2, nx // 2), dtype=a.dtype)
        nz = flat != 0
        idx = np.argmax(nz, axis=2)
        anynz = nz.any(axis=2)
        out[anynz] = np.take_along_axis(flat, idx[..., None], axis=2)[..., 0][anynz]
        return out

    def _relax(self, eps, driven, tol=1e-9, itmax=20000, omega=None):
        """Solve by nested iteration: coarse grids first, each solution
        prolonged to seed the next. The fine grid then starts with only
        short-wavelength error left, which relaxation removes quickly."""
        levels = [(eps, self.cond)]
        while min(levels[-1][0].shape) > 48 and len(levels) < 6:
            e, c = levels[-1]
            levels.append((self._coarsen(e, 'mean'), self._coarsen(c, 'cond')))

        phi = None
        for lvl in range(len(levels) - 1, -1, -1):
            e, c = levels[lvl]
            if phi is None:
                phi = np.zeros(e.shape)
            else:
                phi = np.kron(phi, np.ones((2, 2)))       # piecewise injection
                ny, nx = e.shape
                if phi.shape != e.shape:                  # odd sizes: pad/crop
                    q = np.zeros(e.shape)
                    m0 = min(phi.shape[0], ny); m1 = min(phi.shape[1], nx)
                    q[:m0, :m1] = phi[:m0, :m1]
                    if m0 < ny: q[m0:, :] = q[m0 - 1, :]
                    if m1 < nx: q[:, m1:] = q[:, m1 - 1:m1]
                    phi = q
            # coarse levels only need to be solved well enough to be a good
            # starting point, so the tolerance is relaxed away from the finest
            t = tol if lvl == 0 else tol * 10.0 ** lvl
            phi, it = self._sor(phi, c, e, driven, t, itmax)
        self._last_iters = it
        return phi

    def _charges(self, phi, eps):
        """Charge per unit length on each conductor, by discrete Gauss law.

        In two dimensions the flux through a face of height h is
        eps*(dphi/h)*h = eps*dphi, so the cell size cancels and the sum over
        the faces bounding a conductor is the enclosed charge directly.
        """
        ex, ey = self._face_eps(eps)
        q = {}
        for cid in list(range(1, self._n_cond + 1)) + [-1]:
            m = self.cond == cid
            if not m.any():
                continue
            tot = 0.0
            # west faces of the conductor: neighbour to the left is outside
            sel = m[:, 1:] & ~m[:, :-1]
            tot += np.sum(ex[sel] * (phi[:, 1:][sel] - phi[:, :-1][sel]))
            sel = m[:, :-1] & ~m[:, 1:]
            tot += np.sum(ex[sel] * (phi[:, :-1][sel] - phi[:, 1:][sel]))
            sel = m[1:, :] & ~m[:-1, :]
            tot += np.sum(ey[sel] * (phi[1:, :][sel] - phi[:-1, :][sel]))
            sel = m[:-1, :] & ~m[1:, :]
            tot += np.sum(ey[sel] * (phi[:-1, :][sel] - phi[1:, :][sel]))
            q[cid] = EPS0 * tot
        return q

    def capacitance(self, air=False):
        """Maxwell capacitance matrix, farads per metre, conductors 1..N."""
        eps = np.ones_like(self.eps) if air else self.eps
        n = self._n_cond
        C = np.zeros((n, n))
        self.phi_last = None
        for k in range(1, n + 1):
            phi = self._relax(eps, k)
            if k == 1:
                self.phi_last = phi
            q = self._charges(phi, eps)
            for m in range(1, n + 1):
                C[m - 1, k - 1] = q.get(m, 0.0)
        return 0.5 * (C + C.T)       # symmetrise: the residual asymmetry is
                                     # the discretisation error, and halving
                                     # it is the usual estimate of the truth


def rlgc(cs):
    """Return (C, L) per metre for a cross-section, using L = mu0 eps0 inv(C_air)."""
    C = cs.capacitance(air=False)
    Ca = cs.capacitance(air=True)
    L = MU0 * EPS0 * np.linalg.inv(Ca)
    return C, L


def single_z0(C, L):
    return float(np.sqrt(L[0, 0] / C[0, 0]))


def modal(C, L):
    """Even- and odd-mode impedances and velocities for a symmetric pair.

    The modes of a symmetric two-line system are the sum and difference of the
    line voltages, so the modal parameters follow from the matrix entries
    without an eigen-decomposition.
    """
    Cs, Cm = C[0, 0], -C[0, 1]
    Ls, Lm = L[0, 0], L[0, 1]
    c_even, c_odd = Cs - Cm, Cs + Cm
    l_even, l_odd = Ls + Lm, Ls - Lm
    z0e, z0o = np.sqrt(l_even / c_even), np.sqrt(l_odd / c_odd)
    ve, vo = 1.0 / np.sqrt(l_even * c_even), 1.0 / np.sqrt(l_odd * c_odd)
    return dict(z0e=float(z0e), z0o=float(z0o), zdiff=float(2 * z0o),
                zcomm=float(z0e / 2), v_even=float(ve), v_odd=float(vo),
                k=float((z0e - z0o) / (z0e + z0o)),
                Cs=float(Cs), Cm=float(Cm), Ls=float(Ls), Lm=float(Lm))


# -- the closed forms we check the solver against ---------------------------

def ellipk_ratio(k):
    """K(k)/K(k') by the arithmetic-geometric mean, for 0 < k < 1.

    K(k) = pi / (2 * AGM(1, k')), so the ratio is AGM(1, k) / AGM(1, k').
    """
    def agm(a, b):
        for _ in range(60):
            a, b = 0.5 * (a + b), np.sqrt(a * b)
        return a
    kp = np.sqrt(1.0 - k * k)
    return agm(1.0, k) / agm(1.0, kp)


def cohn_stripline(w, b, er):
    """Cohn's exact zero-thickness stripline impedance, w and b in the same units."""
    k = 1.0 / np.cosh(np.pi * w / (2.0 * b))
    return 30.0 * np.pi / np.sqrt(er) * ellipk_ratio(k)


# Cohn's coupled result is conventionally written with K(k')/K(k), the
# reciprocal of the ratio above; sech and tanh of the same argument are
# complementary moduli, which is why the two forms agree in the wide-spacing
# limit where the coupled pair becomes two isolated lines.


def cohn_coupled_stripline(w, s, b, er):
    """Cohn's edge-coupled stripline even- and odd-mode impedances."""
    tw = np.tanh(np.pi * w / (2.0 * b))
    tws = np.tanh(np.pi * (w + s) / (2.0 * b))
    ke = tw * tws
    ko = tw / tws
    z0e = 30.0 * np.pi / np.sqrt(er) / ellipk_ratio(ke)
    z0o = 30.0 * np.pi / np.sqrt(er) / ellipk_ratio(ko)
    return float(z0e), float(z0o)


def hammerstad_microstrip(w, h, er):
    """Hammerstad's microstrip impedance and effective permittivity."""
    u = w / h
    if u <= 1.0:
        ee = (er + 1) / 2 + (er - 1) / 2 * ((1 + 12 / u) ** -0.5 + 0.04 * (1 - u) ** 2)
        z0 = 60.0 / np.sqrt(ee) * np.log(8.0 / u + u / 4.0)
    else:
        ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
        z0 = 120.0 * np.pi / (np.sqrt(ee) * (u + 1.393 + 0.667 * np.log(u + 1.444)))
    return float(z0), float(ee)
