"""Figures for 'Matrix Concepts in Digital Filter Design'."""

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


def _block(ax, x, y, w, h, label, sub=None, fc=None):
    fc = fc or HEX["ink"]
    ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2 + (0.03 if sub else 0), label, color="white",
            ha="center", va="center", fontsize=9, fontweight="bold")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.06, sub, color="#AFC0D6",
                ha="center", va="center", fontsize=6.8)


def _arrow(ax, p, q, color=None, lw=1.4, label=None, dy=0.03):
    color = color or HEX["navy"]
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=lw))
    if label:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dy, label, ha="center",
                va="bottom", fontsize=7.2, color=color)


# --- 1. state-space block ---------------------------------------------------
def fig_statespace():
    fig, ax = plt.subplots(figsize=(6.0, 2.5))
    ax.add_patch(plt.Circle((0.34, 0.62), 0.035, fc="white", ec=HEX["navy"], lw=1.2))
    ax.text(0.34, 0.62, "+", ha="center", va="center", fontsize=9, color=HEX["navy"])
    _block(ax, 0.44, 0.53, 0.12, 0.18, "$z^{-1}$", fc=HEX["ink"])
    _block(ax, 0.70, 0.53, 0.13, 0.18, "c$^{T}$", fc=HEX["teal"])
    _block(ax, 0.44, 0.20, 0.12, 0.16, "A", fc=HEX["navy"])
    _block(ax, 0.14, 0.53, 0.10, 0.18, "b", fc=HEX["teal"])

    _arrow(ax, (0.03, 0.62), (0.135, 0.62), label="x[n]")
    _arrow(ax, (0.245, 0.62), (0.30, 0.62))
    _arrow(ax, (0.375, 0.62), (0.435, 0.62), label="q[n+1]", dy=0.12)
    _arrow(ax, (0.565, 0.62), (0.695, 0.62), label="q[n]", dy=0.12)
    _arrow(ax, (0.835, 0.62), (0.95, 0.62), label="y[n]")

    ax.plot([0.63, 0.63], [0.62, 0.28], color=HEX["navy"], lw=1.2)
    _arrow(ax, (0.63, 0.28), (0.565, 0.28))
    _arrow(ax, (0.435, 0.28), (0.34, 0.28))
    ax.plot([0.34, 0.34], [0.28, 0.583], color=HEX["navy"], lw=1.2)
    ax.text(0.50, 0.11, "feedback path: the state is fed back through A",
            ha="center", fontsize=7, color=HEX["grey"])
    ax.text(0.50, 0.87, "q[n+1] = A q[n] + b x[n]        y[n] = c$^{T}$ q[n] + d x[n]",
            ha="center", fontsize=8.2, color=HEX["navy"])
    ax.set_xlim(0, 1); ax.set_ylim(0.05, 0.95); ax.axis("off")
    return save(fig, "df_statespace.png")


# --- 2. z-plane stability ---------------------------------------------------
def fig_zplane():
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    th = np.linspace(0, 2 * np.pi, 500)
    ax.fill(np.cos(th), np.sin(th), color=HEX["pale"], zorder=0)
    ax.plot(np.cos(th), np.sin(th), color=HEX["navy"], lw=1.3)
    stable = 0.62 * np.exp(1j * np.array([0.9, -0.9]))
    marg = np.exp(1j * np.array([2.3, -2.3]))
    unst = 1.28 * np.exp(1j * np.array([0.35, -0.35]))
    ax.plot(stable.real, stable.imag, "x", ms=8, mew=2, color=HEX["teal"])
    ax.plot(marg.real, marg.imag, "x", ms=8, mew=2, color=HEX["amber"])
    ax.plot(unst.real, unst.imag, "x", ms=8, mew=2, color=HEX["red"])
    ax.text(0.05, 0.05, "inside:\nstable", fontsize=7, color=HEX["teal"])
    ax.text(-1.50, 1.06, "on the circle:\nmarginal", fontsize=7, color=HEX["amber"])
    ax.text(1.50, 1.06, "outside:\nunstable", fontsize=7, color=HEX["red"], ha="right")
    ax.axhline(0, color=HEX["grey"], lw=0.6); ax.axvline(0, color=HEX["grey"], lw=0.6)
    ax.set_xlim(-1.55, 1.55); ax.set_ylim(-1.55, 1.55); ax.set_aspect("equal")
    ax.set_xlabel("Re z"); ax.set_ylabel("Im z")
    ax.set_title("z-plane: poles of H(z)", pad=6)
    _clean(ax)
    return save(fig, "df_zplane.png")


