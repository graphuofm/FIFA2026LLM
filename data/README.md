# World Cup 2026 LLM Forecasting — Dataset

Structured data extracted from four LLMs (Claude, ChatGPT, Gemini, Grok) acting
as forecasting agents on the **72 group-stage matches** of the 2026 FIFA World
Cup (11–27 June 2026). Each model was given, per match, a pre-match prompt
(~24h before kickoff) and a post-match reflection prompt (with the final score).
The first 2 matches also have a T-30min "updated forecast" prompt; that step was
dropped afterwards.

## Files

| File | Rows | What |
|------|------|------|
| `raw/{claude,chatgpt,gemini,grok}.txt` | — | Original pasted transcripts (read-only, untouched) |
| `raw/prompts.txt` | — | The prompt templates |
| `metadata/schedule.csv` | 72 | Canonical fixtures: match_id, date, group, team_a, team_b, kickoff, venue, city |
| `metadata/results.csv` | 72 | Ground-truth final scores + outcome (read by hand from the transcripts) |
| `metadata/odds.csv` | 72 | Pre-match market odds (1X2) + implied probabilities, each with source URL |
| `processed/{model}.csv` | 72 each | One row per match per model — everything the model said |

Data is kept **one table per model** (they can be joined later on `match_id`).
`match_id` (m01–m72) is the chronological schedule order.

## Columns in `processed/{model}.csv`

- **Fixture / truth**: `match_id, date, group, team_a, team_b, final_score_a, final_score_b, outcome`
  - `outcome` ∈ {`team_a_win`, `draw`, `team_b_win`} — team_a is the first-listed side; `final_score_a`/`_b` are in that same order.
- **Pre-match forecast (T-24h)**: `pre_p_team_a_win, pre_p_draw, pre_p_team_b_win, pre_bet_pick, pre_bet_stake_usd, pre_reasoning, pre_key_sources`
- **T-30min update** (only m01, m02): `t30_*` (same shape)
- **Post-match reflection**: `refl_outcome_vs_prediction, refl_was_well_calibrated, refl_luck, refl_key_factor_missed, refl_key_factor_overweighted, refl_counterfactual, refl_would_bet_differently, refl_confidence`
- `_parse_issue`: non-empty when a row needed repair/recovery or a source anomaly was found (see below).

The models were asked for win/draw/win **probabilities and a bet only** — they
did NOT predict scorelines. Final scores are ground truth, not a model output.

## Coverage

| model | matches | pre | post | bets placed (≠no_bet) |
|-------|:---:|:---:|:---:|:---:|
| claude | 72 | 72 | 72 | 48 |
| chatgpt | 72 | 72 | 72 | 41 |
| gemini | 72 | 72 | **70** | 71 |
| grok | 72 | 72 | 72 | 72 |

## Known source gaps & repairs (nothing fabricated)

- **gemini m01, m03**: no post-match reflection exists in the source transcript — left blank.
- **gemini m03**: the T-24h prompt was pasted twice with two different forecasts
  (0.55/0.28/0.17 and 0.64/0.22/0.14); the **first** was kept, flagged in `_parse_issue`.
- **claude m52**: the reflection was generated twice (luck "neither" then "unlucky");
  the **first** was kept, flagged.
- **chatgpt m02**: no fixture header in the paste → match_id assigned by position (verified Korea Republic vs Czechia).
- **chatgpt m34, m58, m72**: reflection JSON was missing its closing brace in the paste → recovered.
- **claude m32**: a stray `]` broke the pre-match JSON → repaired.

## Betting odds (`metadata/odds.csv`)

Pre-match 1X2 market odds for all 72 matches, collected from the web with a
**source URL recorded per match**. Where possible the odds article was one the
models themselves cited; gaps were filled by search.

- `odds_{home,draw,away}_raw` — as published (American `-250`, fractional `11/2`, or decimal `1.57`)
- `odds_{home,draw,away}_dec` — decimal odds
- `imp_{home,draw,away}` — vig-removed implied probabilities (sum to 1); `overround` is the raw bookmaker margin
- `home` = team_a, `away` = team_b (same orientation as everything else)
- `book` — which sportsbook. Odds are **not** from a single consistent book/closing line
  (availability varied): bet365, FanDuel, Kalshi, Ladbrokes, Paddy Power, Sports Interaction, etc.
  **Kalshi is a prediction market**, so its overround is ~1.00 (near-zero vig) — expected, not an error.

