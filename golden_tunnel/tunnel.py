"""Build the golden tunnel.

THE IDEA IN ONE PARAGRAPH
Take your best batches ("golden batches"). At every time point (say day 5.25),
look at what pH / DO / OUR those batches had. Compute the average and the
standard deviation (SD = how spread out they are). The tunnel is the band
    lower = average - k * SD        upper = average + k * SD
drawn across time. A new batch that stays inside the tunnel is behaving like
your best batches; one that leaves the tunnel deserves attention.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .simulate import PARAMETERS

# A tunnel can never be thinner than this (in the parameter's own units).
# Without it, time points where all golden batches happen to agree (e.g. day 0,
# when every batch starts at the same setpoint) would give a zero-width tunnel
# and trigger false alarms.
DEFAULT_MIN_WIDTH = {"pH": 0.02, "DO": 1.0, "OUR": 0.15}  # minimum SD floor


@dataclass
class Tunnel:
    """Holds the finished tunnel: one row per (parameter, time point)."""

    table: pd.DataFrame          # columns: parameter, time_day, mean, sd, lower, upper
    k: float                     # how many SDs wide each side is
    golden_batch_ids: list[str]  # which batches built it

    def bounds(self, parameter: str) -> pd.DataFrame:
        """Return the tunnel rows for one parameter, sorted by time."""
        return (self.table[self.table["parameter"] == parameter]
                .sort_values("time_day").reset_index(drop=True))

    @property
    def parameters(self) -> list[str]:
        return list(self.table["parameter"].unique())

    def save(self, path: str) -> None:
        self.table.to_csv(path, index=False)


def select_golden_batches(
    summary: pd.DataFrame,
    top_fraction: float = 0.25,
    require_no_deviation: bool = True,
) -> list[str]:
    """Choose golden batches.

    A batch is golden if
      1. it is in the top `top_fraction` of batches by titer, AND
      2. (optionally) no deviation was recorded for it.

    In a real plant, "golden" is a quality decision (right yield, right product
    quality, clean batch record) - not just a statistics decision.
    """
    if not 0 < top_fraction <= 1:
        raise ValueError("top_fraction must be between 0 and 1")
    cutoff = summary["titer_g_L"].quantile(1 - top_fraction)
    mask = summary["titer_g_L"] >= cutoff
    if require_no_deviation:
        mask &= ~summary["deviation_recorded"]
    return summary.loc[mask, "batch_id"].tolist()


def build_tunnel(
    timeseries: pd.DataFrame,
    golden_batch_ids: list[str],
    k: float = 3.0,
    parameters: list[str] | None = None,
    smooth_window: int = 3,
    min_sd: dict[str, float] | None = None,
) -> Tunnel:
    """Compute mean +/- k*SD across golden batches at each time point.

    Parameters
    ----------
    timeseries       : long table with columns batch_id, time_day, <parameters>
    golden_batch_ids : which batches to use
    k                : tunnel half-width in SDs (1 = tight, 3 = common in SPC)
    smooth_window    : rolling average (in time points) to smooth the tunnel edges
    min_sd           : per-parameter minimum SD (see DEFAULT_MIN_WIDTH)
    """
    if len(golden_batch_ids) < 5:
        raise ValueError(
            f"Only {len(golden_batch_ids)} golden batches - too few to estimate "
            "a reliable tunnel. Aim for at least 10-15 in practice."
        )
    parameters = parameters or PARAMETERS
    floors = {**DEFAULT_MIN_WIDTH, **(min_sd or {})}
    golden = timeseries[timeseries["batch_id"].isin(golden_batch_ids)]

    pieces = []
    for p in parameters:
        # Rows = batches, columns = time points. This is the "stack of curves".
        wide = golden.pivot(index="batch_id", columns="time_day", values=p)
        mean = wide.mean(axis=0)
        sd = wide.std(axis=0, ddof=1)
        if smooth_window > 1:
            mean = mean.rolling(smooth_window, center=True, min_periods=1).mean()
            sd = sd.rolling(smooth_window, center=True, min_periods=1).mean()
        sd = sd.clip(lower=floors.get(p, 0.0))
        pieces.append(pd.DataFrame({
            "parameter": p,
            "time_day": wide.columns.to_numpy(),
            "mean": mean.to_numpy(),
            "sd": sd.to_numpy(),
            "lower": (mean - k * sd).to_numpy(),
            "upper": (mean + k * sd).to_numpy(),
        }))
    table = pd.concat(pieces, ignore_index=True)
    return Tunnel(table=table, k=k, golden_batch_ids=list(golden_batch_ids))
