"""How good are the LLMs at *prediction* (setting betting aside)?

Key questions:
  1. Are they just echoing the betting market they web-searched?
  2. When they disagree with the market, who's right?
  3. Does averaging the 4 models beat any single one / the market?
  4. Can they discriminate draws at all?
  5. Skill vs naive baselines (Brier skill score).
"""
import math
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
META, PROC = ROOT / "data" / "metadata", ROOT / "data" / "processed"
MODELS = ["claude", "chatgpt", "gemini", "grok"]
OUT = ["team_a_win", "draw", "team_b_win"]

res = pd.read_csv(META / "results.csv").set_index("match_id")
odds = pd.read_csv(META / "odds.csv").set_index("match_id")
frames = {m: pd.read_csv(PROC / f"{m}.csv").set_index("match_id") for m in MODELS}
ids = list(res.index)


def probs(df, mid):
    r = df.loc[mid]
    p = [float(r.pre_p_team_a_win), float(r.pre_p_draw), float(r.pre_p_team_b_win)]
    s = sum(p) or 1
    return [x / s for x in p]


def mkt(mid):
    r = odds.loc[mid]
    return [float(r.imp_home), float(r.imp_draw), float(r.imp_away)]


def onehot(mid):
    o = res.loc[mid, "outcome"]
    return [1 if x == o else 0 for x in OUT]


def brier(p, mid):
    oh = onehot(mid); return sum((p[i] - oh[i]) ** 2 for i in range(3))


def argi(p):
    return max(range(3), key=lambda i: p[i])


def corr(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs); vy = sum((b - my) ** 2 for b in ys)
    return cov / math.sqrt(vx * vy)

# ---- 1. Are they echoing the market? -------------------------------------
print("=" * 68)
print("1. AI probabilities vs MARKET implied probabilities")
print("   (corr over 72x3 points; MAD = mean abs diff; agree = same top pick)")
print("=" * 68)
for m in MODELS:
    xs, ys, mad, agree = [], [], 0.0, 0
    for mid in ids:
        p, q = probs(frames[m], mid), mkt(mid)
        for i in range(3):
            xs.append(p[i]); ys.append(q[i]); mad += abs(p[i] - q[i])
        agree += argi(p) == argi(q)
    print(f"  {m:8s}: corr={corr(xs,ys):.3f}   MAD={mad/(72*3):.3f}   "
          f"top-pick agrees with market {agree}/72 ({agree/72:.0%})")

# ---- 2. When AI disagrees with the market, who is right? ------------------
print("\n" + "=" * 68)
print("2. When AI's top pick != market's top pick, who wins?")
print("=" * 68)
for m in MODELS:
    diff = ai_right = mkt_right = both_wrong = 0
    for mid in ids:
        ap, mp = argi(probs(frames[m], mid)), argi(mkt(mid))
        if ap == mp:
            continue
        diff += 1
        act = OUT.index(res.loc[mid, "outcome"])
        ai_right += ap == act; mkt_right += mp == act
        both_wrong += (ap != act and mp != act)
    print(f"  {m:8s}: disagreed {diff:2d}x -> AI right {ai_right}, "
          f"market right {mkt_right}, both wrong {both_wrong}")

# ---- 3. Ensemble of the 4 models -----------------------------------------
print("\n" + "=" * 68)
print("3. Skill scores (Brier; lower better) + accuracy")
print("=" * 68)


def score(getp):
    b = a = 0.0
    for mid in ids:
        p = getp(mid); b += brier(p, mid); a += argi(p) == OUT.index(res.loc[mid, "outcome"])
    return a / 72, b / 72


def ens(mid):
    ps = [probs(frames[m], mid) for m in MODELS]
    return [sum(p[i] for p in ps) / 4 for i in range(3)]


for name, f in ([(m, (lambda mid, m=m: probs(frames[m], mid))) for m in MODELS]
                + [("ENSEMBLE(4)", ens), ("market", mkt)]):
    acc, bs = score(f)
    print(f"  {name:12s}: accuracy={acc:.3f}  brier={bs:.4f}")

# Brier skill score of each vs market and vs 'always home'
def bss(getp, ref):
    _, bm = score(getp); _, br = score(ref)
    return 1 - bm / br
always_home = lambda mid: [1.0, 0.0, 0.0]
base_rate = lambda mid: [0.44, 0.28, 0.28]
print("\n  Brier Skill Score vs base-rate constant [.44/.28/.28] (>0 = better):")
for name, f in [(m, (lambda mid, m=m: probs(frames[m], mid))) for m in MODELS] + [("market", mkt)]:
    print(f"     {name:8s}: {bss(f, base_rate):+.3f}")

# ---- 4. Can they discriminate draws? -------------------------------------
print("\n" + "=" * 68)
print("4. Draw discrimination: mean P(draw) on the 20 draws vs 52 non-draws")
print("=" * 68)
draw_ids = [mid for mid in ids if res.loc[mid, "outcome"] == "draw"]
non_ids = [mid for mid in ids if res.loc[mid, "outcome"] != "draw"]
for m in MODELS + ["market"]:
    g = (lambda mid: mkt(mid)) if m == "market" else (lambda mid, m=m: probs(frames[m], mid))
    pd_draw = sum(g(mid)[1] for mid in draw_ids) / len(draw_ids)
    pd_non = sum(g(mid)[1] for mid in non_ids) / len(non_ids)
    print(f"  {m:8s}: P(draw) on draws={pd_draw:.3f}  on non-draws={pd_non:.3f}  "
          f"gap={pd_draw-pd_non:+.3f}")

# ---- 5. Do the models agree with each other? -----------------------------
print("\n" + "=" * 68)
print("5. Pairwise agreement of top pick between models")
print("=" * 68)
for i, a in enumerate(MODELS):
    for b in MODELS[i + 1:]:
        ag = sum(argi(probs(frames[a], mid)) == argi(probs(frames[b], mid)) for mid in ids)
        print(f"  {a:8s} vs {b:8s}: {ag}/72 ({ag/72:.0%})")
allsame = sum(len({argi(probs(frames[m], mid)) for m in MODELS}) == 1 for mid in ids)
print(f"  all four identical top pick: {allsame}/72 ({allsame/72:.0%})")
