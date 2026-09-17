"""Figures for the Signal Integrity long-form report.

Every figure is drawn from the same JSON the decks embed, so a figure and the
slide it corresponds to cannot disagree.
"""

import json
import os

import numpy as np

from docstyle import HEX, mpl_setup

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '_si_data')
OUT = os.path.join(HERE, 'figs_si')
plt = mpl_setup()
os.makedirs(OUT, exist_ok=True)

NAVY, TEAL, RED, GREY = HEX['navy'], HEX['teal'], HEX['red'], HEX['grey']
AMBER = HEX['amber']
PURPLE = '#6B46C1'


def D(n):
    return json.load(open(os.path.join(DATA, 'deck%02d.json' % n)))


def save(fig, name):
    p = os.path.join(OUT, name + '.png')
    fig.savefig(p)
    plt.close(fig)
    print('  %s' % name)


def tidy(ax, xl=None, yl=None, ti=None, grid=True):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(True, lw=0.4, color='#DDE3EA', zorder=0)
        ax.set_axisbelow(True)
    if xl: ax.set_xlabel(xl)
    if yl: ax.set_ylabel(yl)
    if ti: ax.set_title(ti)


# ------------------------------------------------------------- chapter 1 ---
def f_regions():
    r = D(1)['regions']
    fig, ax = plt.subplots(figsize=(6.4, 1.5))
    bands = [(1e5, r['f_lc'], 'lumped', '#D8DEE6'),
             (r['f_lc'], r['f_skin'], 'LC', '#BBD3E8'),
             (r['f_skin'], r['f_diel'], 'skin effect', '#A8D5CF'),
             (r['f_diel'], r['f_wg'], 'dielectric loss', '#F0D9A8'),
             (r['f_wg'], 5e11, 'waveguide', '#E8BDBD')]
    for lo, hi, lab, col in bands:
        ax.axvspan(lo, hi, color=col, lw=0)
        if np.log10(hi / lo) > 0.45:
            ax.text(np.sqrt(lo * hi), 0.5, lab, ha='center', va='center',
                    fontsize=7.2, color=NAVY)
    for f, lab in ((r['f_lc'], '%.1f MHz' % (r['f_lc'] / 1e6)),
                   (r['f_skin'], '%.0f MHz' % (r['f_skin'] / 1e6)),
                   (r['f_diel'], '%.0f MHz' % (r['f_diel'] / 1e6)),
                   (r['f_wg'], '%.0f GHz' % (r['f_wg'] / 1e9))):
        ax.axvline(f, color=NAVY, lw=0.8)
        ax.text(f, 1.06, lab, ha='center', fontsize=6.4, color=NAVY)
    ax.set_xscale('log'); ax.set_xlim(1e5, 5e11); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xlabel('frequency, Hz')
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    save(fig, 'regions')


def f_coax():
    c = D(1)['coax']['air']
    x = np.array(c['x'])
    fig, ax = plt.subplots(figsize=(4.4, 2.5))
    ax.plot(x, 1.0 / np.array(c['atten']), color=RED, lw=1.6,
            label='reciprocal of attenuation')
    ax.plot(x, c['power'], color=TEAL, lw=1.6, label='power handling')
    for xv, col, lab in ((c['x_min_atten'], RED, '%.1f Ω' % c['z_min_atten']),
                         (c['x_max_power'], TEAL, '%.1f Ω' % c['z_max_power'])):
        ax.axvline(xv, color=col, ls='--', lw=0.9)
        ax.text(xv, 1.03, lab, ha='center', fontsize=6.8, color=col)
    ax.set_xscale('log'); ax.set_xlim(1.2, 12); ax.set_ylim(0, 1.12)
    ax.set_xticks([1.5, 2, 3, 4, 6, 8, 12])
    ax.set_xticklabels(['1.5', '2', '3', '4', '6', '8', '12'])
    ax.minorticks_off()
    tidy(ax, 'outer / inner radius,  b/a', 'normalised')
    ax.legend(loc='lower center')
    save(fig, 'coax')