# --- 2b. leaky bucket + 2-point averager ------------------------------------
def fig_intuition():
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.2))
    n = np.arange(0, 61)
    for r, col in [(0.5, HEX["grey"]), (0.9, HEX["navy"]), (0.98, HEX["red"])]:
        axes[0].plot(n, r ** n, color=col, lw=1.3, label="r = %.2f" % r)
    axes[0].set_xlabel("samples n"); axes[0].set_ylabel("$r^{\\,n}$")
    axes[0].set_title("How much of the past survives", pad=5, fontsize=8.2)
    axes[0].legend(loc="upper right")

    w = np.linspace(0, np.pi, 600)
    axes[1].plot(w / np.pi, np.abs(np.cos(w / 2)), color=HEX["navy"], lw=1.5)
    axes[1].set_xlabel("ω / π"); axes[1].set_ylabel("|H|")
    axes[1].set_title("Two-point averager: zero at z = −1", pad=5, fontsize=8.2)
    axes[1].annotate("full-rate wiggle\ncancels exactly", xy=(0.98, 0.03),
                     xytext=(0.06, 0.20), fontsize=7, color=HEX["red"],
                     arrowprops=dict(arrowstyle="->", color=HEX["red"], lw=0.8))
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "df_intuition.png")


# --- 4. resonator -----------------------------------------------------------
def fig_resonator():
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.3))
    w = np.linspace(0, np.pi, 2000)
    z = np.exp(1j * w)
    for r, col, lw in [(0.6, HEX["grey"], 1.1), (0.9, HEX["navy"], 1.5),
                       (0.97, HEX["red"], 1.2)]:
        p = r * np.exp(1j * 0.8)
        H = 1.0 / ((z - p) * (z - np.conj(p)))
        axes[0].plot(w, 20 * np.log10(np.abs(H) / np.abs(H).max() * 1.0 + 1e-12)
                     + 20 * np.log10(np.abs(H).max()), color=col, lw=lw,
                     label="r = %.2f" % r)
    axes[0].axvline(0.8, color=HEX["teal"], lw=0.8, ls=":")
    axes[0].set_xlabel("ω (rad/sample)"); axes[0].set_ylabel("|H| (dB)")
    axes[0].set_title("Pole radius sets sharpness", pad=5, fontsize=8.2)
    axes[0].legend(loc="upper right")

    n = np.arange(0, 90)
    for r, col in [(0.9, HEX["navy"]), (0.97, HEX["red"])]:
        axes[1].plot(n, r ** n * np.cos(0.8 * n), color=col, lw=1.0,
                     label="r = %.2f" % r)
    axes[1].set_xlabel("samples n"); axes[1].set_ylabel("h[n]")
    axes[1].set_title("The same poles, seen in time", pad=5, fontsize=8.2)
    axes[1].legend(loc="upper right")
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "df_resonator.png")


