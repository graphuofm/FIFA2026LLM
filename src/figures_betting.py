"""Betting figures: bankroll curves (with a market baseline) and the
single-column fade-the-market breakdown."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

import vizstyle as V

ROOT = Path(__file__).resolve().parent.parent
ANA = ROOT / "data" / "analysis"
V.apply()
M = V.MODELS


def fig_bankroll():
    """Cumulative virtual profit; four agents (own picks) + a market baseline."""
    bank = pd.read_csv(ANA / "bankroll.csv").set_index("mnum")
    summ = pd.read_csv(ANA / "betting_summary.csv")
    summ = summ[summ.phase == "all"].set_index("model")
    fig, ax = plt.subplots(figsize=(V.COL2, 3.0))
    ax.axhline(0, color=V.BASE, lw=0.9)
    ax.axvline(72.5, color=V.MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.text(72.5, ax.get_ylim()[1], "  knockout →", va="top", ha="left",
            fontsize=6.8, color=V.MUTED)
    # market baseline: flat $100 on the market favourite each match
    if "market" in bank.columns:
        mk = bank["market"]
        ax.plot(mk.index, mk.values, color=V.MARKET_COLOR, lw=1.6, ls=(0, (5, 2)),
                zorder=1)
        ax.text(mk.index[-1] + 1.5, mk.values[-1],
                f"Market (flat-fav)  ${mk.values[-1]:+.0f}", va="center",
                fontsize=7.2, color=V.MARKET_COLOR, weight="bold")
    finals = {m: bank[m].iloc[-1] for m in M}
    for m in M:
        s = bank[m]
        ax.plot(s.index, s.values, color=V.MODEL_COLOR[m], lw=1.8,
                marker=V.MODEL_MARKER[m], markevery=[len(s) - 1], markersize=5.5,
                markeredgecolor="white", markeredgewidth=0.6, zorder=3)
        roi = summ.loc[m, "roi_pct"]
        ax.text(s.index[-1] + 1.5, s.values[-1],
                f"{V.MODEL_LABEL[m]}  ${finals[m]:+.0f}  ({roi:+.1f}%)",
                va="center", fontsize=7.4, color=V.MODEL_COLOR[m], weight="bold")
    ax.set_xlim(1, 124)
    ax.set_xlabel("Match number (m01 → m104)")
    ax.set_ylabel("Cumulative net profit (virtual $)")
    ax.text(36, ax.get_ylim()[1], "group stage", va="top", ha="center",
            fontsize=6.8, color=V.MUTED)
    V.despine(ax)
    ax.set_title("Cumulative virtual profit at real 1X2 odds "
                 "(agents' own stakes; market = flat stake on its favourite)",
                 fontsize=8.6, color=V.INK, loc="left")
    V.save(fig, "fig_bankroll")


def fig_contrarian():
    """Single-column: (top) share of bets fading the market; (bottom) profit split."""
    con = pd.read_csv(ANA / "contrarian.csv").set_index("model")
    fig, (axT, axB) = plt.subplots(2, 1, figsize=(V.COL1, 3.5),
                                   gridspec_kw={"height_ratios": [1, 1.2]})
    y = np.arange(len(M))[::-1]
    # top: contrarian share
    for yi, m in zip(y, M):
        sh = con.loc[m, "contrarian_share"]
        axT.barh(yi, sh, color=V.MODEL_COLOR[m], edgecolor="white")
        axT.text(sh + 0.012, yi, f"{sh:.0%}", va="center", fontsize=7.4, color=V.INK)
    axT.set_yticks(y); axT.set_yticklabels([V.MODEL_LABEL[m] for m in M])
    axT.set_xlim(0, 0.72); axT.set_xticks([0, 0.2, 0.4, 0.6])
    axT.set_xticklabels(["0", "20%", "40%", "60%"])
    axT.set_xlabel("Share of bets that fade the market", fontsize=7.8)
    V.despine(axT, left=False)
    # bottom: profit split conforming vs contrarian
    for yi, m in zip(y, M):
        cp, xp = con.loc[m, "conform_profit"], con.loc[m, "contrarian_profit"]
        axB.barh(yi + 0.2, cp, height=0.36, color=V.GOOD, edgecolor="white",
                 label="with market" if yi == y[0] else None)
        axB.barh(yi - 0.2, xp, height=0.36, color=V.BAD, edgecolor="white",
                 label="against market" if yi == y[0] else None)
        axB.text(cp + (10 if cp >= 0 else -10), yi + 0.2, f"{cp:+.0f}",
                 va="center", ha="left" if cp >= 0 else "right", fontsize=6.4, color=V.INK2)
        axB.text(xp + (10 if xp >= 0 else -10), yi - 0.2, f"{xp:+.0f}",
                 va="center", ha="left" if xp >= 0 else "right", fontsize=6.4, color=V.INK2)
    axB.axvline(0, color=V.BASE, lw=0.9)
    axB.set_yticks(y); axB.set_yticklabels([V.MODEL_LABEL[m] for m in M])
    axB.set_xlim(-320, 720); axB.set_xlabel("Net profit (virtual $)", fontsize=7.8)
    V.despine(axB, left=False)
    axB.legend(loc="lower right", fontsize=6.8, handlelength=1.0)
    fig.suptitle("Fading the market loses for every agent", fontsize=9,
                 x=0.02, ha="left", y=1.0, color=V.INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    V.save(fig, "fig_contrarian")


def main():
    fig_bankroll()
    fig_contrarian()


if __name__ == "__main__":
    main()
