"""End-to-end builder for the World Cup 2026 LLM forecasting dataset.

Outputs (all under data/):
  metadata/schedule.csv          canonical 72-match group-stage schedule
  metadata/results.csv           final scores (cross-model consensus)
  processed/all_forecasts.csv    one row per (match, model, prompt_type)
  processed/parse_errors.csv     responses that looked real but failed json.loads
  processed/missing_data.csv     (match, model) cells with a missing prompt
  processed/forecasts_with_truth.csv   forecasts joined to ground truth
"""
from __future__ import annotations
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

import parse_core as pc
import schedule as sch

MODELS = ["claude", "chatgpt", "gemini", "grok"]
ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
PROC = ROOT / "data" / "processed"

COMPACT_START = re.compile(r"\b\d{2}-\d{2}\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+[A-L]\s")
FIFA_START = re.compile(
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+June\s+2026"
)
_MDLINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def strip_md(s: str) -> str:
    return _MDLINK.sub(r"\1", s)


# --------------------------------------------------------------------------- #
# 1. segment a file into ordered per-match blocks
# --------------------------------------------------------------------------- #
def reflection_ends(block: str):
    ends = []
    for st, en, o in pc.iter_top_objects(block):
        if pc.POST_KEY in o and not pc.is_template(o, pc.POST_TEMPLATE_SIGS):
            if pc._try(o)[0] is not None:
                ends.append(en)
    return ends


def segment(text: str):
    """Return ordered list of match-block strings."""
    bounds = sorted({m.start() for m in COMPACT_START.finditer(text)}
                    | {m.start() for m in FIFA_START.finditer(text)})
    coarse = []
    if not bounds or bounds[0] > 0:
        head = text[: bounds[0]] if bounds else text
        if head.strip():
            coarse.append(head)
    for i, pos in enumerate(bounds):
        end = bounds[i + 1] if i + 1 < len(bounds) else len(text)
        coarse.append(text[pos:end])

    blocks = []
    for block in coarse:
        ends = reflection_ends(block)
        if len(ends) <= 1:
            blocks.append(block)
        else:  # >1 completed match glued together (a header was missing)
            prev = 0
            for en in ends:
                blocks.append(block[prev:en])
                prev = en
            if block[prev:].strip():
                blocks[-1] += block[prev:]
    return blocks


def block_teams(block: str):
    """(team_a, team_b) for a block: prefer the pasted score block, else header."""
    sb = pc.extract_score_block(block)
    if sb:
        return sb[0], sb[1]
    header = strip_md(re.split(r"You are participating", block, maxsplit=1)[0])
    parsed = sch.parse_header(header)
    if parsed:
        return parsed["team_a"], parsed["team_b"]
    return None, None


# --------------------------------------------------------------------------- #
# 2. canonical schedule (from grok headers)
# --------------------------------------------------------------------------- #
def build_schedule():
    text = pc.read("grok")
    rows = []
    for block in segment(text):
        header = strip_md(re.split(r"You are participating", block, maxsplit=1)[0])
        info = sch.parse_header(header)
        if info:
            rows.append(info)
    df = pd.DataFrame(rows).drop_duplicates(subset=["team_a", "team_b"])
    df = df.reset_index(drop=True)
    df.insert(0, "match_id", [f"m{i+1:02d}" for i in range(len(df))])
    df["stage"] = "group"
    df["key"] = [frozenset((sch.norm_team(a), sch.norm_team(b)))
                 for a, b in zip(df.team_a, df.team_b)]
    return df


# --------------------------------------------------------------------------- #
# 3. per-model extraction aligned to schedule
# --------------------------------------------------------------------------- #
def prob_fields(j):
    p = (j or {}).get("probabilities", {}) or {}
    b = (j or {}).get("bet", {}) or {}
    return {
        "p_team_a_win": p.get("team_a_win"),
        "p_draw": p.get("draw"),
        "p_team_b_win": p.get("team_b_win"),
        "bet_pick": b.get("pick"),
        "bet_stake_usd": b.get("stake_usd"),
        "reasoning": (j or {}).get("reasoning"),
        "key_sources": " | ".join((j or {}).get("key_sources", []) or []),
    }


def refl_fields(j):
    j = j or {}
    keys = ["outcome_vs_prediction", "was_my_forecast_well_calibrated",
            "did_i_get_lucky_or_unlucky", "key_factor_i_missed",
            "key_factor_i_overweighted", "counterfactual",
            "would_i_bet_differently_now", "confidence_in_this_reflection"]
    return {k: j.get(k) for k in keys}


