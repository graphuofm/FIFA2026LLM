"""Canonical knockout-stage metadata for the World Cup 2026 LLM forecasting study.

These 32 fixtures (m73-m104) and their ground-truth results were read BY HAND
from the four transcripts, not regex-scraped: the knockout headers come in four
different renderings, some Round-of-16 fixtures were pasted with bracket
placeholders ("W74 vs W77") whose numbers do NOT line up with reality, and the
final scores were pasted in a dozen inconsistent phrasings (penalty shootouts,
lower-cased team names, teams occasionally in the opposite order). Everything
below is the resolved truth, cross-checked across all four models.

Orientation: team_a is the FIRST-listed side in the pre-match prompt (the side
`team_a_win` refers to); final_score_a / pen_a belong to team_a.

Knockout outcome model
----------------------
`outcome` in {team_a_win, draw, team_b_win} is the 90-minute (== end of extra
time) result from the pasted final score, exactly the 3-way space the models
forecast. Four ties finished level and were decided on penalties -> outcome is
`draw` (the models' draw bucket was for "no winner in normal/extra time"), and
`decided_by='penalties'` with pen_a/pen_b filled. `advanced` names the side that
progressed (the shootout winner for penalty ties; for m103/m104 it is simply the
match winner). This keeps probability scoring identical to the group stage while
still recording who went through.
"""
from __future__ import annotations

# match_id: (date, weekday, stage, team_a, team_b, kickoff, venue, city)
FIXTURES = {
    "m73": ("2026-06-28", "Sunday",    "round_of_32", "South Africa", "Canada",                 "14:00", "Los Angeles Stadium", "Los Angeles"),
    "m74": ("2026-06-29", "Monday",    "round_of_32", "Germany",      "Paraguay",               "15:30", "Boston Stadium",      "Boston"),
    "m75": ("2026-06-29", "Monday",    "round_of_32", "Netherlands",  "Morocco",                "20:00", "Monterrey Stadium",   "Monterrey"),
    "m76": ("2026-06-29", "Monday",    "round_of_32", "Brazil",       "Japan",                  "12:00", "Houston Stadium",     "Houston"),
    "m77": ("2026-06-30", "Tuesday",   "round_of_32", "Mexico",       "Ecuador",                "20:00", "Mexico City Stadium", "Mexico City"),
    "m78": ("2026-06-30", "Tuesday",   "round_of_32", "France",       "Sweden",                 "16:00", "NY/NJ Stadium",       "New Jersey"),
    "m79": ("2026-06-30", "Tuesday",   "round_of_32", "Côte d'Ivoire", "Norway",                "12:00", "Dallas Stadium",      "Dallas"),
    "m80": ("2026-07-01", "Wednesday", "round_of_32", "USA",          "Bosnia and Herzegovina", "19:00", "SF Bay Area Stadium", "San Francisco Bay Area"),
    "m81": ("2026-07-01", "Wednesday", "round_of_32", "Belgium",      "Senegal",                "15:00", "Seattle Stadium",     "Seattle"),
    "m82": ("2026-07-01", "Wednesday", "round_of_32", "England",      "Congo DR",               "11:00", "Atlanta Stadium",     "Atlanta"),
    "m83": ("2026-07-02", "Thursday",  "round_of_32", "Switzerland",  "Algeria",                "22:00", "BC Place Vancouver",  "Vancouver"),
    "m84": ("2026-07-02", "Thursday",  "round_of_32", "Portugal",     "Croatia",                "18:00", "Toronto Stadium",     "Toronto"),
    "m85": ("2026-07-02", "Thursday",  "round_of_32", "Spain",        "Austria",                "14:00", "Los Angeles Stadium", "Los Angeles"),
    "m86": ("2026-07-03", "Friday",    "round_of_32", "Colombia",     "Ghana",                  "20:30", "Kansas City Stadium", "Kansas City"),
    "m87": ("2026-07-03", "Friday",    "round_of_32", "Argentina",    "Cabo Verde",             "17:00", "Miami Stadium",       "Miami"),
    "m88": ("2026-07-03", "Friday",    "round_of_32", "Australia",    "Egypt",                  "13:00", "Dallas Stadium",      "Dallas"),
    "m89": ("2026-07-04", "Saturday",  "round_of_16", "Paraguay",     "France",                 "16:00", "Philadelphia Stadium", "Philadelphia"),
    "m90": ("2026-07-04", "Saturday",  "round_of_16", "Canada",       "Morocco",                "12:00", "Houston Stadium",     "Houston"),
    "m91": ("2026-07-05", "Sunday",    "round_of_16", "Mexico",       "England",                "19:00", "Mexico City Stadium", "Mexico City"),
    "m92": ("2026-07-05", "Sunday",    "round_of_16", "Brazil",       "Norway",                 "15:00", "NY/NJ Stadium",       "New Jersey"),
    "m93": ("2026-07-06", "Monday",    "round_of_16", "USA",          "Belgium",                "19:00", "Seattle Stadium",     "Seattle"),
    "m94": ("2026-07-06", "Monday",    "round_of_16", "Portugal",     "Spain",                  "14:00", "Dallas Stadium",      "Dallas"),
    "m95": ("2026-07-07", "Tuesday",   "round_of_16", "Switzerland",  "Colombia",               "15:00", "BC Place Vancouver",  "Vancouver"),
    "m96": ("2026-07-07", "Tuesday",   "round_of_16", "Argentina",    "Egypt",                  "11:00", "Atlanta Stadium",     "Atlanta"),
    "m97": ("2026-07-09", "Thursday",  "quarter_final", "France",     "Morocco",                "15:00", "Boston Stadium",      "Boston"),
    "m98": ("2026-07-10", "Friday",    "quarter_final", "Spain",      "Belgium",                "14:00", "Los Angeles Stadium", "Los Angeles"),
    "m99": ("2026-07-11", "Saturday",  "quarter_final", "Argentina",  "Switzerland",            "20:00", "Kansas City Stadium", "Kansas City"),
    "m100": ("2026-07-11", "Saturday", "quarter_final", "Norway",     "England",                "16:00", "Miami Stadium",       "Miami"),
    "m101": ("2026-07-14", "Tuesday",  "semi_final",   "France",      "Spain",                  "14:00", "Dallas Stadium",      "Dallas"),
    "m102": ("2026-07-15", "Wednesday", "semi_final",  "England",     "Argentina",              "14:00", "Atlanta Stadium",     "Atlanta"),
    "m103": ("2026-07-18", "Saturday", "third_place",  "France",      "England",                "16:00", "Miami Stadium",       "Miami"),
    "m104": ("2026-07-19", "Sunday",   "final",        "Spain",       "Argentina",              "14:00", "NY/NJ Stadium",       "New Jersey"),
}

