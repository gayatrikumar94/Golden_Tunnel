"""Automated tests. Run with:  pytest -q   (install pytest first: pip install pytest)"""

import numpy as np
import pandas as pd
import pytest

from golden_tunnel import (build_tunnel, evaluate_batch, select_golden_batches,
                           simulate_batches)


@pytest.fixture(scope="module")
def data():
    ts, summary = simulate_batches(n_batches=80, seed=1)
    golden = select_golden_batches(summary, top_fraction=0.5)
    return ts, summary, golden


def test_simulation_shapes(data):
    ts, summary, _ = data
    assert summary["batch_id"].is_unique
    assert set(["batch_id", "time_day", "pH", "DO", "OUR"]) <= set(ts.columns)
    assert ts.groupby("batch_id").size().nunique() == 1  # same length for every batch


def test_golden_batches_have_no_deviation_and_good_titer(data):
    _, summary, golden = data
    g = summary[summary["batch_id"].isin(golden)]
    assert len(g) > 5
    assert not g["deviation_recorded"].any()
    assert g["titer_g_L"].min() >= summary["titer_g_L"].median() - 1e-9


def test_tunnel_lower_below_mean_below_upper(data):
    ts, _, golden = data
    t = build_tunnel(ts, golden, k=3).table
    assert (t["lower"] < t["mean"]).all() and (t["mean"] < t["upper"]).all()


def test_wider_k_gives_wider_tunnel(data):
    ts, _, golden = data
    w2 = build_tunnel(ts, golden, k=2).table.eval("upper - lower").mean()
    w3 = build_tunnel(ts, golden, k=3).table.eval("upper - lower").mean()
    assert w3 > w2


def test_golden_batch_mostly_inside_its_own_tunnel(data):
    ts, _, golden = data
    tunnel = build_tunnel(ts, golden, k=3)
    rep = evaluate_batch(ts[ts["batch_id"] == golden[0]], tunnel)
    assert rep.pct_inside > 95


def test_obviously_bad_batch_triggers_alarm(data):
    ts, _, golden = data
    tunnel = build_tunnel(ts, golden, k=3)
    bad = ts[ts["batch_id"] == golden[0]].copy()
    bad.loc[bad["time_day"] >= 6, "pH"] -= 0.3          # simulate a big pH crash
    rep = evaluate_batch(bad, tunnel)
    assert rep.alarm and rep.per_parameter["pH"]["alarm"]
    assert 6 <= rep.first_alarm_day <= 7                # alarm raised soon after the crash


def test_single_noisy_reading_does_not_alarm(data):
    ts, _, golden = data
    tunnel = build_tunnel(ts, golden, k=3)
    b = ts[ts["batch_id"] == golden[0]].copy()
    b.loc[b.index[20], "DO"] -= 30                      # one wild reading only
    assert not evaluate_batch(b, tunnel, consecutive=3).per_parameter["DO"]["alarm"]


def test_too_few_golden_batches_raises(data):
    ts, _, golden = data
    with pytest.raises(ValueError):
        build_tunnel(ts, golden[:3])
