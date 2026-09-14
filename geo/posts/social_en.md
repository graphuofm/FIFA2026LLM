# English social posts

Rules for every post: post from your own account, say you are an author, keep the numbers exactly as written, and reply to comments yourself.

---

## X / Twitter thread (no Premium: every post is under 280 characters)

Attach `docs/figures/og_betting.png` to post 1 and `docs/figures/fig_contrarian.png` to post 4.
Per your preference, the thread does not compare the AIs with the betting market; the paper and project page cover that.

**1/**
We had four AI models forecast and place virtual bets on all 104 matches of the 2026 World Cup: Claude Opus 4.8, ChatGPT (GPT-5.5), Gemini 3.1 Pro and Grok Expert Mode. Real pre-match odds, no hindsight.

Here is what happened 🧵

**2/**
On predictions they were almost clones: the same pick in 96 of 104 matches, accuracy 65-68%.

**3/**
Money is where they split. Virtual profit at real odds:

Grok +$650 (ROI +10.3%)
Gemini +$322
ChatGPT +$118
Claude -$275

Grok's knockout run: +$595, 24 of 32 bets won.

**4/**
Betting against the market mostly hurt. Contrarian bets won 21-40% of the time vs 48-69% when agreeing with it.

Claude bet against the favourite on 58% of its bets. Grok did it on 5%.

**5/**
Shared blind spot: 24 of 104 matches were draws after 90 minutes, but no model made a draw its top pick more than 4 times.

22 of the 32 matches all four got wrong were draws.

**6/**
Everything is open: 416 forecasts with reasoning, 414 self-reflections, odds and results.

Paper: https://arxiv.org/abs/2607.17765
Data: https://huggingface.co/datasets/dingjiacheng/wc2026-agents
Code: https://github.com/graphuofm/FIFA2026LLM

(Optional last line if you want to tag: `@grok @xai`)

---

## LinkedIn post

We ran a 104-match experiment during the 2026 FIFA World Cup: four AI models acting as forecasting agents, betting virtual money at real odds.

Claude Opus 4.8, ChatGPT (GPT-5.5), Gemini 3.1 Pro and Grok (Expert Mode) each searched the web before every match, gave win/draw/loss probabilities, and decided whether and how much to bet. After each match they reflected on the result.

What we found:
• The models agreed on 96 of 104 picks and landed between 65% and 68% accuracy.
• None beat the betting market's Brier score. Backing the market favourite every match made +$1,041.
• Their decisions diverged: Grok +$650, Gemini +$322, ChatGPT +$118, Claude -$275.
• Betting against the market lowered hit rates for every model.
• On their own wrong picks, Gemini admitted the error 86% of the time; ChatGPT 36%.

The takeaway for anyone deploying AI agents: models that look identical on accuracy can behave very differently once they have to act. Evaluate the decisions, not just the predictions.

Paper (arXiv:2607.17765), open dataset and code: https://graphuofm.github.io/FIFA2026LLM/

Joint work with Cong Guo at the University of Memphis. #AI #MachineLearning #LLM #WorldCup2026 #SportsAnalytics

---

## Reddit: r/MachineLearning

**Title:**
[R] WC2026-Agents: Claude Opus 4.8, GPT-5.5, Gemini 3.1 Pro and Grok as forecasting agents on all 104 World Cup 2026 matches, scored against betting odds

**Body:**
I'm one of the authors. We used the 2026 World Cup as a contamination-free testbed for LLM forecasting agents: every match kicked off after the models' training cutoffs.

**Setup.** For each of the 104 matches, four web-enabled models (Claude Opus 4.8, ChatGPT GPT-5.5 high reasoning, Gemini 3.1 Pro, Grok Expert Mode) ran the same loop about 24h before kickoff: search, output 1X2 probabilities plus a virtual bet (stake up to $100, or no bet) with reasoning. After the match they got only the final score and filled an 8-field reflection. The vig-removed pre-match market is scored as a fifth forecaster.

**Results.**

| | Acc | Brier | Log-loss | Profit | ROI |
|---|---|---|---|---|---|
| Market | 68.3% | 0.469 | 0.807 | +$1,041 (flat on fav) | |
| Grok | 68.3% | 0.4706 | 0.803 | +$650 | +10.3% |
| Gemini | 65.4% | 0.4828 | 0.820 | +$322 | +3.7% |
| ChatGPT | 68.3% | 0.4729 | 0.814 | +$118 | +8.0% |
| Claude | 66.3% | 0.4705 | 0.806 | -$275 | -18.1% |

- Same argmax in 96/104 matches; all 8 splits were 3-1.
- No agent beats the market on Brier; log-loss differences vs the market are within noise.
- Contrarian bets (backing a non-favourite) hit 21-40% vs 48-69% conforming.
- Draws: 24/104 matches, but at most 4 draw argmax picks per model.
- Self-reports on wrong picks: "incorrect" 86% (Gemini) down to 36% (ChatGPT).

**Limitations.** One tournament, n=104, virtual stakes, consumer model versions from June-July 2026. Accuracy gaps of 1-3 matches are not significant.

Paper: https://arxiv.org/abs/2607.17765
Dataset (CC BY 4.0): https://huggingface.co/datasets/dingjiacheng/wc2026-agents
Code: https://github.com/graphuofm/FIFA2026LLM

Happy to answer questions about the protocol or the data.

---

## Reddit: r/dataisbeautiful

**Title:** [OC] Four AI models bet virtual money on all 104 matches of the 2026 World Cup at real odds. None beat the betting market.

**Image:** `docs/figures/fig_bankroll.png`

**First comment (required for [OC]):**
Source: our open dataset WC2026-Agents (arXiv:2607.17765). Before each match, Claude Opus 4.8, ChatGPT (GPT-5.5), Gemini 3.1 Pro and Grok gave win/draw/loss probabilities and chose a stake of up to $100, settled at real pre-match odds. The dashed line is a flat bet on the market favourite in every match. Tools: Python, pandas, matplotlib. Data and code: https://github.com/graphuofm/FIFA2026LLM. I'm one of the authors.

---

## Hacker News

**Title:** Show HN: Four LLMs bet on all 104 World Cup 2026 matches at real odds

**URL:** https://graphuofm.github.io/FIFA2026LLM/

**First comment:**
Author here. During the 2026 World Cup we had Claude Opus 4.8, GPT-5.5, Gemini 3.1 Pro and Grok forecast every match about a day before kickoff, with web search, and place a virtual bet. After each match they reflected on the result.

The part I found most interesting: the four models picked the same outcome in 96 of 104 matches, but their betting ranged from -$275 to +$650, mostly because of how often they bet against the market. None of them beat the market's Brier score, and a flat bet on the favourite out-earned all four.

Everything is open (416 forecasts with full reasoning, reflections, odds, results) and one script reproduces the numbers. Happy to answer questions.

---

## Reply template (Reddit / Quora / forums)

Use only when someone directly asks which AI predicts sports best, or whether AI can beat bookmakers. Adapt it to the question; never paste it unprompted.

> Disclosure: I co-authored a study on exactly this. We had Claude Opus 4.8, ChatGPT (GPT-5.5), Gemini 3.1 Pro and Grok forecast all 104 matches of the 2026 World Cup before kickoff and bet virtual money at real odds. Accuracy was nearly identical (65-68%, same pick in 96 of 104 matches) and none beat the betting market's Brier score. In betting, Grok did best (+$650) and Claude worst (-$275), and backing the market favourite every match (+$1,041) beat all of them. Data and paper: https://graphuofm.github.io/FIFA2026LLM/
