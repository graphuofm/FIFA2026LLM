"""Build a blind human-validation sample for the keyword lexicon, and score it.

The reviewers asked whether the 13-category keyword coding matches human
judgement. This draws a stratified random sample, hides the lexicon's label, and
scores agreement (raw + Cohen's kappa) once a human has filled in the blanks.

    python src/rebuttal_lexicon_sample.py make    # -> lexicon_validation_sample.csv (label this)
    python src/rebuttal_lexicon_sample.py score   # -> agreement + Cohen's kappa

Label the `human_cites_market` column with 1 (the text refers to betting odds,
the market, bookmakers, or implied/market probabilities) or 0 (it does not).
Do not open the key file before labelling.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ANA = ROOT / "data" / "analysis"
OUT = ANA / "rebuttal"
SAMPLE = OUT / "lexicon_validation_sample.csv"
KEY = OUT / "lexicon_validation_key.csv"
N_PER_CELL = 15          # per model x lexicon-label cell -> up to 120 items


def make():
    df = pd.read_csv(ANA / "forecasts_tidy_coded.csv")
    rng = np.random.default_rng(20260929)
    picks = []
    for model, g in df.groupby("model"):
        for lab, gg in g.groupby(g.market_odds.fillna(0).astype(int)):
            take = min(N_PER_CELL, len(gg))
            picks.append(gg.sample(take, random_state=int(rng.integers(1e6))))
    s = pd.concat(picks).sample(frac=1, random_state=7).reset_index(drop=True)
    s["item_id"] = [f"i{n:03d}" for n in range(1, len(s) + 1)]
    key = s[["item_id", "model", "match_id", "market_odds"]].rename(
        columns={"market_odds": "lexicon_cites_market"})
    out = s[["item_id", "reasoning"]].copy()
    out["reasoning"] = out.reasoning.astype(str).str.replace(r"\s+", " ", regex=True).str.slice(0, 1500)
    out["human_cites_market"] = ""
    out.to_csv(SAMPLE, index=False)
    key.to_csv(KEY, index=False)
    print(f"wrote {len(out)} items to {SAMPLE.name} (label human_cites_market with 1/0)")
    print(f"key hidden in {KEY.name} - do not open before labelling")


def score():
    s = pd.read_csv(SAMPLE)
    k = pd.read_csv(KEY)
    d = s.merge(k, on="item_id")
    d = d[d.human_cites_market.astype(str).str.strip().isin(["0", "1"])]
    if d.empty:
        raise SystemExit("no labelled rows yet")
    h = d.human_cites_market.astype(int).to_numpy()
    m = d.lexicon_cites_market.astype(int).to_numpy()
    agree = (h == m).mean()
    # Cohen's kappa
    po = agree
    pe = sum((h == v).mean() * (m == v).mean() for v in (0, 1))
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    tp = int(((h == 1) & (m == 1)).sum()); fp = int(((h == 0) & (m == 1)).sum())
    fn = int(((h == 1) & (m == 0)).sum()); tn = int(((h == 0) & (m == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    print(f"labelled items: {len(d)}")
    print(f"raw agreement: {agree:.3f}   Cohen's kappa: {kappa:.3f}")
    print(f"lexicon precision: {prec:.3f}   recall: {rec:.3f}")
    print(f"confusion (human x lexicon): tp {tp}  fp {fp}  fn {fn}  tn {tn}")
    pd.DataFrame([{"n": len(d), "agreement": round(agree, 3), "kappa": round(kappa, 3),
                   "precision": round(prec, 3), "recall": round(rec, 3),
                   "tp": tp, "fp": fp, "fn": fn, "tn": tn}]).to_csv(
        OUT / "lexicon_validation_result.csv", index=False)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "make"
    (make if cmd == "make" else score)()
