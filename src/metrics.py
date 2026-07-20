"""Compute forecasting metrics per model (+ a market baseline) and surface
interesting findings. Uses the T-24h pre-match forecast for every match.

Metrics per model:
  accuracy   : argmax(prob) == actual outcome
  brier      : sum_i (p_i - o_i)^2  (multiclass, 0..2)
  log_loss   : -log(p_actual), clipped
  roi        : profit / total_staked, settling pre_bet_pick at market odds
Also: market baseline from the vig-removed implied probabilities in odds.csv.
"""
import math
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
META, PROC = ROOT / "data" / "metadata", ROOT / "data" / "processed"
MODELS = ["claude", "chatgpt", "gemini", "grok"]
OUTCOMES = ["team_a_win", "draw", "team_b_win"]


def load():
    res = pd.read_csv(META / "results.csv").set_index("match_id")
    odds = pd.read_csv(META / "odds.csv").set_index("match_id")
    frames = {m: pd.read_csv(PROC / f"{m}.csv").set_index("match_id") for m in MODELS}
    return res, odds, frames


def onehot(outcome):
    return [1 if o == outcome else 0 for o in OUTCOMES]


def argmax_pick(p):
    return OUTCOMES[max(range(3), key=lambda i: p[i])]


def model_metrics(df, res, odds):
    rows_acc = rows_brier = rows_ll = 0
    n = 0
    staked = profit = n_bets = bet_wins = 0.0
    dec_cols = {"team_a_win": "odds_home_dec", "draw": "odds_draw_dec",
                "team_b_win": "odds_away_dec"}
    draw_prob_sum = 0.0
    for mid, r in df.iterrows():
        if pd.isna(r.pre_p_team_a_win):
            continue
        p = [float(r.pre_p_team_a_win), float(r.pre_p_draw), float(r.pre_p_team_b_win)]
        s = sum(p) or 1.0
        p = [x / s for x in p]
        actual = res.loc[mid, "outcome"]
        oh = onehot(actual)
        n += 1
        draw_prob_sum += p[1]
        rows_acc += (argmax_pick(p) == actual)
        rows_brier += sum((p[i] - oh[i]) ** 2 for i in range(3))
        pa = min(max(p[OUTCOMES.index(actual)], 1e-6), 1.0)
        rows_ll += -math.log(pa)
        # betting
        pick = r.pre_bet_pick
        stake = float(r.pre_bet_stake_usd or 0)
        if pick in dec_cols and stake > 0:
            dec = odds.loc[mid, dec_cols[pick]]
            if pd.notna(dec):
                staked += stake
                n_bets += 1
                if pick == actual:
                    profit += stake * (float(dec) - 1)
                    bet_wins += 1
                else:
                    profit -= stake
    return {
        "n": n,
        "accuracy": round(rows_acc / n, 4),
        "brier": round(rows_brier / n, 4),
        "log_loss": round(rows_ll / n, 4),
        "mean_draw_prob": round(draw_prob_sum / n, 4),
        "n_bets": int(n_bets),
        "total_staked": round(staked, 0),
        "net_profit": round(profit, 2),
        "roi_pct": round(100 * profit / staked, 2) if staked else None,
        "bet_hit_rate": round(bet_wins / n_bets, 4) if n_bets else None,
    }


def market_metrics(odds, res):
    acc = brier = ll = n = draw = 0
    for mid, r in odds.iterrows():
        if pd.isna(r.imp_home):
            continue
        p = [float(r.imp_home), float(r.imp_draw), float(r.imp_away)]
        actual = res.loc[mid, "outcome"]
        oh = onehot(actual)
        n += 1
        draw += p[1]
        acc += (argmax_pick(p) == actual)
        brier += sum((p[i] - oh[i]) ** 2 for i in range(3))
        ll += -math.log(min(max(p[OUTCOMES.index(actual)], 1e-6), 1.0))
    return {"n": n, "accuracy": round(acc / n, 4), "brier": round(brier / n, 4),
            "log_loss": round(ll / n, 4), "mean_draw_prob": round(draw / n, 4),
            "n_bets": None, "total_staked": None, "net_profit": None,
            "roi_pct": None, "bet_hit_rate": None}


def main():
    res, odds, frames = load()
    rows = {}
    for m in MODELS:
        rows[m] = model_metrics(frames[m], res, odds)
    rows["market"] = market_metrics(odds, res)
    out = pd.DataFrame(rows).T
    out.index.name = "model"
    out.to_csv(META.parent / "processed" / "model_metrics.csv")

    # context
    n_draw = (res.outcome == "draw").sum()
    print(f"Group stage: {len(res)} matches, actual draws = {n_draw} "
          f"({100*n_draw/len(res):.0f}%)\n")
    cols = ["n", "accuracy", "brier", "log_loss", "mean_draw_prob",
            "n_bets", "total_staked", "net_profit", "roi_pct", "bet_hit_rate"]
    print(out[cols].to_string())
    return out


if __name__ == "__main__":
    main()
