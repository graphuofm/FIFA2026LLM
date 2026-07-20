"""Unified analysis layer for the WC2026 LLM-forecasting study (all 104 matches).

Builds one tidy table (one row per model x match) from the group-stage per-model
CSVs (m01-m72) and the knockout per-model CSVs (m73-m104), then computes the
odds-independent results the paper needs:

  * per-model, per-stage accuracy / Brier / log-loss / draw-mass
  * calibration: reliability bins + ECE (expected calibration error)
  * convergence: how often the four models pick the SAME argmax (the reason
    accuracy can't separate them) + pairwise agreement
  * reflection: self-labeling honesty vs realized correctness

Betting/market analysis lives in betting.py (needs odds); reasoning-factor and
reflection-factor coding live in reasoning.py.

Outputs go to data/analysis/.
"""
from __future__ import annotations
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
META = ROOT / "data" / "metadata"
ANA = ROOT / "data" / "analysis"
MODELS = ["claude", "chatgpt", "gemini", "grok"]
OUTCOMES = ["team_a_win", "draw", "team_b_win"]

KO_STAGE_ORDER = ["round_of_32", "round_of_16", "quarter_final",
                  "semi_final", "third_place", "final"]


def _winner_side(row):
    a, b = row["final_score_a"], row["final_score_b"]
    if pd.isna(a) or pd.isna(b):
        return None
    return "team_a" if a > b else "team_b" if b > a else None  # draw -> no side


def load_tidy() -> pd.DataFrame:
    """One row per (model, match). Group + knockout, harmonised columns."""
    rows = []
    for model in MODELS:
        g = pd.read_csv(PROC / f"{model}.csv")
        g["stage"] = "group"
        g["decided_by"] = "regulation"
        g["advanced"] = g.apply(_winner_side, axis=1)
        k = pd.read_csv(PROC / f"{model}_knockout.csv")
        for df, phase in [(g, "group"), (k, "knockout")]:
            for r in df.itertuples():
                rows.append({
                    "model": model, "match_id": r.match_id, "phase": phase,
                    "stage": r.stage, "team_a": r.team_a, "team_b": r.team_b,
                    "final_score_a": r.final_score_a, "final_score_b": r.final_score_b,
                    "outcome": r.outcome, "decided_by": r.decided_by,
                    "advanced": getattr(r, "advanced", None),
                    "p_a": r.pre_p_team_a_win, "p_draw": r.pre_p_draw,
                    "p_b": r.pre_p_team_b_win,
                    "bet_pick": r.pre_bet_pick, "bet_stake": r.pre_bet_stake_usd,
                    "reasoning": r.pre_reasoning,
                    "refl_outcome": r.refl_outcome_vs_prediction,
                    "refl_calibrated": r.refl_was_well_calibrated,
                    "refl_luck": r.refl_luck,
                    "refl_missed": r.refl_key_factor_missed,
                    "refl_overweighted": r.refl_key_factor_overweighted,
                    "refl_bet_diff": r.refl_would_bet_differently,
                    "refl_conf": r.refl_confidence,
                })
    df = pd.DataFrame(rows)
    df = df[df.p_a.notna()].copy()
    s = df[["p_a", "p_draw", "p_b"]].sum(axis=1).replace(0, 1)
    for c in ["p_a", "p_draw", "p_b"]:
        df[c] = df[c] / s
    df["argmax"] = df[["p_a", "p_draw", "p_b"]].values.argmax(axis=1)
    df["pick_outcome"] = df["argmax"].map(dict(enumerate(OUTCOMES)))
    df["correct"] = df["pick_outcome"] == df["outcome"]
    oh = df["outcome"].map({o: i for i, o in enumerate(OUTCOMES)})
    df["p_actual"] = [row[["p_a", "p_draw", "p_b"]].values[i]
                      for (_, row), i in zip(df.iterrows(), oh)]
    df["brier"] = ((df.p_a - (df.outcome == "team_a_win")) ** 2
                   + (df.p_draw - (df.outcome == "draw")) ** 2
                   + (df.p_b - (df.outcome == "team_b_win")) ** 2)
    df["logloss"] = -df["p_actual"].clip(1e-6, 1).map(math.log)
    df["conf"] = df[["p_a", "p_draw", "p_b"]].max(axis=1)
    return df


