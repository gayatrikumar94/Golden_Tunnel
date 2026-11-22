"""Golden Tunnel: batch monitoring for bioprocess (CHO fed-batch) data.

Modules
-------
simulate : creates realistic *simulated* CHO fed-batch data (pH, DO, OUR, titer)
tunnel   : picks golden batches and builds the golden tunnel (mean +/- k*SD band)
monitor  : checks a new batch against the tunnel and raises alarms
plotting : makes the charts
"""

from .simulate import simulate_batches, PARAMETERS
from .tunnel import select_golden_batches, build_tunnel, Tunnel
from .monitor import evaluate_batch, evaluate_many, summarize_performance

__all__ = [
    "simulate_batches", "PARAMETERS",
    "select_golden_batches", "build_tunnel", "Tunnel",
    "evaluate_batch", "evaluate_many", "summarize_performance",
]
__version__ = "1.0.0"
