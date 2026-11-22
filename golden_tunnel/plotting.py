"""Charts for the golden tunnel."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # draw to files; no pop-up window needed
import matplotlib.pyplot as plt
import numpy as np

from .monitor import BatchReport
from .tunnel import Tunnel

UNITS = {"pH": "pH", "DO": "DO (% air sat.)", "OUR": "OUR (mmol/L/h)"}
BLUE, RED, GREY = "#1f6feb", "#d1242f", "#8c959f"


def plot_tunnel(timeseries, tunnel: Tunnel, path: str, max_curves: int = 40) -> None:
    """Figure 1: the golden batches and the tunnel they create."""
    params = tunnel.parameters
    fig, axes = plt.subplots(len(params), 1, figsize=(9, 3 * len(params)), sharex=True)
    for ax, p in zip(np.atleast_1d(axes), params):
        tb = tunnel.bounds(p)
        for bid in tunnel.golden_batch_ids[:max_curves]:
            g = timeseries[timeseries["batch_id"] == bid]
            ax.plot(g["time_day"], g[p], color=GREY, alpha=0.35, lw=0.8)
        ax.fill_between(tb["time_day"], tb["lower"], tb["upper"], color=BLUE, alpha=0.18,
                        label=f"Golden tunnel (mean ± {tunnel.k:g} SD)")
        ax.plot(tb["time_day"], tb["mean"], color=BLUE, lw=2, label="Golden mean")
        ax.set_ylabel(UNITS.get(p, p))
        ax.grid(alpha=0.25)
    np.atleast_1d(axes)[0].legend(loc="upper right", fontsize=8)
    np.atleast_1d(axes)[0].set_title(f"Golden tunnel built from {len(tunnel.golden_batch_ids)} golden batches (simulated data)")
    np.atleast_1d(axes)[-1].set_xlabel("Culture time (days)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_batch_vs_tunnel(report: BatchReport, tunnel: Tunnel, path: str, titer: float | None = None) -> None:
    """Figure 2/3: one batch drawn over the tunnel, out-of-tunnel points in red."""
    params = tunnel.parameters
    fig, axes = plt.subplots(len(params), 1, figsize=(9, 3 * len(params)), sharex=True)
    for ax, p in zip(np.atleast_1d(axes), params):
        tb = tunnel.bounds(p)
        pts = report.pointwise[report.pointwise["parameter"] == p]
        ax.fill_between(tb["time_day"], tb["lower"], tb["upper"], color=BLUE, alpha=0.18)
        ax.plot(tb["time_day"], tb["mean"], color=BLUE, lw=1.5, ls="--")
        ax.plot(pts["time_day"], pts["value"], color="black", lw=1.4)
        bad = pts[pts["outside"]]
        ax.scatter(bad["time_day"], bad["value"], color=RED, s=18, zorder=3, label="Outside tunnel")
        day = report.per_parameter[p]["first_alarm_day"]
        if day is not None:
            ax.axvline(day, color=RED, ls=":", lw=1.5)
            ax.text(day, ax.get_ylim()[1], f" ALARM day {day:.2f}", color=RED, va="top", fontsize=8)
        ax.set_ylabel(UNITS.get(p, p))
        ax.grid(alpha=0.25)
    status = "ALARM" if report.alarm else "IN CONTROL"
    t_txt = f" | titer {titer:.2f} g/L" if titer is not None else ""
    np.atleast_1d(axes)[0].set_title(f"Batch {report.batch_id}: {status} | {report.pct_inside:.0f}% of readings inside tunnel{t_txt}")
    np.atleast_1d(axes)[-1].set_xlabel("Culture time (days)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_validation(results, summary, path: str, low_titer_threshold: float) -> None:
    """Figure 4: does staying inside the tunnel go with higher titer?"""
    m = results if "titer_g_L" in results.columns else results.merge(summary[["batch_id", "titer_g_L"]], on="batch_id")
    fig, ax = plt.subplots(figsize=(8, 5))
    for alarm, color, label in [(False, BLUE, "No alarm"), (True, RED, "Alarm")]:
        s = m[m["alarm"] == alarm]
        ax.scatter(s["pct_inside"], s["titer_g_L"], color=color, alpha=0.75, label=f"{label} (n={len(s)})")
    ax.axhline(low_titer_threshold, color=GREY, ls="--", label=f"Low-titer limit ({low_titer_threshold} g/L)")
    ax.set_xlabel("% of readings inside golden tunnel")
    ax.set_ylabel("Final titer (g/L)")
    ax.set_title("Held-out batches: tunnel adherence vs. final titer (simulated)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
