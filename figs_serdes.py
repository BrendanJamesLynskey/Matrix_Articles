"""Figures for 'Equalisation in High-Speed Serial Links'.

Every plot is drawn from the channel model in serdes_model.py — nothing here is
sketched by hand.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docstyle import HEX, mpl_setup
import serdes_model as SM

plt = mpl_setup()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
os.makedirs(OUT, exist_ok=True)

D = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "_serdes_arrays.npy"), allow_pickle=True).item()
FREQ, S21, S21B, S11B = D['freq'], D['s21'], D['s21b'], D['s11b']
HC, PR, PRC = D['H'], D['pr'], D['pr_c']
M, UI, FNYQ = SM.M, SM.UI, SM.FNYQ


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return p


def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# --- 1. channel topology ----------------------------------------------------
def fig_topology():
    fig, ax = plt.subplots(figsize=(6.4, 2.1))
    blocks = [(0.02, 0.10, "Tx\ndie", HEX["ink"]),
              (0.14, 0.08, "pkg\n0.4\"", HEX["navy"]),
              (0.245, 0.13, "line card\n6\"", HEX["teal"]),
              (0.39, 0.07, "conn", HEX["red"]),
              (0.475, 0.155, "backplane\n18\"", HEX["teal"]),
              (0.645, 0.07, "conn", HEX["red"]),
              (0.73, 0.11, "line card\n4\"", HEX["teal"]),
              (0.855, 0.08, "pkg\n0.4\"", HEX["navy"]),
              (0.95, 0.05, "Rx", HEX["ink"])]
    for x, wdt, lab, col in blocks:
        ax.add_patch(plt.Rectangle((x, 0.42), wdt, 0.24, fc=col, ec="none"))
        ax.text(x + wdt / 2, 0.54, lab, ha="center", va="center",
                color="white", fontsize=6.4, linespacing=1.3)
    ax.annotate("", xy=(0.995, 0.54), xytext=(0.0, 0.54),
                arrowprops=dict(arrowstyle="-", color=HEX["grey"], lw=0.6),
                zorder=0)
    # the stub
    ax.plot([0.70, 0.70], [0.42, 0.22], color=HEX["amber"], lw=3, solid_capstyle="butt")
    ax.annotate("un-backdrilled via stub, 110 mil\n→ λ/4 resonance at 13.9 GHz",
                xy=(0.70, 0.24), xytext=(0.50, 0.06), fontsize=6.6,
                color=HEX["amber"],
                arrowprops=dict(arrowstyle="->", color=HEX["amber"], lw=0.8))
    ax.text(0.5, 0.86, "28.8 inch of 100 Ω differential stripline, Dk 3.7, "
                       "163 ps/inch", ha="center", fontsize=7.2, color=HEX["navy"])
    ax.text(0.5, 0.75, "28 GBd NRZ  •  UI = 35.7 ps  •  Nyquist 14 GHz",
            ha="center", fontsize=7.2, color=HEX["grey"])
    ax.set_xlim(-0.01, 1.01); ax.set_ylim(0.0, 0.95); ax.axis("off")
    return save(fig, "sd_topology.png")


# --- 2. insertion and return loss -------------------------------------------
def fig_channel():
    f = FREQ / 1e9
    keep = f <= 45
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.5))
    axes[0].plot(f[keep], 20 * np.log10(np.abs(S21[keep]) + 1e-30),
                 color=HEX["red"], lw=1.4, label="with 110 mil stub")
    axes[0].plot(f[keep], 20 * np.log10(np.abs(S21B[keep]) + 1e-30),
                 color=HEX["teal"], lw=1.6, label="back-drilled")
    axes[0].axvline(FNYQ / 1e9, color=HEX["amber"], lw=1.0, ls=":")
    axes[0].set_ylim(-80, 2)
    axes[0].set_xlabel("frequency (GHz)"); axes[0].set_ylabel("$|S_{dd21}|$ (dB)")
    axes[0].set_title("Differential insertion loss", pad=5, fontsize=8.2)
    axes[0].legend(loc="lower left", fontsize=6.6)
    axes[0].annotate("Nyquist", xy=(14, -72), xytext=(16, -72),
                     fontsize=6.6, color=HEX["amber"])
    axes[0].annotate("−24.6 dB", xy=(14, -24.6), xytext=(19, -18),
                     fontsize=7, color=HEX["teal"],
                     arrowprops=dict(arrowstyle="->", color=HEX["teal"], lw=0.8))

    axes[1].plot(f[keep], 20 * np.log10(np.abs(S11B[keep]) + 1e-30),
                 color=HEX["navy"], lw=1.4)
    axes[1].axvline(FNYQ / 1e9, color=HEX["amber"], lw=1.0, ls=":")
    axes[1].set_ylim(-45, 0)
    axes[1].set_xlabel("frequency (GHz)"); axes[1].set_ylabel("$|S_{dd11}|$ (dB)")
    axes[1].set_title("Differential return loss — the ripple is reflections",
                      pad=5, fontsize=8.2)
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "sd_channel.png")


# --- 3. CTLE family ---------------------------------------------------------
def fig_ctle():
    f = FREQ
    keep = f <= 45e9
    fig, ax = plt.subplots(figsize=(4.4, 2.3))
    for att, col in [(-3.0, HEX["grey"]), (-6.0, HEX["navy"]), (-9.0, HEX["red"])]:
        H = SM.ctle(f, dc_att_db=att)
        ax.plot(f[keep] / 1e9, 20 * np.log10(np.abs(H[keep])), color=col, lw=1.4,
                label="%g dB DC attenuation" % att)
    ax.plot(f[keep] / 1e9, -20 * np.log10(np.abs(S21B[keep]) + 1e-30) - 24.6,
            color=HEX["teal"], lw=1.2, ls="--", label="inverse channel (for scale)")
    ax.axvline(FNYQ / 1e9, color=HEX["amber"], lw=1.0, ls=":")
    ax.set_ylim(-14, 22)
    ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("gain (dB)")
    ax.set_title("CTLE: buy high-frequency gain by giving up low", pad=5, fontsize=8.2)
    ax.legend(loc="upper left", fontsize=6.2)
    _clean(ax)
    return save(fig, "sd_ctle.png")


# --- 4. pulse responses -----------------------------------------------------
def _stem(ax, taps, cursor, col, label):
    n = np.arange(len(taps)) - cursor
    ax.axhline(0, color=HEX["grey"], lw=0.7)
    ax.vlines(n, 0, taps, color=col, lw=1.6)
    ax.plot(n, taps, "o", ms=3.2, color=col)
    ax.plot([0], [taps[cursor]], "o", ms=6, mfc="none", mew=1.6, color=HEX["amber"])
    ax.set_xlabel("symbol index relative to the cursor")
    ax.set_title(label, pad=5, fontsize=8.2)
    _clean(ax)


def fig_pulse():
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.5))
    t = (np.arange(len(PR)) / M) * UI * 1e12
    span = t <= 900
    axes[0].plot(t[span], PR[span], color=HEX["red"], lw=1.3, label="channel only")
    axes[0].plot(t[span], PRC[span], color=HEX["teal"], lw=1.3, label="after CTLE")
    axes[0].set_xlabel("time (ps)"); axes[0].set_ylabel("amplitude (fraction of swing)")
    axes[0].set_title("Single-bit response", pad=5, fontsize=8.2)
    axes[0].legend(loc="upper right", fontsize=6.6)
    _clean(axes[0])

    _stem(axes[1], D['taps'], int(D['cur']), HEX["red"],
          "Sampled on the UI grid: one cursor, a lot of ISI")
    axes[1].set_ylabel("tap value")
    fig.tight_layout()
    return save(fig, "sd_pulse.png")


def fig_taps_stages():
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.3))
    _stem(axes[0], D['taps'], int(D['cur']), HEX["red"],
          "channel only  (cursor %.3f)" % D['taps'][int(D['cur'])])
    _stem(axes[1], D['taps_c'], int(D['cur_c']), HEX["amber"],
          "+ CTLE  (cursor %.3f)" % D['taps_c'][int(D['cur_c'])])
    comb, dcur = D['comb'], int(D['dcur'])
    _stem(axes[2], comb, dcur, HEX["teal"], "+ Tx FFE (DFE span shaded)")
    nb = int(D['ndfe'])
    axes[2].axvspan(0.5, nb + 0.5, color=HEX["teal"], alpha=0.12)
    axes[0].set_ylabel("tap value")
    for ax in axes:
        ax.set_xlim(-7, 16)
    fig.tight_layout()
    return save(fig, "sd_taps.png")


# --- 5. eye diagrams --------------------------------------------------------
def _impulse(hhalf):
    return SM.impulse_from_h(hhalf)


def _eye(ax, wave, title, nui=2, ntraces=400, col=HEX["teal"]):
    seg = nui * M
    start = len(wave) // 4
    xs = np.arange(seg) / M - nui / 2.0
    for k in range(ntraces):
        i = start + k * M
        if i + seg > len(wave):
            break
        ax.plot(xs, wave[i:i + seg], color=col, lw=0.35, alpha=0.14)
    ax.set_xlim(-nui / 2.0, nui / 2.0)
    ax.set_xlabel("UI"); ax.set_title(title, pad=5, fontsize=8.0)
    _clean(ax)


def _upsample(taps):
    u = np.zeros((len(taps) - 1) * M + 1)
    u[::M] = taps
    return u


def _chain(hhalf, bits, txffe=None, rxffe=None):
    """Return (waveform, symbols, sample-rate pulse response) for the chain."""
    imp = _impulse(hhalf)
    if txffe is not None:
        imp = np.convolve(imp, _upsample(txffe))
    if rxffe is not None:
        imp = np.convolve(imp, _upsample(rxffe))
    sym = bits.astype(float) * 2 - 1
    held = np.repeat(sym, M)
    wave = np.convolve(held, imp)[:len(held)]
    pulse = np.convolve(np.ones(M), imp)
    return wave, sym, held, pulse


def _eye_from(ax, wave, pulse, title, col, skip_ui=20):
    n0 = int(np.argmax(pulse))                  # the cursor is the positive peak
    amp = float(np.abs(pulse[n0])) or 1.0
    w = wave / amp
    seg = 2 * M
    # begin well after the channel's bulk delay, and keep the cursor at UI = 0
    start = n0 + skip_ui * M - M
    xs = np.arange(seg) / M - 1.0
    segs = []
    for k in range(1200):
        i = start + k * M
        if i < 0 or i + seg > len(w):
            break
        segs.append(w[i:i + seg])
        ax.plot(xs, segs[-1], color=col, lw=0.3, alpha=0.07)
    if segs:
        mn = np.min(np.abs(np.array(segs)), axis=0)[M]
        ax.annotate("", xy=(0, mn), xytext=(0, -mn),
                    arrowprops=dict(arrowstyle="<->", color=HEX["navy"], lw=1.1))
        ax.text(0.04, 0, "%.2f" % (2 * mn), fontsize=6.6, color=HEX["navy"],
                va="center")
    ax.axvline(0, color=HEX["navy"], lw=0.6, ls=":")
    ax.set_xlim(-1, 1)
    ax.set_xlabel("UI"); ax.set_title(title, pad=5, fontsize=8.0)
    _clean(ax)


def fig_eyes():
    rng = np.random.default_rng(7)
    bits = rng.integers(0, 2, 4000)
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.3))

    w0, _, _, p0 = _chain(S21B, bits)
    _eye_from(axes[0], w0, p0, "channel only — shut", HEX["red"])

    w1, _, _, p1 = _chain(S21B * HC, bits)
    _eye_from(axes[1], w1, p1, "+ CTLE — still shut", HEX["amber"])

    w2, sym, held, p2 = _chain(S21B * HC, bits, txffe=D['ffe'])
    n0 = int(np.argmax(p2))
    comb, dcur, nb = D['comb'], int(D['dcur']), int(D['ndfe'])
    dfe = comb[dcur + 1: dcur + 1 + nb] * p2[n0]
    # symbol m's cursor lands at sample n0 + m*M, so the tap that cancels the
    # k-th post-cursor must be indexed from that reference, not from zero.
    corr = np.zeros_like(w2)
    for k, ck in enumerate(dfe, start=1):
        d = n0 + k * M
        if d < len(corr):
            corr[d:] += ck * held[:len(corr) - d]
    _eye_from(axes[2], w2 - corr, p2,
              "+ Tx FFE + DFE — open", HEX["teal"])
    axes[0].set_ylabel("amplitude / cursor")
    fig.tight_layout()
    return save(fig, "sd_eyes.png")


# --- 6. noise budget --------------------------------------------------------
def fig_budget(R):
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4))
    names = ["receiver\nnoise", "crosstalk", "jitter", "residual\nISI"]
    vals = [R['sigma_rx_eff'], R['sigma_xt_eff'], R['sigma_jit'], R['sigma_isi']]
    cols = [HEX["navy"], HEX["red"], HEX["amber"], HEX["grey"]]
    axes[0].bar(names, vals, color=cols, width=0.62)
    axes[0].axhline(R['sigma_tot'], color=HEX["teal"], lw=1.4, ls="--")
    axes[0].text(3.45, R['sigma_tot'] + 0.06, "total %.2f mV rms" % R['sigma_tot'],
                 ha="right", fontsize=6.8, color=HEX["teal"])
    axes[0].set_ylabel("mV rms (referred to the Rx input)")
    axes[0].set_title("Where the noise comes from", pad=5, fontsize=8.2)
    axes[0].tick_params(axis="x", labelsize=6.4)

    from math import erfc as _erfc, sqrt as _sqrt
    q = np.linspace(3, 9, 400)
    ber = np.array([0.5 * _erfc(v / _sqrt(2)) for v in q])
    axes[1].semilogy(q, ber, color=HEX["navy"], lw=1.6)
    axes[1].axhline(1e-12, color=HEX["red"], lw=1.1, ls="--")
    axes[1].plot([R['Q']], [10 ** R['ber_exp']], "o", ms=7, color=HEX["teal"])
    axes[1].annotate("this link\nQ = %.2f" % R['Q'],
                     xy=(R['Q'], 10 ** R['ber_exp']), xytext=(R['Q'] - 2.6, 1e-16),
                     fontsize=7, color=HEX["teal"],
                     arrowprops=dict(arrowstyle="->", color=HEX["teal"], lw=0.8))
    axes[1].plot([R['pam4_Q']], [10 ** R['pam4_ber_exp']], "s", ms=6, color=HEX["red"])
    axes[1].text(R['pam4_Q'] + 0.1, 10 ** R['pam4_ber_exp'] * 2,
                 "same channel,\nPAM4", fontsize=6.8, color=HEX["red"])
    axes[1].text(8.9, 2e-12, "1e−12 target", ha="right", fontsize=6.6, color=HEX["red"])
    axes[1].set_ylim(1e-20, 1)
    axes[1].set_xlabel("Q"); axes[1].set_ylabel("BER")
    axes[1].set_title("Q to bit error rate", pad=5, fontsize=8.2)
    for ax in axes:
        _clean(ax)
    fig.tight_layout()
    return save(fig, "sd_budget.png")


# --- 7. NRZ vs PAM4 ---------------------------------------------------------
def fig_pam4(R):
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.3))
    for ax, (levels, name, col) in zip(axes, [([-1, 1], "NRZ — 1 eye", HEX["teal"]),
                                              ([-1, -1 / 3, 1 / 3, 1], "PAM4 — 3 eyes",
                                               HEX["red"])]):
        for L in levels:
            ax.axhline(L, color=col, lw=2.0)
        for a, b in zip(levels[:-1], levels[1:]):
            ax.add_patch(plt.Rectangle((0.18, a + 0.02), 0.64, (b - a) - 0.04,
                                       fc=col, alpha=0.14, ec="none"))
            ax.annotate("", xy=(0.5, b - 0.02), xytext=(0.5, a + 0.02),
                        arrowprops=dict(arrowstyle="<->", color=col, lw=0.9))
        ax.set_ylim(-1.35, 1.35); ax.set_xlim(0, 1)
        ax.set_xticks([]); ax.set_title(name, pad=5, fontsize=8.2)
        _clean(ax)
    axes[0].set_ylabel("normalised amplitude")
    axes[0].text(0.5, 1.18, "eye = %.0f mV" % R['eye_mv'], ha="center",
                 fontsize=7.2, color=HEX["teal"])
    axes[1].text(0.5, 1.18, "each eye = %.0f mV  (−9.5 dB)" % R['pam4_eye_mv'],
                 ha="center", fontsize=7.2, color=HEX["red"])
    fig.tight_layout()
    return save(fig, "sd_pam4.png")


# --- 8. history timeline ----------------------------------------------------
def fig_history():
    items = [(2002, "XAUI 3.125G", "passive de-emphasis"),
             (2007, "10GBASE-KR", "Tx FFE + Rx DFE, link training"),
             (2011, "CEI-28G", "CTLE + multi-tap DFE"),
             (2017, "400GbE / CEI-56G", "PAM4, FEC mandatory"),
             (2022, "802.3ck / CEI-112G", "ADC-DSP receivers"),
             (2026, "802.3dj / 224G", "MLSE, stronger FEC")]
    fig, ax = plt.subplots(figsize=(6.6, 2.0))
    ax.plot([2000, 2028], [0, 0], color=HEX["grey"], lw=1.2)
    for i, (yr, name, note) in enumerate(items):
        up = 1 if i % 2 == 0 else -1
        ax.plot([yr, yr], [0, 0.30 * up], color=HEX["teal"], lw=1.0)
        ax.plot([yr], [0], "o", ms=5, color=HEX["teal"])
        ax.text(yr, 0.36 * up, name, ha="center",
                va="bottom" if up > 0 else "top", fontsize=7, color=HEX["navy"],
                fontweight="bold")
        ax.text(yr, 0.56 * up, note, ha="center",
                va="bottom" if up > 0 else "top", fontsize=6.2, color=HEX["grey"])
    ax.set_ylim(-1.1, 1.1); ax.set_xlim(1999, 2029)
    ax.set_yticks([]); ax.spines['left'].set_visible(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Each generation added a block, not a better cable",
                 pad=8, fontsize=8.4)
    return save(fig, "sd_history.png")


if __name__ == "__main__":
    import json
    R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "_serdes_results.json")))
    for fn in (fig_topology, fig_channel, fig_ctle, fig_pulse, fig_taps_stages,
               fig_eyes, fig_history):
        print(fn())
    print(fig_budget(R))
    print(fig_pam4(R))


# --- 10. what actually falls monotonically ----------------------------------
def fig_stages(R):
    st = R['stages']
    names = ["channel\nonly", "+ CTLE", "+ transmit\nFFE", "+ DFE\n(5 taps)"]
    x = np.arange(len(st))
    fig, ax = plt.subplots(figsize=(6.0, 2.7))
    ax.plot(x, [s['snr_n'] for s in st], "o-", color=HEX["red"], lw=1.8, ms=6,
            label="signal to non-ISI noise")
    ax.plot(x, [s['snr_i'] for s in st], "s-", color=HEX["teal"], lw=1.8, ms=6,
            label="signal to residual ISI")
    ax.plot(x, [20 * np.log10(s['q']) for s in st], "^--", color=HEX["navy"],
            lw=1.6, ms=6, label="the two combined (20 log Q)")
    ax.axhline(20 * np.log10(7.034), color=HEX["amber"], lw=1.1, ls=":")
    ax.text(-0.05, 20 * np.log10(7.034) + 0.8, "Q needed for 1e−12", fontsize=6.6,
            color=HEX["amber"], ha="left")
    last = len(st) - 1
    for i, s in enumerate(st):
        # the two series cross at the end, so flip which side the labels sit on
        up_n, up_i = ((0, -12), (0, 8)) if i == last else ((0, 8), (0, -12))
        ax.annotate("%.1f" % s['snr_n'], (i, s['snr_n']), textcoords="offset points",
                    xytext=up_n, ha="center", fontsize=6.4, color=HEX["red"])
        ax.annotate("%.1f" % s['snr_i'], (i, s['snr_i']), textcoords="offset points",
                    xytext=up_i, ha="center", fontsize=6.4, color=HEX["teal"])
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("dB")
    ax.set_ylim(-7, 35)
    ax.set_title("Every linear block trades signal-to-noise for signal-to-ISI",
                 pad=6, fontsize=8.4)
    ax.legend(loc="center left", bbox_to_anchor=(0.02, 0.42), fontsize=6.8)
    _clean(ax)
    return save(fig, "sd_stages.png")
