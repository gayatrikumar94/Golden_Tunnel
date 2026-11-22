"""Check batches against the golden tunnel and raise alarms."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .tunnel import Tunnel


@dataclass
class BatchReport:
    """Result of checking one batch."""

    batch_id: str
    alarm: bool                      # True if any parameter raised an alarm
    first_alarm_day: float | None    # earliest day an alarm was confirmed
    pct_inside: float                # % of all readings inside the tunnel
    per_parameter: dict = field(default_factory=dict)
    pointwise: pd.DataFrame | None = None   # every reading with its status


def _first_run(flags: np.ndarray, n: int) -> int | None:
    """Index where the first run of `n` consecutive True values *ends*.

    We alarm at the END of the run (the moment we have n bad readings in a
    row), because in real life that is when you would actually know.
    """
    run = 0
    for i, f in enumerate(flags):
        run = run + 1 if f else 0
        if run >= n:
            return i
    return None


def evaluate_batch(
    batch: pd.DataFrame,
    tunnel: Tunnel,
    consecutive: int = 3,
    batch_id: str | None = None,
) -> BatchReport:
    """Compare one batch's curves to the tunnel.

    consecutive : alarm only if this many readings in a row are outside.
                  Prevents one noisy reading from triggering a false alarm.
    """
    batch = batch.sort_values("time_day")
    bid = batch_id or str(batch["batch_id"].iloc[0])
    t = batch["time_day"].to_numpy()

    point_frames, per_param, alarm_days = [], {}, []
    total_points = inside_points = 0

    for p in tunnel.parameters:
        tb = tunnel.bounds(p)
        # Line the tunnel up with this batch's time stamps (handles different sampling)
        mean = np.interp(t, tb["time_day"], tb["mean"])
        sd = np.interp(t, tb["time_day"], tb["sd"])
        lo = np.interp(t, tb["time_day"], tb["lower"])
        hi = np.interp(t, tb["time_day"], tb["upper"])
        x = batch[p].to_numpy()

        outside = (x < lo) | (x > hi)
        z = (x - mean) / sd                       # distance from average, in SDs
        idx = _first_run(outside, consecutive)
        alarm_day = float(t[idx]) if idx is not None else None
        if alarm_day is not None:
            alarm_days.append(alarm_day)

        per_param[p] = {
            "alarm": idx is not None,
            "first_alarm_day": alarm_day,
            "pct_outside": float(100 * outside.mean()),
            "max_abs_z": float(np.nanmax(np.abs(z))),
        }
        inside_points += int((~outside).sum())
        total_points += outside.size
        point_frames.append(pd.DataFrame({
            "batch_id": bid, "parameter": p, "time_day": t, "value": x,
            "lower": lo, "upper": hi, "z": z, "outside": outside,
        }))

    return BatchReport(
        batch_id=bid,
        alarm=bool(alarm_days),
        first_alarm_day=min(alarm_days) if alarm_days else None,
        pct_inside=100 * inside_points / total_points,
        per_parameter=per_param,
        pointwise=pd.concat(point_frames, ignore_index=True),
    )


def evaluate_many(
    timeseries: pd.DataFrame, tunnel: Tunnel, batch_ids: list[str], consecutive: int = 3
) -> tuple[pd.DataFrame, dict[str, BatchReport]]:
    """Evaluate many batches; returns a tidy table plus the full reports."""
    reports, rows = {}, []
    for bid in batch_ids:
        sub = timeseries[timeseries["batch_id"] == bid]
        rep = evaluate_batch(sub, tunnel, consecutive, batch_id=bid)
        reports[bid] = rep
        row = {"batch_id": bid, "alarm": rep.alarm,
               "first_alarm_day": rep.first_alarm_day,
               "pct_inside": round(rep.pct_inside, 1)}
        for p, d in rep.per_parameter.items():
            row[f"{p}_alarm"] = d["alarm"]
        rows.append(row)
    return pd.DataFrame(rows), reports


def summarize_performance(results: pd.DataFrame, summary: pd.DataFrame) -> dict:
    """How good is the tunnel at catching low-titer batches?

    Compares the alarm (what the tunnel said) with low_titer (what happened).
      true positive  : alarm AND low titer   -> good catch
      false positive : alarm BUT titer fine  -> false alarm
      false negative : no alarm BUT low titer-> missed problem
      true negative  : no alarm AND titer ok -> correctly quiet
    """
    extra = summary[["batch_id", "low_titer", "fault_type", "titer_g_L"]]
    # Avoid duplicate columns if the results table already carries them.
    m = results.drop(columns=[c for c in extra.columns if c != "batch_id" and c in results.columns]
                     ).merge(extra, on="batch_id")
    tp = int((m.alarm & m.low_titer).sum())
    fp = int((m.alarm & ~m.low_titer).sum())
    fn = int((~m.alarm & m.low_titer).sum())
    tn = int((~m.alarm & ~m.low_titer).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    caught = m[m.alarm & m.low_titer]["first_alarm_day"]
    return {
        "n_batches": len(m), "true_positive": tp, "false_positive": fp,
        "false_negative": fn, "true_negative": tn,
        "precision": precision, "recall": recall,
        "median_alarm_day_for_caught_batches": float(caught.median()) if len(caught) else float("nan"),
    }
