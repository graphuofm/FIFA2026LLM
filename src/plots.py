"""Generate report figures into reports/figures/."""
import math
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
META, PROC = ROOT / "data" / "metadata", ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
MODELS = ["claude", "chatgpt", "gemini", "grok"]
COLORS = {"claude": "#D97757", "chatgpt": "#10A37F", "gemini": "#4285F4",
          "grok": "#111111", "market": "#888888"}
OUT = ["team_a_win", "draw", "team_b_win"]
DEC = {"team_a_win": "odds_home_dec", "draw": "odds_draw_dec", "team_b_win": "odds_away_dec"}

res = pd.read_csv(META / "results.csv").set_index("match_id")
odds = pd.read_csv(META / "odds.csv").set_index("match_id")
mm = pd.read_csv(PROC / "model_metrics.csv").set_index("model")


def amax(r):
    p = [r.pre_p_team_a_win, r.pre_p_draw, r.pre_p_team_b_win]
    return OUT[max(range(3), key=lambda i: p[i])]


plt.rcParams.update({"figure.dpi": 130, "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6})

# ---- Fig 1: accuracy & Brier vs market -----------------------------------
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
order = MODELS + ["market"]
ax[0].bar(order, [mm.loc[m, "accuracy"] for m in order],
          color=[COLORS[m] for m in order])
ax[0].axhline(mm.loc["market", "accuracy"], ls="--", c="#888", lw=1)
ax[0].set_title("Accuracy (argmax = outcome)"); ax[0].set_ylim(0.5, 0.72)
for i, m in enumerate(order):
    ax[0].text(i, mm.loc[m, "accuracy"] + .004, f"{mm.loc[m,'accuracy']:.0%}", ha="center")
ax[1].bar(order, [mm.loc[m, "brier"] for m in order], color=[COLORS[m] for m in order])
ax[1].axhline(mm.loc["market", "brier"], ls="--", c="#888", lw=1)
ax[1].set_title("Brier score (lower = better)"); ax[1].set_ylim(0.47, 0.50)
fig.suptitle("Nobody beats the market on accuracy; Gemini edges it on Brier", y=1.02)
fig.tight_layout(); fig.savefig(FIG / "accuracy_brier.png", bbox_inches="tight")

# ---- Fig 2: ROI / profit --------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
prof = [mm.loc[m, "net_profit"] for m in MODELS]
bars = ax.bar(MODELS, prof, color=[COLORS[m] for m in MODELS])
ax.axhline(0, c="#444", lw=1)
for i, m in enumerate(MODELS):
    ax.text(i, prof[i] + (12 if prof[i] >= 0 else -22),
            f"${prof[i]:+.0f}\n{mm.loc[m,'roi_pct']:+.1f}%  ({int(mm.loc[m,'n_bets'])} bets)",
            ha="center", va="bottom" if prof[i] >= 0 else "top", fontsize=9)
ax.set_title("Virtual betting P&L — discipline (Claude) lost, aggression (Gemini) won")
ax.set_ylabel("net profit (USD)"); ax.set_ylim(-380, 340)
fig.tight_layout(); fig.savefig(FIG / "roi.png", bbox_inches="tight")

# ---- Fig 3: calibration curves -------------------------------------------
fig, ax = plt.subplots(figsize=(6, 6))
ax.plot([0.3, 1], [0.3, 1], ls="--", c="#aaa", label="perfect")
bins = [(0.33, 0.5), (0.5, 0.65), (0.65, 0.8), (0.8, 1.01)]
for m in MODELS:
    df = pd.read_csv(PROC / f"{m}.csv").set_index("match_id")
    df = df[df.pre_p_team_a_win.notna()].copy()
    df["conf"] = df[["pre_p_team_a_win", "pre_p_draw", "pre_p_team_b_win"]].max(axis=1)
    df["hit"] = [amax(r) == res.loc[i, "outcome"] for i, r in df.iterrows()]
    xs, ys = [], []
    for lo, hi in bins:
        b = df[(df.conf >= lo) & (df.conf < hi)]
        if len(b) >= 4:
            xs.append(b.conf.mean()); ys.append(b.hit.mean())
    ax.plot(xs, ys, "-o", color=COLORS[m], label=m)
ax.set_xlabel("model's stated probability of its top pick")
ax.set_ylabel("actual hit rate")
ax.set_title("Calibration: points above the line = underconfident")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "calibration.png", bbox_inches="tight")

# ---- Fig 4: draw blindness ------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
actual_draw = (res.outcome == "draw").mean()
mdp = [mm.loc[m, "mean_draw_prob"] for m in MODELS] + [mm.loc["market", "mean_draw_prob"]]
ax.bar(MODELS + ["market"], mdp, color=[COLORS[m] for m in MODELS + ["market"]])
ax.axhline(actual_draw, c="crimson", lw=1.5, ls="--",
           label=f"actual draw rate = {actual_draw:.0%}")
ax.set_title("Draw blindness: everyone under-priced draws (20/72 were draws)")
ax.set_ylabel("mean P(draw)"); ax.set_ylim(0, 0.32); ax.legend()
fig.tight_layout(); fig.savefig(FIG / "draws.png", bbox_inches="tight")

print("wrote", *[p.name for p in sorted(FIG.glob("*.png"))])
