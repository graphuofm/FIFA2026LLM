# Market-citation code: human validation criteria

Written criteria used for the blind validation reported in the KDD rebuttal
(n = 40 of a 95-item stratified sample drawn by `src/rebuttal_lexicon_sample.py`).

**Question for each pre-match forecast:** does the reasoning text reference
betting-market price information?

**Label 1** if the text contains any of:

- odds in any notation: American (`-150`, `+250`), fractional (`8/15`, `2/7`), decimal
- implied probability, market price, "market implies", de-vigged market
- "betting odds", "betting markets", "betting favorite"
- a sportsbook or prediction-market name (DraftKings, FanDuel, bet365, Kalshi, Vegas)

**Label 0** if the text only discusses squad quality, recent form, injuries, FIFA
ranking, head-to-head, home advantage, xG or similar, with no price information.

**Boundary rules, fixed before labelling:**

| Case | Label |
|---|---|
| "clear favourite" with no price attached | 0 |
| a percentage from a forecasting model (e.g. the Opta supercomputer) rather than a market | 0 |
| both a model forecast and odds in the same text | 1 |

**Procedure.** One author labelled 40 items without seeing the code's output
(first pass). The items where the author and the code disagreed were then
re-read against these criteria (adjudication pass). Both passes are reported:

| Pass | Agreement | Cohen's kappa | Precision | Recall |
|---|---|---|---|---|
| First (blind) | 0.775 | 0.54 | 0.731 | 0.905 |
| After adjudication | 0.950 | 0.886 | 1.000 | 0.929 |

Both disagreements remaining after adjudication are items the code missed, so on
this subsample the code under-counts rather than over-counts market citation.

Raw labels: `lexicon_validation_human_labels.csv`.
Summary: `lexicon_validation_result.csv`.
