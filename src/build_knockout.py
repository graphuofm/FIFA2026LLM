"""Extract the knockout-stage (m73-m104) forecasts for all four models.

Why this is separate from the group-stage builder: the knockout transcripts do
not have a regex-friendly structure (four different header renderings, bracket
placeholders that mis-number, penalty-shootout score lines in many phrasings).
So we do NOT try to parse fixtures/teams/scores out of the text. Instead:

  * fixtures + ground truth come from the hand-verified tables in knockout_meta
  * each file is split on the pre-match prompt anchor into its 32 blocks, IN
    ORDER (every file has exactly 32, verified), so block i == m(73+i)
  * only the model's own JSON replies are pulled out of each block, by the same
    string-aware brace matcher used for the group stage, then json.loads'd

As a guard against silent misalignment, we still scrape the human-pasted score
line from each block and compare it (as an unordered multiset of the two goal
counts) to the table; any mismatch is written to _parse_issue for review.
"""
from __future__ import annotations
import re
from pathlib import Path

import pandas as pd

import parse_core as pc
import knockout_meta as km

MODELS = ["claude", "chatgpt", "gemini", "grok"]
ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
META = ROOT / "data" / "metadata"

# Canonical raw lives in data/raw/<model>_knockout.txt (read-only, per project
# convention); fall back to the originally-pasted "<model> result knockout.txt"
# at repo root if the copy isn't present.
def _ko_path(m: str) -> Path:
    p = ROOT / "data" / "raw" / f"{m}_knockout.txt"
    return p if p.exists() else ROOT / f"{m} result knockout.txt"

KO_FILE = {m: _ko_path(m) for m in MODELS}

FACTOR_SIG = "which_of_these_i_think_matters_most"
FACTOR_TEMPLATE_SIG = "<none|slight|moderate"
FACTOR_KEYS = ["argentina_2022_champion_status", "spain_2024_euro_champion_status",
               "messi_narrative_or_farewell_tour",
               "neutral_venue_vs_argentina_diaspora_advantage",
               "which_of_these_i_think_matters_most"]


def read_ko(model: str) -> str:
    text = KO_FILE[model].read_text(encoding="utf-8", errors="replace")
    if model == "claude":
        text = pc._clean_claude(text)
    return text


def split_blocks(text: str):
    """One block per pre-match prompt anchor, in file order."""
    idxs = [m.start() for m in re.finditer(re.escape(pc.ANCHOR), text)]
    blocks = []
    for i, start in enumerate(idxs):
        end = idxs[i + 1] if i + 1 < len(idxs) else len(text)
        blocks.append(text[start:end])
    return blocks


def extract_factor(pre_window: str):
    """The final/bronze-only follow-up probe answer, if the model gave one.

    Two shapes occur: a standalone object whose top-level keys ARE the factor
    keys (grok, gemini, and the bronze answers), and — at the final — claude and
    chatgpt fold it into their forecast object under a nested "factor_influence"
    key. Return whichever dict actually carries the answer keys.
    """
    for st, en, obj in pc.iter_top_objects(pre_window):
        if FACTOR_SIG not in obj or FACTOR_TEMPLATE_SIG in obj:
            continue
        parsed, err = pc._try(obj)
        if parsed is None:
            continue
        if isinstance(parsed.get("factor_influence"), dict) \
                and FACTOR_SIG in parsed["factor_influence"]:
            return parsed["factor_influence"]
        if any(k in parsed for k in FACTOR_KEYS):
            return parsed
    return None


_NOISE_SCORE = re.compile(
    r"^(json|show more|show less|thought.*|reflect.*|do not search.*|"
    r"respond in this.*|the match has ended.*|one follow-up.*|sources?|"
    r"sports illustrated|.*\d{1,2}:\d{2}\s*(am|pm).*)$", re.I)


def scrape_score_line(block: str) -> str:
    """The human-pasted final-score line (last real line before 'The match has ended')."""
    i = block.find(pc.POST_MARK)
    if i == -1:
        return ""
    seg = pc.strip_md(block[:i])
    cand = ""
    for ln in seg.splitlines():
        ln = re.sub(r"\s+", " ", ln).strip()
        if not ln or "http" in ln or "{" in ln or "}" in ln:
            continue
        if _NOISE_SCORE.match(ln) or '"' in ln or "<" in ln:
            continue
        cand = ln  # keep the LAST qualifying line
    return cand


def score_multiset_from_line(line: str):
    """Unordered pair of the goal counts in the pasted score line (ignores pens)."""
    # drop the parenthetical/'penalty shootout' figures so we compare 90-min goals
    s = re.sub(r"\(.*?\)", " ", line)
    s = re.sub(r"penalty shootout\s*\d+", " ", s, flags=re.I)
    s = re.sub(r"penalty shootout", " ", s, flags=re.I)
    nums = [int(n) for n in re.findall(r"\b\d{1,2}\b", s)]
    return sorted(nums[:2]) if len(nums) >= 2 else None


def pre_cols(j):
    j = j or {}
    p = j.get("probabilities", {}) or {}
    b = j.get("bet", {}) or {}
    return {
        "pre_p_team_a_win": p.get("team_a_win"),
        "pre_p_draw": p.get("draw"),
        "pre_p_team_b_win": p.get("team_b_win"),
        "pre_bet_pick": b.get("pick"),
        "pre_bet_stake_usd": b.get("stake_usd"),
        "pre_reasoning": j.get("reasoning"),
        "pre_key_sources": " | ".join(j.get("key_sources", []) or []),
    }


