#!/usr/bin/env python3
"""Automatic scores for every run (Kind 2): first and final contract, readings, enforcement, tool use."""
import csv, json, os, re, sys, glob
sys.path.insert(0, os.path.abspath('.'))
import score_ex1 as S
plan = {r["run_id"]: r for r in csv.DictReader(open("run_plan.csv"))}
rows = []
for rid in sorted(os.listdir("runs"), key=lambda x: int(x[1:])):
    d = f"runs/{rid}"; p = plan.get(rid, {})
    arm, cond = p.get("arm"), p.get("condition")
    atts = sorted([f for f in glob.glob(f"{d}/attempt*.lus") if re.search(r"attempt\d+\.lus$", f)], key=lambda f: int(re.search(r"attempt(\d+)\.lus$", f).group(1)))
    atts = [a for a in atts if not a.endswith("_compare.lus")]
    if not atts:
        continue
    first = atts[0]
    final = f"{d}/final.lus" if os.path.exists(f"{d}/final.lus") else atts[-1]
    r = {"run_id": rid, "model": p.get("model"), "arm": arm, "condition": cond, "status": p.get("status", "")}
    meta = open(f"{d}/meta.txt", encoding="utf-8").read()
    g = lambda k: (re.search(r"^" + re.escape(k) + r": *(.*)$", meta, re.M) or [None, ""])[1].strip()
    r.update({"exact_model": g("exact model name"), "setting": g("reasoning setting"), "start": g("start"), "end": g("end")})
    for tag, path in (("first", first), ("final", final)):
        rz, c = S.realizability(path), S.compare(path)
        r[tag + "_file"] = os.path.basename(path)
        r[tag + "_syntax_ok"] = rz["syntax_ok"]
        r[tag + "_verdict"] = rz["result"] or ("syntax error" if not rz["syntax_ok"] else "")
        r[tag + "_conflict"] = rz["conflict"]
        r[tag + "_class"] = c.get("class", "") if not c.get("error") else "not comparable"
        r[tag + "_reading4"] = S.reading4(c) if not c.get("error") else ""
        r[tag + "_reading16"] = S.reading16(c) if not c.get("error") else ""
        for k, v in c.get("enforces", {}).items():
            r[f"{tag}_enf_{k}"] = v
        r[tag + "_never_moves_passes"] = c.get("never_moves_passes", "")
        r[tag + "_n_assumes"] = c.get("n_assumes", 0)
        r[tag + "_compare_error"] = c.get("error", "")
    if arm == "C":
        verdicts = []
        for a in atts:
            out = open(a.replace(".lus", "_out.txt"), encoding="utf-8", errors="replace").read() if os.path.exists(a.replace(".lus", "_out.txt")) else ""
            m = re.search(r"proven (un)?realizable", out)
            verdicts.append(("unrealizable" if m.group(1) else "realizable") if m else "syntax error")
        r["kind2_runs"] = len(atts)
        r["run_verdicts"] = " > ".join(verdicts)
        r["final_tested_by_kind2"] = not os.path.exists(f"{d}/final.lus")
    else:
        r["kind2_runs"] = 0; r["run_verdicts"] = ""; r["final_tested_by_kind2"] = False
        r["proposed_correction"] = os.path.exists(f"{d}/attempt2.lus")
    rows.append(r)
json.dump(rows, open("analysis/auto_scores.json", "w"), indent=1)
cols = []
for r in rows:
    cols += [k for k in r if k not in cols]
with open("analysis/auto_scores.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(len(rows), "runs scored")