def f_tdr():
    d = D(1)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    for k, col in zip(list(d['tdr'])[1:], (NAVY, RED)):
        t = np.array(d['tdr'][k]['t_ns']); z = np.array(d['tdr'][k]['z'])
        m = t < 1.8
        ax.plot(t[m], z[m], lw=1.3, color=col, label=k)
    ax.axhline(50, color=GREY, ls='--', lw=0.8)
    tidy(ax, 'time, ns (two-way)', 'impedance reported, Ω')
    ax.legend(loc='lower right', fontsize=6.4)
    ax = axes[1]
    rr = [r for r in d['tdr_resolution'] if r['reads_ohm']]
    ax.plot([r['length_in'] for r in rr], [r['reads_ohm'] for r in rr],
            'o-', color=NAVY, lw=1.3, ms=3.5)
    ax.axhline(38, color=RED, ls='--', lw=0.9)
    ax.text(1.4, 38.5, 'true 38 Ω', color=RED, fontsize=6.8)
    ax.set_xscale('log')
    tidy(ax, 'length of the 38 Ω section, in', 'impedance reported, Ω')
    save(fig, 'tdr')


# ------------------------------------------------------------- chapter 2 ---
def f_return():
    d = D(2)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    x = np.array(d['profile']['x_over_h'])
    ax.plot(x, d['profile']['j'], color=TEAL, lw=1.6, label='analytic')
    s = d.get('solver', {})
    if s.get('x_over_h'):
        ax.plot(s['x_over_h'], s['solver'], color=NAVY, lw=1.1, ls='--',
                label='field solver')
    ax.axvspan(-3, 3, color='#F3E7C9', zorder=0)
    ax.set_xlim(-8, 8)
    tidy(ax, 'lateral distance, in trace heights', 'current density')
    ax.legend(loc='upper right', fontsize=6.6)
    ax = axes[1]
    k = np.linspace(0.1, 20, 300)
    ax.plot(k, 2 / np.pi * np.arctan(k) * 100, color=NAVY, lw=1.6)
    for kk, lab in ((3, '3h'), (6.3, '6.3h')):
        ax.axvline(kk, color=GREY, ls='--', lw=0.8)
        ax.text(kk + 0.3, 30, lab, fontsize=6.8, color=GREY)
    tidy(ax, 'band half-width, in trace heights', 'return current captured, %')
    save(fig, 'return')


def f_slot():
    d = D(2)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    for k, col in zip(d['slots'], (TEAL, NAVY, AMBER, RED)):
        s = d['slots'][k]
        f = np.array(s['f_ghz']); y = np.array(s['s21_db'])
        m = (f > 0.05) & (f < 40)
        ax.plot(f[m], y[m], lw=1.2, color=col, label=k)
    ax.set_xscale('log'); ax.set_ylim(-40, 2)
    tidy(ax, 'frequency, GHz', 'insertion loss, dB')
    ax.legend(loc='lower left', fontsize=6.4)
    ax = axes[1]
    z = D(2)['plane_z']
    ax.loglog(z['f_ghz'], z['z_ohm'], color=NAVY, lw=1.3)
    ax.axvline(z['f_first_mode_ghz'], color=RED, ls='--', lw=0.9)
    ax.text(z['f_first_mode_ghz'] * 1.1, 10, 'first cavity mode',
            fontsize=6.6, color=RED)
    tidy(ax, 'frequency, GHz', 'impedance between planes, Ω')
    save(fig, 'slot')


# ------------------------------------------------------------- chapter 3 ---
def f_rough():
    d = D(3)
    f = np.array(d['f_ghz'])
    fig, ax = plt.subplots(figsize=(4.6, 2.5))
    for nm, col in (('standard (STD)', RED), ('very low profile (VLP)', AMBER),
                    ('ultra low (HVLP2)', TEAL)):
        if nm not in d['roughness']:
            continue
        r = d['roughness'][nm]
        ax.semilogx(f, r['hammerstad'], ls='--', lw=1.1, color=col)
        ax.semilogx(f, r['huray'], lw=1.5, color=col,
                    label='%s (%.2f µm)' % (nm.split(' (')[0], r['rms_um']))
    ax.axhline(2, color=GREY, ls=':', lw=0.9)
    ax.text(0.12, 2.06, "Hammerstad's ceiling", fontsize=6.4, color=GREY)
    ax.set_xlim(0.1, 100)
    tidy(ax, 'frequency, GHz', 'resistance multiplier')
    ax.legend(loc='upper left', fontsize=6.4,
              title='solid: Huray   dashed: Hammerstad', title_fontsize=6.2)
    save(fig, 'rough')