def build():
    META.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)

    sched = build_schedule()
    key_to_id = dict(zip(sched.key, sched.match_id))
    id_to_teams = {r.match_id: (r.team_a, r.team_b) for r in sched.itertuples()}

    forecast_rows, error_rows, missing_rows = [], [], []
    score_votes = defaultdict(list)  # match_id -> [(sa, sb), ...]
    unmatched = []

    for model in MODELS:
        text = pc.read(model)
        for order, block in enumerate(segment(text)):
            ta, tb = block_teams(block)
            if not ta:
                unmatched.append((model, order, "no teams"))
                continue
            key = frozenset((sch.norm_team(ta), sch.norm_team(tb)))
            mid = key_to_id.get(key)
            if mid is None:
                unmatched.append((model, order, f"{ta} vs {tb}"))
                continue
            cta, ctb = id_to_teams[mid]
            reversed_ = sch.norm_team(ta) != sch.norm_team(cta)

            resp, errs = pc.extract_responses(block)

            # score vote (orient to canonical team_a)
            sb = pc.extract_score_block(block)
            if sb:
                sa, sbv = sb[2], sb[3]
                if reversed_:
                    sa, sbv = sbv, sa
                score_votes[mid].append((sa, sbv))

            # emit forecast rows for pre / t30 / post
            for ptype, slot in [("pre_match", resp["pre"]),
                                ("pre_match_30min", resp["t30"]),
                                ("post_match", resp["post"])]:
                if slot is None:
                    if ptype != "pre_match_30min":  # t30 legitimately absent
                        missing_rows.append(
                            {"match_id": mid, "model": model, "prompt_type": ptype})
                    continue
                base = {"match_id": mid, "model": model, "prompt_type": ptype,
                        "team_a": cta, "team_b": ctb}
                if slot["json"] is None:
                    error_rows.append({**base, "issue": slot["error"],
                                       "raw_response": slot["raw"]})
                    forecast_rows.append({**base, "parse_ok": False,
                                          "raw_response": slot["raw"]})
                    continue
                j = slot["json"]
                extra = prob_fields(j) if ptype != "post_match" else refl_fields(j)
                if reversed_ and ptype != "post_match":
                    extra["p_team_a_win"], extra["p_team_b_win"] = (
                        extra["p_team_b_win"], extra["p_team_a_win"])
                forecast_rows.append({**base, "parse_ok": True, **extra,
                                      "raw_response": slot["raw"]})

    # ---- results.csv (consensus) ----
    res_rows = []
    for mid in sched.match_id:
        votes = score_votes.get(mid, [])
        if not votes:
            res_rows.append({"match_id": mid, "final_score_a": None,
                             "final_score_b": None, "outcome": None,
                             "n_sources": 0, "agreement": None})
            continue
        top, n = Counter(votes).most_common(1)[0]
        sa, sb = top
        outcome = ("home_win" if sa > sb else "away_win" if sb > sa else "draw")
        res_rows.append({"match_id": mid, "final_score_a": sa, "final_score_b": sb,
                         "outcome": outcome, "n_sources": len(votes),
                         "agreement": f"{n}/{len(votes)}"})
    results = pd.DataFrame(res_rows)

    # ---- write everything ----
    sched.drop(columns=["key"]).to_csv(META / "schedule.csv", index=False)
    results.to_csv(META / "results.csv", index=False)

    fc = pd.DataFrame(forecast_rows)
    col_order = ["match_id", "model", "prompt_type", "team_a", "team_b", "parse_ok",
                 "p_team_a_win", "p_draw", "p_team_b_win", "bet_pick",
                 "bet_stake_usd", "outcome_vs_prediction",
                 "was_my_forecast_well_calibrated", "did_i_get_lucky_or_unlucky",
                 "key_factor_i_missed", "key_factor_i_overweighted", "counterfactual",
                 "would_i_bet_differently_now", "confidence_in_this_reflection",
                 "reasoning", "key_sources", "raw_response"]
    for c in col_order:
        if c not in fc.columns:
            fc[c] = None
    fc = fc[col_order].sort_values(["match_id", "model", "prompt_type"])
    fc.to_csv(PROC / "all_forecasts.csv", index=False)

    pd.DataFrame(error_rows).to_csv(PROC / "parse_errors.csv", index=False)
    pd.DataFrame(missing_rows).to_csv(PROC / "missing_data.csv", index=False)

    # ---- forecasts_with_truth ----
    merged = fc.merge(results, on="match_id", how="left")
    merged.to_csv(PROC / "forecasts_with_truth.csv", index=False)

    # ---- console summary ----
    print(f"schedule rows      : {len(sched)}")
    print(f"forecast rows      : {len(fc)}")
    print(f"  pre_match         : {(fc.prompt_type=='pre_match').sum()}")
    print(f"  pre_match_30min   : {(fc.prompt_type=='pre_match_30min').sum()}")
    print(f"  post_match        : {(fc.prompt_type=='post_match').sum()}")
    print(f"parse errors       : {len(error_rows)}")
    print(f"missing cells      : {len(missing_rows)}")
    print(f"results with score : {results.final_score_a.notna().sum()}/72")
    print(f"unmatched blocks   : {len(unmatched)}")
    for u in unmatched:
        print("   -", u)
    print("\nper-model pre/post coverage:")
    for m in MODELS:
        sub = fc[fc.model == m]
        print(f"  {m:8s} pre={ (sub.prompt_type=='pre_match').sum():2d}"
              f"  post={(sub.prompt_type=='post_match').sum():2d}"
              f"  parse_ok={sub.parse_ok.sum():3d}/{len(sub)}")


if __name__ == "__main__":
    build()