# --- 5. two-channel filter bank ---------------------------------------------
def fig_bank():
    fig, ax = plt.subplots(figsize=(6.2, 2.4))
    _block(ax, 0.16, 0.60, 0.11, 0.16, "$H_0$", fc=HEX["teal"])
    _block(ax, 0.16, 0.22, 0.11, 0.16, "$H_1$", fc=HEX["teal"])
    _block(ax, 0.34, 0.60, 0.09, 0.16, "↓2", fc=HEX["navy"])
    _block(ax, 0.34, 0.22, 0.09, 0.16, "↓2", fc=HEX["navy"])
    _block(ax, 0.55, 0.60, 0.09, 0.16, "↑2", fc=HEX["navy"])
    _block(ax, 0.55, 0.22, 0.09, 0.16, "↑2", fc=HEX["navy"])
    _block(ax, 0.71, 0.60, 0.11, 0.16, "$F_0$", fc=HEX["teal"])
    _block(ax, 0.71, 0.22, 0.11, 0.16, "$F_1$", fc=HEX["teal"])
    ax.add_patch(plt.Circle((0.89, 0.49), 0.035, fc="white", ec=HEX["navy"], lw=1.2))
    ax.text(0.89, 0.49, "+", ha="center", va="center", fontsize=9, color=HEX["navy"])

    ax.plot([0.05, 0.11], [0.49, 0.49], color=HEX["navy"], lw=1.2)
    ax.plot([0.11, 0.11], [0.30, 0.68], color=HEX["navy"], lw=1.2)
    _arrow(ax, (0.11, 0.68), (0.155, 0.68))
    _arrow(ax, (0.11, 0.30), (0.155, 0.30))
    ax.text(0.045, 0.53, "x[n]", fontsize=7.5, color=HEX["navy"])
    for y in (0.68, 0.30):
        _arrow(ax, (0.275, y), (0.335, y))
        _arrow(ax, (0.435, y), (0.545, y))
        _arrow(ax, (0.645, y), (0.705, y))
    ax.plot([0.82, 0.89], [0.68, 0.68], color=HEX["navy"], lw=1.2)
    ax.plot([0.82, 0.89], [0.30, 0.30], color=HEX["navy"], lw=1.2)
    ax.plot([0.89, 0.89], [0.68, 0.525], color=HEX["navy"], lw=1.2)
    ax.plot([0.89, 0.89], [0.30, 0.455], color=HEX["navy"], lw=1.2)
    _arrow(ax, (0.925, 0.49), (0.98, 0.49), label="x[n−k]", dy=0.04)
    ax.text(0.50, 0.87, "Perfect reconstruction with no amplitude distortion "
                        "⇔ the polyphase matrix is paraunitary",
            ha="center", fontsize=7.8, color=HEX["navy"])
    ax.text(0.24, 0.05, "analysis", ha="center", fontsize=7, color=HEX["grey"])
    ax.text(0.755, 0.05, "synthesis", ha="center", fontsize=7, color=HEX["grey"])
    ax.set_xlim(0.02, 1.0); ax.set_ylim(0.02, 0.95); ax.axis("off")
    return save(fig, "df_bank.png")


# --- 6. eigenfilter bowl ----------------------------------------------------
def fig_bowl():
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.3))
    a = np.linspace(-1.6, 1.6, 300)
    b = np.linspace(-1.6, 1.6, 300)
    A, B = np.meshgrid(a, b)
    J = 1.0 * A ** 2 + 0.22 * B ** 2 + 0.5 * A * B
    cs = axes[0].contour(A, B, J, levels=10, colors=HEX["navy"], linewidths=0.7)
    axes[0].plot([0], [0], "o", ms=5, color=HEX["red"])
    axes[0].annotate("", xy=(1.25, -1.35), xytext=(-1.25, 1.35),
                     arrowprops=dict(arrowstyle="-", color=HEX["teal"], lw=1.4))
    axes[0].set_xlabel("$w_1$"); axes[0].set_ylabel("$w_2$")
    axes[0].set_title("Stopband energy $w^H Q w$ is a bowl", pad=5, fontsize=8.2)
    axes[0].set_aspect("equal")

    w = np.linspace(0, np.pi, 500)
    for taps, lab, col in [([1, 2, 1], "[1, 2, 1] — smooth, leaks least", HEX["teal"]),
                           ([1, -2, 1], "[1, −2, 1] — alternating, leaks most", HEX["red"])]:
        H = sum(t * np.exp(-1j * k * w) for k, t in enumerate(taps))
        H = np.abs(H) / np.abs(sum(taps) if sum(taps) else 4)
        axes[1].plot(w / np.pi, H, color=col, lw=1.4, label=lab)
    axes[1].set_xlabel("ω / π"); axes[1].set_ylabel("|H| (normalised)")
    axes[1].set_title("The two extreme eigenvectors", pad=5, fontsize=8.2)
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.30),
                   fontsize=6.6, ncol=1)
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "df_bowl.png")


if __name__ == "__main__":
    for f in (fig_statespace, fig_zplane, fig_intuition, fig_resonator,
              fig_bank, fig_bowl):
        print(f())