With odds + forecasts + results in place, ROI is computable: settle each model's
`pre_bet_pick` at that match's odds for the picked outcome.

## Knockout stage (m73–m104)

The 32 knockout matches (28 June – 19 July 2026) are extracted separately
because their transcripts are **not** regex-parseable the way the group stage
was: headers come in four different renderings, some Round-of-16 fixtures were
pasted with bracket placeholders (`W74 vs W77`) whose numbers don't line up with
reality, and the final scores appear in many phrasings (penalty shootouts,
lower-cased names, teams sometimes in the opposite order). So fixtures, team
orientation and ground-truth scores were **read by hand** from the transcripts
(`src/knockout_meta.py`), while each model's JSON replies are pulled out
positionally — every file is exactly 32 sequential blocks in bracket order, so
block *i* = m(73+*i*) — and `json.loads`'d (`src/build_knockout.py`).

| File | Rows | What |
|------|------|------|
| `metadata/schedule_knockout.csv` | 32 | Fixtures m73–m104 (`group` blank, `stage` = round) |
| `metadata/results_knockout.csv` | 32 | Scores + `decided_by`, `pen_a/pen_b`, `advanced`, `advanced_team` |
| `processed/{model}_knockout.csv` | 32 each | One row per match per model (same shape as the group files) |
| `processed/knockout_final_factor_probe.csv` | 7 | The final/bronze-only follow-up "how much did X influence you" probe |
| `processed/model_metrics_knockout.csv` | 4 | accuracy / adv_accuracy / brier / log_loss / draw-mass / bet_hit_rate |

`stage` ∈ {`round_of_32`, `round_of_16`, `quarter_final`, `semi_final`,
`third_place`, `final`}. These files are **separate** from the 72-row
`schedule.csv`/`results.csv` so the group builders never clobber them.

### How knockout ties are scored
The models still forecast a 3-way {team_a_win, draw, team_b_win}. Four ties
finished level and were settled on penalties → `outcome = draw`,
`decided_by = penalties`, with `pen_a/pen_b` and the shootout winner in
`advanced` (m74 Germany–Paraguay, m75 Netherlands–Morocco, m88 Australia–Egypt,
m95 Switzerland–Colombia). This keeps probability scoring (Brier/log-loss/
accuracy vs `outcome`) identical to the group stage — the draw bucket means "no
winner in normal/extra time" — while `advanced`/`advanced_team` still record who
progressed. `adv_accuracy` in the metrics file scores the favored side (argmax
of team_a_win vs team_b_win) against who actually advanced.

### Coverage & notes
- **Full coverage**: all 4 models × 32 matches have a pre-match forecast and a
  post-match reflection; **zero parse errors**, and every model's pasted
  score line agrees with the results table (4-way consensus, checked in code).
- **Round-of-16 placeholders**: m89 (`W74 vs W77`) and m90 (`W73 vs W75`) were
  pasted with bracket codes; the real sides (m89 Paraguay–France, m90 Canada–
  Morocco) were resolved from the models' own text and confirmed by every
  transcript. Team A/B orientation follows the pasted score line.
- **Final & bronze probe**: for m103/m104 the prompt added a follow-up question
  on which narrative factors influenced the forecast. claude/chatgpt/gemini
  answered both; grok only for the final. At the final, claude & chatgpt nested
  the answer under `factor_influence` inside their forecast JSON (handled).
- **ROI not yet computable**: pre-match 1X2 odds for the knockout ties have not
  been collected (`odds.csv` is group-only), so `model_metrics_knockout.csv`
  reports `bet_hit_rate` but no ROI. Collecting `odds_knockout.csv` is the one
  remaining step to match the group-stage analysis.

## Method note

Fixture headers, team alignment and final scores were resolved by **reading the
transcripts** (formats and team names differ across models and don't always line
up). The models' JSON answers were parsed verbatim so their exact wording —
including reasoning — is preserved without transcription error.
