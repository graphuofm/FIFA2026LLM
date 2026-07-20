"""Ground-truth final scores, read by hand from the transcripts.

Scores are stored in canonical (team_a, team_b) order from schedule.csv, i.e.
score_a belongs to team_a. This matters because a few results were pasted with
the teams in the opposite order (e.g. m24 Uzbekistan vs Colombia was pasted as
"Colombia 3 Uzbekistan 1" -> team_a Uzbekistan = 1, team_b Colombia = 3).
Source: data/raw/grok.txt (cross-checked against the other three transcripts).
"""
from pathlib import Path
import pandas as pd
import schedule as sch  # noqa (kept for parity / future use)

# match_id -> (score_a, score_b) in team_a / team_b order
SCORES = {
    "m01": (2, 0), "m02": (2, 1), "m03": (4, 1), "m04": (1, 1), "m05": (1, 1),
    "m06": (1, 1), "m07": (0, 1), "m08": (2, 0), "m09": (7, 1), "m10": (2, 2),
    "m11": (1, 0), "m12": (5, 1), "m13": (0, 0), "m14": (2, 2), "m15": (1, 1),
    "m16": (1, 1), "m17": (3, 1), "m18": (3, 1), "m19": (1, 4), "m20": (3, 0),
    "m21": (1, 1), "m22": (4, 2), "m23": (1, 0), "m24": (1, 3), "m25": (1, 0),
    "m26": (6, 0), "m27": (4, 1), "m28": (1, 1), "m29": (2, 0), "m30": (0, 1),
    "m31": (3, 0), "m32": (0, 1), "m33": (0, 4), "m34": (0, 0), "m35": (2, 1),
    "m36": (5, 1), "m37": (1, 3), "m38": (2, 2), "m39": (0, 0), "m40": (4, 0),
    "m41": (1, 2), "m42": (3, 2), "m43": (3, 0), "m44": (2, 0), "m45": (1, 0),
    "m46": (0, 1), "m47": (0, 0), "m48": (5, 0), "m49": (1, 0), "m50": (0, 3),
    "m51": (4, 2), "m52": (0, 3), "m53": (3, 1), "m54": (2, 1), "m55": (0, 2),
    "m56": (2, 1), "m57": (1, 1), "m58": (1, 3), "m59": (3, 2), "m60": (0, 0),
    "m61": (1, 5), "m62": (1, 1), "m63": (0, 0), "m64": (0, 1), "m65": (5, 0),
    "m66": (1, 4), "m67": (3, 3), "m68": (1, 3), "m69": (0, 0), "m70": (3, 1),
    "m71": (2, 1), "m72": (0, 2),
}


def outcome(a, b):
    return "team_a_win" if a > b else "team_b_win" if b > a else "draw"


def build_results():
    root = Path(__file__).resolve().parent.parent
    meta = root / "data" / "metadata"
    sched = pd.read_csv(meta / "schedule.csv")
    rows = []
    for r in sched.itertuples():
        a, b = SCORES[r.match_id]
        rows.append({"match_id": r.match_id, "team_a": r.team_a, "team_b": r.team_b,
                     "final_score_a": a, "final_score_b": b, "outcome": outcome(a, b)})
    df = pd.DataFrame(rows)
    df.to_csv(meta / "results.csv", index=False)
    return df


def merge_into_models():
    root = Path(__file__).resolve().parent.parent
    proc = root / "data" / "processed"
    res = build_results().set_index("match_id")
    for csv in ["claude.csv", "chatgpt.csv", "gemini.csv", "grok.csv"]:
        p = proc / csv
        df = pd.read_csv(p)
        df["final_score_a"] = df.match_id.map(res.final_score_a)
        df["final_score_b"] = df.match_id.map(res.final_score_b)
        df["outcome"] = df.match_id.map(res.outcome)
        # tidy column order: metadata, truth, then model outputs
        front = ["match_id", "date", "group", "team_a", "team_b",
                 "final_score_a", "final_score_b", "outcome"]
        rest = [c for c in df.columns if c not in front and c != "file_order"]
        df = df[front + rest + ["file_order"]].sort_values("file_order")
        df.to_csv(p, index=False)
        print(f"{csv}: {len(df)} rows, scored {df.final_score_a.notna().sum()}")


if __name__ == "__main__":
    merge_into_models()
