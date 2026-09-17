"""Compute every number the Signal Integrity decks quote, and cache it as JSON.

Each deck embeds the contents of one file from `_si_data/`. Nothing in a deck
body is typed in by hand, so re-running this file is the only way any figure in
the series changes, and `verification.json` records every cross-check against a
published result so a reader can see what has been checked and how closely.
"""

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
OUT = os.path.join(HERE, '_si_data')


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return [_clean(v) for v in o.tolist()]
    if isinstance(o, float) and (o != o or abs(o) == float('inf')):
        return None
    return o


def save(name, obj):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + '.json')
    with open(p, 'w') as fh:
        json.dump(_clean(obj), fh, separators=(',', ':'))
    print('  wrote %-16s %8.1f kB' % (name + '.json', os.path.getsize(p) / 1024))


def thin(a, n=260):
    a = np.asarray(a, float)
    if a.size <= n:
        return a.tolist()
    idx = np.unique(np.round(np.linspace(0, a.size - 1, n)).astype(int))
    return a[idx].tolist()


VER = {}


def check(key, ours, published, source, tol_pct=5.0):
    err = 100.0 * (ours / published - 1) if published else float('nan')
    VER[key] = dict(ours=float(ours), published=float(published),
                    err_pct=float(err), source=source,
                    within_tolerance=bool(abs(err) <= tol_pct))
    return VER[key]


# ---------------------------------------------------------------- deck 01 ---
def deck01():
    from si_models import tline as T
    d = {}
    v = T.verify_against_johnson()
    d['johnson'] = v
    for k, r in v.items():
        if isinstance(r, dict):
            check('tline/' + k, r['ours'], r['johnson'],
                  'Johnson & Graham, Advanced Black Magic 2003, sec 3.10', 2.0)
    d['regions'] = T.regions()
    d['coax'] = {}
    for er, nm in ((1.0, 'air'), (1.05, 'foam'), (2.1, 'PTFE'),
                   (2.25, 'polyethylene')):
        c = T.coax_optimum(er)
        c['x'] = thin(c['x']); c['z'] = thin(c['z'])
        c['atten'] = thin(c['atten']); c['power'] = thin(c['power'])
        d['coax'][nm] = c
    d['bounce'] = {
        'series-terminated (25 ohm source)': T.bounce(25, 50, 1e6, 10),
        'unterminated (5 ohm source)': T.bounce(5, 50, 1e6, 10),
        'over-terminated (90 ohm source)': T.bounce(90, 50, 1e6, 10)}
    d['short'] = {str(tr): T.electrically_short(tr * 1e-12, L * 0.0254,
                                                T.C0 / np.sqrt(4.0))
                  for tr in (20, 100, 500) for L in (2,)}
    tdrs = {}
    for lab, segs in (
            ('a clean 50 ohm line', [{'z0': 50, 'length_in': 4.0}]),
            ('a 0.4 in section at 38 ohm',
             [{'z0': 50, 'length_in': 2.0}, {'z0': 38, 'length_in': 0.4},
              {'z0': 50, 'length_in': 2.0}]),
            ('two discontinuities in series',
             [{'z0': 50, 'length_in': 1.5}, {'z0': 38, 'length_in': 0.5},
              {'z0': 50, 'length_in': 1.0}, {'z0': 62, 'length_in': 0.5},
              {'z0': 50, 'length_in': 1.5}])):
        r = T.tdr(segs, tr_ps=20, ac_db_in_sqrtghz=0.5, ad_db_in_ghz=0.2)
        tdrs[lab] = dict(t_ns=thin(r['t_ns'], 420), z=thin(r['z_profile'], 420),
                         rho=thin(r['rho'], 420))
    d['tdr'] = tdrs
    d['tdr_resolution'] = []
    for L in (0.05, 0.1, 0.2, 0.4, 1.0, 3.0):
        r = T.tdr([{'z0': 50, 'length_in': 2.0}, {'z0': 38, 'length_in': L},
                   {'z0': 50, 'length_in': 2.0}], tr_ps=20)
        z = np.array(r['z_profile']); t = np.array(r['t_ns'])
        w = (t > 0.70) & (t < 0.70 + 2 * L * r['tpd_ps_per_in'] / 1000)
        d['tdr_resolution'].append(dict(
            length_in=L, reads_ohm=float(z[w].min()) if w.any() else None,
            true_ohm=38.0))
    return d


