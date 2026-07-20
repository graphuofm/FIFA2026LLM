"""Per-model extraction (one wide table per model, no cross-model join).

For each model we walk its transcript in file order (= chronological schedule
order), and for each match block we capture EXACTLY what the model said:
  pre-match : probabilities / bet / reasoning / key_sources
  T-30min   : same (only exists for the first 2 matches)
  post-match: the 8 reflection fields
The prompt boilerplate is never captured, only the model's JSON replies.

match_id / date / group / teams come from that block's own fixture header
(each header fully identifies the match), so no fragile cross-file team join.

Final scores (ground truth) are NOT scraped here: this script also dumps a
compact score-context file for a human to read and confirm.
"""
from __future__ import annotations
import re
from pathlib import Path

import pandas as pd

import parse_core as pc
import schedule as sch
from build_dataset import segment, strip_md, block_teams

MODELS = ["claude", "chatgpt", "gemini", "grok"]
ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
META = ROOT / "data" / "metadata"


def load_schedule():
    df = pd.read_csv(META / "schedule.csv")
    key_to_id, id_meta = {}, {}
    for r in df.itertuples():
        key = frozenset((sch.norm_team(r.team_a), sch.norm_team(r.team_b)))
        key_to_id[key] = r.match_id
        id_meta[r.match_id] = dict(date=r.date, group=r.group,
                                   team_a=r.team_a, team_b=r.team_b)
    return key_to_id, id_meta, df


def match_id_for(block, key_to_id):
    """Identify the match from the block's own header (fallback: score block)."""
    header = re.split(r"You are participating", block, maxsplit=1)[0]
    info = sch.parse_header(header)
    if info:
        key = frozenset((sch.norm_team(info["team_a"]), sch.norm_team(info["team_b"])))
        if key in key_to_id:
            return key_to_id[key], (info["team_a"], info["team_b"])
    ta, tb = block_teams(block)
    if ta:
        key = frozenset((sch.norm_team(ta), sch.norm_team(tb)))
        if key in key_to_id:
            return key_to_id[key], (ta, tb)
    return None, (None, None)


