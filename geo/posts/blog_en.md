# Long-form article (Medium / Substack / dev.to / LinkedIn article / Hashnode)

Publishing notes:
- Where the platform allows, set the canonical URL to https://graphuofm.github.io/FIFA2026LLM/ (Medium: "Import a story"; dev.to: `canonical_url` in front matter).
- Cover image: `docs/figures/og_betting.png`. Inline images: `fig_bankroll.png`, `fig_contrarian.png`, `fig_upsets.png` from `docs/figures/`.
- Tags: AI, Machine Learning, World Cup, Sports Analytics, LLM.
- Keep the disclosure line at the top.

Title options (pick one):
1. We had ChatGPT, Claude, Gemini and Grok bet on all 104 World Cup matches. The bookmaker still won.
2. Which AI predicted the 2026 World Cup best? We tracked every match.
3. Four AI models, one bookmaker, 104 World Cup matches: what we learned

---

*Disclosure: I am one of the two authors of the WC2026-Agents paper (arXiv:2607.17765). All data and code are open.*

When the 2026 World Cup kicked off on 11 June, we gave four AI models the same job for every one of its 104 matches. About a day before kickoff, each model searched the web, wrote down probabilities for a win, a draw and a loss, and placed a virtual bet of up to $100. After the final whistle, each model was told the score and asked to reflect on what it got right and wrong.

The four were Claude Opus 4.8, ChatGPT (GPT-5.5 with high reasoning), Gemini 3.1 Pro and Grok in Expert Mode. We used the same versions for the whole tournament. Every match took place after the models' training cutoffs, so none of them could have seen a result. We also scored a fifth forecaster: the betting market itself, using real pre-match odds with the bookmaker's margin removed.

## The short answer

| Forecaster | Accuracy | Brier (lower is better) | Virtual profit | ROI |
|---|---:|---:|---:|---:|
| Betting market | 68.3% | 0.469 | +$1,041 (flat stake on the favourite) | |
| Grok (Expert Mode) | 68.3% | 0.4706 | +$650 | +10.3% |
| Gemini 3.1 Pro | 65.4% | 0.4828 | +$322 | +3.7% |
| ChatGPT (GPT-5.5) | 68.3% | 0.4729 | +$118 | +8.0% |
| Claude Opus 4.8 | 66.3% | 0.4705 | -$275 | -18.1% |

If you only want one sentence: the four AIs predicted almost identically, none of them beat the bookmaker, and they made very different amounts of money doing it.

## 1. They agree with each other almost all the time

The four models picked the same outcome in 96 of the 104 matches. In the 8 matches where they split, it was always three against one, and the odd one out was Gemini six times. Their accuracy spans just three matches, from 65.4% to 68.3%. In the 32 knockout matches, all four got exactly 23 right.

This matters for anyone comparing models on a leaderboard. On a task like this, accuracy cannot tell four frontier models apart.

## 2. The bookmaker is still the one to beat

We turned the pre-match odds into probabilities and scored them the same way as the models. The market's Brier score was 0.469, better than every model. On log-loss, Grok (0.803) and Claude (0.806) came in a hair under the market (0.807), but over 104 matches that is noise, not an edge.

The simplest possible strategy, putting the same stake on the market favourite in every match, finished at +$1,041. No AI earned more.

## 3. The money is where they differ

With nearly identical predictions, their betting results ranged from a $275 loss to a $650 profit. The difference came from decisions, not beliefs:

- **Grok** bet on every match, won 70 of 104 bets, and finished +$650. Most of that came in the knockout stage: 24 wins from 32 bets and +$595.
- **Gemini** staked by far the most ($8,660 in total) and made +$322.
- **ChatGPT** was the most selective, betting on only 55 matches, and made +$118.
- **Claude** bet small but often against the favourite, won only 24 of 73 bets, and lost $275.

## 4. Going against the market mostly hurt

We counted a bet as contrarian when it backed an outcome other than the market favourite. Claude did this on 57% of its bets, ChatGPT on 36%, Gemini on 14% and Grok on just 5%.

Contrarian bets won 21% to 40% of the time, compared with 48% to 69% for bets that agreed with the market. They cost Claude $167, Gemini $112 and ChatGPT $38. Grok placed only five contrarian bets, and those made $64, which is too few to read much into.

The lesson we take from this: when an AI disagrees with a liquid market, treat it as a warning sign rather than a hidden edge.

## 5. They read the world differently

We coded every piece of pre-match reasoning into 13 factors. Claude mentioned the betting odds in 100% of its forecasts, ChatGPT in 92%, Grok in 63% and Gemini in only 12%. Grok leaned hardest on squad quality (88%) and recent form (76%). Almost nobody talked about head-to-head records or fatigue.

Different reading lists, same answers. That is part of why the predictions converge while the bets do not.

## 6. Nobody predicts draws

24 of the 104 matches were level after 90 minutes. Yet no model made a draw its top pick more than four times. The models were not naive about it: they gave draws around 23% probability on average, which matches reality. The problem is that a draw is almost never the single most likely outcome, so a forecaster that always picks its top outcome will miss nearly every draw. Of the 32 matches that all four models got wrong, 22 were draws.

## 7. The upsets nobody saw

Eight knockout matches fooled every model: Germany 1-1 Paraguay, Netherlands 1-1 Morocco, Australia 1-1 Egypt and Switzerland 0-0 Colombia (all decided on penalties), plus Brazil 1-2 Norway, USA 1-4 Belgium, France 0-2 Spain and France 4-6 England. The Germany match is the starkest: the models gave Germany a 75% chance on average.

Asked afterwards what they had missed, the models kept naming the same thing: the underdog's defensive organisation (62% of wrong picks). The factor they said they had over-weighted was the favourite's squad quality (40%).

## 8. Some models admit mistakes, others don't

After a wrong pick, we asked each model to label its own forecast. Gemini called it incorrect 86% of the time. Grok did so 61% of the time, Claude 49% and ChatGPT only 36%, with the rest described as "partially correct" or even "correct". If you plan to let an AI grade its own work, this is worth knowing.

## And the final?

Spain beat Argentina 1-0 on 19 July. Before kickoff, all four models rated a Spain win at least as likely as any other result, with probabilities from 35% to 44%.

## What we think this means

- If you just need a probability, these four models are interchangeable, and the betting market is at least as good.
- If an AI is going to act on its forecast, whether that means spending a budget or placing an order, judge it on its decisions, not its accuracy.
- An AI that frequently disagrees with a well-informed market is more likely wrong than insightful.
- The limits are real: one tournament, 104 matches, virtual money, and model versions from June and July 2026.

## Get the data

Everything is open: 416 forecasts with full reasoning, 414 reflections, results including penalty shootouts, and the odds.

- Paper: https://arxiv.org/abs/2607.17765
- Dataset: https://huggingface.co/datasets/dingjiacheng/wc2026-agents
- Code: https://github.com/graphuofm/FIFA2026LLM
- Project page with FAQ: https://graphuofm.github.io/FIFA2026LLM/

```python
from datasets import load_dataset
forecasts = load_dataset("dingjiacheng/wc2026-agents", "forecasts")
```

*Jiacheng Ding and Cong Guo, University of Memphis. All betting in this study was virtual; nothing here is gambling advice.*
