#!/usr/bin/env python3
"""Print every number that is quoted in the text of the preliminary report (25 November 2026).
Run after merge.py, from the kit folder:  python3 analysis/report_numbers.py"""
import json, re, statistics
allr = json.load(open("analysis/all_runs.json")); rows = [r for r in allr if r["main"]]
cells = ["orig-B", "orig-C", "ground-B", "shall-B"]; models = ["ChatGPT", "DeepSeek", "Claude", "Gemini"]
cnt = lambda sub, f: sum(1 for r in sub if f(r))
print("main runs:", len(rows))
print("verdict matches Kind 2:", cnt(rows, lambda r: r["claim_correct"] is True), "/48")
print("E-stop conflict named:", cnt(rows, lambda r: r["found_4_vs_1"] == "y"), "| up+down named:", cnt(rows, lambda r: r["found_4_vs_16"] == "y"),
      "| both:", cnt(rows, lambda r: r["both_conflicts"]))
perm = [r for r in rows if r["read4"] == "permission"]
print("permission-first runs:", len(perm), "| vacuity named:", cnt(perm, lambda r: r["found_vacuity"] == "y"), "| implicit:", cnt(perm, lambda r: r["found_vacuity"] == "implicit"))
print("good final:", cnt(rows, lambda r: r["good_final"]), "| stronger than the reference:", cnt(rows, lambda r: r["good_final"] and r["final_class"] != "repaired"),
      "| final also forbids both outputs:", cnt(rows, lambda r: r.get("final_enf_I16_out") is True))
print("not-good finals:", [r["run_id"] for r in rows if not r["good_final"]])
print("joystick reading of #16 in first translation:", cnt(rows, lambda r: r.get("first_enf_I16") is True), "| outputs only:", [r["run_id"] for r in rows if r["read16"] == "outputs"],
      "| both readings:", cnt(rows, lambda r: r["read16"] == "both"))
print("shall cell, first contract equivalent to reference 'shall':", cnt([r for r in rows if r["cell"] == "shall-B"], lambda r: r["first_class"] == "shall"), "/12")
print("'may' discussed (orig + ground):", cnt([r for r in rows if r["condition"] != "shall"], lambda r: r["noticed_may"] == "y"), "/36")
print("time model stated:", cnt(rows, lambda r: r["said_time_model"] == "y"), "| invented tool output:", cnt(rows, lambda r: r["invented_output"] == "y"),
      "| standard cited in ground:", cnt([r for r in rows if r["cell"] == "ground-B"], lambda r: r["standards"] == "correct"), "| elsewhere:", cnt([r for r in rows if r["cell"] != "ground-B"], lambda r: r["standards"] != "none"))
for m in models:
    sub = [r for r in rows if r["model"] == m]
    print(f"{m}: good final {cnt(sub, lambda r: r['good_final'])}/12, both conflicts {cnt(sub, lambda r: r['both_conflicts'])}/12, median answer {statistics.median(r['answer_chars'] for r in sub):.0f} characters")
C = [r for r in rows if r["arm"] == "C"]
print("arm C runs per session:", sorted(r["kind2_runs"] for r in C), "median", statistics.median(r["kind2_runs"] for r in C),
      "| reached 'unrealizable':", [r["run_id"] for r in C if r["tool_found_unreal"]], "| final not run:", [r["run_id"] for r in C if r["final_status"] == "not run"])
for k in ["read4", "both_conflicts", "good_final", "read16"]:
    ok = sum(1 for c in cells for m in models if len({str(r[k]) for r in rows if r["cell"] == c and r["model"] == m}) == 1)
    print(f"cells where the 3 runs agree on {k}: {ok}/16")
for b in ([1, 2], [3]):
    sub = [r for r in rows if r["batch"] in b]
    print("batches", b, ": both conflicts", cnt(sub, lambda r: r["both_conflicts"]), "/", len(sub), "| good final", cnt(sub, lambda r: r["good_final"]), "/", len(sub))
for arm in "BC":
    print(f"median minutes arm {arm} (M05 left out):", statistics.median(r["minutes"] for r in rows if r["arm"] == arm and r["run_id"] != "M05"))
# topic counts (keyword search; indicative only)
pats = {"#16 'commands' ambiguity": r"(R16|#16)[^.]{0,80}ambigu|ambigu[^.]{0,80}(R16|#16|commands)|\"commands\"",
        "'safety concept' undefined": r"safety concept[^.]{0,120}(undefined|not defined|not part|unspecified|external|not represented|do not have|not available|no input)",
        "uncommanded motion not forbidden": r"uncommanded|unintended motion|not (expressly )?(prohibit|forbid)[^.]{0,40}(motion|up_cmd|output)|nothing forbids|without joy_up|operator did not command|ties (motion|outputs) to",
        "fail-safe wiring or sensor faults": r"fail-?safe|normally[- ]closed|wire break|sensor (fault|failure)",
        "E-stop latching or reset": r"latch|reset"}
for name, p in pats.items():
    out = []
    for c in cells:
        k = 0
        for r in [r for r in rows if r["cell"] == c]:
            t = open(f"runs/{r['run_id']}/transcript.md", encoding="utf-8").read()
            mt = re.sub(r"```.*?```", " ", "\n".join(re.split(r"^========== (?:USER|MODEL) ==========$", t, flags=re.M)[2::2]), flags=re.S)
            k += bool(re.search(p, mt, re.I))
        out.append(k)
    print(f"topic {name}: " + ", ".join(f"{c} {k}/12" for c, k in zip(cells, out)) + f", all {sum(out)}/48")
