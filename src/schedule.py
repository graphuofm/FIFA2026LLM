"""Build the canonical 72-match group-stage schedule from fixture headers.

Two header renderings appear in the transcripts:
  * FIFA long form (first 2 matches):
      "Thursday 11 June 2026 Mexico 14:00 South Africa First Stage Group A
       Mexico City Stadium(Mexico City)"
  * compact schedule form (all other matches):
      "06-12 Fri D USA 20:00 Paraguay Los Angeles Stadium Los Angeles"
       = MM-DD Wkd Group TeamA Time TeamB Venue City

Team A / Team B order is the study's home/away designation that the
probabilities (team_a_win / team_b_win) refer to, so it must be preserved.
"""
from __future__ import annotations
import re
import unicodedata

# 16 host venues -> metro city. Note Vancouver's venue is "BC Place Vancouver"
# (no "Stadium"), so a plain "...Stadium" anchor is not enough.
VENUES = [
    ("Mexico City Stadium", "Mexico City"),
    ("Guadalajara Stadium", "Guadalajara"),
    ("Monterrey Stadium", "Monterrey"),
    ("Atlanta Stadium", "Atlanta"),
    ("Los Angeles Stadium", "Los Angeles"),
    ("SF Bay Area Stadium", "San Francisco Bay Area"),
    ("Toronto Stadium", "Toronto"),
    ("NY/NJ Stadium", "New Jersey"),
    ("Boston Stadium", "Boston"),
    ("BC Place Vancouver", "Vancouver"),
    ("Houston Stadium", "Houston"),
    ("Dallas Stadium", "Dallas"),
    ("Philadelphia Stadium", "Philadelphia"),
    ("Miami Stadium", "Miami"),
    ("Seattle Stadium", "Seattle"),
    ("Kansas City Stadium", "Kansas City"),
]
# longest suffix first so "San Francisco Bay Area" isn't shadowed
_VENUE_SUFFIX = sorted(
    [(f"{v} {c}", v, c) for v, c in VENUES], key=lambda x: -len(x[0])
)

WEEKDAY = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
           "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}

# venue+city alternation used as a precise right-anchor for team_b. This makes
# header parsing robust to leading UI noise ("Claude finished the response...")
# and to headers that were pasted twice in a row.
_VENUE_CITY_ALT = "(?:" + "|".join(
    re.escape(f"{v} {c}") for v, c in sorted(VENUES, key=lambda x: -len(x[0]) - len(x[1]))
) + ")"
_COMPACT = re.compile(
    r"(\d{2})-(\d{2})\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-L])\s+(.+?)\s+"
    r"(\d{1,2}:\d{2})\s+(.+?)\s+(" + _VENUE_CITY_ALT + r")"
)
_FIFA = re.compile(
    r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+"
    r"June\s+2026\s+(.+?)\s+(\d{1,2}:\d{2})\s+(.+?)\s+First Stage.*?Group\s+([A-L])"
    r".*?([A-Z][\w./ ]*?Stadium)\s*\((.+?)\)",
    re.S,
)


def norm_team(name: str) -> str:
    """Aggressive key for cross-model joins: lowercase, deaccent, alnum only."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("�", "")  # stray replacement chars
    s = re.sub(r"[^a-z0-9]", "", s.lower())
    # common aliases seen in score blocks / reasoning
    alias = {
        "southkorea": "korearepublic", "korea": "korearepublic",
        "czechrepublic": "czechia",
        "usa": "usa", "unitedstates": "usa", "us": "usa",
        "iran": "iriran", "ivorycoast": "cotedivoire",
        "turkey": "turkiye", "capeverde": "caboverde",
        "drcongo": "congodr", "democraticrepublicofthecongo": "congodr",
        "bosnia": "bosniaandherzegovina",
    }
    return alias.get(s, s)


def _split_teamb_venue(tail: str):
    """tail = 'TeamB Venue City' -> (team_b, venue, city)."""
    tail = tail.strip()
    for suffix, venue, city in _VENUE_SUFFIX:
        if tail.endswith(suffix):
            team_b = tail[: -len(suffix)].strip()
            return team_b, venue, city
    # fallback: split on last ' Stadium '
    m = re.search(r"(.+?)\s+(.+Stadium)\s+(.+)$", tail)
    if m:
        return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    return tail, "", ""


_VC_LOOKUP = {f"{v} {c}": (v, c) for v, c in VENUES}


def parse_compact(h: str):
    m = _COMPACT.search(h.strip())  # search, not match: skip any leading noise
    if not m:
        return None
    mm, dd, wkd, group, team_a, kickoff, team_b, venue_city = m.groups()
    venue, city = _VC_LOOKUP[venue_city]
    return {
        "date": f"2026-{mm}-{dd}", "weekday": WEEKDAY[wkd], "group": group,
        "team_a": team_a.strip(), "team_b": team_b.strip(), "kickoff": kickoff,
        "venue": venue, "city": city,
    }


def parse_fifa(h: str):
    m = _FIFA.search(h)
    if not m:
        return None
    wkd, day, team_a, kickoff, team_b, group, venue, city = m.groups()
    return {
        "date": f"2026-06-{int(day):02d}", "weekday": wkd, "group": group,
        "team_a": team_a.strip(), "team_b": team_b.strip(), "kickoff": kickoff,
        "venue": venue.strip(), "city": city.strip(),
    }


def parse_header(h: str):
    """Try compact first, then FIFA long form. Whitespace is collapsed first
    because some transcripts pad headers with runs of spaces/tabs."""
    h = re.sub(r"\s+", " ", h).strip()
    return parse_compact(h) or parse_fifa(h)