# ---------------------------------------------------------------- deck 02 ---
def deck02():
    from si_models import retpath as R
    d = {'fraction': R.verify_return_fraction()}
    check('retpath/return_within_3h', d['fraction']['at_3h'], 0.80,
          'Johnson sec 5.2; Hall & Heck eq (5-15)', 2.0)
    x = np.linspace(-8, 8, 401)
    d['profile'] = dict(x_over_h=x.tolist(),
                        j=R.return_current_density(x).tolist())
    d['solver'] = R.verify_against_solver()
    if d['solver'].get('x_over_h'):
        for k in ('x_over_h', 'solver', 'lorentzian'):
            d['solver'][k] = thin(d['solver'][k], 300)
    d['crossover'] = R.crossover_frequency(0.2, 0.2)
    d['slots'] = {}
    for sl in (5.0, 10.0, 20.0, 40.0):
        s = R.slot_crossing(sl, 1.0, 0.2, 50.0, tr_ps=30)
        s['f_ghz'] = thin(s['f_ghz']); s['s21_db'] = thin(s['s21_db'])
        s['s11_db'] = thin(s['s11_db'])
        d['slots']['%.0f mm slot' % sl] = s
    d['stitch'] = [dict(distance_mm=dd, **{'n%d' % n: R.stitching_via(
        dd, n_return=n)['l_nh'] for n in (1, 2, 4)}) for dd in
        (0.5, 1.0, 1.5, 2.0, 3.0, 5.0)]
    d['stitch_cap'] = [R.stitching_capacitor(c) for c in (1.0, 10.0, 100.0)]
    d['cavity'] = R.cavity_modes(150, 100, 4.0, 5)
    pi = R.plane_impedance(150, 100, 100, 4.0)
    pi['f_ghz'] = thin(pi['f_ghz'], 400); pi['z_ohm'] = thin(pi['z_ohm'], 400)
    d['plane_z'] = pi
    return d


# ---------------------------------------------------------------- deck 03 ---
def deck03():
    from si_models import materials as M
    d = {'roughness_check': M.verify_roughness(),
         'weave_check': M.verify_fibre_weave()}
    for k, r in d['roughness_check'].items():
        check('materials/' + k, r['ours'], r['published'],
              'Hall & Heck, Advanced Signal Integrity, ch. 5', 3.0)
    for k in ('ten_inch_ghz', 'five_inch_ghz'):
        r = d['weave_check'][k]
        check('materials/weave_' + k, r['ours'], r['published'],
              'Hall & Heck, example 7-2', 5.0)
    f = np.logspace(7, 11, 300)
    d['f_ghz'] = (f / 1e9).tolist()
    d['roughness'] = {}
    for nm, rms in M.FOILS.items():
        d['roughness'][nm] = dict(
            rms_um=rms,
            hammerstad=M.hammerstad(f, rms).tolist(),
            huray=M.huray(f, a_um=max(0.25, rms), n_spheres=max(1.0, (rms / 0.4) ** 2 * 6.0),
                          tile_um=max(2.0, 5.0 * rms)).tolist())
    d['skin_depth_um'] = (M.skin_depth(f) * 1e6).tolist()
    d['laminates'] = {}
    for nm, p in M.LAMINATES.items():
        r = M.loss_per_inch(f, p['dk'], p['df'], rms_um=0.4)
        d['laminates'][nm] = dict(
            dk=p['dk'], df=p['df'], era=p['era'],
            alpha_c=thin(r['alpha_c']), alpha_d=thin(r['alpha_d']),
            total=thin(r['total']),
            at_14ghz=float(np.interp(14e9, f, r['total'])),
            at_28ghz=float(np.interp(28e9, f, r['total'])),
            crossover_ghz=r['crossover_ghz'])
    d['f_ghz_thin'] = thin((f / 1e9))
    ds = M.djordjevic_sarkar(f, 3.40, 0.0040, 12e9)
    d['causal_dk'] = dict(f_ghz=thin(f / 1e9), dk=thin(ds['dk']),
                          df=thin(ds['df']), eps_inf=ds['eps_inf'],
                          d_eps=ds['d_eps'])
    fk = np.logspace(7, 11, 500)
    dsk = M.djordjevic_sarkar(fk, 3.40, 0.0040, 12e9)
    d['kk'] = dict(causal=M.kramers_kronig_check(fk, dsk['eps_r']),
                   flat=M.kramers_kronig_check(
                       fk, 3.40 * np.ones_like(fk) - 1j * 3.40 * 0.0040))
    c = M.causality_error(10.0, 3.40, 0.0040, 12e9)
    c['t_ns'] = thin(c['t_ns'], 500); c['y_flat'] = thin(c['y_flat'], 500)
    c['y_causal'] = thin(c['y_causal'], 500)
    d['causality'] = c
    d['weave'] = [M.fibre_weave(st, 10.0, 3.615, f_ghz=14.0) for st in M.WEAVES]
    d['weave_angle'] = [M.fibre_weave('1080 (open)', 10.0, 3.615,
                                      angle_deg=a, f_ghz=14.0)
                        for a in (0, 0.5, 1, 2, 5, 10, 30, 45)]
    return d