def f_laminates():
    d = D(3)
    f = np.array(d['f_ghz_thin'])
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4))
    ax = axes[0]
    for nm, col in (('FR-4 (generic)', RED), ('Isola I-Speed', AMBER),
                    ('Panasonic Megtron 6', TEAL),
                    ('Panasonic Megtron 7', NAVY)):
        if nm not in d['laminates']:
            continue
        L = d['laminates'][nm]
        ax.loglog(f, L['total'], lw=1.4, color=col, label=nm)
    ax.set_xlim(0.5, 60)
    tidy(ax, 'frequency, GHz', 'loss, dB per inch')
    ax.legend(loc='upper left', fontsize=6.2)
    ax = axes[1]
    nm = 'Panasonic Megtron 6'
    if nm in d['laminates']:
        L = d['laminates'][nm]
        ax.plot(f, L['alpha_c'], color=NAVY, lw=1.3, label='conductor')
        ax.plot(f, L['alpha_d'], color=RED, lw=1.3, label='dielectric')
        ax.plot(f, L['total'], color=TEAL, lw=1.7, label='total')
        if L.get('crossover_ghz'):
            ax.axvline(L['crossover_ghz'], color=GREY, ls='--', lw=0.9)
            ax.text(L['crossover_ghz'] * 1.05, 0.02,
                    'crossover %.1f GHz' % L['crossover_ghz'], fontsize=6.4,
                    color=GREY)
    ax.set_xscale('log'); ax.set_xlim(0.5, 60)
    tidy(ax, 'frequency, GHz', 'loss, dB per inch', nm)
    ax.legend(loc='upper left', fontsize=6.4)
    save(fig, 'laminates')


def f_causal():
    d = D(3)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    c = d['causality']
    t = np.array(c['t_ns'])
    t0 = c['time_of_flight_ns']
    m = (t > t0 - 0.18) & (t < t0 + 0.30)
    ax.plot(t[m], np.array(c['y_causal'])[m], color=TEAL, lw=1.4, label='causal')
    ax.plot(t[m], np.array(c['y_flat'])[m], color=RED, lw=1.2,
            label='constant Dk and Df')
    ax.axvline(t0, color=GREY, ls='--', lw=0.9)
    ax.text(t0 + 0.005, ax.get_ylim()[1] * 0.8, 'time of flight',
            fontsize=6.4, color=GREY)
    tidy(ax, 'time, ns', 'impulse response')
    ax.legend(loc='upper right', fontsize=6.6)
    ax = axes[1]
    k = d['causal_dk']
    ax.semilogx(k['f_ghz'], k['dk'], color=NAVY, lw=1.5)
    ax.set_xlim(0.01, 100)
    tidy(ax, 'frequency, GHz', 'Dk')
    ax2 = ax.twinx()
    ax2.semilogx(k['f_ghz'], k['df'], color=RED, lw=1.2)
    ax2.set_ylabel('Df', color=RED); ax2.tick_params(colors=RED)
    ax2.spines['top'].set_visible(False)
    save(fig, 'causal')


def f_weave():
    d = D(3)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    w = d['weave']
    ax.barh(range(len(w)), [x['skew_ps_per_in'] for x in w], color=NAVY, height=0.6)
    ax.set_yticks(range(len(w)))
    ax.set_yticklabels([x['style'] for x in w], fontsize=6.4)
    ax.invert_yaxis()
    tidy(ax, 'skew, ps per inch', None, grid=False)
    ax.grid(True, axis='x', lw=0.4, color='#DDE3EA'); ax.set_axisbelow(True)
    ax = axes[1]
    a = d['weave_angle']
    ax.plot([x['angle_deg'] for x in a], [x['skew_ps'] for x in a],
            'o-', color=TEAL, lw=1.4, ms=3.5)
    ax.set_yscale('log')
    tidy(ax, 'angle to the weave, degrees', 'skew over 10 in, ps')
    save(fig, 'weave')


# ------------------------------------------------------------- chapter 4 ---
def f_stub():
    d = D(4)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    sw = d['stub']['sweep']
    ax.plot([r['stub_mil'] for r in sw], [r['excess_db'] for r in sw],
            color=RED, lw=1.6)
    tidy(ax, 'residual stub, mil', 'excess loss at 14 GHz, dB')
    ax = axes[1]
    for k, col in zip(d['tline_view'], (RED, AMBER, TEAL, NAVY)):
        v = d['tline_view'][k]
        ax.plot(v['f_ghz'], v['s11_db'], lw=1.2, color=col,
                label='%s (%.0f Ω)' % (k, v['z_diff']))
    ax.set_ylim(-45, 0)
    tidy(ax, 'frequency, GHz', 'return loss, dB')
    ax.legend(loc='lower right', fontsize=6.0)
    save(fig, 'stub')


