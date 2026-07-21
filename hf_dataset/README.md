---
license: cc-by-4.0
language:
  - en
pretty_name: WC2026-Agents
size_categories:
  - n<1K
task_categories:
  - tabular-classification
  - time-series-forecasting
tags:
  - llm-agents
  - forecasting
  - calibration
  - sports-analytics
  - prediction-markets
  - benchmark
  - contamination-free
configs:
  - config_name: forecasts
    data_files: data/forecasts.csv
    default: true
  - config_name: metrics
    data_files: data/model_metrics.csv
  - config_name: betting_summary
    data_files: data/betting_summary.csv
  - config_name: final_factor_probe
    data_files: data/final_factor_probe.csv
  - config_name: schedule
    data_files: metadata/schedule.csv
  - config_name: results
    data_files: metadata/results.csv
  - config_name: odds
    data_files: metadata/odds.csv
---

# WC2026-Agents

A **contamination-free benchmark** of four frontier LLMs acting as autonomous
**forecasting agents** over the entire 2026 FIFA World Cup (104 matches). Each
agent — Claude Opus 4.8, ChatGPT (GPT-5.5, high reasoning), Gemini 3.1 Pro, and
Grok (Expert Mode) — ran an identical **search → act → reflect** loop per match:
search the web, commit to a 1X2 (team-A win / draw / team-B win) probability and
a virtual \$100 bet, and, after the match, reflect given only the final score.
Every match kicked off **after the models' training cutoffs**, so the targets
cannot appear in any model's training data. The pre-match **betting market** is
included as a fifth competitor via per-match 1X2 odds.

📄 **Paper:** [arXiv:2607.17765](https://arxiv.org/abs/2607.17765) —
*FIFA World Cup 2026 as a Contamination-Free Benchmark for LLM Forecasting
Agents: Four Models, a Bookmaker, and 104 Matches*
💻 **Code:** https://github.com/graphuofm/FIFA2026LLM

## What's inside

| Config | File | Rows | What |
|---|---|---|---|
| `forecasts` (default) | `data/forecasts.csv` | 416 | One row per (agent, match): probabilities, bet, verbatim reasoning, the 8 reflection fields, outcome, market-implied probs, and settled P&L |
| `metrics` | `data/model_metrics.csv` | 5 | Accuracy / Brier / log-loss / ECE per agent + market |
| `betting_summary` | `data/betting_summary.csv` | — | ROI, bankroll, hit-rate per agent |
| `final_factor_probe` | `data/final_factor_probe.csv` | 7 | Final/bronze-only "which narrative factors influenced you" probe |
| `schedule` | `metadata/schedule.csv` | 104 | Fixtures (group + knockout), stage, venue, kickoff |
| `results` | `metadata/results.csv` | 104 | Ground truth incl. penalty shootouts and who advanced |
| `odds` | `metadata/odds.csv` | 104 | Pre-match 1X2 odds with source URL, vig-removed implied probs |
| `raw/` | `raw/*.txt` | — | Original per-model transcripts (read-only) + the prompt templates |

**Coverage:** 4 agents × 104 matches = **416 forecasts** and **414 reflections**
(two Gemini group reflections are absent in the source and flagged, not imputed).

## Key columns in `forecasts`

- **Identity:** `model`, `match_id`, `phase` (group/knockout), `stage`, `team_a`, `team_b`
- **Truth:** `outcome` ∈ {team_a_win, draw, team_b_win} (90-minute result; a draw
  for the four penalty ties), `decided_by`, `advanced`
- **Forecast:** `p_a`, `p_draw`, `p_b`, `bet_pick`, `bet_stake`, `reasoning`
- **Reflection:** `refl_outcome`, `refl_calibrated`, `refl_luck`, `refl_missed`,
  `refl_overweighted`, `refl_bet_diff`, `refl_conf`
- **Market & P&L:** `imp_home/imp_draw/imp_away`, `odds_*_dec`, `is_bet`, `profit`, `contrarian`

Knockout `outcome` is the 90-minute result (how a 1X2 bet settles); penalty
shootout winners are recorded separately in `advanced` / `results`.

## Load it

```python
from datasets import load_dataset
ds = load_dataset("dingjiacheng/wc2026-agents", "forecasts")       # default
odds = load_dataset("dingjiacheng/wc2026-agents", "odds")
```

Or just read the CSVs with pandas.

## Headline results (reference evaluation)

- The four agents pick the **same** outcome in **92%** of matches; **none beats
  the market's Brier score** — indeed a flat stake on the market favourite
  out-earns all four agents.
- They diverge as *decision-makers*: betting ROI from **−18% to +10%**; fading
  the market is unprofitable for all four; market-citation in reasoning ranges
  **12% (Gemini) to 100% (Claude)**; self-reported error rate on wrong picks
  ranges **36% (ChatGPT) to 86% (Gemini)**.

## Ethics

All betting is virtual; the dataset is a measurement instrument, not gambling
advice. Records are model outputs and public fixtures/scores/odds — no human
subjects or personal data.

## Citation

```bibtex
@misc{ding2026wc2026agents,
  title         = {{FIFA} World Cup 2026 as a Contamination-Free Benchmark for
                   {LLM} Forecasting Agents: Four Models, a Bookmaker, and 104 Matches},
  author        = {Ding, Jiacheng and Guo, Cong and Xu, Jason},
  year          = {2026},
  eprint        = {2607.17765},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2607.17765}
}
```
