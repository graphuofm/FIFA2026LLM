"""Rebuild the whole pipeline end-to-end: processed data -> analysis -> figures.

Run from anywhere:  python src/run_all.py
"""
from __future__ import annotations
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # unicode team names on Windows
except Exception:
    pass

STEPS = [
    ("group: per-model tables",      "build_per_model", "build"),
    ("group: merge ground truth",    "results_truth",   "merge_into_models"),
    ("knockout: per-model tables",   "build_knockout",  "build"),
    ("knockout: odds",               "build_odds_knockout", "build"),
    ("unified metrics + convergence","analysis",        "main"),
    ("reasoning factor coding",      "reasoning",        "build"),
    ("betting + market baseline",    "betting",          "build"),
    ("group metrics",                "metrics",          "main"),
    ("knockout metrics",             "metrics_knockout", "main"),
    ("figures (core)",               "figures",          "main"),
    ("figures (betting)",            "figures_betting",  "main"),
]


def main():
    import importlib
    for i, (label, mod, fn) in enumerate(STEPS, 1):
        print(f"\n{'='*70}\n[{i}/{len(STEPS)}] {label}  ({mod}.{fn})\n{'='*70}")
        m = importlib.import_module(mod)
        getattr(m, fn)()
    print("\nDONE. See data/processed, data/analysis, and paper/figures.")


if __name__ == "__main__":
    main()
