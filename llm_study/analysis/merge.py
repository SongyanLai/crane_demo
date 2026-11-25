import json, re, datetime
auto = {r["run_id"]: r for r in json.load(open("analysis/auto_scores.json"))}
man = json.load(open("analysis/manual_scores.json"))
rows = []
for rid, a in auto.items():
    if rid == "M01":   # excluded run
        continue
    r = dict(a); r.update(man.get(rid, {}))
    r["main"] = rid != "M09"
    r["cell"] = f'{r["condition"]}-{r["arm"]}'
    # minutes
    try:
        f = "%Y-%m-%d %H:%M"
        r["minutes"] = (datetime.datetime.strptime(r["end"], f) - datetime.datetime.strptime(r["start"], f)).seconds / 60
    except Exception:
        r["minutes"] = None
    # batch: 1-2 = before randomisation, 3 = randomised
    n = int(rid[1:]); r["batch"] = 3 if n >= 35 else (1 if n <= 16 or n in (33, 34) else 2)
    # translation of the original: first syntactically valid contract (M13: attempt2)
    if r["first_verdict"] == "syntax error" and r["arm"] == "C":
        r["orig_verdict"] = r["run_verdicts"].split(" > ")[1]
    else:
        r["orig_verdict"] = r["first_verdict"]
    exp = {"ok": "realizable", "conflict": "unrealizable"}.get(r.get("claim_verdict"))
    r["claim_correct"] = (exp == r["orig_verdict"]) if exp else None
    r["both_conflicts"] = r.get("found_4_vs_1") == "y" and r.get("found_4_vs_16") == "y"
    r["good_final"] = (r["final_verdict"] == "realizable" and r.get("final_enf_I01") is True and r.get("final_enf_I03") is True
                       and r.get("final_enf_I04_repaired") is True and r.get("final_enf_I16") is True and r.get("final_never_moves_passes") is False)
    r["final_requires_lowering"] = r.get("final_enf_I04_repaired") is True
    r["final_keeps_16_operator"] = r.get("final_enf_I16") is True
    t = open(f"runs/{rid}/transcript.md", encoding="utf-8").read()
    model_text = "\n".join(re.split(r"^========== (?:USER|MODEL) ==========$", t, flags=re.M)[2::2])
    r["mentions_uncommanded"] = bool(re.search(r"uncommanded|unintended motion|not (expressly )?prohibit uncommanded|without joy_up|operator did not command|unrequested|ties (motion|outputs) to", model_text, re.I))
    r["mentions_output_exclusion"] = bool(re.search(r"never (be )?(both|true at the same time|active at the same time)|not \(up_cmd and down_cmd\)|mutual(ly)? exclusi", model_text, re.I))
    r["answer_chars"] = len(model_text)
    rows.append(r)
