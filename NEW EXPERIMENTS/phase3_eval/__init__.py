"""
phase3_eval/__init__.py

Phase 3 Evaluation Suite: Deterministic Hero Trace & Monte Carlo Stress Testing.
"""

from .run_hero_trace import run_hero_trace_all, HeroTraceRunner
from .run_monte_carlo import run_monte_carlo_suite, MonteCarloRunner
from .analyze_phase3 import generate_phase3_publication_plots

__all__ = [
    "run_hero_trace_all",
    "HeroTraceRunner",
    "run_monte_carlo_suite",
    "MonteCarloRunner",
    "generate_phase3_publication_plots",
]