# ---------------------------------------------------------------- deck 04 ---
def deck04():
    from si_models import via as V
    from si_models import retpath as R
    d = {}
    d['params'] = dict(
        c_tight=V.via_capacitance(0.120, 0.018, 0.030),
        c_open=V.via_capacitance(0.120, 0.018, 0.050),
        l_isolated=V.via_inductance(0.120, 0.010),
        l_with_return=[dict(distance_mm=dd, n=n,
                            l_nh=R.stitching_via(dd, plane_gap_mm=3.05,
                                                 n_return=n)['l_nh'])
                       for dd in (0.5, 1.0, 2.0) for n in (1, 2, 4)],
        z_coax_30=V.via_coax_impedance(0.010, 0.030),
        z_coax_50=V.via_coax_impedance(0.010, 0.050))
    a = V.antipad_sweep(0.010, 0.120, 3.7, 0.018, z_target=100.0)
    d['antipad'] = a
    d['models'] = {}
    for cpf, lnh, lab in ((1.015, 2.969, 'tight antipad, remote return'),
                          (0.359, 0.30, 'open antipad, close ground vias')):
        m = V.model_comparison(cpf, lnh, z0=100.0)
        m['f_ghz'] = thin(m['f_ghz']); m['s11_pi_db'] = thin(m['s11_pi_db'])
        m['s21_pi_db'] = thin(m['s21_pi_db'])
        d['models'][lab] = m
    d['stub'] = V.backdrill_sweep(0.120, 0.25, 14.0)
    d['stub_notch'] = [dict(mil=m, ghz=V.stub_notch_ghz(m / 1000.0))
                       for m in (8, 20, 40, 60, 90, 110, 150)]
    f = np.linspace(0.2e9, 40e9, 400)
    d['tline_view'] = {}
    for da in (0.030, 0.040, 0.050, 0.065):
        r = V.via_as_tline(f, 0.120, 0.010, da, 3.7, 100.0)
        d['tline_view']['%.0f mil antipad' % (da * 1000)] = dict(
            z_diff=r['z_via_diff'], f_ghz=thin(r['f_ghz']),
            s11_db=thin(r['s11_db']), s21_db=thin(r['s21_db']))
    d['optimise'] = {}
    for lc in (0.05, 0.08, 0.15):
        o = V.optimise_via(0.120, 0.010, 3.7, 100.0, launch_c_pf=lc,
                           f_nyq_ghz=14.0)
        d['optimise']['%.2f pF launch' % lc] = dict(
            best=o['best'], widest=o['widest'],
            matched=o['impedance_matched'], gain_db=o['gain_db'],
            sweep=o['sweep'][::3])
    d['thickness'] = [dict(t_mil=t * 1000,
                           s11_14=float(np.interp(
                               14, V.via_as_tline(f, t, 0.010, 0.050, 3.7,
                                                  100.0)['f_ghz'],
                               V.via_as_tline(f, t, 0.010, 0.050, 3.7,
                                              100.0)['s11_db'])))
                      for t in (0.062, 0.093, 0.120, 0.160, 0.200, 0.250)]
    d['via_xtalk'] = [dict(s2_mil=s2 * 1000,
                           lm_nh=V.via_crosstalk_inductance(0.060, 0.040,
                                                            s2, 0.040, 0.005))
                      for s2 in (0.030, 0.040, 0.050, 0.070, 0.100)]
    return d


