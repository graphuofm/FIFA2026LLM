"""Rebuttal analyses: bootstrap CIs, stake-controlled betting counterfactuals,
market-citation conditioning, trait stability across disjoint halves, and a
probability-aware view of the reflection task.

Run: python src/rebuttal_stats.py   ->  data/analysis/rebuttal/*.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ANA = ROOT / "data" / "analysis"
OUT = ANA / "rebuttal"
OUT.mkdir(parents=True, exist_ok=True)

MODELS = ["claude", "chatgpt", "gemini", "grok"]
OUTCOMES = ["team_a_win", "draw", "team_b_win"]
DEC = {"team_a_win": "odds_home_dec", "draw": "odds_draw_dec", "team_b_win": "odds_away_dec"}
B = 10000
rng = np.random.default_rng(20260929)


def load():
    df = pd.read_csv(ANA / "forecasts_with_odds.csv")
    coded = pd.read_csv(ANA / "forecasts_tidy_coded.csv")[["model", "match_id", "market_odds"]]
    return df.merge(coded, on=["model", "match_id"], how="left")


def per_match_scores(p3: np.ndarray, outcome_idx: np.ndarray):
    """correct / brier / logloss per row for a (n,3) probability matrix."""
    n = len(outcome_idx)
    onehot = np.zeros((n, 3))
    onehot[np.arange(n), outcome_idx] = 1
    correct = (p3.argmax(axis=1) == outcome_idx).astype(float)
    brier = ((p3 - onehot) ** 2).sum(axis=1)
    p_true = np.clip(p3[np.arange(n), outcome_idx], 1e-12, 1)
    return correct, brier, -np.log(p_true)


def ci(v, lo=2.5, hi=97.5):
    return float(np.percentile(v, lo)), float(np.percentile(v, hi))


def main():
    df = load()
    matches = sorted(df.match_id.unique())
    midx = {m: i for i, m in enumerate(matches)}
    n = len(matches)
    out_idx = np.zeros(n, dtype=int)
    for _, r in df.drop_duplicates("match_id").iterrows():
        out_idx[midx[r.match_id]] = OUTCOMES.index(r.outcome)

    # ---------- per-entity per-match score arrays ----------
    ent = {}
    for m in MODELS:
        d = df[df.model == m].set_index("match_id").loc[matches]
        p3 = d[["p_a", "p_draw", "p_b"]].to_numpy()
        ent[m] = per_match_scores(p3, out_idx)
    mk = df.drop_duplicates("match_id").set_index("match_id").loc[matches]
    ent["market"] = per_match_scores(mk[["imp_home", "imp_draw", "imp_away"]].to_numpy(), out_idx)

    boot = rng.integers(0, n, size=(B, n))

    # ---------- 1. bootstrap CIs for accuracy / brier / logloss ----------
    rows, dist = [], {}
    for name, (c, b, l) in ent.items():
        for metric, arr in (("accuracy", c), ("brier", b), ("log_loss", l)):
            bs = arr[boot].mean(axis=1)
            dist[(name, metric)] = bs
            lo, hi = ci(bs)
            rows.append({"entity": name, "metric": metric, "value": round(arr.mean(), 4),
                         "ci95_lo": round(lo, 4), "ci95_hi": round(hi, 4)})
    pd.DataFrame(rows).to_csv(OUT / "bootstrap_metrics.csv", index=False)

    # ---------- 2. paired differences (every pair, both directions handled once) ----------
    drows = []
    names = MODELS + ["market"]
    for metric in ("accuracy", "brier", "log_loss"):
        for i, a in enumerate(names):
            for b_ in names[i + 1:]:
                d = dist[(a, metric)] - dist[(b_, metric)]
                lo, hi = ci(d)
                # two-sided bootstrap p: how often the difference changes sign
                p = 2 * min((d <= 0).mean(), (d >= 0).mean())
                drows.append({"metric": metric, "a": a, "b": b_,
                              "diff_a_minus_b": round(float(d.mean()), 4),
                              "ci95_lo": round(lo, 4), "ci95_hi": round(hi, 4),
                              "boot_p": round(float(min(p, 1.0)), 3),
                              "significant_at_05": bool(lo > 0 or hi < 0)})
    pd.DataFrame(drows).to_csv(OUT / "bootstrap_pairwise.csv", index=False)

    # ---------- 3. betting: actual vs stake-controlled counterfactuals ----------
    brows = []
    for m in MODELS:
        d = df[df.model == m].set_index("match_id").loc[matches]
        staked = d.staked.fillna(0).to_numpy()
        profit = d.profit.fillna(0).to_numpy()
        is_bet = d.is_bet.fillna(False).to_numpy().astype(bool)
        win = d.win.fillna(False).to_numpy().astype(bool)
        dec_pick = np.array([r[DEC[r.bet_pick]] if r.bet_pick in DEC else np.nan
                             for _, r in d.iterrows()], dtype=float)
        # (a) flat $100 on the same bets it actually placed -> removes stake sizing
        flat = np.where(is_bet, np.where(win, 100 * (dec_pick - 1), -100.0), 0.0)
        flat_staked = np.where(is_bet, 100.0, 0.0)
        # (b) flat $100 on its argmax in every match -> also removes bet selection
        dec_arg = np.array([r[DEC[r.pick_outcome]] for _, r in d.iterrows()], dtype=float)
        arg_win = (d.pick_outcome.to_numpy() == np.array([OUTCOMES[i] for i in out_idx]))
        always = np.where(arg_win, 100 * (dec_arg - 1), -100.0)

        def roi_ci(pr, st):
            num = pr[boot].sum(axis=1)
            den = st[boot].sum(axis=1)
            r = 100 * num / np.where(den == 0, np.nan, den)
            return round(float(100 * pr.sum() / st.sum()), 2), *[round(x, 2) for x in ci(r)]

        a_roi, a_lo, a_hi = roi_ci(profit, staked)
        f_roi, f_lo, f_hi = roi_ci(flat, flat_staked)
        w_roi, w_lo, w_hi = roi_ci(always, np.full(n, 100.0))
        brows.append({"model": m, "n_bets": int(is_bet.sum()),
                      "actual_profit": round(profit.sum(), 2), "actual_roi": a_roi,
                      "actual_roi_ci_lo": a_lo, "actual_roi_ci_hi": a_hi,
                      "flatstake_profit": round(flat.sum(), 2), "flatstake_roi": f_roi,
                      "flatstake_roi_ci_lo": f_lo, "flatstake_roi_ci_hi": f_hi,
                      "argmax_always_profit": round(always.sum(), 2), "argmax_always_roi": w_roi,
                      "argmax_always_ci_lo": w_lo, "argmax_always_ci_hi": w_hi})
    # market favourite flat baseline
    mk_dec = np.array([r[DEC[r.market_fav_outcome]] for _, r in mk.iterrows()], dtype=float)
    mk_win = (mk.market_fav_outcome.to_numpy() == np.array([OUTCOMES[i] for i in out_idx]))
    mk_pr = np.where(mk_win, 100 * (mk_dec - 1), -100.0)
    num = mk_pr[boot].sum(axis=1)
    lo, hi = ci(100 * num / (100.0 * n))
    brows.append({"model": "market_favourite_flat", "n_bets": n,
                  "actual_profit": round(mk_pr.sum(), 2),
                  "actual_roi": round(float(100 * mk_pr.sum() / (100.0 * n)), 2),
                  "actual_roi_ci_lo": round(lo, 2), "actual_roi_ci_hi": round(hi, 2)})
    pd.DataFrame(brows).to_csv(OUT / "betting_counterfactuals.csv", index=False)

    # ---------- 4. does citing the market explain the convergence? ----------
    crows = []
    for m in MODELS:
        d = df[df.model == m].copy()
        d["agrees_with_market"] = d.pick_outcome == d.market_fav_outcome
        for cited, g in d.groupby(d.market_odds.fillna(0).astype(int)):
            p3 = g[["p_a", "p_draw", "p_b"]].to_numpy()
            oi = np.array([OUTCOMES.index(o) for o in g.outcome])
            c, b, l = per_match_scores(p3, oi)
            crows.append({"model": m, "cites_market": bool(cited), "n": len(g),
                          "accuracy": round(c.mean(), 3), "brier": round(b.mean(), 4),
                          "agrees_with_market_fav": round(g.agrees_with_market.mean(), 3),
                          "corr_p_a_vs_market": round(float(np.corrcoef(g.p_a, g.imp_home)[0, 1]), 3)})
    pd.DataFrame(crows).to_csv(OUT / "market_citation_conditional.csv", index=False)

    # ---------- 5. are the behavioural traits stable across disjoint halves? ----------
    srows = []
    for m in MODELS:
        for phase in ("group", "knockout"):
            d = df[(df.model == m) & (df.phase == phase)]
            bets = d[d.is_bet.fillna(False).astype(bool)]
            wrong = d[~d.correct.astype(bool)]
            srows.append({"model": m, "phase": phase, "n": len(d),
                          "accuracy": round(d.correct.astype(bool).mean(), 3),
                          "bet_rate": round(len(bets) / len(d), 3),
                          "mean_stake": round(bets.staked.mean(), 1) if len(bets) else None,
                          "contrarian_share": round(bets.contrarian.astype(bool).mean(), 3) if len(bets) else None,
                          "cites_market": round(d.market_odds.fillna(0).astype(int).mean(), 3),
                          "own_error_rate": round((wrong.refl_outcome == "incorrect").mean(), 3) if len(wrong) else None})
    st = pd.DataFrame(srows)
    st.to_csv(OUT / "trait_stability_group_vs_knockout.csv", index=False)

    # ---------- 6. reflection: is the self-label probability-aware? ----------
    rrows = []
    for m in MODELS:
        d = df[(df.model == m) & (~df.correct.astype(bool))]
        for lab in ("incorrect", "partially_correct", "correct"):
            g = d[d.refl_outcome == lab]
            if len(g):
                rrows.append({"model": m, "self_label_on_wrong_pick": lab, "n": len(g),
                              "mean_p_on_true_outcome": round(g.p_actual.mean(), 3),
                              "mean_p_on_its_pick": round(g[["p_a", "p_draw", "p_b"]].max(axis=1).mean(), 3)})
        # near-misses: did it hedge? admission rate when it gave the true outcome >=30%
        hi_p = d[d.p_actual >= 0.30]
        lo_p = d[d.p_actual < 0.30]
        rrows.append({"model": m, "self_label_on_wrong_pick": "ADMIT_RATE p_true>=0.30",
                      "n": len(hi_p),
                      "mean_p_on_true_outcome": round((hi_p.refl_outcome == "incorrect").mean(), 3) if len(hi_p) else None,
                      "mean_p_on_its_pick": None})
        rrows.append({"model": m, "self_label_on_wrong_pick": "ADMIT_RATE p_true<0.30",
                      "n": len(lo_p),
                      "mean_p_on_true_outcome": round((lo_p.refl_outcome == "incorrect").mean(), 3) if len(lo_p) else None,
                      "mean_p_on_its_pick": None})
    pd.DataFrame(rrows).to_csv(OUT / "reflection_probability_aware.csv", index=False)

    # ---------- 7. behavioural rates: precision of the traits that DO separate ----------
    # bootstrap over matches so the rates are comparable with the metric CIs above
    trait_arr, trrows = {}, []
    for m in MODELS:
        d = df[df.model == m].set_index("match_id").loc[matches]
        is_bet = d.is_bet.fillna(False).to_numpy().astype(float)
        contr = (d.contrarian.fillna(False).to_numpy().astype(float)) * is_bet
        cites = d.market_odds.fillna(0).to_numpy().astype(float)
        wrong = (~d.correct.astype(bool)).to_numpy().astype(float)
        admit = ((d.refl_outcome == "incorrect").to_numpy().astype(float)) * wrong
        trait_arr[m] = {"bet_rate": (is_bet, np.ones(n)),
                        "contrarian_share": (contr, is_bet),
                        "cites_market": (cites, np.ones(n)),
                        "own_error_rate": (admit, wrong)}
        for t, (num, den) in trait_arr[m].items():
            bs = num[boot].sum(axis=1) / np.where(den[boot].sum(axis=1) == 0, np.nan,
                                                  den[boot].sum(axis=1))
            lo, hi = ci(bs)
            trrows.append({"model": m, "trait": t,
                           "value": round(float(num.sum() / den.sum()), 3),
                           "ci95_lo": round(lo, 3), "ci95_hi": round(hi, 3)})
    pd.DataFrame(trrows).to_csv(OUT / "trait_rates_ci.csv", index=False)

    # pairwise: which behavioural differences (and ROI gaps) survive resampling?
    prows = []
    for t in ("bet_rate", "contrarian_share", "cites_market", "own_error_rate"):
        for i, a in enumerate(MODELS):
            for b_ in MODELS[i + 1:]:
                da = trait_arr[a][t]
                db = trait_arr[b_][t]
                ra = da[0][boot].sum(axis=1) / np.where(da[1][boot].sum(axis=1) == 0, np.nan, da[1][boot].sum(axis=1))
                rb = db[0][boot].sum(axis=1) / np.where(db[1][boot].sum(axis=1) == 0, np.nan, db[1][boot].sum(axis=1))
                d = ra - rb
                lo, hi = ci(d[~np.isnan(d)])
                prows.append({"quantity": t, "a": a, "b": b_,
                              "diff": round(float(np.nanmean(d)), 3),
                              "ci95_lo": round(lo, 3), "ci95_hi": round(hi, 3),
                              "significant_at_05": bool(lo > 0 or hi < 0)})
    # ROI pairwise
    roi_d = {}
    for m in MODELS:
        d = df[df.model == m].set_index("match_id").loc[matches]
        pr = d.profit.fillna(0).to_numpy()
        stk = d.staked.fillna(0).to_numpy()
        roi_d[m] = 100 * pr[boot].sum(axis=1) / np.where(stk[boot].sum(axis=1) == 0, np.nan, stk[boot].sum(axis=1))
    for i, a in enumerate(MODELS):
        for b_ in MODELS[i + 1:]:
            d = roi_d[a] - roi_d[b_]
            lo, hi = ci(d[~np.isnan(d)])
            prows.append({"quantity": "roi_pct", "a": a, "b": b_,
                          "diff": round(float(np.nanmean(d)), 2),
                          "ci95_lo": round(lo, 2), "ci95_hi": round(hi, 2),
                          "significant_at_05": bool(lo > 0 or hi < 0)})
    pd.DataFrame(prows).to_csv(OUT / "trait_pairwise.csv", index=False)

    # ---------- 8. does the vig-removal choice change the market baseline? ----------
    # stored implied probs use proportional normalisation; compare with the power
    # method (p_i proportional to (1/o_i)^k, k solved so the three sum to 1)
    dec = mk[["odds_home_dec", "odds_draw_dec", "odds_away_dec"]].to_numpy()
    raw = 1.0 / dec
    prop = raw / raw.sum(axis=1, keepdims=True)

    def power_devig(row, lo=0.5, hi=1.5, iters=60):
        for _ in range(iters):
            k = (lo + hi) / 2
            s = (row ** k).sum()
            if s > 1:
                lo = k
            else:
                hi = k
        k = (lo + hi) / 2
        return row ** k

    powr = np.vstack([power_devig(r) for r in raw])
    vrows = []
    for label, P in (("proportional (used in paper)", prop), ("power method", powr)):
        c, b, l = per_match_scores(P, out_idx)
        vrows.append({"devig_method": label, "accuracy": round(c.mean(), 4),
                      "brier": round(b.mean(), 4), "log_loss": round(l.mean(), 4),
                      "mean_overround": round(float(raw.sum(axis=1).mean()), 4),
                      "max_abs_prob_shift_vs_proportional": round(float(np.abs(P - prop).max()), 4)})
    pd.DataFrame(vrows).to_csv(OUT / "devig_robustness.csv", index=False)

    # ---------- console summary ----------
    bm = pd.read_csv(OUT / "bootstrap_metrics.csv")
    print("\n== 1. metrics with 95% bootstrap CIs ==")
    print(bm.pivot(index="entity", columns="metric", values=["value", "ci95_lo", "ci95_hi"]).to_string())
    pw = pd.read_csv(OUT / "bootstrap_pairwise.csv")
    print("\n== 2. differences that ARE significant at 95% ==")
    sig = pw[pw.significant_at_05]
    print(sig.to_string(index=False) if len(sig) else "  none")
    print(f"  ({len(pw) - len(sig)} of {len(pw)} pairwise comparisons are NOT significant)")
    print("\n== 3. betting with stake sizing removed ==")
    print(pd.read_csv(OUT / "betting_counterfactuals.csv").to_string(index=False))
    print("\n== 4. conditioning on whether the forecast cites the market ==")
    print(pd.read_csv(OUT / "market_citation_conditional.csv").to_string(index=False))
    print("\n== 5. trait stability, group vs knockout (disjoint halves) ==")
    print(st.to_string(index=False))
    print("\n== 6. reflection vs the probability it gave the true outcome ==")
    print(pd.read_csv(OUT / "reflection_probability_aware.csv").to_string(index=False))
    print("\n== 7. behavioural traits with 95% CIs ==")
    print(pd.read_csv(OUT / "trait_rates_ci.csv").to_string(index=False))
    tp = pd.read_csv(OUT / "trait_pairwise.csv")
    sig = tp[tp.significant_at_05]
    print(f"\n== 7b. pairwise: {len(sig)} of {len(tp)} behavioural/ROI differences ARE significant ==")
    print(sig.to_string(index=False))
    print("\n   NOT significant:")
    print(tp[~tp.significant_at_05].to_string(index=False))


if __name__ == "__main__":
    main()
