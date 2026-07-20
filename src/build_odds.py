"""Build data/metadata/odds.csv from odds_data.ODDS.

Raw odds come in three formats (auto-detected):
  American  "+155" / "-250"   fractional "11/2"   decimal "1.57"
All are converted to decimal odds and implied probability. The raw implied
probabilities sum to >1 (the bookmaker overround / vig); we also give the
vig-removed "fair" probabilities (each divided by the sum).

Columns: match_id, team_a, team_b, book, source_url,
  odds_{home,draw,away}_raw, odds_{home,draw,away}_dec,
  imp_{home,draw,away}  (vig-removed, sum to 1), overround
"""
from pathlib import Path
import pandas as pd
from odds_data import ODDS


def to_decimal(raw):
    if raw is None or raw == "":
        return None
    s = str(raw).strip()
    if "/" in s:                                   # fractional a/b
        a, b = s.split("/")
        return 1 + float(a) / float(b)
    if s[0] in "+-":                               # American moneyline
        v = float(s)
        return 1 + v / 100 if v > 0 else 1 + 100 / abs(v)
    return float(s)                                # decimal


def build():
    root = Path(__file__).resolve().parent.parent
    meta = root / "data" / "metadata"
    sched = pd.read_csv(meta / "schedule.csv").set_index("match_id")

    rows = []
    for i in range(1, 73):
        mid = f"m{i:02d}"
        home, draw, away, book, url = ODDS.get(mid, (None, None, None, None, None))
        dh, dd, da = to_decimal(home), to_decimal(draw), to_decimal(away)
        row = {
            "match_id": mid,
            "team_a": sched.loc[mid, "team_a"], "team_b": sched.loc[mid, "team_b"],
            "book": book, "source_url": url,
            "odds_home_raw": home, "odds_draw_raw": draw, "odds_away_raw": away,
            "odds_home_dec": dh, "odds_draw_dec": dd, "odds_away_dec": da,
        }
        if dh and dd and da:
            ih, idr, ia = 1 / dh, 1 / dd, 1 / da
            tot = ih + idr + ia
            row.update(imp_home=round(ih / tot, 4), imp_draw=round(idr / tot, 4),
                       imp_away=round(ia / tot, 4), overround=round(tot, 4))
        else:
            row.update(imp_home=None, imp_draw=None, imp_away=None, overround=None)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(meta / "odds.csv", index=False)

    have = df.odds_home_dec.notna() & df.odds_draw_dec.notna() & df.odds_away_dec.notna()
    print(f"odds.csv: {len(df)} matches, complete 1X2 for {have.sum()}/72")
    miss = df.loc[~have, "match_id"].tolist()
    if miss:
        print("  incomplete:", miss)
    print(f"  books used: {df.book.value_counts().to_dict()}")
    print(f"  overround range: {df.overround.min():.3f}–{df.overround.max():.3f} "
          f"(median {df.overround.median():.3f})")


if __name__ == "__main__":
    build()
