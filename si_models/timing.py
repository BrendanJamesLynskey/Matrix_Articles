"""Timing, flight time and the budget -- the model behind deck 09.

Everything else in this series is about whether a waveform survives. This deck
is about whether it arrives when it is supposed to, which is a separate
question with a separate arithmetic, and it is where signal integrity meets
the timing closure the digital designer cares about.

The distinction that causes the most trouble is between propagation delay and
flight time. Propagation delay is a property of the line. Flight time is the
interval between the driver reaching its switching threshold and the receiver
reaching its own, and on a loaded or badly terminated net it is not the same
number -- it can be considerably longer, because the receiver waits for a
reflection before it crosses.

The deck's argument is about why serial links displaced wide parallel buses,
and `bus_comparison()` makes it arithmetically rather than historically: a
common-clock bus spends its budget on clock skew, a source-synchronous bus
spends it on lane-to-lane skew that grows with width, and an embedded-clock
serial link spends nothing on either because its clock is recovered per lane.
"""

import numpy as np

C0 = 299792458.0
INCH = 0.0254


def flight_time(length_in, er=4.0, z0=50.0, z_source=20.0, c_load_pf=3.0,
                v_swing=1.0, v_thresh=0.5, n_bounce=24):
    """Flight time to a threshold, against the line's own propagation delay.

    A driver whose impedance is below the line impedance launches more than
    half the swing and the receiver crosses on the first incident wave. A
    driver whose impedance is above it launches less, and the receiver has to
    wait for the reflection from its own open-circuited end to come back --
    which costs a full round trip, not a fraction of one.
    """
    v = C0 / np.sqrt(er)
    tpd = length_in * INCH / v
    gl = 1.0                                  # high-impedance receiver
    gs = (z_source - z0) / (z_source + z0)
    a0 = v_swing * z0 / (z0 + z_source)

    t, amp, total = [], a0, 0.0
    cross = None
    for k in range(n_bounce):
        total += amp
        t_arr = (2 * k + 1) * tpd
        total += amp * gl
        if cross is None and total >= v_thresh * v_swing:
            cross = t_arr
        t.append(dict(t_s=float(t_arr), v_load=float(total)))
        amp *= gl * gs
    # a capacitive load slows the final edge: one RC of the load against the
    # line, added to the arrival of the wave that crosses
    rc = z0 * c_load_pf * 1e-12
    return dict(tpd_s=float(tpd), tpd_ps=float(tpd * 1e12),
                first_incident_v=float(a0 * (1 + gl)),
                crosses_on_first_incident=bool(a0 * (1 + gl) >= v_thresh),
                flight_time_ps=float(((cross if cross else tpd) + rc) * 1e12),
                excess_over_tpd_ps=float((((cross if cross else tpd) + rc)
                                          - tpd) * 1e12),
                rc_ps=float(rc * 1e12), steps=t,
                gamma_source=float(gs))


def setup_hold_margin(period_ps, t_co_ps, t_su_ps, t_hold_ps,
                      flight_max_ps, flight_min_ps, clock_skew_ps,
                      jitter_pp_ps=0.0, derate_pct=0.0):
    """Setup and hold margins for a synchronous transfer.

    Setup is threatened by everything being slow: a late clock-to-output, a
    long flight, a clock that arrives early at the receiver. Hold is threatened
    by the opposite, and crucially hold has no period in it -- making the clock
    slower does not fix a hold violation, which is why hold failures are
    silicon or layout problems rather than frequency problems.
    """
    d = 1.0 + derate_pct / 100.0
    setup = (period_ps - t_co_ps * d - flight_max_ps * d - t_su_ps
             - clock_skew_ps - jitter_pp_ps / 2.0)
    hold = (t_co_ps / d + flight_min_ps / d - t_hold_ps
            - clock_skew_ps - jitter_pp_ps / 2.0)
    return dict(period_ps=period_ps, setup_margin_ps=float(setup),
                hold_margin_ps=float(hold),
                setup_ok=bool(setup >= 0), hold_ok=bool(hold >= 0),
                f_max_mhz=float(1e6 / (t_co_ps * d + flight_max_ps * d + t_su_ps
                                       + clock_skew_ps + jitter_pp_ps / 2.0)))