def metrics_by(df, by):
    g = df.groupby(by)
    out = g.agg(n=("correct", "size"), accuracy=("correct", "mean"),
                brier=("brier", "mean"), log_loss=("logloss", "mean"),
                mean_draw_prob=("p_draw", "mean"),
                mean_conf=("conf", "mean")).round(4)
    return out.reset_index()


def ece(df, model, bins=10):
    """Expected calibration error on the argmax-confidence vs correctness."""
    d = df[df.model == model]
    edges = [i / bins for i in range(bins + 1)]
    tot, e = len(d), 0.0
    rows = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        m = (d.conf > lo) & (d.conf <= hi) if i else (d.conf >= lo) & (d.conf <= hi)
        sub = d[m]
        if len(sub):
            acc, cf = sub.correct.mean(), sub.conf.mean()
            e += len(sub) / tot * abs(acc - cf)
            rows.append({"model": model, "bin_lo": lo, "bin_hi": hi,
                         "n": len(sub), "conf": round(cf, 4), "acc": round(acc, 4)})
    return round(e, 4), rows


def convergence(df):
    """Per match, do all 4 models share one argmax? Pairwise agreement too."""
    piv = df.pivot_table(index="match_id", columns="model",
                         values="pick_outcome", aggfunc="first")
    piv = piv.dropna()
    same = (piv.nunique(axis=1) == 1)
    # attach phase
    phase = df.drop_duplicates("match_id").set_index("match_id")["phase"]
    piv = piv.join(phase)
    by_phase = piv.assign(same=same).groupby("phase")["same"].agg(["mean", "size"])
    pair = {}
    for i, a in enumerate(MODELS):
        for b in MODELS[i + 1:]:
            pair[f"{a}~{b}"] = round((piv[a] == piv[b]).mean(), 3)
    return round(same.mean(), 3), by_phase.round(3), pair, piv, same


def reflection_honesty(df):
    """When the model's argmax was wrong, what does its self-label say?"""
    rows = []
    for m in MODELS:
        d = df[(df.model == m) & (~df.correct)]
        vc = d.refl_outcome.value_counts()
        rows.append({"model": m, "n_wrong": len(d),
                     "self_incorrect": int(vc.get("incorrect", 0)),
                     "self_partial": int(vc.get("partially_correct", 0)),
                     "self_correct": int(vc.get("correct", 0)),
                     "own_error_rate": round(vc.get("incorrect", 0) / len(d), 3) if len(d) else None})
    # also: when RIGHT, do they say correct?
    for r in rows:
        d = df[(df.model == r["model"]) & (df.correct)]
        r["when_right_says_correct"] = round((d.refl_outcome == "correct").mean(), 3)
    return pd.DataFrame(rows)


def main():
    ANA.mkdir(parents=True, exist_ok=True)
    df = load_tidy()
    df.to_csv(ANA / "forecasts_tidy_104.csv", index=False)
    print(f"tidy rows: {len(df)}  ({df.phase.value_counts().to_dict()})\n")

    # per model overall + per phase
    overall = metrics_by(df, "model")
    per_phase = metrics_by(df, ["model", "phase"])
    overall.to_csv(ANA / "metrics_overall.csv", index=False)
    per_phase.to_csv(ANA / "metrics_by_phase.csv", index=False)
    print("== Overall (104 matches) =="); print(overall.to_string(index=False))
    print("\n== By phase =="); print(per_phase.to_string(index=False))

    # calibration
    calib_rows, eces = [], {}
    for m in MODELS:
        e, rows = ece(df, m)
        eces[m] = e
        calib_rows += rows
    pd.DataFrame(calib_rows).to_csv(ANA / "calibration_bins.csv", index=False)
    print("\n== ECE (lower=better) =="); print(eces)

    # convergence
    frac, by_phase, pair, piv, same = convergence(df)
    print(f"\n== Convergence: all-4 identical argmax = {frac:.1%} of matches ==")
    print(by_phase); print("pairwise:", pair)
    piv.assign(all_same=same).to_csv(ANA / "convergence_by_match.csv")

    # reflection honesty
    hon = reflection_honesty(df)
    hon.to_csv(ANA / "reflection_honesty.csv", index=False)
    print("\n== Reflection honesty =="); print(hon.to_string(index=False))
    return df


if __name__ == "__main__":
    main()