def pre_cols(prefix, j):
    p = (j or {}).get("probabilities", {}) or {}
    b = (j or {}).get("bet", {}) or {}
    return {
        f"{prefix}_p_team_a_win": p.get("team_a_win"),
        f"{prefix}_p_draw": p.get("draw"),
        f"{prefix}_p_team_b_win": p.get("team_b_win"),
        f"{prefix}_bet_pick": b.get("pick"),
        f"{prefix}_bet_stake_usd": b.get("stake_usd"),
        f"{prefix}_reasoning": (j or {}).get("reasoning"),
        f"{prefix}_key_sources": " | ".join((j or {}).get("key_sources", []) or []),
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


def score_context(block):
    """Compact raw window that contains the pasted final score, for human read."""
    i = block.find(pc.POST_MARK)
    if i == -1:
        return ""
    before = strip_md(block[max(0, i - 90):i])
    seg = strip_md(block[i:])
    objs = [(st, en, o) for st, en, o in pc.iter_top_objects(seg) if pc.POST_KEY in o]
    mid = seg[objs[0][1]:objs[-1][0]] if len(objs) >= 2 else ""
    ctx = (before + " || " + mid).replace("\n", " ")
    return re.sub(r"\s+", " ", ctx).strip()[:160]


ALL_IDS = [f"m{i:02d}" for i in range(1, 73)]
PRE_KEYS_ROW = ["pre_p_team_a_win", "pre_p_draw", "pre_p_team_b_win",
                "pre_bet_pick", "pre_bet_stake_usd", "pre_reasoning", "pre_key_sources"]
REFL_KEYS_ROW = ["refl_outcome_vs_prediction", "refl_was_well_calibrated", "refl_luck",
                 "refl_key_factor_missed", "refl_key_factor_overweighted",
                 "refl_counterfactual", "refl_would_bet_differently", "refl_confidence"]


def _has(row, keys):
    # NB: empty string counts as absent — pre_cols emits "" for key_sources when
    # there is no forecast, which must NOT make an orphan look like a full match.
    return any(row.get(k) not in (None, "") for k in keys)


def _add_issue(row, msg):
    row["_parse_issue"] = ((row.get("_parse_issue") + "; ") if row.get("_parse_issue")
                           else "") + msg


def _next_missing(last_mid, used):
    """First schedule id after last_mid that hasn't been used yet."""
    start = ALL_IDS.index(last_mid) + 1 if last_mid in ALL_IDS else 0
    for mid in ALL_IDS[start:]:
        if mid not in used:
            return mid
    return None


def reconcile(rows, id_meta):
    """Collapse duplicate-header blocks, re-home orphan reflections, and assign
    header-less blocks by position. Returns a clean list of per-match rows."""
    final, order, used, last_mid = {}, [], set(), None
    for row in rows:
        mid = row["match_id"]
        haspre, haspost = _has(row, PRE_KEYS_ROW), _has(row, REFL_KEYS_ROW)
        if mid is None:
            if haspre:                       # header-less full match (e.g. chatgpt m02)
                mid = _next_missing(last_mid, used)
                if mid is None:
                    continue
                row["match_id"] = mid
                row.update({k: id_meta[mid][k] for k in ("date", "group", "team_a", "team_b")})
                _add_issue(row, "match_id assigned by position (no header)")
            elif haspost and last_mid in final:
                if not _has(final[last_mid], REFL_KEYS_ROW):
                    for k in REFL_KEYS_ROW:  # orphan reflection -> previous match
                        final[last_mid][k] = row.get(k)
                    _add_issue(final[last_mid], "reflection re-homed from orphan block")
                else:                        # a 2nd reflection for the same match
                    _add_issue(final[last_mid], "duplicate reflection in source (kept first)")
                continue
            else:
                continue                     # empty fragment
        if mid in final:                     # duplicate header -> merge, keep first
            for k in PRE_KEYS_ROW + REFL_KEYS_ROW:
                if final[mid].get(k) is None and row.get(k) is not None:
                    final[mid][k] = row.get(k)
            _add_issue(final[mid], f"duplicate block merged (file_order {row['file_order']})")
        else:
            final[mid] = row
            order.append(mid)
        used.add(mid)
        last_mid = mid
    return [final[m] for m in order]


def build():
    key_to_id, id_meta, sched = load_schedule()
    score_dump = []

    for model in MODELS:
        text = pc.read(model)
        rows = []
        for order, block in enumerate(segment(text)):
            mid, (ta, tb) = match_id_for(block, key_to_id)
            resp, errs = pc.extract_responses(block)
            row = {"match_id": mid, "file_order": order}
            if mid:
                row.update({"date": id_meta[mid]["date"], "group": id_meta[mid]["group"],
                            "team_a": id_meta[mid]["team_a"], "team_b": id_meta[mid]["team_b"]})
            else:
                row.update({"date": None, "group": None, "team_a": ta, "team_b": tb})
            row.update(pre_cols("pre", (resp["pre"] or {}).get("json")))
            row.update(pre_cols("t30", (resp["t30"] or {}).get("json")))
            row.update(refl_cols((resp["post"] or {}).get("json")))
            row["_parse_issue"] = "; ".join(
                [s for s in [
                    (resp["pre"] or {}).get("error"),
                    (resp["post"] or {}).get("error"),
                ] if s] + errs) or None
            rows.append(row)
            if model == "grok" and mid:
                score_dump.append((mid, id_meta[mid]["team_a"], id_meta[mid]["team_b"],
                                   score_context(block)))

        rows = reconcile(rows, id_meta)
        df = pd.DataFrame(rows).sort_values("match_id")
        df.to_csv(PROC / f"{model}.csv", index=False)
        print(f"{model:8s}: {len(df)} matches, "
              f"pre_ok={df.pre_p_team_a_win.notna().sum()}, "
              f"refl_ok={df.refl_outcome_vs_prediction.notna().sum()}, "
              f"issues={df._parse_issue.notna().sum()}")

    # score contexts for human verification (from grok, ordered by match_id)
    score_dump.sort(key=lambda x: x[0])
    lines = [f"{mid}  {a} vs {b}\n     {ctx}" for mid, a, b, ctx in score_dump]
    (PROC / "score_context_grok.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote score_context_grok.txt ({len(score_dump)} matches)")


if __name__ == "__main__":
    build()