def f_viaopt():
    d = D(4)['optimise']
    fig, ax = plt.subplots(figsize=(4.6, 2.5))
    for k, col in zip(d, (TEAL, NAVY, RED)):
        sw = d[k]['sweep']
        ax.plot([r['d_anti_mil'] for r in sw], [r['s11_nyq_db'] for r in sw],
                lw=1.4, color=col, label=k)
        b = d[k]['best']
        ax.plot([b['d_anti_mil']], [b['s11_nyq_db']], 'o', color=col, ms=4)
    m = list(d.values())[0]['matched']
    ax.axvline(m['d_anti_mil'], color=GREY, ls='--', lw=0.9)
    ax.text(m['d_anti_mil'] + 1, -5, 'barrel matched\nto 100 Ω',
            fontsize=6.2, color=GREY)
    ax.set_ylim(-40, 0)
    tidy(ax, 'antipad diameter, mil', 'return loss at 14 GHz, dB')
    ax.legend(loc='lower left', fontsize=6.4, title='launch capacitance',
              title_fontsize=6.2)
    save(fig, 'viaopt')


# ------------------------------------------------------------- chapter 5 ---
def f_coupling():
    d = D(5)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    rows = d['coupling_cost']['rows']
    ax.plot([r['s_mm'] for r in rows], [r['extra_loss_db'] for r in rows],
            'o-', color=RED, lw=1.5, ms=3.5)
    tidy(ax, 'edge-to-edge spacing, mm', 'extra loss over 10 in at 14 GHz, dB')
    ax2 = ax.twinx()
    ax2.plot([r['s_mm'] for r in rows], [r['coupling_pct'] for r in rows],
             's--', color=TEAL, lw=1.1, ms=3)
    ax2.set_ylabel('coupling, %', color=TEAL); ax2.tick_params(colors=TEAL)
    ax2.spines['top'].set_visible(False)
    ax = axes[1]
    t = d['thickness']
    ax.plot([r['t_um'] for r in t['rows']], [r['zdiff'] for r in t['rows']],
            'o-', color=NAVY, lw=1.5, ms=3.5)
    ax.axhline(t['cohn_zdiff'], color=GREY, ls='--', lw=0.9)
    ax.text(20, t['cohn_zdiff'] + 1.5, 'Cohn, zero thickness',
            fontsize=6.4, color=GREY)
    tidy(ax, 'copper thickness, µm', 'differential impedance, Ω')
    save(fig, 'coupling')


def f_skewconv():
    d = D(5)['skew']
    fig, ax = plt.subplots(figsize=(4.6, 2.3))
    for k, col in zip(d, (TEAL, NAVY, AMBER, RED, PURPLE)):
        s = d[k]
        f = np.array(s['f_ghz']); y = np.array(s['scd21_db'])
        m = f <= 50
        ax.plot(f[m], y[m], lw=1.2, color=col, label=k)
    ax.axvline(14, color=GREY, ls='--', lw=0.9)
    ax.set_ylim(-45, 3)
    tidy(ax, 'frequency, GHz', 'differential to common, dB')
    ax.legend(loc='lower right', fontsize=6.2, ncol=2, title='intra-pair skew',
              title_fontsize=6.2)
    save(fig, 'skewconv')