# ---------------------------------------------------------------- deck 05 ---
def deck05():
    from si_models import diffpair as D
    d = {'solver_check': D.verify_against_solver(),
         'thickness': D.thickness_effect()}
    for r in d['solver_check']:
        check('diffpair/zdiff_w%.2f_s%.2f' % (r['w_mm'], r['s_mm']),
              r['zdiff_solver'], r['zdiff_cohn'],
              'Cohn 1955, exact coupled-stripline result', 1.0)
    d['coupling_cost'] = D.coupling_cost(use_solver=True)
    d['skew'] = {}
    for sk in (1.0, 2.0, 5.0, 10.0, 20.0):
        r = D.skew_conversion(sk)
        d['skew']['%g ps' % sk] = dict(
            f_ghz=thin(r['f_ghz']), scd21_db=thin(r['scd21_db']),
            sdd21_db=thin(r['sdd21_db']),
            f_full_conversion_ghz=r['f_full_conversion_ghz'])
    mv = D.mode_velocity_conversion()
    mv['f_ghz'] = thin(mv['f_ghz'])
    mv['conversion_db'] = thin(mv['conversion_db'])
    d['mode_velocity'] = mv
    d['cmrr'] = [D.common_mode_rejection(50.0, imb, gm)
                 for imb, gm in ((0.5, 0.05), (2.0, 0.2), (5.0, 0.5))]
    d['termination'] = D.termination_options(100.0)
    return d


# ---------------------------------------------------------------- deck 06 ---
def deck06():
    from si_models import xtalk as X
    from si_models import diffpair as D
    from si_models.fdm2d import CrossSection, rlgc, modal
    d = {}
    strip = D.pair_from_geometry(0.20, 0.20, 0.40, 4.0)
    d['stripline_modal'] = {k: strip[k] for k in
                            ('z0e', 'z0o', 'k', 'Ls', 'Lm', 'Cs', 'Cm')}
    d['stripline_coeff'] = X.coefficients(strip)
    W, h, t, er, cell = 12 * 0.2, 0.2, 0.018, 4.0, 0.01
    cs = CrossSection(W, 20 * h, cell)
    cs.dielectric(0, W, 0, h, er)
    cs.ground_plane(0, cell)
    cs.conductor(W / 2 - 0.3, W / 2 - 0.1, h, h + t, 1)
    cs.conductor(W / 2 + 0.1, W / 2 + 0.3, h, h + t, 2)
    C, L = rlgc(cs)
    ms = modal(C, L)
    d['microstrip_modal'] = {k: ms[k] for k in
                             ('z0e', 'z0o', 'k', 'Ls', 'Lm', 'Cs', 'Cm')}
    d['microstrip_coeff'] = X.coefficients(ms)
    d['spacing'] = X.spacing_sweep(length_in=6.0, tr_ps=20.0)
    d['length'] = []
    for L_in in (0.5, 1, 2, 4, 6, 10, 20):
        r = X.next_fext(strip, L_in, 20.0, 4.0)
        rm = X.next_fext(ms, L_in, 20.0, 4.0)
        d['length'].append(dict(length_in=L_in, next_strip=r['next_pct'],
                                fext_strip=r['fext_pct'],
                                next_micro=rm['next_pct'],
                                fext_micro=rm['fext_pct'],
                                saturation_in=r['saturation_length_in']))
    d['risetime'] = []
    for tr in (10, 20, 40, 80, 160):
        r = X.next_fext(ms, 6.0, tr, 4.0)
        d['risetime'].append(dict(tr_ps=tr, next_pct=r['next_pct'],
                                  fext_pct=r['fext_pct'],
                                  saturation_in=r['saturation_length_in']))
    d['guard'] = {k: dict(next_pct=v['next_pct'], fext_pct=v['fext_pct'],
                          kb=v['kb'], kf=v['kf'])
                  for k, v in X.guard_comparison().items()}
    n = [X.next_fext(strip, 6.0, 20.0, 4.0)['next_v'] * 0.4] * 4
    fx = [X.next_fext(ms, 6.0, 20.0, 4.0)['fext_v'] * 0.4] * 4
    d['icn'] = X.icn(n, fx, 0.4)
    d['budget'] = X.budget_impact(d['icn']['icn_mv'], 4.0, 44.5)
    return d


