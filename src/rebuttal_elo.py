"""Elo baseline for the 104 WC2026 matches (reviewer-requested domain baseline).

Ratings are built from public international results (martj42/international_results,
CC0) using only matches played BEFORE the tournament (2026-06-11), then mapped to
1X2 probabilities by a multinomial logistic fit on historical matches, so the
baseline never sees a 2026 World Cup result.

Run: python src/rebuttal_elo.py   ->  data/analysis/rebuttal/elo_baseline*.csv
"""
from __future__ import annotations
from pathlib import Path
import urllib.request
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ANA = ROOT / "data" / "analysis"
OUT = ANA / "rebuttal"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "international_results.csv"
URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

CUTOFF = "2026-06-11"          # first WC2026 match
FIT_FROM = "2006-01-01"        # history used to fit the Elo -> 1X2 mapping
HOSTS = {"United States", "USA", "Canada", "Mexico"}
OUTCOMES = ["team_a_win", "draw", "team_b_win"]
HOME_ADV = 100.0               # Elo points, applied only to host nations here

# our fixtures use FIFA naming; the public archive uses common English names
TEAM_MAP = {
    "USA": "United States",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "Türkiye": "Turkey",
    "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "Congo DR": "DR Congo",
    "Czechia": "Czech Republic",
}


def k_factor(tournament: str, gd: int) -> float:
    t = (tournament or "").lower()
    if "world cup" in t and "qualification" not in t:
        k = 60.0
    elif any(s in t for s in ("copa", "euro", "african cup", "asian cup", "gold cup", "confederations")):
        k = 50.0
    elif "qualification" in t or "nations league" in t:
        k = 40.0
    else:
        k = 20.0
    if gd == 2:
        k *= 1.5
    elif gd >= 3:
        k *= 1.75 + (gd - 3) / 8.0
    return k


def fetch():
    if not CACHE.exists():
        print("downloading international results ...")
        urllib.request.urlretrieve(URL, CACHE)
    h = pd.read_csv(CACHE)
    h["date"] = pd.to_datetime(h["date"])
    return h


def build_ratings(hist: pd.DataFrame):
    """Walk history chronologically; return final ratings and the fit sample."""
    R: dict[str, float] = {}
    fit_rows = []
    for r in hist.itertuples(index=False):
        ha, aw = r.home_team, r.away_team
        ra, rb = R.get(ha, 1500.0), R.get(aw, 1500.0)
        neutral = bool(r.neutral) if not pd.isna(r.neutral) else False
        adv = 0.0 if neutral else HOME_ADV
        dr = (ra + adv) - rb
        if r.date >= pd.Timestamp(FIT_FROM):
            if r.home_score > r.away_score:
                y = 0
            elif r.home_score == r.away_score:
                y = 1
            else:
                y = 2
            fit_rows.append((dr, y))
        we = 1.0 / (10 ** (-dr / 400.0) + 1.0)
        gd = int(abs(r.home_score - r.away_score))
        w = 1.0 if r.home_score > r.away_score else (0.5 if r.home_score == r.away_score else 0.0)
        k = k_factor(r.tournament, gd)
        delta = k * (w - we)
        R[ha] = ra + delta
        R[aw] = rb - delta
    return R, np.array(fit_rows, dtype=float)