# match_id: (score_a, score_b, decided_by, pen_a, pen_b)
#   decided_by in {regulation, penalties}.  pen_* None unless a shootout.
#   (No knockout tie was pasted as decided by a golden/ET goal; ET-level ties
#    all show as a shootout. Non-level scores are taken at face value.)
RESULTS = {
    "m73": (0, 1, "regulation", None, None),
    "m74": (1, 1, "penalties", 3, 4),
    "m75": (1, 1, "penalties", 2, 3),
    "m76": (2, 1, "regulation", None, None),
    "m77": (2, 0, "regulation", None, None),
    "m78": (3, 0, "regulation", None, None),
    "m79": (1, 2, "regulation", None, None),
    "m80": (2, 0, "regulation", None, None),
    "m81": (3, 2, "regulation", None, None),
    "m82": (2, 1, "regulation", None, None),
    "m83": (2, 0, "regulation", None, None),
    "m84": (2, 1, "regulation", None, None),
    "m85": (3, 0, "regulation", None, None),
    "m86": (1, 0, "regulation", None, None),
    "m87": (3, 2, "regulation", None, None),
    "m88": (1, 1, "penalties", 2, 4),
    "m89": (0, 1, "regulation", None, None),
    "m90": (0, 3, "regulation", None, None),
    "m91": (2, 3, "regulation", None, None),
    "m92": (1, 2, "regulation", None, None),
    "m93": (1, 4, "regulation", None, None),
    "m94": (0, 1, "regulation", None, None),
    "m95": (0, 0, "penalties", 4, 3),
    "m96": (3, 2, "regulation", None, None),
    "m97": (2, 0, "regulation", None, None),
    "m98": (2, 1, "regulation", None, None),
    "m99": (3, 1, "regulation", None, None),
    "m100": (1, 2, "regulation", None, None),
    "m101": (0, 2, "regulation", None, None),
    "m102": (1, 2, "regulation", None, None),
    "m103": (4, 6, "regulation", None, None),
    "m104": (1, 0, "regulation", None, None),
}

KO_IDS = [f"m{i}" for i in range(73, 105)]


def outcome_of(mid: str) -> str:
    a, b, _, _, _ = RESULTS[mid]
    return "team_a_win" if a > b else "team_b_win" if b > a else "draw"


def advanced_of(mid: str) -> str:
    """Side that progressed: shootout winner for penalty ties, else match winner."""
    a, b, decided, pa, pb = RESULTS[mid]
    if decided == "penalties":
        return "team_a" if pa > pb else "team_b"
    return "team_a" if a > b else "team_b"
