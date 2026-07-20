# World Cup 2026 — LLM Forecasting: Initial Findings

Four LLMs (Claude, ChatGPT, Gemini, Grok) forecast all **72 group-stage
matches** with win/draw/win probabilities and a virtual $100 bet each. Metrics
use the T-24h pre-match forecast; the betting market (vig-removed implied
probabilities) is included as a baseline. 20 of 72 matches (28%) were draws.

## Leaderboards

| model | accuracy | Brier ↓ | log-loss ↓ | ROI | net P&L | bets |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| **market** | **66.7%** | **0.486** | 0.827 | — | — | — |
| chatgpt | 66.7% | 0.493 | 0.838 | +3.2% | +$38 | 41 |
| grok | 66.7% | 0.491 | 0.826 | +1.2% | +$55 | 72 |
| **gemini** | 62.5% | **0.485** | **0.820** | **+4.4%** | **+$268** | 71 |
| claude | 63.9% | 0.489 | 0.828 | **−28.6%** | **−$308** | 48 |

## The five interesting findings

**1. Nobody beats the market on accuracy.** All four land at 62–67% vs the
market's 66.7%. ChatGPT and Grok essentially *replicate* the market favourite:
flat-staking their top pick returns the exact same +4.2% as flat-staking the
market favourite. The LLMs are, on picks, a slightly noisier mirror of the book.
Gemini alone edges the market on *probabilistic* score (Brier 0.485 vs 0.486,
log-loss 0.820 vs 0.827) — a tie, but a respectable one.

**2. Draw blindness is total and universal.** 28% of matches were draws; each
model named "draw" as its single most-likely outcome only **1–4 times out of
72**, catching **1–2 of the 20 draws**. Of the 24 matches where *all four models
were simultaneously wrong, ~19 were draws.* The biggest "upsets" weren't shocks —
they were goalless/level draws the market also missed (Spain 0-0 Cabo Verde,
priced 7%; Ecuador 0-0 Curaçao, 9%; Qatar 1-1 Switzerland, 15%). Draw prediction
is the single largest exploitable weakness in these agents.

**3. Discipline lost, aggression won — the opposite of the intended lesson.**
Claude was the most "responsible" agent: smallest average stake ($22), bet only
when it saw "value", frequently reasoned itself into *no_bet*. It lost the most,
**−$308 (−28.6% ROI)**. Gemini bet on 71/72 matches at an $85 average stake and
made **+$268**. Grok bet on all 72 and finished +$55.

**4. …but Gemini's profit did NOT come from backing favourites.** Break Gemini's
bets down: its 64 favourite-backing bets *lost* −$113 (favourites pay short
odds, so its 36% misses hurt). All of its profit — **+$381** — came from just
**7 contrarian/value bets** that hit 57% at long odds. Grok's small profit is the
mirror image: it made +$63 grinding favourites and lost on its rare value plays.
Claude's failure is *adverse selection*: by only betting perceived-mispriced
games it concentrated its money on exactly the coin-flips and upsets, and its bet
hit-rate (33%) was far below its forecast accuracy (64%).

**5. Self-assessment is miscalibrated — and model-specific.** In the post-match
reflections: Gemini rated its own confidence at a mean of **0.92** (and saw the
world in binary — 42 "correct" vs 26 "incorrect", almost no "partially"). Grok
cried **"unlucky" 25 times** out of 72 — five times more than anyone else. Claude
was the most self-critical on outcomes (only 35/72 "correct") yet still declared
its forecast "well-calibrated" 66/72 times, even while losing money. The models'
narratives about their own performance don't match the scoreboard.

## Calibration
Mid-range picks are mildly **under**confident (say ~57%, right ~65%). Grok is the
exception at the top end: on its most confident picks (stated ~85%) it was right
only 71% — over-confident exactly when it's surest. See `figures/calibration.png`.

## Files
- `data/processed/model_metrics.csv` — the leaderboard numbers
- `reports/figures/` — accuracy_brier, roi, calibration, draws
- Reproduce: `python src/metrics.py`, `python src/findings.py`, `python src/plots.py`

## Caveats
Odds are pre-match lines from mixed books (best available per match, each
sourced), not one consistent closing line; treat ROI as indicative. n=72 is
small — single big-odds bets swing ROI a lot (Gemini's edge is 7 bets).