def refl_cols(j):
    j = j or {}
    return {
        "refl_outcome_vs_prediction": j.get("outcome_vs_prediction"),
        "refl_was_well_calibrated": j.get("was_my_forecast_well_calibrated"),
        "refl_luck": j.get("did_i_get_lucky_or_unlucky"),
        "refl_key_factor_missed": j.get("key_factor_i_missed"),
        "refl_key_factor_overweighted": j.get("key_factor_i_overweighted"),
        "refl_counterfactual": j.get("counterfactual"),
        "refl_would_bet_differently": j.get("would_i_bet_differently_now"),
        "refl_confidence": j.get("confidence_in_this_reflection"),
    }


FRONT = ["match_id", "date", "stage", "team_a", "team_b",
         "final_score_a", "final_score_b", "outcome", "decided_by",
         "pen_a", "pen_b", "advanced"]
PRE = list(pre_cols(None).keys())
REFL = list(refl_cols(None).keys())


def write_metadata():
    """Canonical knockout schedule + results, parallel to the group-stage files.
    Kept SEPARATE from metadata/{schedule,results}.csv so the group builders
    (which regenerate those from 72 fixtures) never clobber the knockout rows."""
    sched = [{
        "match_id": mid, "date": d, "weekday": wk, "group": "", "team_a": ta,
        "team_b": tb, "kickoff": kick, "venue": ven, "city": city, "stage": st,
    } for mid, (d, wk, st, ta, tb, kick, ven, city) in km.FIXTURES.items()]
    pd.DataFrame(sched).to_csv(META / "schedule_knockout.csv", index=False)

    res = []
    for mid, (sa, sbv, decided, pa, pb) in km.RESULTS.items():
        _, _, _, ta, tb, *_ = km.FIXTURES[mid]
        adv = km.advanced_of(mid)
        res.append({
            "match_id": mid, "team_a": ta, "team_b": tb,
            "final_score_a": sa, "final_score_b": sbv,
            "outcome": km.outcome_of(mid), "decided_by": decided,
            "pen_a": pa, "pen_b": pb, "advanced": adv,
            "advanced_team": ta if adv == "team_a" else tb,
        })
    rdf = pd.DataFrame(res)
    rdf[["pen_a", "pen_b"]] = rdf[["pen_a", "pen_b"]].astype("Int64")
    rdf.to_csv(META / "results_knockout.csv", index=False)


def build():
    write_metadata()
    factor_rows = []
    per_model_counts = {}

    for model in MODELS:
        text = read_ko(model)
        blocks = split_blocks(text)
        assert len(blocks) == 32, f"{model}: expected 32 blocks, got {len(blocks)}"

        rows = []
        for i, block in enumerate(blocks):
            mid = km.KO_IDS[i]
            date, wkd, stage, ta, tb, kick, venue, city = km.FIXTURES[mid]
            sa, sbv, decided, pa, pb = km.RESULTS[mid]

            resp, errs = pc.extract_responses(block)
            issues = list(errs)
            for slot in ("pre", "post"):
                e = (resp[slot] or {}).get("error")
                if e:
                    issues.append(f"{slot}: {e}")
            if resp["pre"] is None:
                issues.append("no pre-match forecast found")
            if resp["post"] is None:
                issues.append("no reflection found")

            # score-line cross-check against the hand-verified table
            line = scrape_score_line(block)
            ms = score_multiset_from_line(line)
            if ms is not None and ms != sorted((sa, sbv)):
                issues.append(f"score-line {line!r} != table {sa}-{sbv}")

            row = {
                "match_id": mid, "date": date, "stage": stage,
                "team_a": ta, "team_b": tb,
                "final_score_a": sa, "final_score_b": sbv,
                "outcome": km.outcome_of(mid), "decided_by": decided,
                "pen_a": pa, "pen_b": pb, "advanced": km.advanced_of(mid),
            }
            row.update(pre_cols((resp["pre"] or {}).get("json")))
            row.update(refl_cols((resp["post"] or {}).get("json")))
            row["_parse_issue"] = "; ".join(issues) or None
            row["file_order"] = i
            rows.append(row)

            # final/bronze follow-up probe -> separate table
            post_i = block.find(pc.POST_MARK)
            factor = extract_factor(block[:post_i] if post_i != -1 else block)
            if factor:
                factor_rows.append({"match_id": mid, "model": model,
                                    **{k: factor.get(k) for k in FACTOR_KEYS}})

        df = pd.DataFrame(rows)[FRONT + PRE + REFL + ["_parse_issue", "file_order"]]
        df[["pen_a", "pen_b"]] = df[["pen_a", "pen_b"]].astype("Int64")
        df.to_csv(PROC / f"{model}_knockout.csv", index=False)
        per_model_counts[model] = dict(
            n=len(df),
            pre_ok=int(df.pre_p_team_a_win.notna().sum()),
            refl_ok=int(df.refl_outcome_vs_prediction.notna().sum()),
            issues=int(df._parse_issue.notna().sum()),
        )

    if factor_rows:
        pd.DataFrame(factor_rows).sort_values(["match_id", "model"]).to_csv(
            PROC / "knockout_final_factor_probe.csv", index=False)

    print("per-model knockout extraction:")
    for m, c in per_model_counts.items():
        print(f"  {m:8s} n={c['n']} pre_ok={c['pre_ok']} "
              f"refl_ok={c['refl_ok']} issues={c['issues']}")
    print(f"\nfinal/bronze factor-probe answers: {len(factor_rows)}")
    return per_model_counts


if __name__ == "__main__":
    build()
