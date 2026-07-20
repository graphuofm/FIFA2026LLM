"""
Core parsing utilities for the World Cup 2026 LLM forecasting study.

Each raw model file (data/raw/{claude,chatgpt,gemini,grok}.txt) is a
manually-copied transcript of one long conversation covering ~72 group-stage
matches. Per match the conversation contains:

    [fixture header]                         (teams / date / group / venue)
    T-24h pre-match prompt  + JSON response
    [first 2 matches only] T-30min prompt + JSON response
    post-match reflection prompt + final score + JSON response

We split on the T-24h prompt anchor (appears exactly once per match), then
pull the JSON objects out of each block with a string-aware brace matcher.
Nothing is ever silently dropped: unparseable-but-real responses are logged.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

# --- anchors that appear once per match -------------------------------------
ANCHOR = "You are participating in a research study on LLM forecasting"
T30_MARK = "kicks off in about 30 minutes"
POST_MARK = "The match has ended"

# JSON template signatures (the pasted prompt schema, NOT a model answer)
PRE_TEMPLATE_SIGS = ("<0-1>", "team_a_win|draw|team_b_win", "<0-100>")
POST_TEMPLATE_SIGS = ("<correct|incorrect", "<true|false>", "<lucky|unlucky",
                      "one factor I underweighted")

PRE_KEYS = ("probabilities", "bet")
POST_KEY = "outcome_vs_prediction"


def read(model: str) -> str:
    p = Path(__file__).resolve().parent.parent / "data" / "raw" / f"{model}.txt"
    text = p.read_text(encoding="utf-8", errors="replace")
    if model == "claude":
        text = _clean_claude(text)
    return text


def _clean_claude(text: str) -> str:
    """Claude's UI export injects noise that corrupts brace matching:
      * labels 'Claude finished the response', 'You said:', 'Claude responded:'
      * a STRAY '{' right after 'Claude responded:' that wraps a duplicated
        thinking-summary line, e.g.  'responded: {Synthesized ... value{ <json> }'
        -> the stray brace never closes, so the real JSON object is swallowed.
    Valid JSON always opens with '{' immediately followed by '"' (or '}'), so any
    '{' NOT followed by a quote/brace is UI noise and is safe to drop.
    """
    text = text.replace("Claude finished the response", " ")
    text = text.replace("You said:", " ").replace("Claude responded:", " ")
    text = re.sub(r'\{(?!\s*["}])', " ", text)
    return text


def split_matches(text: str):
    """Return list of (header_text, body_text) per match, in file order.

    header of match i = text between end of previous block and anchor[i];
    body = anchor[i] .. anchor[i+1].
    """
    idxs = [m.start() for m in re.finditer(re.escape(ANCHOR), text)]
    matches = []
    for i, start in enumerate(idxs):
        end = idxs[i + 1] if i + 1 < len(idxs) else len(text)
        body = text[start:end]
        # header = the tail of the PREVIOUS segment (before this anchor)
        prev_start = idxs[i - 1] if i > 0 else 0
        header = text[prev_start:start]
        matches.append((header, body))
    return matches


def iter_top_objects(s: str):
    """Yield (start, end, substring) for every top-level {...}, string-aware.

    Only DOUBLE quotes delimit strings (JSON). Prose apostrophes such as
    "South Africa's" must NOT be treated as string starts, or the brace
    depth desyncs for the rest of the block.
    """
    depth = 0
    start = None
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    yield start, i + 1, s[start:i + 1]
                    start = None


def _clean_json(raw: str) -> str:
    """Repair the small deviations we see in practice before json.loads."""
    t = raw.strip()
    # drop a leading bare 'json' word that Claude sometimes prints
    t = re.sub(r"^json\s*", "", t, flags=re.I)
    # curly quotes used as string delimiters -> straight (rare; only outermost)
    # normalise smart double quotes that some transcripts use for keys
    t = t.replace("“", '"').replace("”", '"')
    # trailing commas before } or ]
    t = re.sub(r",\s*([}\]])", r"\1", t)
    # paste typo: a stray ']' closes the reasoning value before "key_sources"
    #   ..."reasoning": "... pass."],  "key_sources": [...]   ->   remove the ']'
    t = re.sub(r'"\]\s*,(\s*"key_sources")', r'",\1', t)
    return t


def is_template(obj_str: str, sigs) -> bool:
    return any(sig in obj_str for sig in sigs)


def extract_responses(body: str):
    """From one match body, return dict with parsed responses + raw + errors.

    keys: pre, t30, post  -> each {'json': dict|None, 'raw': str, 'error': str|None}
    A slot is None if that prompt/response is absent for this match.
    """
    out = {"pre": None, "t30": None, "post": None}
    errors = []

    # locate the reflection prompt so we can tell pre-window from post-window
    post_i = body.find(POST_MARK)
    pre_window = body[:post_i] if post_i != -1 else body
    post_window = body[post_i:] if post_i != -1 else ""

    # --- pre-match forecasts (T-24h and optional T-30min) in pre_window ------
    forecasts = []
    for st, en, obj in iter_top_objects(pre_window):
        if not any(k in obj for k in PRE_KEYS):
            continue
        if is_template(obj, PRE_TEMPLATE_SIGS):
            continue
        parsed, err = _try(obj)
        forecasts.append({"json": parsed, "raw": obj, "error": err})

    if forecasts:
        out["pre"] = forecasts[0]
        if len(forecasts) >= 2:
            out["t30"] = forecasts[1]
        if len(forecasts) > 2:
            errors.append(f"{len(forecasts)} pre-match JSONs found (expected 1-2)")

    # --- post-match reflection in post_window -------------------------------
    reflections = []
    for st, en, obj in iter_top_objects(post_window):
        if POST_KEY not in obj:
            continue
        if is_template(obj, POST_TEMPLATE_SIGS):
            continue
        parsed, err = _try(obj)
        reflections.append({"json": parsed, "raw": obj, "error": err})

    if not reflections:  # recover an unclosed reflection object (missing final '}')
        rec = _recover_object(post_window, POST_KEY, POST_TEMPLATE_SIGS)
        if rec:
            reflections.append(rec)
            errors.append("post reflection recovered (unclosed brace)")

    if reflections:
        out["post"] = reflections[-1]  # response follows the template
        if len(reflections) > 1:
            errors.append(f"{len(reflections)} post-match JSONs found (expected 1)")

    if out["pre"] is None:  # recover an unclosed pre-match forecast
        rec = _recover_object(pre_window, "probabilities", PRE_TEMPLATE_SIGS)
        if rec:
            out["pre"] = rec
            errors.append("pre forecast recovered (unclosed brace)")

    return out, errors


def _recover_object(window: str, key: str, template_sigs):
    """Rescue a response whose closing '}' was lost when the transcript was
    pasted. Take the last non-template '{...' that contains `key`, trim any
    trailing separator, and balance the braces before parsing."""
    for m in reversed(list(re.finditer(re.escape(key), window))):
        start = window.rfind("{", 0, m.start())
        if start == -1:
            continue
        frag = window[start:]
        if is_template(frag, template_sigs):
            continue
        frag = re.split(r"[—_]{4,}", frag)[0].rstrip()  # drop trailing separator
        opens, closes = frag.count("{"), frag.count("}")
        if closes < opens:
            frag = frag.rstrip().rstrip(",") + "}" * (opens - closes)
        parsed, err = _try(frag)
        if parsed is not None:
            return {"json": parsed, "raw": frag, "error": None}
    return None


def _try(obj_str: str):
    try:
        return json.loads(_clean_json(obj_str)), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


_MDLINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_NOISE = re.compile(
    r"^(json|show more|show less|searched the web|thought for.*|fox sports|"
    r"final score.*|reflect .*|the match .*|do not search.*|respond in this.*|"
    r".*\d{1,2}:\d{2}\s*(am|pm).*)$",
    re.I,
)


def strip_md(s: str) -> str:
    """Turn markdown links '[text](url)' into just 'text'."""
    return _MDLINK.sub(r"\1", s)


def extract_score_block(body: str):
    """Return (team_a, team_b, score_a, score_b) or None.

    Ground truth is pasted by the human right after the reflection prompt,
    between the prompt's schema template and the model's JSON reply, as
    TeamA / TeamB / scoreA / scoreB. Claude embeds it in bing markdown links,
    so we strip links first; UI noise (timestamps, 'json', 'Show more') is
    filtered out before picking the two names and two integers.
    """
    post_i = body.find(POST_MARK)
    if post_i == -1:
        return None
    seg = strip_md(body[post_i:])

    objs = [(st, en, o) for st, en, o in iter_top_objects(seg) if POST_KEY in o]
    if objs:
        mid = seg[objs[0][1]:objs[-1][0]]
    else:
        mid = seg

    lines = []
    for ln in mid.splitlines():
        ln = re.sub(r"\s+", " ", ln).strip().rstrip("{").strip()
        if ln and "http" not in ln and not _NOISE.match(ln):
            lines.append(ln)
    names = [ln for ln in lines if not re.fullmatch(r"\d{1,2}", ln)]
    nums = [ln for ln in lines if re.fullmatch(r"\d{1,2}", ln)]
    if len(names) >= 2 and len(nums) >= 2:
        return names[0], names[1], int(nums[0]), int(nums[1])
    return None
