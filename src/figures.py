"""Publication figures (odds-independent set) — unified palette, data-forward.

Reads data/analysis/* and writes vector PDFs to paper/figures/. Betting figures
live in figures_betting.py. Every colour comes from vizstyle so a hue has one
meaning across the whole paper.
"""
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
PROC = ROOT / "data" / "processed"
V.apply()
M = V.MODELS
LBL = V.MODEL_LABEL


def _mc(m):
    return V.MODEL_COLOR[m]


def _model_legend(ax, loc="lower right", **kw):
    h = [Line2D([], [], marker=V.MODEL_MARKER[m], color=_mc(m), ls="",
                markersize=6, label=LBL[m]) for m in M]
    ax.legend(handles=h, loc=loc, handletextpad=0.3, **kw)


# --------------------------------------------------------------------------- #
def fig_leaderboard():
    ph = pd.read_csv(ANA / "metrics_by_phase.csv")
    mkt = pd.read_csv(ANA / "market_baseline.csv").set_index("phase")
    ents = M + ["market"]
    fig, axes = plt.subplots(1, 3, figsize=(V.COL2, 2.55))
    specs = [("accuracy", "Accuracy", True), ("brier", "Brier score", False),
             ("log_loss", "Log loss", False)]
    x = np.arange(len(ents)); w = 0.38

    def val(e, phase, col):
        return (float(mkt.loc[phase, col]) if e == "market"
                else float(ph[(ph.model == e) & (ph.phase == phase)][col].iloc[0]))

    for ax, (col, title, up) in zip(axes, specs):
        for i, e in enumerate(ents):
            c = V.MARKET_COLOR if e == "market" else _mc(e)
            ax.bar(x[i] - w / 2, val(e, "group", col), w, color=c, alpha=0.40,
                   edgecolor="white", linewidth=0.7)
            ax.bar(x[i] + w / 2, val(e, "knockout", col), w, color=c,
                   edgecolor="white", linewidth=0.7)
        ax.set_title(title + ("  ↑" if up else "  ↓"), color=V.INK, fontsize=9)
        ax.set_xticks(x)
        ax.set_xticklabels([LBL[m] for m in M] + ["Market"], rotation=32, ha="right")
        t = ax.get_xticklabels()[-1]; t.set_color(V.MARKET_COLOR); t.set_weight("bold")
        V.despine(ax)
        lo = min(val(e, p, col) for e in ents for p in ["group", "knockout"])
        hi = max(val(e, p, col) for e in ents for p in ["group", "knockout"])
        pad = (hi - lo) * 0.28 + 1e-3
        ax.set_ylim(max(0, lo - pad), hi + pad)
    axes[0].legend(handles=[Patch(facecolor=V.MUTED, alpha=0.40, label="Group (72)"),
                            Patch(facecolor=V.MUTED, label="Knockout (32)")],
                   loc="upper left", fontsize=7.2, handlelength=1.0)
    fig.suptitle("Predictive scores by phase: four agents and the market",
                 fontsize=10, x=0.02, ha="left", y=1.03, color=V.INK)
    fig.tight_layout()
    V.save(fig, "fig_leaderboard")


# --------------------------------------------------------------------------- #
def fig_market_scatter():
    """Data-forward: every forecast vs the market it could see (416 points)."""
    df = pd.read_csv(ANA / "forecasts_with_odds.csv")
    fig, axes = plt.subplots(1, 4, figsize=(V.COL2, 2.15), sharex=True, sharey=True)
    for ax, m in zip(axes, M):
        d = df[df.model == m]
        ax.plot([0, 1], [0, 1], ls=(0, (3, 3)), lw=0.9, color=V.MUTED, zorder=1)
        for ok, col in [(True, V.GOOD), (False, V.BAD)]:
            s = d[d.correct == ok]
            ax.scatter(s.imp_home, s.p_a, s=14, color=col, alpha=0.7,
                       edgecolor="white", linewidth=0.3, zorder=2)
        r = np.corrcoef(d.imp_home, d.p_a)[0, 1]
        ax.set_title(f"{LBL[m]}", color=_mc(m), fontsize=9, weight="bold")
        ax.text(0.05, 0.93, f"r={r:.2f}", transform=ax.transAxes, fontsize=7.6,
                color=V.INK2, va="top")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
        ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
        V.despine(ax)
        ax.set_xlabel("Market P")
    axes[0].set_ylabel("Model P(team A win)")
    axes[-1].legend(handles=[Line2D([], [], marker="o", ls="", color=V.GOOD, label="pick correct"),
                             Line2D([], [], marker="o", ls="", color=V.BAD, label="pick wrong")],
                    loc="lower right", fontsize=6.8, handletextpad=0.2)
    fig.suptitle("Agent vs. market-implied probability (team-A win), 104 matches per agent", fontsize=9, x=0.02, ha="left", y=1.05, color=V.INK)
    fig.tight_layout()
    V.save(fig, "fig_market_scatter")


