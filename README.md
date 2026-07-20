# FIFA World Cup 2026 × LLMs

Paired **forecast + reflection** data from four frontier LLMs acting as
autonomous sports forecasters across **all 104 matches** of the 2026 FIFA World
Cup (11 June – 19 July 2026), with ground truth, real pre-match betting odds,
a full analysis pipeline, and an ACM-format paper.

> **Models.** Claude Opus 4.8 · ChatGPT (GPT-5.5 Thinking, high reasoning) ·
> Gemini 3.1 Pro · Grok (Expert Mode). Each was web-enabled and held constant
> across the tournament, given an identical two-prompt protocol per match.

## The headline findings

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **The four models converge** — identical top pick in **92%** of matches, so accuracy (65–68%) can't tell them apart, and **none beats the market** (Brier 0.469). | `fig_convergence`, `fig_leaderboard` |
| 2 | **Betting separates them** — Grok **+$650** (ROI +10.3%), ChatGPT +$118, Gemini +$322, Claude **−$275**. | `fig_bankroll` |
| 3 | **Fading the market loses money for everyone** — contrarian bets hit 21–40% (ROI −24…+33%); Claude fades the market on **57%** of bets and bleeds. | `fig_contrarian` |
| 4 | **Different information diets, same picks** — Claude cites the market in **100%** of forecasts, Gemini in **12%**. | `fig_reasoning_factors` |
| 5 | **Reflection is a fingerprint** — on its own wrong picks, Gemini admits “incorrect” **86%** of the time, ChatGPT only **36%**. | `fig_reflection` |
| 6 | **8 matches fooled everyone** — all backed the favourite; recurring blind spots: underdog defensive organisation (62%) and penalty/knockout variance (32%). | `fig_upsets` |

## Repository layout

```
data/
  raw/          original per-model transcripts (read-only)   {model}.txt, {model}_knockout.txt
  metadata/     schedule*.csv, results*.csv, odds*.csv        (fixtures, ground truth, 1X2 odds)
  processed/    {model}.csv (group), {model}_knockout.csv, final-factor probe
  analysis/     tidy 104-match table + every analysis output CSV
src/            parsing + analysis + figure code (see below)
paper/          main.tex (ACM sigconf) + references.bib + figures/
reports/        earlier group-stage descriptive report
```

## Dataset at a glance

- **104 matches** (m01–m72 group, m73–m104 knockout). One row per match per model.
- **416 pre-match forecasts** and **414 reflections** (2 Gemini group reflections
  are missing in the source and flagged, not dropped).
- Per forecast: `probabilities` (team_a_win/draw/team_b_win), `bet` (pick + stake),
  free-text `reasoning`, `key_sources`. Per reflection: outcome self-label,
  calibration self-judgement, luck, missed/over-weighted factor, counterfactual,
  would-bet-differently, confidence.
- Ground truth includes **penalty shootouts**: knockout `outcome` is the
  90-minute result (a `draw` for the 4 penalty ties — how a 1X2 bet settles),
  with `decided_by`, `pen_a/pen_b`, and `advanced` recorded separately.
- **Odds**: opening 1X2 lines (mostly DraftKings previews) with a source URL per
  match, vig-removed to implied probabilities, cross-checked against the odds the
  models themselves cited.

See [`data/README.md`](data/README.md) for the full schema and known source
quirks.

## Reproduce

```bash
pip install -r requirements.txt
python src/run_all.py          # rebuild every processed/analysis CSV + all figures
cd paper && latexmk -pdf main.tex   # build the paper (needs a LaTeX install)
```

Individual stages (run from `src/`): `build_per_model.py` + `results_truth.py`
(group), `build_knockout.py`, `build_odds_knockout.py`, `analysis.py`,
`reasoning.py`, `betting.py`, `figures.py`, `figures_betting.py`.

## How the analysis works (short version)

- **Accuracy / Brier / log-loss** vs the 3-way outcome; **ECE** + reliability
  curves for top-pick calibration; **convergence** = fraction of matches all four
  share an argmax.
- **Betting**: each model's own pick+stake settled at that match's decimal odds
  on the 90-minute result → bankroll, ROI, hit-rate. A **contrarian** bet fades
  the market favourite; we compare contrarian vs conforming P&L.
- **Market baseline**: vig-removed implied probabilities scored as a 5th forecaster.
- **Content coding**: reasoning/reflection text coded into 13 factor categories
  with a transparent keyword lexicon (`src/reasoning.py`), no model in the loop.

## Citation

```bibtex
@misc{ding2026wc2026agents,
  title        = {{FIFA} World Cup 2026 as a Contamination-Free Benchmark for
                  {LLM} Forecasting Agents: Four Models, a Bookmaker, and 104 Matches},
  author       = {Ding, Jiacheng and Guo, Cong and Xu, Jason},
  year         = {2026},
  note         = {Dataset and benchmark. Under review, KDD 2027 Datasets and Benchmarks Track},
  howpublished = {\url{https://github.com/graphuofm/FIFA2026LLM}}
}
```

## Licence

Code under [MIT](LICENSE). Dataset (`data/`) under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — please cite if you
use it. Betting figures are for research only and are not gambling advice.
