"""Simulate CHO fed-batch bioreactor data.

WHY SIMULATE?
Real batch data is confidential, so portfolio projects use simulated data.
The numbers below are *not* real measurements; they are shaped to look like a
14-day CHO (Chinese Hamster Ovary) fed-batch run so the tunnel logic can be
demonstrated and tested.

The three online process parameters we track
--------------------------------------------
pH   : acidity of the culture. Controlled near 7.0 with CO2 / base addition.
DO   : dissolved oxygen (% of air saturation). Controlled near 40%.
OUR  : oxygen uptake rate (mmol/L/h). Tells you how many healthy cells are
       "breathing", so it rises, peaks mid-run, then falls as cells age.

The final product concentration (titer, g/L) is related to the cumulative
oxygen the cells consumed (area under the OUR curve) - a standard idea,
because more healthy respiring cells for longer means more antibody made.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PARAMETERS = ["pH", "DO", "OUR"]

# Titer below this value is called "low titer" (our pretend specification).
LOW_TITER_THRESHOLD_G_L = 3.5


def _our_shape(t: np.ndarray, t_peak: float, a: float = 2.6) -> np.ndarray:
    """A smooth hump that equals 1.0 at t_peak (cells grow, peak, then decline)."""
    x = np.clip(t / t_peak, 1e-6, None)
    return x**a * np.exp(a * (1 - x))


def simulate_batches(
    n_batches: int = 120,
    run_days: float = 14.0,
    step_days: float = 0.25,
    fault_rate: float = 0.30,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create simulated batches.

    Returns
    -------
    timeseries : one row per batch per time point
                 (batch_id, time_day, pH, DO, OUR)
    summary    : one row per batch
                 (batch_id, titer_g_L, low_titer, deviation_recorded, fault_type)

    NOTE: `fault_type` is the simulation's "answer key". The tunnel never sees
    it. It exists only so we can check afterwards whether monitoring worked.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(0, run_days + 1e-9, step_days)
    fault_types = ["ph_drift", "do_excursion", "low_growth"]

    ts_rows, summary_rows = [], []

    for i in range(n_batches):
        batch_id = f"B{i + 1:03d}"

        # ---- Natural batch-to-batch variation (every real batch is slightly different)
        t_peak = rng.normal(7.0, 0.35)             # day the cells peak
        peak_our = rng.normal(6.0, 0.35)           # height of the OUR peak
        titer_scale = rng.normal(1.0, 0.05)

        # ---- Optionally inject a process problem
        fault = "none"
        if rng.random() < fault_rate:
            fault = str(rng.choice(fault_types))
        if fault == "low_growth":
            peak_our *= rng.uniform(0.60, 0.80)
            t_peak += rng.uniform(0.5, 1.5)

        shape = _our_shape(t, t_peak)

        # ---- OUR
        our = peak_our * shape * (1 + rng.normal(0, 0.025, t.size))

        # ---- DO: controlled at ~40 %, dips slightly when cells breathe hardest
        do = 40 - 4.0 * shape + rng.normal(0, 1.0, t.size)
        if fault == "do_excursion":
            start = rng.uniform(4, 7)
            window = (t >= start) & (t <= start + rng.uniform(2.0, 3.5))
            do[window] -= rng.uniform(12, 20)

        # ---- pH: held near 7.0, small dip at peak metabolism, gentle late rise
        ph = 7.00 - 0.03 * shape + 0.006 * np.clip(t - 9, 0, None)
        ph += rng.normal(0, 0.010, t.size)
        if fault == "ph_drift":
            start = rng.uniform(4, 7)
            ph -= rng.uniform(0.08, 0.15) * np.clip(t - start, 0, None) / 4

        # ---- Titer: proportional to cumulative oxygen use, penalised by faults
        cumulative_our = np.trapezoid(our, t)
        titer = 0.0713 * cumulative_our * titer_scale
        if fault == "ph_drift":
            titer *= rng.uniform(0.75, 0.90)
        elif fault == "do_excursion":
            titer *= rng.uniform(0.78, 0.92)
        titer *= 1 + rng.normal(0, 0.02)

        # Only some faults get written up as deviations in the batch record.
        deviation_recorded = (fault != "none") and (rng.random() < 0.7)

        ts_rows.append(pd.DataFrame({
            "batch_id": batch_id, "time_day": t, "pH": ph, "DO": do, "OUR": our,
        }))
        summary_rows.append({
            "batch_id": batch_id,
            "titer_g_L": round(float(titer), 3),
            "deviation_recorded": bool(deviation_recorded),
            "fault_type": fault,
        })

    timeseries = pd.concat(ts_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    summary["low_titer"] = summary["titer_g_L"] < LOW_TITER_THRESHOLD_G_L
    return timeseries, summary