# ---------------------------------------------------------------- deck 07 ---
def deck07():
    from si_models import pdn as P
    d = {'target': P.target_impedance(0.9, 5.0, 20.0)}
    z = P.pdn_impedance()
    f = z['f']
    d['f_hz'] = thin(f, 420)
    d['z_ohm'] = thin(z['z'], 420)
    d['parts'] = {k: thin(v, 420) for k, v in z['parts'].items()}
    d['peaks'] = P.antiresonances(f, z['z'])
    d['caps'] = {k: dict(srf_hz=P.series_resonance(v['c'], v['esl'], 0.6e-9),
                         srf_bare_hz=P.series_resonance(v['c'], v['esl']),
                         **v) for k, v in P.CAP_LIBRARY.items()}
    d['mounting'] = [dict(vias=n,
                          l_ph=P.mounting_inductance(0.8, 1.6, n) * 1e12)
                     for n in (1, 2, 4, 8)]
    d['more_caps'] = []
    for cnt in (10, 20, 40, 80, 160):
        zz = P.pdn_impedance(f, tiers=[('100 uF bulk (tantalum)', 4, 1.2e-9),
                                       ('10 uF 0805', 10, 0.9e-9),
                                       ('100 nF 0402', cnt, 0.6e-9)])
        pk = P.antiresonances(f, zz['z'])
        d['more_caps'].append(dict(count=cnt,
                                   worst_peak_ohm=pk[0]['z_ohm'] if pk else None,
                                   worst_peak_hz=pk[0]['f_hz'] if pk else None,
                                   z_at_100mhz=float(np.interp(1e8, f, zz['z'])),
                                   z_at_1ghz=float(np.interp(1e9, f, zz['z']))))
    d['ssn'] = [P.ssn(n, 0.020, 25.0, 60.0) for n in (1, 4, 16, 32, 64)]
    rs = P.ripple_sweep(20.0, -20.0, 4e6, 14e9)
    rs['f_hz'] = thin(rs['f_hz'])
    rs['jitter_pp_ps'] = thin(rs['jitter_pp_ps'])
    d['ripple'] = rs
    d['psrr'] = [dict(psrr_db=p,
                      jitter_pp_ps=P.supply_noise_to_jitter(
                          20.0, 5e6, p, pll_bw_hz=4e6,
                          f_carrier=14e9)['jitter_pp_ps'])
                 for p in (-10, -20, -30, -40)]
    return d