def fit_softmax(X1: np.ndarray, y: np.ndarray, iters=4000, lr=0.5):
    """3-class logistic on [1, dr/400]; plain gradient descent, deterministic."""
    X = np.column_stack([np.ones(len(X1)), X1 / 400.0])
    W = np.zeros((2, 3))
    Y = np.zeros((len(y), 3))
    Y[np.arange(len(y)), y.astype(int)] = 1
    for _ in range(iters):
        z = X @ W
        z -= z.max(axis=1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(axis=1, keepdims=True)
        W -= lr * (X.T @ (p - Y)) / len(y)
    return W


def predict(W: np.ndarray, dr: np.ndarray):
    X = np.column_stack([np.ones(len(dr)), dr / 400.0])
    z = X @ W
    z -= z.max(axis=1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(axis=1, keepdims=True)


def main():
    hist = fetch().sort_values("date")
    pre = hist[hist.date < pd.Timestamp(CUTOFF)].dropna(subset=["home_score", "away_score"])
    print(f"history: {len(pre)} matches up to {CUTOFF}")
    R, fit = build_ratings(pre)
    W = fit_softmax(fit[:, 0], fit[:, 1])
    print(f"fit sample: {len(fit)} matches from {FIT_FROM}")

    tidy = pd.read_csv(ANA / "forecasts_with_odds.csv")
    wc = tidy.drop_duplicates("match_id")[["match_id", "team_a", "team_b", "outcome"]].copy()

    missing = sorted({TEAM_MAP.get(t, t) for t in pd.concat([wc.team_a, wc.team_b])
                      if TEAM_MAP.get(t, t) not in R})
    if missing:
        raise SystemExit(f"unmapped teams (would silently default to 1500): {missing}")
    print("all 48 teams matched to rated names")

    dr = []
    for r in wc.itertuples(index=False):
        ra = R[TEAM_MAP.get(r.team_a, r.team_a)]
        rb = R[TEAM_MAP.get(r.team_b, r.team_b)]
        adv = HOME_ADV if r.team_a in HOSTS else (-HOME_ADV if r.team_b in HOSTS else 0.0)
        dr.append(ra + adv - rb)
    dr = np.array(dr)
    P = predict(W, dr)
    wc["elo_a"] = [round(R[TEAM_MAP.get(t, t)], 1) for t in wc.team_a]
    wc["elo_b"] = [round(R[TEAM_MAP.get(t, t)], 1) for t in wc.team_b]
    wc[["p_a", "p_draw", "p_b"]] = P.round(4)

    oi = np.array([OUTCOMES.index(o) for o in wc.outcome])
    onehot = np.zeros((len(wc), 3))
    onehot[np.arange(len(wc)), oi] = 1
    acc = (P.argmax(axis=1) == oi).mean()
    brier = ((P - onehot) ** 2).sum(axis=1).mean()
    ll = -np.log(np.clip(P[np.arange(len(wc)), oi], 1e-12, 1)).mean()
    wc.to_csv(OUT / "elo_baseline_per_match.csv", index=False)

    # bootstrap CI over matches, and a paired comparison with the agents/market
    rng = np.random.default_rng(20260929)
    n = len(wc)
    boot = rng.integers(0, n, size=(10000, n))
    per_corr = (P.argmax(axis=1) == oi).astype(float)
    per_brier = ((P - onehot) ** 2).sum(axis=1)
    rows = [{"entity": "elo", "metric": "accuracy", "value": round(acc, 4),
             "ci95_lo": round(float(np.percentile(per_corr[boot].mean(axis=1), 2.5)), 4),
             "ci95_hi": round(float(np.percentile(per_corr[boot].mean(axis=1), 97.5)), 4)},
            {"entity": "elo", "metric": "brier", "value": round(brier, 4),
             "ci95_lo": round(float(np.percentile(per_brier[boot].mean(axis=1), 2.5)), 4),
             "ci95_hi": round(float(np.percentile(per_brier[boot].mean(axis=1), 97.5)), 4)},
            {"entity": "elo", "metric": "log_loss", "value": round(ll, 4),
             "ci95_lo": None, "ci95_hi": None}]
    pd.DataFrame(rows).to_csv(OUT / "elo_baseline_metrics.csv", index=False)
    print(f"\nElo baseline over {n} matches: accuracy {acc:.3f}  Brier {brier:.4f}  log-loss {ll:.4f}")
    print("top-5 |Elo gap| matches:")
    wc["gap"] = np.abs(dr).round(0)
    print(wc.nlargest(5, "gap")[["match_id", "team_a", "team_b", "elo_a", "elo_b", "p_a", "p_draw", "p_b", "outcome"]].to_string(index=False))


if __name__ == "__main__":
    main()
