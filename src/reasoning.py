"""Content coding of the models' free-text reasoning and reflections.

We code every pre-match `reasoning` string into a fixed set of FACTOR categories
with a transparent keyword lexicon (documented below, reproducible — no LLM in
the loop), then:
  * frequency of each factor per model  -> "what the AI cares about"
  * does mentioning a factor associate with being correct?
  * MARKET ENGAGEMENT: how often each model explicitly cites the betting
    market / odds, and — the question the user cares about — when a model bets
    AGAINST the market favorite, what does it cite instead and does it pay off?
And we mine the post-match reflections (`key_factor_i_missed` /
`_overweighted`) for the recurring blind-spots that become candidate future
features.

Outputs -> data/analysis/.
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

from analysis import load_tidy, MODELS, ANA

# --- factor lexicon: category -> regex (case-insensitive, word-ish) ----------
LEX = {
    "market_odds":        r"market|moneyline|money line|odds|implied|de-?vig|vig|kalshi|bookmak|sportsbook|price[ds]?|opta|supercomputer|fanduel|bet365|\b[-+]\d{3}\b",
    "squad_depth_quality":r"squad depth|depth|quality|talent|deeper|roster|superior side|stronger side|class\b",
    "star_player":        r"star|world-class|messi|mbapp|haaland|kane|bellingham|yamal|vin[ií]cius|de bruyne|lukaku|salah|ødegaard|david\b|hakimi|individual",
    "form_momentum":      r"\bform\b|unbeaten|momentum|recent|streak|\brun\b|in-form",
    "fifa_ranking":       r"ranking|ranked|fifa #|\bfifa\b.{0,6}rank",
    "injuries_susp":      r"injur|doubt|suspen|absence|absent|fitness|\bout\b|miss(?:ing|es)|hamstring",
    "head_to_head":       r"h2h|head-to-head|historical|history|all-time|meeting|rivalry|previous",
    "home_altitude":      r"\bhome\b|host|altitude|crowd|azteca|diaspora|neutral venue",
    "defense_organized":  r"defensiv|defen[cs]e|organi[sz]ed|low block|compact|clean sheet|resilien|disciplin|solid",
    "attack_threat":      r"attack|firepower|scoring|goal-?scoring|\bgoals\b|pace|transition|overload|creativ",
    "experience_motiv":   r"knockout experience|experience|motivation|pedigree|big-game|big game|tournament experience|champion",
    "fatigue_rest":       r"fatigue|\brest\b|short rest|120-?minute|recovery|rotation|tired|congest",
    "variance_penalty":   r"penalt|shootout|coin-?flip|variance|lottery|low-scoring|tight|nervy|margin",
}
FACTORS = list(LEX)
LEX_RE = {k: re.compile(v, re.I) for k, v in LEX.items()}


def code_factors(text: str):
    t = str(text or "")
    return {f: bool(LEX_RE[f].search(t)) for f in FACTORS}


def build():
    df = load_tidy()
    # code each reasoning
    codes = df.reasoning.apply(lambda t: pd.Series(code_factors(t)))
    dfx = pd.concat([df.reset_index(drop=True), codes], axis=1)

    # 1) factor frequency per model + overall
    freq = dfx.groupby("model")[FACTORS].mean().round(3)
    freq.loc["ALL"] = dfx[FACTORS].mean().round(3)
    freq.T.to_csv(ANA / "factor_frequency.csv")
    print("== Factor mention rate (share of forecasts) ==")
    print(freq.T.sort_values("ALL", ascending=False).to_string())

    # 2) factor -> correctness association (overall)
    assoc = []
    base = dfx.correct.mean()
    for f in FACTORS:
        sub = dfx[dfx[f]]
        assoc.append({"factor": f, "mention_rate": round(dfx[f].mean(), 3),
                      "acc_when_mentioned": round(sub.correct.mean(), 3),
                      "acc_lift_vs_base": round(sub.correct.mean() - base, 3)})
    pd.DataFrame(assoc).sort_values("mention_rate", ascending=False).to_csv(
        ANA / "factor_correctness.csv", index=False)

    # 3) market engagement + contrarian behaviour (needs no odds: 'contrarian'
    #    here = model's argmax disagrees with the side it says the market favors
    #    is hard without odds; instead we log market-citation rate and the
    #    bet-vs-argmax, leaving odds-based contrarian to betting.py)
    mkt = dfx.groupby("model")["market_odds"].mean().round(3)
    print("\n== Market/odds citation rate ==")
    print(mkt.to_string())

    # 4) reflection blind-spots: code key_factor_i_missed / _overweighted
    for col, out in [("refl_missed", "reflection_missed_factors.csv"),
                     ("refl_overweighted", "reflection_overweighted_factors.csv")]:
        rc = df[col].apply(lambda t: pd.Series(code_factors(t)))
        rcx = pd.concat([df[["model", "phase", "correct"]].reset_index(drop=True), rc], axis=1)
        # focus on WRONG predictions (where a real lesson exists)
        wrong = rcx[~rcx.correct]
        tab = wrong[FACTORS].mean().round(3).sort_values(ascending=False)
        tab.to_csv(ANA / out, header=["rate_among_wrong"])
        print(f"\n== Top {col} factors (among wrong preds) ==")
        print(tab.head(6).to_string())

    dfx.to_csv(ANA / "forecasts_tidy_coded.csv", index=False)
    return dfx


if __name__ == "__main__":
    build()
