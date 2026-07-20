"""Betting P&L, market baseline, and against-the-market analysis (all 104 matches).

Each model's OWN pick+stake is settled at that match's 1X2 decimal odds on the
90-minute result (so a `draw` bet wins the four penalty ties; a win bet loses
them — standard 1X2). We report:
  * per-model bankroll, ROI, hit-rate (overall + by phase)   -> "who earns most"
  * the market as a 5th forecaster (implied probs -> accuracy/Brier/log-loss)
  * CONTRARIAN behaviour: bets whose pick differs from the market's favoured
    outcome — how often each model fades the market, the edge it believed it
    had (model prob - market prob), and whether fading paid off.

Outputs -> data/analysis/.
"""
from __future__ import annotations
import math
from pathlib import Path
import pandas as pd

from analysis import load_tidy, MODELS, OUTCOMES, ANA

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
DEC = {"team_a_win": "odds_home_dec", "draw": "odds_draw_dec", "team_b_win": "odds_away_dec"}
IMP = {"team_a_win": "imp_home", "draw": "imp_draw", "team_b_win": "imp_away"}


def load_odds():
    g = pd.read_csv(META / "odds.csv")
    k = pd.read_csv(META / "odds_knockout.csv")
    return pd.concat([g, k], ignore_index=True).set_index("match_id")


def mnum(mid):
    return int(str(mid)[1:])


def build():
    df = load_tidy()
    odds = load_odds()
    df = df[df.match_id.isin(odds.index)].copy()
    for c in ["odds_home_dec", "odds_draw_dec", "odds_away_dec",
              "imp_home", "imp_draw", "imp_away"]:
        df[c] = df.match_id.map(odds[c])
    df["mnum"] = df.match_id.map(mnum)
    df["market_fav"] = df[["imp_home", "imp_draw", "imp_away"]].values.argmax(axis=1)
    df["market_fav_outcome"] = df["market_fav"].map(dict(enumerate(OUTCOMES)))

    # ---- settle each model's own bet ----
    def settle(r):
        if r.bet_pick not in DEC or not (r.bet_stake and r.bet_stake > 0):
            return pd.Series({"staked": 0.0, "profit": 0.0, "is_bet": False,
                              "win": None, "contrarian": None, "edge": None})
        dec = r[DEC[r.bet_pick]]
        stake = float(r.bet_stake)
        win = (r.bet_pick == r.outcome)
        profit = stake * (dec - 1) if win else -stake
        contrarian = (r.bet_pick != r.market_fav_outcome)
        edge = float(getattr(r, {"team_a_win": "p_a", "draw": "p_draw",
                                  "team_b_win": "p_b"}[r.bet_pick])) - float(r[IMP[r.bet_pick]])
        return pd.Series({"staked": stake, "profit": profit, "is_bet": True,
                          "win": win, "contrarian": contrarian, "edge": edge})

    settled = df.apply(settle, axis=1)
    df = pd.concat([df, settled], axis=1)

    # ---- per-model summary (overall + by phase) ----
    def summ(sub):
        b = sub[sub.is_bet]
        staked, profit = b.staked.sum(), b.profit.sum()
        return pd.Series({
            "n_bets": int(len(b)), "staked": round(staked, 0),
            "net_profit": round(profit, 2),
            "roi_pct": round(100 * profit / staked, 2) if staked else None,
            "hit_rate": round(b.win.mean(), 3) if len(b) else None,
            "mean_stake": round(b.staked.mean(), 1) if len(b) else None,
        })
    rows = []
    for m in MODELS:
        d = df[df.model == m]
        r = summ(d); r["model"] = m; r["phase"] = "all"; rows.append(r)
        for ph in ["group", "knockout"]:
            r = summ(d[d.phase == ph]); r["model"] = m; r["phase"] = ph; rows.append(r)
    bet = pd.DataFrame(rows)[["model", "phase", "n_bets", "staked", "net_profit",
                              "roi_pct", "hit_rate", "mean_stake"]]
    bet.to_csv(ANA / "betting_summary.csv", index=False)
    print("== Betting P&L (each model's own picks @ 1X2 odds) ==")
    print(bet[bet.phase == "all"].to_string(index=False))

    # ---- bankroll curve (cumulative net profit over match order) ----
    bank = {}
    for m in MODELS:
        d = df[df.model == m].sort_values("mnum")
        bank[m] = d.groupby("mnum").profit.sum().cumsum()
    bankroll = pd.DataFrame(bank).sort_index().ffill()
    bankroll.to_csv(ANA / "bankroll.csv")
    print("\nfinal bankroll (net $ from $ staked):")
    print({m: round(bankroll[m].iloc[-1], 0) for m in MODELS})

    # ---- contrarian (fade-the-market) analysis ----
    crows = []
    for m in MODELS:
        b = df[(df.model == m) & (df.is_bet)]
        con, conf = b[b.contrarian == True], b[b.contrarian == False]  # noqa: E712
        crows.append({
            "model": m,
            "n_bets": len(b),
            "n_contrarian": len(con),
            "contrarian_share": round(len(con) / len(b), 3) if len(b) else None,
            "contrarian_hit": round(con.win.mean(), 3) if len(con) else None,
            "contrarian_profit": round(con.profit.sum(), 1),
            "contrarian_roi": round(100 * con.profit.sum() / con.staked.sum(), 1) if con.staked.sum() else None,
            "conform_hit": round(conf.win.mean(), 3) if len(conf) else None,
            "conform_profit": round(conf.profit.sum(), 1),
            "mean_edge_claimed": round(b.edge.mean(), 3),
        })
    con = pd.DataFrame(crows)
    con.to_csv(ANA / "contrarian.csv", index=False)
    print("\n== Fade-the-market (contrarian) bets ==")
    print(con.to_string(index=False))

    # ---- market as a 5th forecaster ----
    mrows = []
    for ph in ["group", "knockout", "all"]:
        sub = odds if ph == "all" else odds.loc[[i for i in odds.index
                                                 if (mnum(i) <= 72) == (ph == "group")]]
        res = df.drop_duplicates("match_id").set_index("match_id")["outcome"]
        acc = brier = ll = n = draw = 0
        for mid, r in sub.iterrows():
            if mid not in res.index or pd.isna(r.imp_home):
                continue
            p = [r.imp_home, r.imp_draw, r.imp_away]
            a = res[mid]; oh = [int(o == a) for o in OUTCOMES]
            n += 1; draw += p[1]
            acc += (OUTCOMES[p.index(max(p))] == a)
            brier += sum((p[i] - oh[i]) ** 2 for i in range(3))
            ll += -math.log(min(max(p[OUTCOMES.index(a)], 1e-6), 1))
        mrows.append({"phase": ph, "n": n, "accuracy": round(acc / n, 4),
                      "brier": round(brier / n, 4), "log_loss": round(ll / n, 4),
                      "mean_draw_prob": round(draw / n, 4)})
    mkt = pd.DataFrame(mrows)
    mkt.to_csv(ANA / "market_baseline.csv", index=False)
    print("\n== Market baseline (implied probs as a forecaster) ==")
    print(mkt.to_string(index=False))

    df.to_csv(ANA / "forecasts_with_odds.csv", index=False)
    return df


if __name__ == "__main__":
    build()
