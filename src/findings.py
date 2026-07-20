"""Dig into the interesting behavioural findings behind the headline metrics."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
META, PROC = ROOT / "data" / "metadata", ROOT / "data" / "processed"
MODELS = ["claude", "chatgpt", "gemini", "grok"]
OUT = ["team_a_win", "draw", "team_b_win"]
DEC = {"team_a_win": "odds_home_dec", "draw": "odds_draw_dec", "team_b_win": "odds_away_dec"}

res = pd.read_csv(META / "results.csv").set_index("match_id")
odds = pd.read_csv(META / "odds.csv").set_index("match_id")


def argmax(r):
    p = [r.pre_p_team_a_win, r.pre_p_draw, r.pre_p_team_b_win]
    return OUT[max(range(3), key=lambda i: p[i])]


print("=" * 66)
print("DRAW BLINDNESS  (20/72 = 28% of matches were draws)")
print("=" * 66)
for m in MODELS:
    df = pd.read_csv(PROC / f"{m}.csv").set_index("match_id")
    df = df[df.pre_p_team_a_win.notna()]
    df["amax"] = df.apply(argmax, axis=1)
    picked_draw = (df.amax == "draw").sum()
    draws = res.loc[df.index, "outcome"] == "draw"
    # of the actual draws, how many did the model's argmax call?
    hit_draws = ((df.amax == "draw") & draws.values).sum()
    print(f"  {m:8s}: argmax=draw on {picked_draw:2d}/72 matches; "
          f"caught {hit_draws}/{draws.sum()} actual draws")

print("\n" + "=" * 66)
print("BETTING BEHAVIOUR: back your own favourite, or hunt 'value'?")
print("=" * 66)
for m in MODELS:
    df = pd.read_csv(PROC / f"{m}.csv").set_index("match_id")
    df = df[df.pre_p_team_a_win.notna()]
    df["amax"] = df.apply(argmax, axis=1)
    bets = df[(df.pre_bet_pick.isin(OUT)) & (df.pre_bet_stake_usd > 0)]
    fav = bets[bets.pre_bet_pick == bets.amax]          # backed own top pick
    con = bets[bets.pre_bet_pick != bets.amax]          # contrarian / value

    def pnl(sub):
        prof = st = 0.0
        wins = 0
        for mid, r in sub.iterrows():
            dec = odds.loc[mid, DEC[r.pre_bet_pick]]
            st += r.pre_bet_stake_usd
            if r.pre_bet_pick == res.loc[mid, "outcome"]:
                prof += r.pre_bet_stake_usd * (dec - 1); wins += 1
            else:
                prof -= r.pre_bet_stake_usd
        return len(sub), st, prof, (wins / len(sub) if len(sub) else 0)

    nb, stall, prall, _ = pnl(bets)
    nf, stf, prf, hf = pnl(fav)
    nc, stc, prc, hc = pnl(con)
    print(f"\n  {m}: {nb} bets, avg stake ${stall/nb:.0f}")
    print(f"     back-favourite : {nf:2d} bets, hit {hf:4.0%}, P&L ${prf:+.0f}")
    print(f"     contrarian/value: {nc:2d} bets, hit {hc:4.0%}, P&L ${prc:+.0f}")

print("\n" + "=" * 66)
print("CALIBRATION: when a model says X%, does X% happen? (by top-pick conf)")
print("=" * 66)
bins = [(0.33, 0.5), (0.5, 0.65), (0.65, 0.8), (0.8, 1.01)]
for m in MODELS:
    df = pd.read_csv(PROC / f"{m}.csv").set_index("match_id")
    df = df[df.pre_p_team_a_win.notna()]
    df["amax"] = df.apply(argmax, axis=1)
    df["conf"] = df[["pre_p_team_a_win", "pre_p_draw", "pre_p_team_b_win"]].max(axis=1)
    df["hit"] = [row.amax == res.loc[mid, "outcome"] for mid, row in df.iterrows()]
    print(f"  {m}:")
    for lo, hi in bins:
        b = df[(df.conf >= lo) & (df.conf < hi)]
        if len(b):
            print(f"     conf {lo:.2f}-{hi:.2f}: n={len(b):2d}  "
                  f"avg_pred={b.conf.mean():.2f}  actual={b.hit.mean():.2f}")

print("\n" + "=" * 66)
print("SELF-AWARENESS: post-match reflection distributions")
print("=" * 66)
for m in MODELS:
    df = pd.read_csv(PROC / f"{m}.csv").set_index("match_id")
    df = df[df.refl_outcome_vs_prediction.notna()]
    oc = df.refl_outcome_vs_prediction.value_counts().to_dict()
    luck = df.refl_luck.value_counts().to_dict()
    calib = df.refl_was_well_calibrated
    # does self-rated "well calibrated" line up with being right?
    print(f"  {m:8s} (n={len(df)}): outcome_self={oc}")
    print(f"           luck={luck}  said_well_calibrated={calib.sum()}/{len(df)}  "
          f"mean_confidence={df.refl_confidence.mean():.2f}")
