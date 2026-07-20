"""Knockout-stage forecasting metrics per model (m73-m104).

Uses the T-24h pre-match forecast. The knockout probability space is the same
3-way {team_a_win, draw, team_b_win} the models were asked for, so accuracy /
Brier / log-loss are scored against `outcome` exactly as in the group stage —
where `outcome == draw` for the four ties settled on penalties (the model's draw
bucket == "level after normal/extra time").

Added: `adv_accuracy`, a knockout-only metric — did the side the model favored
to WIN (argmax over team_a_win vs team_b_win, ignoring the draw bucket) actually
advance? This scores the thing a knockout is really about: who goes through.

No ROI here: pre-match 1X2 odds for the knockout ties have not been collected
yet (metadata/odds.csv covers only the 72 group matches). `n_bets` and
`bet_hit_rate` settle the model's own pick against the 3-way outcome and need no
odds; ROI is left for when odds_knockout.csv exists.
"""
import math
from pathlib import Path
import pandas as pd

import knockout_meta as km

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
MODELS = ["claude", "chatgpt", "gemini", "grok"]
OUTCOMES = ["team_a_win", "draw", "team_b_win"]


def onehot(o):
    return [1 if x == o else 0 for x in OUTCOMES]


def argmax_pick(p):
    return OUTCOMES[max(range(3), key=lambda i: p[i])]


def model_metrics(df):
    n = acc = brier = ll = draw_mass = adv_hit = 0
    n_bets = bet_wins = 0
    for r in df.itertuples():
        if pd.isna(r.pre_p_team_a_win):
            continue
        p = [float(r.pre_p_team_a_win), float(r.pre_p_draw), float(r.pre_p_team_b_win)]
        s = sum(p) or 1.0
        p = [x / s for x in p]
        actual = r.outcome
        oh = onehot(actual)
        n += 1
        draw_mass += p[1]
        acc += (argmax_pick(p) == actual)
        brier += sum((p[i] - oh[i]) ** 2 for i in range(3))
        ll += -math.log(min(max(p[OUTCOMES.index(actual)], 1e-6), 1.0))
        # advancement: favored side to WIN vs who actually went through
        fav = "team_a" if p[0] >= p[2] else "team_b"
        adv_hit += (fav == r.advanced)
        # bet settled against the 3-way outcome (no odds needed for hit-rate)
        if r.pre_bet_pick in OUTCOMES and float(r.pre_bet_stake_usd or 0) > 0:
            n_bets += 1
            bet_wins += (r.pre_bet_pick == actual)
    return {
        "n": n,
        "accuracy": round(acc / n, 4),
        "adv_accuracy": round(adv_hit / n, 4),
        "brier": round(brier / n, 4),
        "log_loss": round(ll / n, 4),
        "mean_draw_prob": round(draw_mass / n, 4),
        "n_bets": n_bets,
        "bet_hit_rate": round(bet_wins / n_bets, 4) if n_bets else None,
    }


def main():
    rows = {m: model_metrics(pd.read_csv(PROC / f"{m}_knockout.csv")) for m in MODELS}
    out = pd.DataFrame(rows).T
    out.index.name = "model"
    out.to_csv(PROC / "model_metrics_knockout.csv")

    n_draw = sum(km.outcome_of(mid) == "draw" for mid in km.KO_IDS)
    print(f"Knockout: {len(km.KO_IDS)} matches, "
          f"penalty ties (outcome=draw) = {n_draw}\n")
    print(out.to_string())
    return out


if __name__ == "__main__":
    main()