# ---------------------------------------------------------------- deck 08 ---
def deck08():
    from si_models import jitter as J
    d = {'q': {str(b): J.q_from_ber(b) for b in
               (1e-3, 1e-6, 1e-9, 1e-12, 1e-15, 1e-17)}}
    d['dual_dirac'] = [J.dual_dirac(rj, dj, 1e-12)
                       for rj, dj in ((0.5, 5.0), (0.8, 12.0), (1.5, 12.0),
                                      (0.8, 20.0))]
    d['bathtubs'] = {}
    for lab, (rj, dj) in (('RJ 0.5 ps, DJ 8 ps', (0.5, 8.0)),
                          ('RJ 1.0 ps, DJ 8 ps', (1.0, 8.0)),
                          ('RJ 0.5 ps, DJ 16 ps', (0.5, 16.0))):
        b = J.bathtub(rj, dj, 35.7, 400)
        d['bathtubs'][lab] = dict(t_ps=thin(b['t_ps'], 300),
                                  ber=thin(b['ber'], 300),
                                  **J.eye_opening(b))
    d['extrapolation'] = []
    for w in (0.0, 1e-9, 1e-8, 1e-7):
        e = J.extrapolation_error(w2=w)
        e['weight'] = w
        d['extrapolation'].append({k: v for k, v in e.items()
                                   if not isinstance(v, (list, tuple))})
    il = J.integration_limits_matter()
    d['phase_noise'] = dict(rows=il['rows'], f_hz=thin(il['f_hz'], 300),
                            l_dbc=thin(il['l_dbc'], 300),
                            f_carrier=il['f_carrier'])
    jt = J.jitter_tolerance(bw_hz=4e6, budget_ui=0.15)
    d['jtol'] = dict(f_hz=thin(jt['f_hz']), tol_ui=thin(jt['tol_ui']),
                     bw_hz=jt['bw_hz'], budget_ui=jt['budget_ui'])
    d['jtol_bw'] = {}
    for bw in (1e6, 4e6, 16e6):
        r = J.jitter_tolerance(bw_hz=bw, budget_ui=0.15)
        d['jtol_bw']['%g MHz' % (bw / 1e6)] = dict(
            f_hz=thin(r['f_hz'], 200), tol_ui=thin(r['tol_ui'], 200))
    tr = J.cdr_transfer(np.logspace(3, 9, 300), 4e6)
    d['cdr'] = dict(f_hz=thin(tr['f_hz'], 240),
                    transfer_db=thin(tr['jitter_transfer_db'], 240),
                    error_db=thin(tr['error_db'], 240))
    try:
        from si_models import sparam_qc as Q
        ch = Q.reference_channel(0.0)
        p = Q.pulse_from_s21(ch['s21'], ch['M'], ch['NFFT'])
        pk = int(np.argmax(p))
        d['ddj'] = J.ddj_from_pulse(p, ch['M'], pk, depth=6)
    except Exception as exc:
        d['ddj'] = dict(ok=False, error=str(exc))
    return d


# ---------------------------------------------------------------- deck 09 ---
def deck09():
    from si_models import timing as T
    d = {'flight': [dict(z_source=z,
                         **{k: v for k, v in
                            T.flight_time(8.0, 4.0, 50.0, z).items()
                            if k != 'steps'})
                    for z in (10, 20, 50, 75, 150, 250, 400)]}
    d['flight_steps'] = T.flight_time(8.0, 4.0, 50.0, 300.0)['steps'][:14]
    d['bus'] = T.bus_comparison()
    d['stat'] = {}
    for n, terms in ((4, [12, 8, 6, 5]),
                     (8, [12, 8, 6, 5, 4, 3, 3, 2]),
                     (16, [12, 8, 6, 5, 4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1])):
        d['stat']['%d terms' % n] = T.worst_case_vs_statistical(terms)
    d['skew'] = T.skew_budget()
    d['margins'] = [T.setup_hold_margin(per, 150, 60, 40, 1400, 1300, 50, 30, 10)
                    for per in (2500, 1250, 625, 312.5)]
    return d