# --------------------------------------------------------------------------- #
def fig_calibration():
    df = pd.read_csv(ANA / "forecasts_tidy_104.csv")
    fig, axes = plt.subplots(2, 2, figsize=(V.COL1 * 1.7, V.COL1 * 1.72))
    bins = np.round(np.arange(0, 1.01, 0.1), 2)
    for ax, m in zip(axes.ravel(), M):
        d = df[df.model == m]
        ax.plot([0.33, 1], [0.33, 1], ls=(0, (3, 3)), lw=0.9, color=V.MUTED, zorder=1)
        xs, ys, ns = [], [], []
        for i in range(len(bins) - 1):
            lo, hi = bins[i], bins[i + 1]
            mm = (d.conf > lo) & (d.conf <= hi) if i else (d.conf >= lo) & (d.conf <= hi)
            sub = d[mm]
            if len(sub):
                xs.append(sub.conf.mean()); ys.append(sub.correct.mean()); ns.append(len(sub))
        ax.fill_between([0.33, 1], [0.33, 1], 1, color=V.GOOD, alpha=0.05, zorder=0)
        ax.plot(xs, ys, "-", color=_mc(m), lw=1.7, zorder=2)
        ax.scatter(xs, ys, s=[16 + n * 3 for n in ns], color=_mc(m),
                   marker=V.MODEL_MARKER[m], edgecolor="white", linewidth=0.7, zorder=3)
        e = sum(n / len(d) * abs(a - c) for a, c, n in zip(ys, xs, ns))
        ax.text(0.37, 0.95, f"{LBL[m]}", fontsize=9, weight="bold", color=_mc(m), va="top")
        ax.text(0.37, 0.86, f"ECE={e:.3f}", fontsize=8, color=V.INK2, va="top")
        ax.set_xlim(0.33, 1); ax.set_ylim(0.33, 1); ax.set_aspect("equal")
        ax.set_xticks([0.4, 0.6, 0.8, 1.0]); ax.set_yticks([0.4, 0.6, 0.8, 1.0])
        V.despine(ax)
    for ax in axes[-1]:
        ax.set_xlabel("Mean predicted confidence")
    for ax in axes[:, 0]:
        ax.set_ylabel("Empirical accuracy")
    fig.suptitle("Reliability of the top pick (above the diagonal = under-confident)",
                 fontsize=9.3, x=0.02, ha="left", y=1.0, color=V.INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    V.save(fig, "fig_calibration")


# --------------------------------------------------------------------------- #
def fig_convergence():
    df = pd.read_csv(ANA / "forecasts_tidy_104.csv")
    piv = df.pivot_table(index="match_id", columns="model",
                         values="pick_outcome", aggfunc="first").dropna()
    corr = df.pivot_table(index="match_id", columns="model",
                          values="correct", aggfunc="first").dropna()
    phase = df.drop_duplicates("match_id").set_index("match_id")["phase"]
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(V.COL2, 2.7),
                                   gridspec_kw={"width_ratios": [1, 1.15]})
    A = np.zeros((4, 4))
    for i, a in enumerate(M):
        for j, b in enumerate(M):
            A[i, j] = (piv[a] == piv[b]).mean()
    im = axA.imshow(A, cmap=V.SEQ, vmin=0.85, vmax=1.0)
    axA.set_xticks(range(4)); axA.set_yticks(range(4))
    axA.set_xticklabels([LBL[m] for m in M], rotation=30, ha="right")
    axA.set_yticklabels([LBL[m] for m in M])
    for i in range(4):
        for j in range(4):
            axA.text(j, i, f"{A[i,j]:.2f}", ha="center", va="center", fontsize=8,
                     color="white" if A[i, j] > 0.96 else V.INK)
    axA.set_title("Pairwise same-pick rate", color=V.INK, fontsize=9)
    for s in axA.spines.values():
        s.set_visible(False)
    axA.tick_params(length=0)

    nc = corr.sum(axis=1).astype(int)
    cats = pd.DataFrame({"phase": phase.reindex(nc.index), "nc": nc})
    gs = ["group", "knockout"]
    ur = np.array([((cats.phase == g) & (cats.nc == 4)).sum() for g in gs])
    uw = np.array([((cats.phase == g) & (cats.nc == 0)).sum() for g in gs])
    mx = np.array([((cats.phase == g) & (cats.nc.between(1, 3))).sum() for g in gs])
    x = np.arange(2)
    axB.bar(x, ur, color=V.GOOD, edgecolor="white", label="unanimous · correct")
    axB.bar(x, uw, bottom=ur, color=V.BAD, edgecolor="white", label="unanimous · wrong")
    axB.bar(x, mx, bottom=ur + uw, color=V.MID, edgecolor="white", label="models split")
    for xi in x:
        axB.text(xi, ur[xi] / 2, f"{ur[xi]}", ha="center", va="center", fontsize=8,
                 color="white", weight="bold")
        axB.text(xi, ur[xi] + uw[xi] / 2, f"{uw[xi]}", ha="center", va="center",
                 fontsize=8, color="white", weight="bold")
        axB.text(xi, ur[xi] + uw[xi] + mx[xi] + 1.2, f"split {mx[xi]}", ha="center",
                 fontsize=7, color=V.MUTED)
    axB.set_xticks(x); axB.set_xticklabels(["Group (72)", "Knockout (32)"])
    axB.set_ylabel("Matches")
    axB.set_title("Rarely split; unanimous ≈ 2× more right than wrong", fontsize=9, color=V.INK)
    axB.legend(loc="center right", fontsize=7.2, handlelength=1.1)
    V.despine(axB)
    fig.suptitle("Agreement of the four agents' top pick",
                 fontsize=10, x=0.02, ha="left", y=1.02, color=V.INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    V.save(fig, "fig_convergence")


# --------------------------------------------------------------------------- #
def fig_reasoning_factors():
    """Dumbbell: each factor's citation rate, one dot per model, sorted."""
    freq = pd.read_csv(ANA / "factor_frequency.csv", index_col=0)
    order = freq["ALL"].sort_values().index  # ascending -> top at top after invert
    nice = {"market_odds": "market / odds", "squad_depth_quality": "squad depth · quality",
            "attack_threat": "attacking threat", "defense_organized": "defensive organisation",
            "form_momentum": "form · momentum", "star_player": "star player",
            "injuries_susp": "injuries · susp.", "fifa_ranking": "FIFA ranking",
            "variance_penalty": "variance · penalties", "experience_motiv": "experience · motivation",
            "home_altitude": "home · altitude", "head_to_head": "head-to-head",
            "fatigue_rest": "fatigue · rest"}
    fig, ax = plt.subplots(figsize=(V.COL1 * 1.62, 4.1))
    y = np.arange(len(order))
    for yi, f in zip(y, order):
        vals = [freq.loc[f, m] for m in M]
        ax.plot([min(vals), max(vals)], [yi, yi], color=V.GRID, lw=3, solid_capstyle="round", zorder=1)
        for m in M:
            ax.scatter(freq.loc[f, m], yi, s=42, color=_mc(m), marker=V.MODEL_MARKER[m],
                       edgecolor="white", linewidth=0.6, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([nice.get(f, f) for f in order])
    # spotlight the market row + callout in the open bottom-left band
    yi = list(order).index("market_odds")
    ax.axhspan(yi - 0.45, yi + 0.45, color=V.BAD, alpha=0.07, zorder=0)
    ax.annotate("Gemini barely cites the\nmarket (12%); Claude\nalways does (100%)",
                xy=(0.12, yi), xytext=(0.44, 1.1), fontsize=7.6, color=V.BAD,
                va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color=V.BAD, lw=0.9,
                                connectionstyle="arc3,rad=-0.25", alpha=0.6))
    ax.set_xlim(-0.02, 1.02); ax.set_xlabel("Share of pre-match forecasts citing the factor")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
    V.despine(ax, left=False)
    _model_legend(ax, loc="lower right", fontsize=7.4, ncol=2, columnspacing=0.8)
    ax.set_title("Factor citation rate in pre-match reasoning", fontsize=9.6, color=V.INK)
    V.save(fig, "fig_reasoning_factors")


# --------------------------------------------------------------------------- #
def fig_reflection():
    hon = pd.read_csv(ANA / "reflection_honesty.csv").set_index("model")
    fig, ax = plt.subplots(figsize=(V.COL1 * 1.5, 2.35))
    y = np.arange(len(M))[::-1]
    for yi, m in zip(y, M):
        n = hon.loc[m, "n_wrong"]
        inc, par, cor = (hon.loc[m, "self_incorrect"] / n,
                         hon.loc[m, "self_partial"] / n, hon.loc[m, "self_correct"] / n)
        ax.barh(yi, inc, color=V.GOOD, edgecolor="white")
        ax.barh(yi, par, left=inc, color=V.MID, edgecolor="white")
        ax.barh(yi, cor, left=inc + par, color=V.BAD, edgecolor="white")
        ax.text(inc / 2, yi, f"{inc:.0%}", ha="center", va="center", fontsize=8, color="white")
        if cor > 0.03:
            ax.text(inc + par + cor / 2, yi, f"{cor:.0%}", ha="center", va="center",
                    fontsize=7.5, color="white")
    ax.set_yticks(y); ax.set_yticklabels([LBL[m] for m in M])
    ax.set_xlim(0, 1); ax.set_xlabel("Share of the model's own wrong picks")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
    V.despine(ax, left=False)
    ax.legend(handles=[Patch(facecolor=V.GOOD, label='owns it ("incorrect")'),
                       Patch(facecolor=V.MID, label='"partially correct"'),
                       Patch(facecolor=V.BAD, label='denies ("correct")')],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=7.2, handlelength=1.0)
    ax.set_title("Self-assessment on the agent's own wrong picks",
                 fontsize=8.8, color=V.INK, pad=22)
    V.save(fig, "fig_reflection")


# --------------------------------------------------------------------------- #
def fig_upsets():
    df = pd.read_csv(ANA / "forecasts_tidy_104.csv")
    UP = ["m74", "m75", "m88", "m95", "m92", "m93", "m101", "m103"]
    recs = []
    for mid in UP:
        d = df[df.match_id == mid]; r = d.iloc[0]
        pfav = max(d.p_a.mean(), d.p_b.mean())
        fav = r.team_a if d.p_a.mean() >= d.p_b.mean() else r.team_b
        pen = r.decided_by == "penalties"
        recs.append((f"{r.team_a} {int(r.final_score_a)}–{int(r.final_score_b)} {r.team_b}",
                     pfav, fav, pen))
    recs.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(V.COL2, 2.9))
    y = np.arange(len(recs))
    for yi, (label, pfav, fav, pen) in zip(y, recs):
        ax.plot([0.33, pfav], [yi, yi], color=V.GRID, lw=2.4, solid_capstyle="round", zorder=1)
        ax.scatter(pfav, yi, s=95, color=V.BAD, marker="P" if pen else "X",
                   edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(pfav + 0.013, yi, f"{pfav:.0%} on {fav}", va="center", ha="left",
                fontsize=7.2, color=V.INK)
    ax.axvline(0.5, color=V.BASE, lw=0.9, zorder=0)
    ax.text(0.5, len(recs) - 0.35, "coin flip", fontsize=6.8, color=V.MUTED, ha="center")
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in recs], fontsize=7.6)
    ax.set_ylim(-0.7, len(recs) - 0.2); ax.set_xlim(0.33, 1.02)
    ax.set_xlabel("Mean consensus probability on the favorite (all 4 models)")
    ax.set_xticks([0.4, 0.5, 0.6, 0.7, 0.8])
    ax.set_xticklabels(["40%", "50%", "60%", "70%", "80%"])
    V.despine(ax, left=False)
    ax.legend(handles=[Line2D([], [], ls="", marker="P", color=V.BAD, markersize=9,
                              label="lost on penalties (90' draw)"),
                       Line2D([], [], ls="", marker="X", color=V.BAD, markersize=8,
                              label="lost in regulation")],
              loc="lower right", fontsize=7.2)
    ax.set_title("Matches mispredicted by all four agents",
                 fontsize=9.6, color=V.INK)
    V.save(fig, "fig_upsets")


def main():
    fig_leaderboard()
    fig_market_scatter()
    fig_calibration()
    fig_convergence()
    fig_reasoning_factors()
    fig_reflection()
    fig_upsets()


if __name__ == "__main__":
    main()