json.dump(rows, open("analysis/all_runs.json", "w"), indent=1)
main = [r for r in rows if r["main"]]
print("main runs:", len(main), "| cells:", sorted({r['cell'] for r in main}))
def pct(k, n): return f"{k}/{n}"
for cell in ["orig-C", "orig-B", "ground-B", "shall-B"]:
    sub = [r for r in main if r["cell"] == cell]
    r4 = {}
    for r in sub: r4[r["first_reading4"]] = r4.get(r["first_reading4"], 0) + 1
    r16 = {}
    for r in sub: r16[r["first_reading16"]] = r16.get(r["first_reading16"], 0) + 1
    print(f"\n== {cell} ({len(sub)} runs) first reading #4: {r4} | #16: {r16}")
    for k in ["claim_correct", "both_conflicts", "good_final", "final_requires_lowering", "final_keeps_16_operator", "mentions_uncommanded", "mentions_output_exclusion"]:
        print(f"   {k:26s} {sum(1 for r in sub if r[k] is True)}/{len(sub)}")
    for k in ["found_4_vs_1", "found_4_vs_16", "found_vacuity"]:
        c = {}
        for r in sub: c[r[k]] = c.get(r[k], 0) + 1
        print(f"   {k:26s} {c}")
    print("   minutes median:", sorted(r["minutes"] for r in sub)[len(sub)//2], "| per model good_final:", {m: sum(r["good_final"] for r in sub if r["model"] == m) for m in ["ChatGPT","DeepSeek","Claude","Gemini"]})

# ---- second pass: readings from enforcement flags, tool use, stability, order, effort
def r4(r, t="first"):
    if r.get(f"{t}_enf_I04_shall"): return "obligation"
    if r.get(f"{t}_enf_I04_estop_only"): return "obligation, E-stop exception"
    if r.get(f"{t}_enf_I04_repaired"): return "obligation, both exceptions"
    return "permission"
for r in rows:
    r["read4"] = r4(r, "first"); r["final_read4"] = r4(r, "final")
    r["read16"] = r["first_reading16"]
    r["tool_found_unreal"] = "unrealizable" in r.get("run_verdicts", "")
    if r["arm"] == "C":   # was the final contract run by Kind 2 during the session?
        refs = ("may", "may_out16", "shall", "repaired", "shall_out16", "repaired_out16")
        if r["final_tested_by_kind2"]:
            r["final_status"] = "tested"
        elif r["final_class"] in refs and r["kind2_runs"] == 1 and r["first_class"] == r["final_class"]:
            r["final_status"] = "equivalent to tested"   # differs from the tested file only in comments or layout
        else:
            r["final_status"] = "not run"
json.dump(rows, open("analysis/all_runs.json", "w"), indent=1)
main = [r for r in rows if r["main"]]
models = ["ChatGPT", "DeepSeek", "Claude", "Gemini"]
cells = ["orig-B", "orig-C", "ground-B", "shall-B"]
print("\n### reading of #4 in the first translation, per cell and model (P=permission, O=obligation, Ob=both exceptions)")
for c in cells:
    print(c, {m: [ {"permission":"P","obligation":"O","obligation, both exceptions":"Ob","obligation, E-stop exception":"Oe"}[r["read4"]] for r in main if r["cell"]==c and r["model"]==m] for m in models})
print("\n### reading of #16 (first), per cell and model")
for c in cells:
    print(c, {m: [r["read16"] for r in main if r["cell"]==c and r["model"]==m] for m in models})
print("\n### final reading of #4 (after correction), per cell and model")
for c in cells:
    print(c, {m: [{"permission":"P","obligation":"O","obligation, both exceptions":"Ob","obligation, E-stop exception":"Oe"}[r["final_read4"]] for r in main if r["cell"]==c and r["model"]==m] for m in models})
print("\n### arm C tool use")
for r in [r for r in main if r["arm"]=="C"]:
    print(f'{r["run_id"]} {r["model"]:8s} runs={r["kind2_runs"]} seq=[{r["run_verdicts"]}] final_tested={r["final_tested_by_kind2"]} good_final={r["good_final"]} minutes={r["minutes"]}')
print("\n### stability: do the 3 runs of a cell agree?")
agree = {k: 0 for k in ["read4", "both_conflicts", "good_final", "read16"]}
ncell = 0
for c in cells:
    for m in models:
        sub = [r for r in main if r["cell"]==c and r["model"]==m]
        ncell += 1
        for k in agree:
            if len({str(r[k]) for r in sub}) == 1: agree[k] += 1
print({k: f"{v}/{ncell}" for k, v in agree.items()})
print("\n### order check: batches 1-2 vs batch 3 (randomised)")
for b in ([1,2],[3]):
    sub = [r for r in main if r["batch"] in b]
    print(b, len(sub), {k: sum(1 for r in sub if r[k] is True) for k in ["both_conflicts","good_final","claim_correct"]},
          "obligation-first:", sum(1 for r in sub if r["read4"]!="permission"))
print("\n### effort (minutes, median and range) per arm and model")
for arm in ["B","C"]:
    for m in models:
        mins = sorted(r["minutes"] for r in main if r["arm"]==arm and r["model"]==m)
        print(arm, m, "median", mins[len(mins)//2], "range", mins[0], "-", mins[-1], "| answer chars median", sorted(r["answer_chars"] for r in main if r["arm"]==arm and r["model"]==m)[len(mins)//2])
