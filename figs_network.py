"""Figures for 'Matrix Methods in Network Parameters'."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docstyle import HEX, mpl_setup

plt = mpl_setup()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
os.makedirs(OUT, exist_ok=True)


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return p


def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# --- 1. N-port conventions --------------------------------------------------
def fig_nport():
    fig, ax = plt.subplots(figsize=(6.0, 2.5))
    ax.add_patch(plt.Rectangle((0.36, 0.16), 0.28, 0.68, fc=HEX["ink"], ec="none"))
    ax.text(0.50, 0.58, "N-port network", color="white", ha="center",
            va="center", fontsize=9.5, fontweight="bold")
    ax.text(0.50, 0.42, "Z, Y or S", color="#AFC0D6", ha="center",
            va="center", fontsize=8)
    ports = [(0.75, "port 1", "1"), (0.55, "port 2", "2"), (0.28, "port N", "N")]
    for y, lab, idx in ports:
        ax.annotate("", xy=(0.355, y), xytext=(0.17, y),
                    arrowprops=dict(arrowstyle="-|>", color=HEX["teal"], lw=1.5))
        ax.text(0.165, y + 0.035, "$I_%s$" % idx, color=HEX["teal"], ha="right",
                va="bottom", fontsize=8)
        ax.text(0.165, y - 0.045, "$V_%s$" % idx, color=HEX["navy"], ha="right",
                va="top", fontsize=8)
        ax.text(0.30, y + 0.035, lab, color=HEX["grey"], ha="center",
                va="bottom", fontsize=7)
        ax.plot([0.13, 0.17], [y, y], color=HEX["navy"], lw=1.0)
        ax.plot([0.13], [y], marker="o", ms=3.5, color=HEX["navy"])
    ax.text(0.255, 0.42, "$\\vdots$", ha="center", va="center",
            fontsize=11, color=HEX["grey"])
    ax.text(0.70, 0.50,
            "$\\mathbf{V}=\\mathbf{Z}\\,\\mathbf{I}$\n"
            "$\\mathbf{I}=\\mathbf{Y}\\,\\mathbf{V}$\n"
            "$\\mathbf{b}=\\mathbf{S}\\,\\mathbf{a}$",
            ha="left", va="center", fontsize=8.5, color=HEX["navy"])
    ax.set_xlim(0, 1); ax.set_ylim(0.1, 0.95); ax.axis("off")
    ax.set_title("Port conventions: currents defined into the network",
                 pad=6, loc="left", x=0.02)
    return save(fig, "n_ports.png")


# --- 2. two-port wave picture ----------------------------------------------
def fig_waves():
    fig, ax = plt.subplots(figsize=(6.0, 2.45))
    ax.add_patch(plt.Rectangle((0.38, 0.28), 0.24, 0.44, fc=HEX["ink"], ec="none"))
    ax.text(0.50, 0.56, "S", color="white", ha="center", va="center",
            fontsize=15, fontweight="bold")
    ax.text(0.50, 0.38, "two-port, reference $Z_0$", color="#AFC0D6",
            ha="center", va="center", fontsize=7)

    ax.annotate("", xy=(0.375, 0.63), xytext=(0.13, 0.63),
                arrowprops=dict(arrowstyle="-|>", color=HEX["teal"], lw=1.6))
    ax.text(0.13, 0.665, "$V_1^{+}$  incident", color=HEX["teal"], fontsize=7.6)
    ax.annotate("", xy=(0.13, 0.38), xytext=(0.375, 0.38),
                arrowprops=dict(arrowstyle="-|>", color=HEX["red"], lw=1.6))
    ax.text(0.13, 0.30, "$V_1^{-}$  reflected", color=HEX["red"], fontsize=7.6)

    ax.annotate("", xy=(0.87, 0.63), xytext=(0.625, 0.63),
                arrowprops=dict(arrowstyle="-|>", color=HEX["red"], lw=1.6))
    ax.text(0.87, 0.665, "$V_2^{-}$  transmitted", color=HEX["red"],
            fontsize=7.6, ha="right")
    ax.annotate("", xy=(0.625, 0.38), xytext=(0.87, 0.38),
                arrowprops=dict(arrowstyle="-|>", color=HEX["teal"], lw=1.6))
    ax.text(0.87, 0.30, "$V_2^{+}$  incident", color=HEX["teal"],
            fontsize=7.6, ha="right")

    ax.text(0.50, 0.15,
            "$S_{21}=V_2^{-}/V_1^{+}$ with $V_2^{+}=0$   —   magnitude and phase at "
            "port 2 relative to the wave driven into port 1",
            ha="center", va="center", fontsize=7.4, color=HEX["navy"])
    ax.set_xlim(0.05, 0.95); ax.set_ylim(0.08, 0.80); ax.axis("off")
    return save(fig, "waves.png")


# --- 3. eigenvalues of S at one frequency ----------------------------------
def fig_lambda_plane():
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=HEX["navy"], lw=1.2)
    ax.fill(np.cos(th), np.sin(th), color=HEX["pale"], zorder=0)
    loss_free = np.exp(1j * np.array([0.6, 2.4, -1.3]))
    lossy = 0.62 * np.exp(1j * np.array([1.4, -2.2]))
    ax.plot(loss_free.real, loss_free.imag, "o", ms=6, color=HEX["teal"],
            label="lossless: $|\\lambda|=1$")
    ax.plot(lossy.real, lossy.imag, "s", ms=6, color=HEX["red"],
            label="with loss: $|\\lambda|<1$")
    ax.axhline(0, color=HEX["grey"], lw=0.6)
    ax.axvline(0, color=HEX["grey"], lw=0.6)
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.set_xlabel("Re $\\lambda$"); ax.set_ylabel("Im $\\lambda$")
    ax.set_title("Eigenvalues of S at one frequency", pad=6)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=1)
    _clean(ax)
    return save(fig, "lambda_plane.png")


# --- 3b. even / odd modes of the 25-ohm example ----------------------------
def fig_modes():
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.2))
    for ax, (title, sgn, note, col) in zip(axes, [
            ("Even drive: $\\lambda=+1$", +1,
             "same voltage both ends\nno current in R, no loss", HEX["teal"]),
            ("Odd drive: $\\lambda=-0.6$", -1,
             "full difference across R\nR dissipates, mode shrinks", HEX["red"])]):
        ax.add_patch(plt.Rectangle((0.42, 0.44), 0.16, 0.12, fc="white",
                                   ec=HEX["navy"], lw=1.2))
        ax.text(0.50, 0.50, "25 Ω", ha="center", va="center", fontsize=7.5,
                color=HEX["navy"])
        ax.plot([0.18, 0.42], [0.50, 0.50], color=HEX["navy"], lw=1.2)
        ax.plot([0.58, 0.82], [0.50, 0.50], color=HEX["navy"], lw=1.2)
        for x, s in ((0.18, +1), (0.82, sgn)):
            ax.annotate("", xy=(x, 0.50 + 0.22 * s), xytext=(x, 0.50),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.6))
            ax.text(x, 0.50 + 0.26 * s, "+V" if s > 0 else "−V", ha="center",
                    va="bottom" if s > 0 else "top", color=col, fontsize=8)
        ax.text(0.50, 0.16, note, ha="center", va="center", fontsize=7,
                color=HEX["grey"])
        ax.set_title(title, pad=5)
        ax.set_xlim(0.05, 0.95); ax.set_ylim(0.05, 0.95); ax.axis("off")
    fig.tight_layout()
    return save(fig, "modes.png")


# --- 4/5. pole-zero map and its response -----------------------------------
SIG, W0, WZ = 0.08, 1.0, 2.0


def fig_polezero():
    fig, ax = plt.subplots(figsize=(3.5, 3.3))
    ax.axvline(0, color=HEX["navy"], lw=1.3)
    ax.axhline(0, color=HEX["grey"], lw=0.6)
    ax.fill_betweenx([-2.6, 2.6], -1.2, 0, color=HEX["pale"], zorder=0)
    ax.plot([-SIG, -SIG], [W0, -W0], "x", ms=9, mew=2, color=HEX["red"])
    ax.plot([0, 0], [WZ, -WZ], "o", ms=8, mfc="none", mew=1.6, color=HEX["teal"])
    ax.annotate("pole pair,\ndistance σ = 0.08", xy=(-SIG, W0), xytext=(-1.05, 1.35),
                fontsize=7, color=HEX["red"],
                arrowprops=dict(arrowstyle="->", color=HEX["red"], lw=0.8))
    ax.annotate("zero on the axis\nat ω = 2", xy=(0, WZ), xytext=(-1.1, 2.3),
                fontsize=7, color=HEX["teal"],
                arrowprops=dict(arrowstyle="->", color=HEX["teal"], lw=0.8))
    ax.text(-1.15, -2.35, "stable half-plane", fontsize=7, color=HEX["grey"])
    ax.set_xlim(-1.2, 0.45); ax.set_ylim(-2.6, 2.6)
    ax.set_xlabel("σ = Re s"); ax.set_ylabel("jω = Im s")
    ax.set_title("s-plane: poles set peaks, zeros set nulls", pad=6, fontsize=8.2)
    _clean(ax)
    return save(fig, "polezero.png")


def _H(s):
    return (s ** 2 + WZ ** 2) / (s ** 2 + 2 * SIG * s + W0 ** 2)


def fig_response():
    w = np.linspace(0.01, 3.2, 3000)
    h = _H(1j * w)
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.3))
    axes[0].plot(w, np.abs(h), color=HEX["navy"], lw=1.5)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("ω (rad/s)"); axes[0].set_ylabel("|H(jω)|")
    axes[0].set_title("Frequency response", pad=5, fontsize=8.2)
    axes[0].annotate("peak near ω₀ = 1", xy=(1.0, np.abs(_H(1j))), xytext=(1.25, 8),
                     fontsize=7, color=HEX["red"],
                     arrowprops=dict(arrowstyle="->", color=HEX["red"], lw=0.8))
    axes[0].annotate("null at ω = 2", xy=(2.0, 0.02), xytext=(2.05, 0.15),
                     fontsize=7, color=HEX["teal"],
                     arrowprops=dict(arrowstyle="->", color=HEX["teal"], lw=0.8))
    t = np.linspace(0, 60, 4000)
    imp = np.exp(-SIG * t) * np.cos(W0 * t)
    axes[1].plot(t, imp, color=HEX["navy"], lw=0.8)
    axes[1].plot(t, np.exp(-SIG * t), color=HEX["red"], lw=1.0, ls="--",
                 label="envelope $e^{-\\sigma t}$")
    axes[1].plot(t, -np.exp(-SIG * t), color=HEX["red"], lw=1.0, ls="--")
    axes[1].set_xlabel("t (s)"); axes[1].set_ylabel("h(t)")
    axes[1].set_title("Impulse response — same network", pad=5, fontsize=8.2)
    axes[1].legend(loc="upper right")
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "response_pair.png")


# --- 6. Kramers-Kronig pair -------------------------------------------------
def fig_kk():
    w = np.linspace(-6, 6, 1200)
    h = 1.0 / (1j * w + 1)
    fig, ax = plt.subplots(figsize=(4.6, 2.1))
    ax.plot(w, h.real, color=HEX["navy"], lw=1.4, label="Re H — absorptive")
    ax.plot(w, h.imag, color=HEX["red"], lw=1.4, label="Im H — dispersive")
    ax.axhline(0, color=HEX["grey"], lw=0.6)
    ax.set_xlabel("ω"); ax.set_title("H(s) = 1/(s+1): the two curves are not independent",
                                     pad=5, fontsize=8.2)
    ax.legend(loc="upper right")
    _clean(ax)
    return save(fig, "kk.png")


# --- 7. passivity violation between samples --------------------------------
def fig_passivity():
    w = np.linspace(0, 10, 2000)
    smax = 0.86 + 0.20 * np.exp(-((w - 6.15) ** 2) / (2 * 0.09 ** 2))
    samples = np.arange(0, 10.01, 0.5)
    ss = 0.86 + 0.20 * np.exp(-((samples - 6.15) ** 2) / (2 * 0.09 ** 2))
    fig, ax = plt.subplots(figsize=(4.9, 2.1))
    ax.plot(w, smax, color=HEX["navy"], lw=1.3, label="true $\\sigma_{max}(\\omega)$")
    ax.plot(samples, ss, "o", ms=4, color=HEX["teal"], label="sampled sweep")
    ax.axhline(1.0, color=HEX["red"], lw=1.1, ls="--", label="passivity limit σ = 1")
    ax.annotate("violation sits between two samples", xy=(6.15, 1.06),
                xytext=(2.1, 1.10), fontsize=7, color=HEX["red"],
                arrowprops=dict(arrowstyle="->", color=HEX["red"], lw=0.8))
    ax.set_ylim(0.78, 1.16)
    ax.set_xlabel("frequency"); ax.set_ylabel("$\\sigma_{max}$")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=3)
    _clean(ax)
    return save(fig, "passivity.png")


# --- 8. Smith chart / bilinear map -----------------------------------------
def fig_smith():
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 3.0))
    th = np.linspace(0, 2 * np.pi, 500)
    for ax in axes:
        ax.plot(np.cos(th), np.sin(th), color=HEX["navy"], lw=1.2)
        ax.axhline(0, color=HEX["grey"], lw=0.6)
        ax.set_aspect("equal")
        ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.25, 1.25)
        _clean(ax)

    x = np.linspace(-60, 60, 4000)
    for r, lw in [(0.0, 1.2), (0.5, 0.9), (1.0, 1.1), (2.0, 0.9), (5.0, 0.9)]:
        z = r + 1j * x
        g = (z - 1) / (z + 1)
        axes[0].plot(g.real, g.imag, color=HEX["teal"], lw=lw)
        if r:
            yoff = {0.5: 0.10, 1.0: -0.16, 2.0: 0.10, 5.0: -0.16}[r]
            axes[0].text((r - 1) / (r + 1), yoff, "r = %g" % r, fontsize=6.4,
                         color=HEX["teal"], ha="center",
                         va="bottom" if yoff > 0 else "top")
    axes[0].set_title("Γ = (z−1)/(z+1) maps constant-r lines to circles",
                      pad=6, fontsize=8.0)
    axes[0].set_xlabel("Re Γ"); axes[0].set_ylabel("Im Γ")

    pts = [(-1.0, "short\nΓ = −1", "right"), (-1 / 3, "25 Ω\nΓ = −1/3", "center"),
           (0.0, "matched\nΓ = 0", "center"), (1 / 3, "100 Ω\nΓ = +1/3", "center"),
           (1.0, "open\nΓ = +1", "left")]
    for g, lab, ha in pts:
        axes[1].plot([g], [0], "o", ms=6, color=HEX["red"])
        axes[1].text(g, -0.14 if abs(g) != 1 / 3 else 0.10, lab, fontsize=6.6,
                     ha=ha, va="top" if abs(g) != 1 / 3 else "bottom",
                     color=HEX["navy"])
    axes[1].text(-0.95, 1.05, "left of centre: low Z", fontsize=6.6, color=HEX["grey"])
    axes[1].text(0.95, 1.05, "right: high Z", fontsize=6.6, color=HEX["grey"], ha="right")
    axes[1].set_title("Worked points, $Z_0$ = 50 Ω", pad=6, fontsize=8.0)
    axes[1].set_xlabel("Re Γ")
    fig.tight_layout()
    return save(fig, "smith.png")


if __name__ == "__main__":
    for f in (fig_nport, fig_waves, fig_lambda_plane, fig_modes, fig_polezero,
              fig_response, fig_kk, fig_passivity, fig_smith):
        print(f())


# --- 9a. mixed-mode block structure ----------------------------------------
def fig_mixedmode_blocks():
    fig, ax = plt.subplots(figsize=(4.4, 3.4))
    cells = [(0, 1, "$S_{dd}$", "differential in,\ndifferential out", HEX["teal"]),
             (1, 1, "$S_{dc}$", "common in,\ndifferential out", HEX["red"]),
             (0, 0, "$S_{cd}$", "differential in,\ncommon out", HEX["red"]),
             (1, 0, "$S_{cc}$", "common in,\ncommon out", HEX["navy"])]
    for cx, cy, lab, sub, col in cells:
        ax.add_patch(plt.Rectangle((cx, cy), 1, 1, fc="white", ec=col, lw=1.8))
        ax.text(cx + 0.5, cy + 0.66, lab, ha="center", va="center",
                fontsize=13, color=col, fontweight="bold")
        ax.text(cx + 0.5, cy + 0.32, sub, ha="center", va="center",
                fontsize=6.6, color=HEX["grey"])
    ax.plot([0, 2], [1, 1], color=HEX["grey"], lw=0.8, ls=":")
    ax.plot([1, 1], [0, 2], color=HEX["grey"], lw=0.8, ls=":")
    ax.text(0.5, 2.10, "the signal path", ha="center", fontsize=7,
            color=HEX["teal"])
    ax.text(1.5, 2.10, "mode conversion", ha="center", fontsize=7, color=HEX["red"])
    ax.text(0.5, -0.20, "mode conversion", ha="center", fontsize=7, color=HEX["red"])
    ax.text(1.5, -0.20, "common-mode path", ha="center", fontsize=7,
            color=HEX["navy"])
    ax.text(1.0, -0.40, "both off-diagonal blocks vanish for a perfectly symmetric pair",
            ha="center", fontsize=6.6, color=HEX["grey"])
    ax.set_xlim(-0.12, 2.12); ax.set_ylim(-0.62, 2.30)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("The four quadrants of a mixed-mode S-matrix", pad=10, fontsize=8.4)
    return save(fig, "mixedmode_blocks.png")


# --- 9b. mode conversion from intra-pair skew ------------------------------
def fig_skew_conversion():
    f = np.linspace(0.05, 40, 2000) * 1e9
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.5))

    for dt, col, ls in [(1e-12, HEX["grey"], "-"), (2e-12, HEX["navy"], "-"),
                        (5e-12, HEX["red"], "-")]:
        conv = 20 * np.log10(np.maximum(np.abs(np.sin(np.pi * f * dt)), 1e-6))
        axes[0].plot(f / 1e9, conv, color=col, ls=ls, lw=1.5,
                     label="%g ps skew" % (dt * 1e12))
    axes[0].set_ylim(-45, 3)
    axes[0].set_xlabel("frequency (GHz)")
    axes[0].set_ylabel("$|S_{cd21}|$ relative to through (dB)")
    axes[0].set_title("Mode conversion grows as sin(πfΔt)", pad=5, fontsize=8.2)
    axes[0].legend(loc="lower right")
    for fn, lab in [(14, "14"), (26.56, "26.6")]:
        axes[0].axvline(fn, color=HEX["teal"], lw=0.8, ls=":")
        axes[0].text(fn + 0.6, -42, lab + " GHz", fontsize=6.4, color=HEX["teal"])

    for dt, col in [(1e-12, HEX["grey"]), (2e-12, HEX["navy"]), (5e-12, HEX["red"])]:
        keep = 20 * np.log10(np.maximum(np.abs(np.cos(np.pi * f * dt)), 1e-6))
        axes[1].plot(f / 1e9, keep, color=col, lw=1.5,
                     label="%g ps skew" % (dt * 1e12))
    axes[1].set_ylim(-3.2, 0.3)
    axes[1].set_xlabel("frequency (GHz)")
    axes[1].set_ylabel("$|S_{dd21}|$ penalty (dB)")
    axes[1].set_title("What the differential path actually loses", pad=5, fontsize=8.2)
    axes[1].legend(loc="lower left")
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "skew_conversion.png")