# ---------------------------------------------------------------- deck 10 ---
def deck10():
    from si_models import sparam_qc as Q
    ch = Q.reference_channel(0.0)
    d = {'equalised': Q.equalised_eye(ch['s21'], ch)}
    d['qc'] = Q.qc_summary(ch)
    d['truncation'] = Q.truncation_study(ch)
    d['dc'] = Q.dc_study(ch)
    d['minphase_sweep'] = [
        dict(depth_db=dd,
             **Q.causality_minimum_phase(
                 Q.inject_magnitude_only_error(ch, depth_db=dd) if dd > 0
                 else ch['s21'], ch['f']))
        for dd in (0.0, 1.0, 2.0, 4.0, 8.0)]
    d['echo'] = Q.echo_placement_study(ch)
    d['correlation'] = Q.correlation_study(ch)
    try:
        d['deembed'] = Q.deembed_study(ch)
    except Exception as exc:
        d['deembed'] = dict(error=str(exc))
    f = ch['f']
    m = f <= 50e9
    d['channel'] = dict(
        f_ghz=thin(f[m] / 1e9, 300),
        s21_db=thin(20 * np.log10(np.abs(ch['s21'][m]) + 1e-15), 300),
        s11_db=thin(20 * np.log10(np.abs(ch['s11'][m]) + 1e-15), 300))
    return d


# ---------------------------------------------------------------- deck 11 ---
def deck11():
    from si_models import sparam_qc as Q
    from si_models import com as C
    ch = Q.reference_channel(0.0)
    ch_stub = Q.reference_channel(0.110)
    base = C.com(ch)
    d = {'com': base, 'interpret': C.interpret(base),
         'com_with_stub': C.com(ch_stub),
         'masks': C.compliance_masks(ch),
         'masks_with_stub': C.compliance_masks(ch_stub)}
    d['backdrill_gain_db'] = base['com_db'] - d['com_with_stub']['com_db']
    sv = C.sensitivity(ch)
    seen, rows = set(), []
    for r in sv['rows']:
        if r['variant'] in seen:
            continue
        seen.add(r['variant'])
        rows.append({k: r[k] for k in
                     ('variant', 'com_db', 'cursor_mv', 'isi_mv', 'noise_mv',
                      'ctle_db', 'n_dfe')})
    d['sensitivity'] = rows
    ild = C.insertion_loss_fit(ch['f'], ch['s21'], 30.0)
    d['ild'] = dict(f_ghz=thin(ild['f_ghz'], 300),
                    il_db=thin(ild['il_db'], 300),
                    fit_db=thin(ild['fit_db'], 300),
                    ild_db=thin(ild['ild_db'], 300),
                    ild_rms_db=ild['ild_rms_db'], ild_max_db=ild['ild_max_db'])
    ild2 = C.insertion_loss_fit(ch_stub['f'], ch_stub['s21'], 30.0)
    d['ild_stub'] = dict(ild_rms_db=ild2['ild_rms_db'],
                         ild_max_db=ild2['ild_max_db'],
                         ild_db=thin(ild2['ild_db'], 300),
                         f_ghz=thin(ild2['f_ghz'], 300))
    d['hand_budget'] = dict(q=6.01, shortfall_db=1.36, target_ber=1e-12,
                            source='SerDes_Equalisation, serdes_model.py')
    return d


if __name__ == '__main__':
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    fns = {'deck01': deck01, 'deck02': deck02, 'deck03': deck03,
           'deck04': deck04, 'deck05': deck05, 'deck06': deck06,
           'deck07': deck07, 'deck08': deck08, 'deck09': deck09,
           'deck10': deck10, 'deck11': deck11}
    for nm, fn in fns.items():
        if only and nm not in only:
            continue
        t0 = time.time()
        print('%s ...' % nm)
        save(nm, fn())
        print('  %.1f s' % (time.time() - t0))
    if os.path.exists(os.path.join(OUT, 'verification.json')):
        old = json.load(open(os.path.join(OUT, 'verification.json')))
        old.update(VER)
        VER.update(old)
    save('verification', VER)