# ------------------------------------------------------------- chapter 6 ---
def f_xtalk():
    d = D(6)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    L = d['length']
    ax.plot([r['length_in'] for r in L], [r['next_micro'] for r in L],
            'o-', color=RED, lw=1.3, ms=3, label='NEXT, microstrip')
    ax.plot([r['length_in'] for r in L], [r['fext_micro'] for r in L],
            's-', color=AMBER, lw=1.3, ms=3, label='FEXT, microstrip')
    if 'fext_micro_linear' in L[0]:
        ax.plot([r['length_in'] for r in L],
                [abs(r['fext_micro_linear']) for r in L],
                ':', color=AMBER, lw=1.0,
                label='FEXT, first-order formula')
    ax.plot([r['length_in'] for r in L], [r['next_strip'] for r in L],
            '^-', color=NAVY, lw=1.3, ms=3, label='NEXT, stripline')
    ax.plot([r['length_in'] for r in L], [r['fext_strip'] for r in L],
            'v-', color=TEAL, lw=1.6, ms=3, label='FEXT, stripline (zero)')
    ax.set_ylim(0, 105)
    tidy(ax, 'coupled length, in', 'crosstalk, % of aggressor swing')
    ax.legend(loc='upper left', fontsize=5.8)
    ax = axes[1]
    rows = d['spacing']['rows']
    ax.plot([r['spacing_w'] for r in rows], [r['next_pct'] for r in rows],
            'o-', color=NAVY, lw=1.5, ms=3.5)
    ax.axvline(3, color=RED, ls='--', lw=0.9)
    ax.text(3.1, max(r['next_pct'] for r in rows) * 0.6,
            'the three-widths rule', fontsize=6.4, color=RED)
    tidy(ax, 'spacing, in trace widths', 'near-end crosstalk, % of swing')
    save(fig, 'xtalk')


# ------------------------------------------------------------- chapter 7 ---
def f_pdn():
    d = D(7)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4))
    ax = axes[0]
    for k in d['parts']:
        ax.loglog(d['f_hz'], d['parts'][k], lw=0.7, color='#C3CBD6')
    ax.loglog(d['f_hz'], d['z_ohm'], lw=1.6, color=NAVY)
    ax.axhline(d['target']['z_target'], color=RED, ls='--', lw=1.0)
    ax.text(2e3, d['target']['z_target'] * 1.3,
            'target %.0f mΩ' % (1000 * d['target']['z_target']),
            fontsize=6.4, color=RED)
    for p in d['peaks'][:2]:
        ax.plot([p['f_hz']], [p['z_ohm']], 'o', color=AMBER, ms=4)
    ax.set_ylim(1e-4, 1e2)
    tidy(ax, 'frequency, Hz', 'impedance, Ω')
    ax = axes[1]
    mc = d['more_caps']
    ax.plot([r['count'] for r in mc], [1000 * r['worst_peak_ohm'] for r in mc],
            'o-', color=RED, lw=1.5, ms=3.5, label='worst anti-resonant peak')
    ax.plot([r['count'] for r in mc], [1000 * r['z_at_100mhz'] for r in mc],
            's-', color=TEAL, lw=1.5, ms=3.5, label='impedance at 100 MHz')
    ax.set_xscale('log')
    tidy(ax, 'number of 100 nF capacitors', 'impedance, mΩ')
    ax.legend(loc='center left', fontsize=6.4)
    save(fig, 'pdn')


def f_ripple():
    d = D(7)['ripple']
    fig, ax = plt.subplots(figsize=(4.6, 2.2))
    ax.semilogx(d['f_hz'], d['jitter_pp_ps'], color=NAVY, lw=1.6)
    ax.axvline(d['pll_bw_hz'], color=AMBER, ls='--', lw=1.0)
    ax.text(d['pll_bw_hz'] * 1.2, max(d['jitter_pp_ps']) * 0.8,
            'loop bandwidth', fontsize=6.6, color=AMBER)
    ax.plot([d['worst_f_hz']], [d['worst_jitter_pp_ps']], 'o', color=RED, ms=4.5)
    tidy(ax, 'frequency of the supply tone, Hz', 'jitter, ps peak to peak')
    save(fig, 'ripple')


# ------------------------------------------------------------- chapter 8 ---
def f_bathtub():
    d = D(8)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    for k, col in zip(d['bathtubs'], (NAVY, RED, AMBER)):
        b = d['bathtubs'][k]
        ax.semilogy(b['t_ps'], np.clip(b['ber'], 1e-18, 1), lw=1.3, color=col,
                    label=k)
    ax.axhline(1e-12, color=GREY, ls='--', lw=0.9)
    ax.set_ylim(1e-18, 1)
    tidy(ax, 'sampling position, ps', 'error ratio')
    ax.legend(loc='upper center', fontsize=6.0)
    ax = axes[1]
    jt = D(8)['jtol_bw']
    for k, col in zip(jt, (TEAL, NAVY, RED)):
        ax.loglog(jt[k]['f_hz'], jt[k]['tol_ui'], lw=1.4, color=col,
                  label=k + ' loop')
    tidy(ax, 'jitter frequency, Hz', 'tolerance, UI peak to peak')
    ax.legend(loc='upper right', fontsize=6.4)
    save(fig, 'bathtub')


