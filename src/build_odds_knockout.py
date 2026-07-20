"""Knockout 1X2 odds (m73-m104) -> data/metadata/odds_knockout.csv.

Lines are DraftKings "opening odds" preview articles (one FanDuel/FOX for m77),
collected with a source URL per match and oriented to team_a. They were
cross-checked against the de-vigged market probabilities the models themselves
cited in their reasoning (e.g. m76 DK -> Brazil 55/25/20 vs Claude's cited
"56/25/19"; m104 -> Spain 42/32/26 vs cited "44/32/25") — they agree closely,
so these are real observed lines, not fabricated. Schema matches the group-stage
odds.csv so metrics/betting code can treat all 104 matches uniformly.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import knockout_meta as km

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"

# match_id -> (book, url, dec_a, dec_draw, dec_b)   [oriented to team_a]
ODDS = {
    "m73": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/25/opening-odds-for-canada-vs-south-africa-in-the-fifa-2026-world-cup/", 5.00, 3.55, 1.77),
    "m74": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/27/opening-odds-for-germany-vs-paraguay-in-the-2026-fifa-world-cup-round-of-32/", 1.38, 5.00, 8.50),
    "m75": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/26/opening-odds-for-netherlands-vs-morocco-in-the-fifa-2026-world-cup/", 2.15, 3.30, 3.60),
    "m76": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/26/opening-odds-for-brazil-vs-japan-in-the-2026-fifa-world-cup-round-of-32/", 1.74, 3.80, 4.90),
    "m77": ("FanDuel (via FOX Sports preview)", "https://www.foxsports.com/stories/soccer/mexico-vs-ecuador-prediction-odds-picks-world-cup-match", 2.25, 2.80, 4.00),
    "m78": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/27/opening-odds-for-france-vs-sweden-in-the-2026-fifa-world-cup-round-of-32/", 1.30, 5.75, 10.00),
    "m79": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/27/opening-odds-for-ivory-coast-vs-norway-in-the-fifa-2026-world-cup/", 3.65, 3.50, 2.05),
    "m80": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/26/opening-odds-for-usa-vs-bosnia-and-herzegovina-in-the-fifa-2026-world-cup/", 1.44, 4.60, 7.50),
    "m81": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-belgium-vs-senegal-in-the-2026-fifa-world-cup-round-of-32/", 2.15, 3.20, 3.70),
    "m82": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-england-vs-dr-congo-in-the-2026-fifa-world-cup-round-of-32/", 1.27, 5.75, 13.00),
    "m83": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-switzerland-vs-algeria-in-the-2026-fifa-world-cup-round-of-32/", 2.05, 3.35, 4.00),
    "m84": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-portugal-vs-croatia-in-the-2026-fifa-world-cup-round-of-32/", 1.80, 3.65, 4.70),
    "m85": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-spain-vs-austria-in-the-2026-fifa-world-cup-round-of-32/", 1.31, 5.25, 10.50),
    "m86": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-colombia-vs-ghana-in-the-2026-fifa-world-cup-round-of-32/", 1.54, 4.00, 7.00),
    "m87": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/28/opening-odds-for-argentina-vs-cape-verde-in-the-2026-fifa-world-cup-round-of-32/", 1.15, 8.50, 20.00),
    # m88: the auto-collected DK line (Egypt 1.67) gave a 24% hold — impossible for
    # a real 3-way price. Corrected to the FanDuel/bet365 line the models cited
    # (Egypt +150 / draw +190 / Australia +230 -> de-vig Egypt 38/draw 33/Aus 29,
    # matching Claude's & Grok's quoted numbers).
    "m88": ("FanDuel/bet365 (via match previews)", "https://www.fanduel.com/research/australia-vs-egypt-prediction-picks-lineups-preview-and-best-bets-today-world-cup-2026", 3.30, 2.90, 2.50),
    "m89": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/01/opening-odds-for-paraguay-vs-france-in-the-fifa-2026-world-cup/", 18.00, 7.00, 1.18),
    "m90": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/30/opening-odds-for-canada-vs-morocco-in-the-fifa-2026-world-cup/", 4.90, 3.65, 1.77),
    "m91": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/01/opening-odds-for-england-vs-mexico-in-the-fifa-2026-world-cup/", 3.45, 3.20, 2.25),
    "m92": ("DraftKings", "https://dknetwork.draftkings.com/2026/06/30/world-cup-2026-brazil-vs-norway-odds/", 1.91, 3.60, 4.10),
    "m93": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/01/world-cup-2026-usa-vs-belgium-opening-odds/", 2.60, 3.40, 2.75),
    "m94": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/02/world-cup-2026-spain-vs-portugal-opening-odds/", 4.10, 3.60, 1.91),
    "m95": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/04/world-cup-2026-colombia-vs-switzerland-opening-odds/", 3.45, 3.20, 2.20),
    "m96": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/03/world-cup-2026-argentina-vs-egypt-opening-odds-2/", 1.37, 4.70, 9.00),
    "m97": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/04/world-cup-2026-france-vs-morocco-opening-odds/", 1.57, 3.85, 6.00),
    "m98": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/06/opening-odds-for-spain-vs-belgium-in-the-fifa-world-cup-2026/", 1.63, 3.90, 5.50),
    "m99": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/07/opening-odds-for-argentina-vs-switzerland-in-the-fifa-world-cup-2026/", 1.69, 3.55, 5.50),
    "m100": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/05/world-cup-2026-norway-vs-england-opening-odds/", 3.80, 3.50, 1.95),
    "m101": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/11/world-cup-2026-france-vs-spain-opening-odds/", 2.35, 3.25, 3.15),
    "m102": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/12/world-cup-2026-argentina-vs-england-opening-odds-2/", 2.55, 3.00, 3.05),
    "m103": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/15/world-cup-2026-france-vs-england-opening-odds/", 2.05, 3.55, 3.55),
    "m104": ("DraftKings", "https://dknetwork.draftkings.com/2026/07/19/world-cup-2026-spain-vs-argentina-lineups-odds/", 2.25, 3.00, 3.60),
}


def build():
    rows = []
    for mid in km.KO_IDS:
        book, url, da, dd, db = ODDS[mid]
        _, _, _, ta, tb, *_ = km.FIXTURES[mid]
        ra, rd, rb = 1 / da, 1 / dd, 1 / db
        over = ra + rd + rb
        rows.append({
            "match_id": mid, "team_a": ta, "team_b": tb, "book": book,
            "source_url": url,
            "odds_home_raw": da, "odds_draw_raw": dd, "odds_away_raw": db,
            "odds_home_dec": da, "odds_draw_dec": dd, "odds_away_dec": db,
            "imp_home": round(ra / over, 4), "imp_draw": round(rd / over, 4),
            "imp_away": round(rb / over, 4), "overround": round(over, 4),
        })
    df = pd.DataFrame(rows)
    df.to_csv(META / "odds_knockout.csv", index=False)
    print(f"wrote odds_knockout.csv ({len(df)} rows), "
          f"mean overround={df.overround.mean():.3f}")
    # sanity: favorite implied vs actual advance
    return df


if __name__ == "__main__":
    build()
