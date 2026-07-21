"""Dedicated social-media figure (for X): which AI profits from betting the
2026 World Cup. Four AI bankroll curves only (no market line), Grok emphasized,
big fonts, standalone PNG sized for X (16:9)."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import vizstyle as V

ROOT = Path(__file__).resolve().parent.parent
ANA = ROOT / "data" / "analysis"
OUT = ROOT / "social"
OUT.mkdir(exist_ok=True)
V.apply()
M = V.MODELS

VER = {"claude": "Claude Opus 4.8", "chatgpt": "ChatGPT (GPT-5.5, high)",
       "gemini": "Gemini 3.1 Pro", "grok": "Grok (Expert Mode)"}


def build():
    bank = pd.read_csv(ANA / "bankroll.csv").set_index("mnum")
    summ = pd.read_csv(ANA / "betting_summary.csv")
    summ = summ[summ.phase == "all"].set_index("model")

    fig, ax = plt.subplots(figsize=(11.0, 6.2), dpi=150)
    ax.axhline(0, color=V.BASE, lw=1.0)
    ax.axvline(72.5, color=V.MUTED, lw=0.9, ls=(0, (3, 3)))
    ax.text(72.5, ax.get_ylim()[1], "  knockout stage →", va="bottom", ha="left",
            fontsize=10, color=V.MUTED)

    order = summ.loc[M, "net_profit"].sort_values(ascending=False).index.tolist()
    for m in M:
        s = bank[m]
        win = (m == "grok")
        ax.plot(s.index, s.values, color=V.MODEL_COLOR[m], lw=3.4 if win else 1.9,
                alpha=1.0 if win else 0.85, zorder=3 if win else 2,
                solid_capstyle="round")
        ax.scatter([s.index[-1]], [s.values[-1]], s=95 if win else 55,
                   color=V.MODEL_COLOR[m], marker=V.MODEL_MARKER[m],
                   edgecolor="white", linewidth=1.0, zorder=4)

    # ranked end labels (top-right)
    y0 = ax.get_ylim()[1]
    for i, m in enumerate(order):
        net = summ.loc[m, "net_profit"]; roi = summ.loc[m, "roi_pct"]
        tag = "  ← most money" if m == "grok" else ""
        ax.text(108, y0 - (i + 1) * (0.115 * (y0 - ax.get_ylim()[0])),
                f"{V.MODEL_LABEL[m]}   ${net:+,.0f}   ({roi:+.1f}% ROI){tag}",
                fontsize=12.5, color=V.MODEL_COLOR[m],
                weight="bold" if m == "grok" else "normal", va="center")

    ax.set_xlim(1, 104); ax.set_ylim(bank[M].min().min() - 60, bank[M].max().max() + 60)
    ax.set_xlabel("Match number  (all 104 matches, June–July 2026)", fontsize=12)
    ax.set_ylabel("Cumulative profit (virtual \\$, real 1X2 odds)", fontsize=12)
    ax.tick_params(labelsize=11)
    V.despine(ax)

    fig.suptitle("Four LLMs bet the entire 2026 FIFA World Cup — Grok made the most money",
                 fontsize=17, weight="bold", x=0.06, ha="left", y=0.99, color=V.INK)
    ax.set_title("104 matches · real bookmaker odds · each model stakes a virtual \\$100 budget",
                 fontsize=11.5, color=V.INK2, loc="left", pad=8)
    fig.text(0.06, 0.015, "Benchmark & data: arxiv.org/abs/2607.17765   ·   "
             "github.com/graphuofm/FIFA2026LLM", fontsize=10, color=V.MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(OUT / "x_betting.png", dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote social/x_betting.png")
    print("final:", {m: (round(summ.loc[m, 'net_profit']), summ.loc[m, 'roi_pct']) for m in order})


if __name__ == "__main__":
    build()
