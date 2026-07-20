"""Betting figures: bankroll curves and the fade-the-market breakdown."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import vizstyle as V

ROOT = Path(__file__).resolve().parent.parent
ANA = ROOT / "data" / "analysis"
V.apply()
M = V.MODELS


def fig_bankroll():
    """Cumulative net profit over the tournament (each model's own picks)."""
    bank = pd.read_csv(ANA / "bankroll.csv").set_index("mnum")
    summ = pd.read_csv(ANA / "betting_summary.csv")
    summ = summ[summ.phase == "all"].set_index("model")
    fig, ax = plt.subplots(figsize=(V.COL2, 3.0))
    ax.axhline(0, color=V.BASE, lw=0.9)
    ax.axvline(72.5, color=V.MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.text(72.5, ax.get_ylim()[1], "  knockout →", va="top", ha="left",
            fontsize=6.8, color=V.MUTED)
    # order labels by final value to avoid overlap
    finals = {m: bank[m].iloc[-1] for m in M}
    for m in M:
        s = bank[m]
        ax.plot(s.index, s.values, color=V.MODEL_COLOR[m], lw=1.8,
                marker=V.MODEL_MARKER[m], markevery=[len(s) - 1], markersize=5.5,
                markeredgecolor="white", markeredgewidth=0.6)
        roi = summ.loc[m, "roi_pct"]
        ax.text(s.index[-1] + 1.5, s.values[-1],
                f"{V.MODEL_LABEL[m]}  ${finals[m]:+.0f}  ({roi:+.1f}%)",
                va="center", fontsize=7.4, color=V.MODEL_COLOR[m], weight="bold")
    ax.set_xlim(1, 116)
    ax.set_xlabel("Match number (m01 → m104)")
    ax.set_ylabel("Cumulative net profit (virtual $)")
    ax.text(36, ax.get_ylim()[1], "group stage", va="top", ha="center",
            fontsize=6.8, color=V.MUTED)
    V.despine(ax)
    ax.set_title("Cumulative virtual profit at real 1X2 odds", fontsize=8.8,
                 color=V.INK, loc="left")
    V.save(fig, "fig_bankroll")


def fig_contrarian():
    """Where the P&L comes from: with-market vs against-market bets."""
    con = pd.read_csv(ANA / "contrarian.csv").set_index("model")
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(V.COL2, 2.7),
                                   gridspec_kw={"width_ratios": [1, 1.25]})
    # LEFT: share of bets that fade the market
    y = np.arange(len(M))[::-1]
    for yi, m in zip(y, M):
        sh = con.loc[m, "contrarian_share"]
        axL.barh(yi, sh, color=V.MODEL_COLOR[m], edgecolor="white")
        axL.text(sh + 0.01, yi, f"{sh:.0%}", va="center", fontsize=7.2, color=V.INK)
    axL.set_yticks(y); axL.set_yticklabels([V.MODEL_LABEL[m] for m in M])
    axL.set_xlim(0, 0.7); axL.set_xlabel("Share of bets that fade the market")
    axL.set_xticks([0, 0.2, 0.4, 0.6]); axL.set_xticklabels(["0", "20%", "40%", "60%"])
    V.despine(axL, left=False)
    axL.set_title("Bets against the\nmarket favourite", fontsize=8.6, color=V.INK)

    # RIGHT: profit from conforming vs contrarian bets (diverging)
    for yi, m in zip(y, M):
        cp = con.loc[m, "conform_profit"]; xp = con.loc[m, "contrarian_profit"]
        axR.barh(yi + 0.18, cp, height=0.34, color=V.GOOD,
                 edgecolor="white", label="with market" if yi == y[0] else None)
        axR.barh(yi - 0.18, xp, height=0.34, color=V.BAD,
                 edgecolor="white", label="against market" if yi == y[0] else None)
        axR.text(cp + (8 if cp >= 0 else -8), yi + 0.18, f"${cp:+.0f}",
                 va="center", ha="left" if cp >= 0 else "right", fontsize=6.6, color=V.INK2)
        axR.text(xp + (8 if xp >= 0 else -8), yi - 0.18, f"${xp:+.0f}",
                 va="center", ha="left" if xp >= 0 else "right", fontsize=6.6, color=V.INK2)
    axR.axvline(0, color=V.BASE, lw=0.9)
    axR.set_yticks(y); axR.set_yticklabels([])
    axR.set_xlabel("Net profit (virtual $)")
    axR.set_xlim(-260, 680)
    V.despine(axR, left=False)
    axR.legend(loc="lower right", fontsize=6.9, handlelength=1.1)
    axR.set_title("Net profit: conforming vs.\ncontrarian bets", fontsize=8.6, color=V.INK)
    V.save(fig, "fig_contrarian")


def main():
    fig_bankroll()
    fig_contrarian()


if __name__ == "__main__":
    main()
