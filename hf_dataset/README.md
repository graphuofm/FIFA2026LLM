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
  - world-cup-2026
  - football
  - betting-odds
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

# WC2026-Agents: ChatGPT vs Claude vs Gemini vs Grok on the 2026 FIFA World Cup

**WC2026-Agents** is a contamination-free benchmark in which four frontier LLMs act as autonomous **forecasting agents** over the entire 2026 FIFA World Cup (104 matches, 11 June to 19 July 2026). Each agent (Claude Opus 4.8, ChatGPT GPT-5.5 with high reasoning, Gemini 3.1 Pro, and Grok Expert Mode) ran an identical **search, act, reflect** loop per match: search the web, commit to a 1X2 (team A win / draw / team B win) probability and a virtual bet of up to $100, and after the match reflect given only the final score. Every match kicked off **after the models' training cutoffs**. The pre-match **betting market** is included as a fifth forecaster via per-match 1X2 odds.

📄 **Paper:** [arXiv:2607.17765](https://arxiv.org/abs/2607.17765), *FIFA World Cup 2026 as a Contamination-Free Benchmark for LLM Forecasting Agents: Four Models, a Bookmaker, and 104 Matches*, Jiacheng Ding and Cong Guo (University of Memphis)
🌐 **Project page:** https://graphuofm.github.io/FIFA2026LLM/ ([中文](https://graphuofm.github.io/FIFA2026LLM/zh.html))
💻 **Code:** https://github.com/graphuofm/FIFA2026LLM

## Headline results

| Forecaster | Accuracy | Brier (lower is better) | Log-loss | Virtual profit | ROI | Bets |
|---|---:|---:|---:|---:|---:|---:|
| Betting market (vig-free odds) | 68.3% | **0.469** | 0.807 | **+$1,041**\* | | 104 |
| Grok (Expert Mode) | 68.3% | 0.4706 | 0.803 | +$650 | +10.3% | 104 |
| Gemini 3.1 Pro | 65.4% | 0.4828 | 0.820 | +$322 | +3.7% | 103 |
| ChatGPT (GPT-5.5) | 68.3% | 0.4729 | 0.814 | +$118 | +8.0% | 55 |
| Claude Opus 4.8 | 66.3% | 0.4705 | 0.806 | -$275 | -18.1% | 73 |

\*Flat stake on the market favourite in every match.

- The four agents pick the **same** outcome in **96 of 104** matches (92%); **none beats the market's Brier score**, and a flat bet on the market favourite out-earns all four.
- They diverge as **decision-makers**: betting ROI from -18.1% to +10.3%. Bets against the market favourite win 21% to 40% of the time (vs 48% to 69% with the market); they lose money for Claude, Gemini and ChatGPT, while Grok's 5 contrarian bets make +$64.
- Market odds are cited in **100%** of Claude's forecasts but only **12%** of Gemini's.
- **Draws**: 24 of 104 matches were 90-minute draws, but no agent made a draw its top pick more than 4 times.
- **Self-reflection**: on wrong picks, Gemini admits "incorrect" **86%** of the time, ChatGPT **36%**.

## What's inside

| Config | File | Rows | What |
|---|---|---|---|
| `forecasts` (default) | `data/forecasts.csv` | 416 | One row per (agent, match): probabilities, bet, verbatim reasoning, the reflection fields, outcome, market-implied probs, and settled P&L |
| `metrics` | `data/model_metrics.csv` | 5 | Accuracy / Brier / log-loss / ECE per agent + market |
| `betting_summary` | `data/betting_summary.csv` | 12 | ROI, profit, hit rate per agent and stage |
| `final_factor_probe` | `data/final_factor_probe.csv` | 7 | Final/bronze-only "which narrative factors influenced you" probe |
| `schedule` | `metadata/schedule.csv` | 104 | Fixtures (group + knockout), stage, venue, kickoff |
| `results` | `metadata/results.csv` | 104 | Ground truth incl. penalty shootouts and who advanced |
| `odds` | `metadata/odds.csv` | 104 | Pre-match 1X2 odds with source URL, vig-removed implied probs |
| `raw/` | `raw/*.txt` | | Original per-model transcripts (read-only) + the prompt templates |

**Coverage:** 4 agents × 104 matches = **416 forecasts** and **414 reflections** (two Gemini group reflections are absent in the source and flagged, not imputed).

## Key columns in `forecasts`

- **Identity:** `model`, `match_id`, `phase` (group/knockout), `stage`, `team_a`, `team_b`
- **Truth:** `outcome` ∈ {team_a_win, draw, team_b_win} (90-minute result; a draw for the four penalty ties), `decided_by`, `advanced`
- **Forecast:** `p_a`, `p_draw`, `p_b`, `bet_pick`, `bet_stake`, `reasoning`
- **Reflection:** `refl_outcome`, `refl_calibrated`, `refl_luck`, `refl_missed`, `refl_overweighted`, `refl_bet_diff`, `refl_conf`
- **Market & P&L:** `imp_home/imp_draw/imp_away`, `odds_*_dec`, `is_bet`, `profit`, `contrarian`

## Load it

```python
from datasets import load_dataset
ds = load_dataset("dingjiacheng/wc2026-agents", "forecasts")       # default
odds = load_dataset("dingjiacheng/wc2026-agents", "odds")
```

## FAQ

**Which AI predicted the 2026 World Cup best?** It depends on the metric: ChatGPT and Grok tied on accuracy (68.3%), Claude (Brier 0.4705) and Grok (0.4706) had the best probability scores, and Grok made the most virtual betting profit (+$650). None beat the betting market's Brier score (0.469).

**Did any AI beat the bookmakers?** No, not convincingly. The market's Brier score was better than every agent's, and backing the market favourite every match (+$1,041) out-earned all four.

**Which matches did every AI get wrong?** 32 of 104, 22 of them draws. In the knockout stage: Germany 1-1 Paraguay, Netherlands 1-1 Morocco, Australia 1-1 Egypt, Switzerland 0-0 Colombia (all on penalties), Brazil 1-2 Norway, USA 1-4 Belgium, France 0-2 Spain, France 4-6 England.

**Did AI predict Spain's win in the final?** All four agents rated a Spain win at least as likely as any other outcome before Spain beat Argentina 1-0 (Spain win probability 35% to 44%).

## Ethics

All betting is virtual; the dataset is a measurement instrument, not gambling advice. Records are model outputs and public fixtures, scores and odds; no human subjects or personal data.

## Citation

```bibtex
@misc{ding2026wc2026agents,
  title         = {{FIFA} World Cup 2026 as a Contamination-Free Benchmark for
                   {LLM} Forecasting Agents: Four Models, a Bookmaker, and 104 Matches},
  author        = {Ding, Jiacheng and Guo, Cong},
  year          = {2026},
  eprint        = {2607.17765},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2607.17765}
}
```