def worst_case_vs_statistical(terms_ps, sigma_divisor=3.0, target_ber=1e-12):
    """Adding a budget two ways, and what the difference is worth.

    A worst-case budget adds every term at its extreme and assumes they all go
    wrong together. A statistical budget treats the independent ones as
    independent and adds them in quadrature. The second is smaller -- often by
    a factor approaching the square root of the number of terms -- and the
    question is whether the independence assumption is earned.

    It usually is for manufacturing spreads across many boards and it usually
    is not for terms that share a cause: two lanes on the same board see the
    same laminate lot, the same temperature and the same supply.

    Both confidence levels are reported, and the gap between them is the point.
    Conventional statistical timing closure works at three sigma, where the
    saving over a worst-case sum is large. A serial link has to work at an
    error ratio of 1e-12, which is slightly past seven sigma, and at that
    confidence the same quadrature sum buys very much less -- which is why a
    technique that transformed processor timing closure did comparatively
    little for link budgets.
    """
    a = np.asarray(list(terms_ps), float)
    wc = float(np.sum(np.abs(a)))
    sigmas = np.abs(a) / sigma_divisor
    rss_sigma = float(np.sqrt(np.sum(sigmas ** 2)))
    from .jitter import q_from_ber
    q = q_from_ber(target_ber)
    stat = float(q * rss_sigma)
    stat3 = 3.0 * rss_sigma
    return dict(worst_case_ps=wc, sigma_ps=rss_sigma,
                statistical_ps=stat, q=float(q),
                statistical_3sigma_ps=float(stat3),
                saving_ps=float(wc - stat), n_terms=len(a),
                ratio=float(stat / wc) if wc else float('nan'),
                ratio_3sigma=float(stat3 / wc) if wc else float('nan'),
                saving_3sigma_ps=float(wc - stat3),
                sigma_divisor=sigma_divisor, target_ber=target_ber)


def bus_comparison(rates_gbps=None, n_bits=32, board_in=8.0, er=4.0,
                   t_su_ps=60.0, t_hold_ps=40.0, t_co_ps=150.0,
                   skew_per_in_ps=1.5, clock_jitter_ps=30.0,
                   match_tolerance_in=0.25, serial_ui_budget=0.7):
    """Why the wide parallel bus ran out and the serial link did not.

    Three clocking schemes are budgeted against the same board.

    In a common-clock bus the data has to cross the board and be captured
    against a clock that has separately crossed the board, so the whole flight
    time and all of the clock skew come out of one cycle.

    A source-synchronous bus forwards its clock with the data, which cancels
    the bulk of the flight time, and is then limited by how well the lanes can
    be length-matched to each other.

    An embedded-clock serial link recovers timing from the data on each lane
    separately, so neither flight time nor lane-to-lane skew appears in its
    budget at all; what remains is jitter and the eye the channel leaves.
    """
    if rates_gbps is None:
        rates_gbps = [0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6]
    v = C0 / np.sqrt(er)
    flight_ps = board_in * INCH / v * 1e12
    lane_skew_ps = match_tolerance_in * skew_per_in_ps * 2 + 0.5 * n_bits ** 0.5
    rows = []
    for r in rates_gbps:
        ui = 1e3 / r                          # ps per bit
        cc = ui - (t_co_ps + flight_ps + t_su_ps + clock_jitter_ps)
        ss = ui - (t_su_ps + t_hold_ps + lane_skew_ps + clock_jitter_ps / 3.0)
        se = ui * serial_ui_budget - (clock_jitter_ps / 6.0)
        rows.append(dict(rate_gbps=r, ui_ps=float(ui),
                         common_clock_ps=float(cc),
                         source_sync_ps=float(ss),
                         serial_ps=float(se),
                         common_ok=bool(cc > 0), source_ok=bool(ss > 0),
                         serial_ok=bool(se > 0)))
    def last_ok(key):
        ok = [r['rate_gbps'] for r in rows if r[key] > 0]
        return float(max(ok)) if ok else 0.0
    return dict(rows=rows, flight_ps=float(flight_ps),
                lane_skew_ps=float(lane_skew_ps), n_bits=n_bits,
                board_in=board_in,
                max_rate_common_clock=last_ok('common_clock_ps'),
                max_rate_source_sync=last_ok('source_sync_ps'),
                max_rate_serial=last_ok('serial_ps'),
                aggregate_parallel_gbps=float(last_ok('source_sync_ps') * n_bits))


def skew_budget(n_bits=32, length_tolerance_mil=25.0, er=4.0,
                weave_skew_ps_per_in=0.5, via_count=4, via_spread_ps=1.0,
                length_in=8.0):
    """Where lane-to-lane skew on a parallel bus actually comes from.

    Length matching is the term everyone controls and it is rarely the largest
    one. The laminate's own variation and the differences between via
    transitions are both harder to see on a layout review and both scale with
    the board rather than with the router's tolerance.
    """
    v = C0 / np.sqrt(er)
    tpd_ps_in = INCH / v * 1e12
    length_ps = length_tolerance_mil / 1000.0 * tpd_ps_in
    weave_ps = weave_skew_ps_per_in * length_in
    via_ps = via_spread_ps * np.sqrt(via_count)
    terms = dict(length_matching=float(length_ps), laminate_weave=float(weave_ps),
                 via_transitions=float(via_ps))
    return dict(terms=terms, tpd_ps_per_in=float(tpd_ps_in),
                worst_case_ps=float(sum(terms.values())),
                rss_ps=float(np.sqrt(sum(v * v for v in terms.values()))),
                n_bits=n_bits)
