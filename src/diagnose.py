"""Quick diagnostics on parse coverage before building final CSVs."""
import parse_core as pc

MODELS = ["claude", "chatgpt", "gemini", "grok"]

for model in MODELS:
    text = pc.read(model)
    matches = pc.split_matches(text)
    n = len(matches)
    pre_ok = pre_err = post_ok = post_err = t30 = score_ok = 0
    err_samples = []
    for hi, (header, body) in enumerate(matches):
        resp, errs = pc.extract_responses(body)
        if resp["pre"]:
            if resp["pre"]["json"] is not None:
                pre_ok += 1
            else:
                pre_err += 1
                if len(err_samples) < 3:
                    err_samples.append((hi, "pre", resp["pre"]["error"]))
        if resp["t30"]:
            t30 += 1
        if resp["post"]:
            if resp["post"]["json"] is not None:
                post_ok += 1
            else:
                post_err += 1
                if len(err_samples) < 3:
                    err_samples.append((hi, "post", resp["post"]["error"]))
        if pc.extract_score_block(body):
            score_ok += 1
    print(f"\n=== {model} ===")
    print(f"  matches split      : {n}")
    print(f"  pre  parsed/failed : {pre_ok}/{pre_err}")
    print(f"  t30  present       : {t30}")
    print(f"  post parsed/failed : {post_ok}/{post_err}")
    print(f"  score extracted    : {score_ok}")
    for hi, kind, err in err_samples:
        print(f"    ! match#{hi} {kind}: {err[:90]}")
