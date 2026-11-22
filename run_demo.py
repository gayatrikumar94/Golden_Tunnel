"""Run the whole Golden Tunnel project from start to finish.

    python run_demo.py                 # default settings
    python run_demo.py --k 2 --seed 7  # tighter tunnel, different random data

Steps:
  1. Simulate 120 CHO fed-batches.
  2. Split them: 70 % "history" (used to build the tunnel), 30 % "new batches".
  3. Pick golden batches from the history and build the tunnel.
  4. Monitor the new batches against the tunnel.
  5. Report how well alarms matched low-titer outcomes and save charts.
"""

import argparse
from pathlib import Path

import numpy as np

from golden_tunnel import (build_tunnel, evaluate_many, select_golden_batches,
                           simulate_batches, summarize_performance)
from golden_tunnel.plotting import plot_batch_vs_tunnel, plot_tunnel, plot_validation
from golden_tunnel.simulate import LOW_TITER_THRESHOLD_G_L


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-batches", type=int, default=120)
    ap.add_argument("--k", type=float, default=3.0, help="tunnel half-width in standard deviations")
    ap.add_argument("--consecutive", type=int, default=3, help="readings in a row outside the tunnel before alarming")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    for folder in ("data", "figures", "reports"):
        Path(folder).mkdir(exist_ok=True)

    # 1. Data -----------------------------------------------------------------
    ts, summary = simulate_batches(n_batches=args.n_batches, seed=args.seed)
    ts.to_csv("data/simulated_timeseries.csv", index=False)
    summary.to_csv("data/simulated_batch_summary.csv", index=False)
    print(f"Simulated {summary.shape[0]} batches, {ts.shape[0]} readings. "
          f"Low-titer rate: {summary.low_titer.mean():.0%}")

    # 2. Split history vs new batches (so we never test on the data used to build the tunnel)
    rng = np.random.default_rng(args.seed)
    # permutation() returns a shuffled COPY. (Shuffling the column's array in place
    # would silently scramble the summary table's batch_id column.)
    ids = rng.permutation(summary["batch_id"].to_numpy())
    n_hist = int(0.7 * len(ids))
    hist_ids, new_ids = list(ids[:n_hist]), sorted(ids[n_hist:])
    hist_summary = summary[summary["batch_id"].isin(hist_ids)]
    new_summary = summary[summary["batch_id"].isin(new_ids)]

    # 3. Golden batches + tunnel ----------------------------------------------
    golden = select_golden_batches(hist_summary, top_fraction=0.5, require_no_deviation=True)
    tunnel = build_tunnel(ts, golden, k=args.k)
    tunnel.save("reports/golden_tunnel_table.csv")
    print(f"History: {len(hist_ids)} batches -> {len(golden)} golden batches -> tunnel (k={args.k:g})")

    # 4. Monitor new batches --------------------------------------------------
    results, reports = evaluate_many(ts, tunnel, new_ids, consecutive=args.consecutive)
    results = results.merge(new_summary[["batch_id", "titer_g_L", "low_titer"]], on="batch_id")
    results.to_csv("reports/monitoring_results.csv", index=False)

    # 5. Performance report ---------------------------------------------------
    perf = summarize_performance(results, new_summary)
    print("\n=== Monitoring performance on NEW batches (simulated) ===")
    print(f"Batches monitored : {perf['n_batches']}")
    print(f"Caught low-titer  : {perf['true_positive']}   Missed: {perf['false_negative']}")
    print(f"False alarms      : {perf['false_positive']}   Correctly quiet: {perf['true_negative']}")
    print(f"Precision         : {perf['precision']:.0%}  (of alarms, how many were real problems)")
    print(f"Recall            : {perf['recall']:.0%}  (of low-titer batches, how many we flagged)")
    print(f"Median alarm day  : {perf['median_alarm_day_for_caught_batches']:.1f} of 14 (earlier = more time to react)")
    Path("reports/performance_summary.txt").write_text("\n".join(f"{k}: {v}" for k, v in perf.items()))

    # 6. Charts ---------------------------------------------------------------
    plot_tunnel(ts, tunnel, "figures/01_golden_tunnel.png")
    flagged = results[results.alarm & results.low_titer].sort_values("first_alarm_day")
    clean = results[~results.alarm & ~results.low_titer].sort_values("pct_inside", ascending=False)
    if len(flagged):
        b = flagged.iloc[0]["batch_id"]
        plot_batch_vs_tunnel(reports[b], tunnel, "figures/02_batch_with_alarm.png",
                             titer=float(summary.set_index("batch_id").loc[b, "titer_g_L"]))
    if len(clean):
        b = clean.iloc[0]["batch_id"]
        plot_batch_vs_tunnel(reports[b], tunnel, "figures/03_batch_in_control.png",
                             titer=float(summary.set_index("batch_id").loc[b, "titer_g_L"]))
    plot_validation(results, summary, "figures/04_validation.png", LOW_TITER_THRESHOLD_G_L)
    print("\nSaved: data/, reports/, figures/ - open the PNGs in figures/ to see the tunnel.")


if __name__ == "__main__":
    main()
