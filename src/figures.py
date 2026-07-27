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
    fig, axes = plt.subplots(2, 2, figsize=(V.COL1, V.COL1 * 1.02),
                             sharex=True, sharey=True)
    axf = axes.ravel()
    for ax, m in zip(axf, M):
        d = df[df.model == m]
        ax.plot([0, 1], [0, 1], ls=(0, (3, 3)), lw=0.8, color=V.MUTED, zorder=1)
        for ok, col in [(True, V.GOOD), (False, V.BAD)]:
            s = d[d.correct == ok]
            ax.scatter(s.imp_home, s.p_a, s=8, color=col, alpha=0.7,
                       edgecolor="white", linewidth=0.2, zorder=2)
        r = np.corrcoef(d.imp_home, d.p_a)[0, 1]
        ax.set_title(LBL[m], color=_mc(m), fontsize=8.4, weight="bold", pad=2)
        ax.text(0.06, 0.95, f"r={r:.2f}", transform=ax.transAxes, fontsize=7,
                color=V.INK2, va="top")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
        ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
        V.despine(ax)
    for ax in axes[1, :]:
        ax.set_xlabel("Market P", fontsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel("Model P(A win)", fontsize=8)
    axf[1].legend(handles=[Line2D([], [], marker="o", ls="", color=V.GOOD, label="correct"),
                           Line2D([], [], marker="o", ls="", color=V.BAD, label="wrong")],
                  loc="lower right", fontsize=6.2, handletextpad=0.2, borderpad=0.2)
    fig.suptitle("Agent vs. market probability (team-A win)", fontsize=8.6,
                 y=1.0, color=V.INK)
    fig.tight_layout()
    V.save(fig, "fig_market_scatter")


# --------------------------------------------------------------------------- #
def fig_calibration():
    df = pd.read_csv(ANA / "forecasts_tidy_104.csv")
    fig, axes = plt.subplots(2, 2, figsize=(V.COL1 * 1.7, V.COL1 * 1.72))
    bins = np.round(np.arange(0, 1.01, 0.1), 2)
    # market reliability (top pick) overlaid on every panel as a reference
    fwo = pd.read_csv(ANA / "forecasts_with_odds.csv").drop_duplicates("match_id")
    imp = fwo[["imp_home", "imp_draw", "imp_away"]].values
    mconf = imp.max(1)
    mpick = np.array(["team_a_win", "draw", "team_b_win"])[imp.argmax(1)]
    mok = (mpick == fwo.outcome.values)
    mxs, mys = [], []
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        sel = (mconf > lo) & (mconf <= hi) if i else (mconf >= lo) & (mconf <= hi)
        if sel.sum():
            mxs.append(mconf[sel].mean()); mys.append(mok[sel].mean())
    for ax, m in zip(axes.ravel(), M):
        d = df[df.model == m]
        ax.plot([0.33, 1], [0.33, 1], ls=(0, (3, 3)), lw=0.9, color=V.MUTED, zorder=1)
        ax.fill_between([0.33, 1], [0.33, 1], 1, color=V.GOOD, alpha=0.05, zorder=0)
        ax.plot(mxs, mys, "-", color=V.MARKET_COLOR, lw=1.2, alpha=0.7, zorder=1.5,
                label="Market")
        xs, ys, ns = [], [], []
        for i in range(len(bins) - 1):
            lo, hi = bins[i], bins[i + 1]
            mm = (d.conf > lo) & (d.conf <= hi) if i else (d.conf >= lo) & (d.conf <= hi)
            sub = d[mm]
            if len(sub):
                xs.append(sub.conf.mean()); ys.append(sub.correct.mean()); ns.append(len(sub))
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
    fig.suptitle("Reliability of the top pick — colour = agent, grey = market "
                 "(all under-confident)", fontsize=8.8, x=0.02, ha="left", y=1.0, color=V.INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    V.save(fig, "fig_calibration")


# --------------------------------------------------------------------------- #
def fig_convergence():
    df = pd.read_csv(ANA / "forecasts_tidy_104.csv")
    fwo = pd.read_csv(ANA / "forecasts_with_odds.csv").drop_duplicates("match_id")
    mk = fwo.set_index("match_id")[["imp_home", "imp_draw", "imp_away"]]
    mkpick = mk.values.argmax(1)
    mkpick = pd.Series([["team_a_win", "draw", "team_b_win"][i] for i in mkpick],
                       index=mk.index)
    piv = df.pivot_table(index="match_id", columns="model",
                         values="pick_outcome", aggfunc="first").dropna()
    corr = df.pivot_table(index="match_id", columns="model",
                          values="correct", aggfunc="first").dropna()
    phase = df.drop_duplicates("match_id").set_index("match_id")["phase"]
    piv["market"] = piv.index.map(mkpick)
    ents = M + ["market"]
    labs = [LBL[m] for m in M] + ["Market"]
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(V.COL1, V.COL1 * 1.34),
                                   gridspec_kw={"height_ratios": [1.5, 1]})
    n = len(ents)
    A = np.zeros((n, n))
    for i, a in enumerate(ents):
        for j, b in enumerate(ents):
            A[i, j] = (piv[a] == piv[b]).mean()
    axA.imshow(A, cmap=V.SEQ, vmin=0.85, vmax=1.0)
    axA.set_xticks(range(n)); axA.set_yticks(range(n))
    axA.set_xticklabels(labs, rotation=30, ha="right", fontsize=7)
    axA.set_yticklabels(labs, fontsize=7)
    for lab in [axA.get_xticklabels()[-1], axA.get_yticklabels()[-1]]:
        lab.set_color(V.MARKET_COLOR); lab.set_weight("bold")
    for i in range(n):
        for j in range(n):
            axA.text(j, i, f"{A[i,j]:.2f}", ha="center", va="center", fontsize=6.3,
                     color="white" if A[i, j] > 0.96 else V.INK)
    axA.set_title("Pairwise same-pick rate", color=V.INK, fontsize=8.4)
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
    axB.bar(x, ur, color=V.GOOD, edgecolor="white", label="unan. correct")
    axB.bar(x, uw, bottom=ur, color=V.BAD, edgecolor="white", label="unan. wrong")
    axB.bar(x, mx, bottom=ur + uw, color=V.MID, edgecolor="white", label="split")
    for xi in x:
        axB.text(xi, ur[xi] / 2, f"{ur[xi]}", ha="center", va="center", fontsize=7.4,
                 color="white", weight="bold")
        axB.text(xi, ur[xi] + uw[xi] / 2, f"{uw[xi]}", ha="center", va="center",
                 fontsize=7.4, color="white", weight="bold")
    axB.set_xticks(x); axB.set_xticklabels(["Group (72)", "Knockout (32)"], fontsize=7.4)
    axB.set_ylabel("Matches", fontsize=8)
    axB.legend(loc="upper right", fontsize=6.2, handlelength=0.9)
    V.despine(axB)
    fig.suptitle("The four agents agree on 92% of picks", fontsize=8.8,
                 y=1.0, color=V.INK)
    fig.tight_layout()
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
    fig, ax = plt.subplots(figsize=(V.COL1 * 1.7, 4.25))
    y = np.arange(len(order))
    mrow = list(order).index("market_odds")
    ax.axhspan(mrow - 0.5, mrow + 0.5, color="#eef2f7", zorder=0)  # subtle market band
    for yi, f in zip(y, order):
        vals = [freq.loc[f, m] for m in M]
        ax.plot([min(vals), max(vals)], [yi, yi], color="#dee2e7", lw=2.2,
                solid_capstyle="round", zorder=1)
        for m in M:
            ax.scatter(freq.loc[f, m], yi, s=58, color=_mc(m), marker=V.MODEL_MARKER[m],
                       edgecolor="white", linewidth=0.9, zorder=3)
    # direct labels on the market-row extremes — no arrow, no callout box
    ax.text(freq.loc["market_odds", "gemini"] - 0.018, mrow, "12%", ha="right",
            va="center", fontsize=7.8, color=_mc("gemini"), weight="bold", zorder=4)
    ax.text(freq.loc["market_odds", "claude"] + 0.02, mrow, "100%", ha="left",
            va="center", fontsize=7.8, color=_mc("claude"), weight="bold", zorder=4)
    ax.set_yticks(y); ax.set_yticklabels([nice.get(f, f) for f in order])
    ax.get_yticklabels()[mrow].set_weight("bold")
    ax.set_xlim(-0.02, 1.07); ax.set_xlabel("Share of pre-match forecasts citing the factor")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
    V.despine(ax, left=False)
    _model_legend(ax, loc="lower right", fontsize=7.6, ncol=2, columnspacing=0.8)
    ax.set_title("Factor citation rate in pre-match reasoning", fontsize=9.8, color=V.INK)
    V.save(fig, "fig_reasoning_factors")


# --------------------------------------------------------------------------- #
def fig_reflection():
    hon = pd.read_csv(ANA / "reflection_honesty.csv").set_index("model")
    OWN, PART, DENY = "#3a8f5b", "#c9ced4", "#c8544f"   # muted honest / neutral / denial
    fig, ax = plt.subplots(figsize=(V.COL1 * 1.6, 2.55))
    y = np.arange(len(M))[::-1]
    h = 0.6
    for yi, m in zip(y, M):
        n = hon.loc[m, "n_wrong"]
        inc, par, cor = (hon.loc[m, "self_incorrect"] / n,
                         hon.loc[m, "self_partial"] / n, hon.loc[m, "self_correct"] / n)
        ax.barh(yi, inc, height=h, color=OWN, edgecolor="white", linewidth=1.3)
        ax.barh(yi, par, left=inc, height=h, color=PART, edgecolor="white", linewidth=1.3)
        ax.barh(yi, cor, left=inc + par, height=h, color=DENY, edgecolor="white", linewidth=1.3)
        ax.text(inc / 2, yi, f"{inc:.0%}", ha="center", va="center", fontsize=8.6,
                color="white", weight="bold")
        if par > 0.10:
            ax.text(inc + par / 2, yi, f"{par:.0%}", ha="center", va="center",
                    fontsize=7.6, color=V.INK2)
        # denial % placed just past the 100% line so tiny segments never clip
        ax.text(1.015, yi, f"{cor:.0%}", ha="left", va="center", fontsize=7.8,
                color=DENY, weight="bold")
    ax.set_yticks(y); ax.set_yticklabels([LBL[m] for m in M])
    ax.set_xlim(0, 1.10); ax.set_xlabel("Share of the model's own wrong picks")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
    V.despine(ax, left=False)
    ax.legend(handles=[Patch(facecolor=OWN, label='owns it ("incorrect")'),
                       Patch(facecolor=PART, label='"partially correct"'),
                       Patch(facecolor=DENY, label='denies ("correct")')],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=7.4, handlelength=1.0)
    ax.set_title("Self-assessment on the agent's own wrong picks",
                 fontsize=9, color=V.INK, pad=22)
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
    fig, ax = plt.subplots(figsize=(V.COL1, 2.7))
    y = np.arange(len(recs))
    for yi, (label, pfav, fav, pen) in zip(y, recs):
        ax.plot([0.33, pfav], [yi, yi], color=V.GRID, lw=1.8, solid_capstyle="round", zorder=1)
        ax.scatter(pfav, yi, s=58, color=V.BAD, marker="P" if pen else "X",
                   edgecolor="white", linewidth=0.7, zorder=3)
        ax.text(pfav + 0.02, yi, f"{pfav:.0%}", va="center", ha="left",
                fontsize=6.8, color=V.INK, weight="bold")
    ax.axvline(0.5, color=V.BASE, lw=0.8, zorder=0)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in recs], fontsize=6.6)
    ax.set_ylim(-0.7, len(recs) - 0.2); ax.set_xlim(0.33, 1.0)
    ax.set_xlabel("Mean consensus prob. on the favorite", fontsize=8)
    ax.set_xticks([0.4, 0.6, 0.8]); ax.set_xticklabels(["40%", "60%", "80%"])
    V.despine(ax, left=False)
    ax.legend(handles=[Line2D([], [], ls="", marker="P", color=V.BAD, markersize=7,
                              label="lost on pens"),
                       Line2D([], [], ls="", marker="X", color=V.BAD, markersize=6,
                              label="lost in reg.")],
              loc="lower right", fontsize=6.2)
    ax.set_title("Eight matches all four agents missed",
                 fontsize=8.6, color=V.INK)
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