# ------------------------------------------------------------- chapter 9 ---
def f_bus():
    d = D(9)['bus']
    fig, ax = plt.subplots(figsize=(4.8, 2.5))
    r = d['rows']
    x = [q['rate_gbps'] for q in r]
    ax.plot(x, [q['common_clock_ps'] for q in r], 'o-', color=GREY, lw=1.4,
            ms=3.5, label='common clock')
    ax.plot(x, [q['source_sync_ps'] for q in r], 's-', color=AMBER, lw=1.4,
            ms=3.5, label='source synchronous')
    ax.plot(x, [q['serial_ps'] for q in r], '^-', color=TEAL, lw=1.6, ms=3.5,
            label='embedded clock')
    ax.axhline(0, color=NAVY, lw=1.0)
    ax.set_xscale('log'); ax.set_ylim(-400, 900)
    ax.set_xticks(x); ax.set_xticklabels(['%g' % v for v in x]); ax.minorticks_off()
    tidy(ax, 'rate per pin, Gb/s', 'timing margin, ps')
    ax.legend(loc='upper right', fontsize=6.6)
    save(fig, 'bus')


# ------------------------------------------------------------ chapter 10 ---
def f_echo():
    d = D(10)
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))
    ax = axes[0]
    c = d['channel']
    ax.plot(c['f_ghz'], c['s21_db'], color=NAVY, lw=1.3, label='insertion loss')
    ax.plot(c['f_ghz'], c['s11_db'], color=GREY, lw=0.9, label='return loss')
    ax.axvline(14, color=RED, ls='--', lw=0.9)
    ax.set_ylim(-80, 3)
    tidy(ax, 'frequency, GHz', 'dB')
    ax.legend(loc='lower left', fontsize=6.4)
    ax = axes[1]
    rows = d['echo']['rows']
    ax.bar(range(len(rows)), [r['eye_err_pct'] for r in rows], color=RED,
           width=0.6)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(['%g' % r['delay_ps'] for r in rows], fontsize=6.6)
    ax.axhline(0, color=NAVY, lw=0.9)
    tidy(ax, 'echo delay, ps', 'eye error, %', grid=False)
    ax.grid(True, axis='y', lw=0.4, color='#DDE3EA'); ax.set_axisbelow(True)
    save(fig, 'echo')


# ------------------------------------------------------------ chapter 11 ---
def f_com():
    d = D(11)
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    rows = d['sensitivity']
    y = np.arange(len(rows))
    cols = [TEAL if r['com_db'] >= 3 else RED for r in rows]
    ax.barh(y, [r['com_db'] for r in rows], color=cols, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels([r['variant'] for r in rows], fontsize=6.4)
    ax.invert_yaxis()
    ax.axvline(3, color=RED, ls='--', lw=1.0)
    ax.text(3.15, len(rows) - 0.4, '3 dB threshold', fontsize=6.4, color=RED)
    tidy(ax, 'channel operating margin, dB', None, grid=False)
    ax.grid(True, axis='x', lw=0.4, color='#DDE3EA'); ax.set_axisbelow(True)
    save(fig, 'com')


def f_ild():
    d = D(11)['ild']
    fig, ax = plt.subplots(figsize=(4.8, 2.3))
    ax.plot(d['f_ghz'], d['il_db'], color=NAVY, lw=1.3, label='insertion loss')
    ax.plot(d['f_ghz'], d['fit_db'], color=GREY, lw=1.0, ls='--',
            label='smooth fit')
    tidy(ax, 'frequency, GHz', 'insertion loss, dB')
    ax.legend(loc='lower left', fontsize=6.4)
    ax2 = ax.twinx()
    ax2.plot(d['f_ghz'], d['ild_db'], color=RED, lw=0.9)
    ax2.set_ylabel('deviation, dB', color=RED); ax2.tick_params(colors=RED)
    ax2.spines['top'].set_visible(False)
    save(fig, 'ild')


ALL = [f_regions, f_coax, f_tdr, f_return, f_slot, f_rough, f_laminates,
       f_causal, f_weave, f_stub, f_viaopt, f_coupling, f_skewconv, f_xtalk,
       f_pdn, f_ripple, f_bathtub, f_bus, f_echo, f_com, f_ild]

if __name__ == '__main__':
    print('figures ->', OUT)
    for fn in ALL:
        try:
            fn()
        except Exception as e:
            print('  FAILED %s: %s' % (fn.__name__, e))
