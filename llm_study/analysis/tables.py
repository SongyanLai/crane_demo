import json, re, statistics
rows = [r for r in json.load(open("analysis/all_runs.json")) if r["main"]]
models = ["ChatGPT", "DeepSeek", "Claude", "Gemini"]
cells = [("orig-B", "Original, no tool (B)"), ("orig-C", "Original, Kind 2 (C)"), ("ground-B", "Domain notes (B)"), ("shall-B", "\\#4 as `shall' (B)")]
T = "report/tables/"
import os; os.makedirs(T, exist_ok=True)
def n(sub, f): return sum(1 for r in sub if f(r))
# --- per cell summary
L = ["\\begin{tabular}{lcccc}", "\\toprule", " & " + " & ".join(l for _, l in cells) + " \\\\", "\\midrule"]
def row(label, f, den=None):
    vals = []
    for c, _ in cells:
        sub = [r for r in rows if r["cell"] == c]
        d = den(sub) if den else len(sub)
        vals.append(f"{n(sub, f)}/{d}" if d else "--")
    L.append(label + " & " + " & ".join(vals) + " \\\\")
row("\\#4 read as an obligation (first translation)", lambda r: r["read4"] != "permission")
row("\\#16 joystick reading kept (first translation)", lambda r: r.get("first_enf_I16") is True)
row("Verdict on own translation matches Kind 2", lambda r: r["claim_correct"] is True)
row("E-stop conflict (\\#4 vs \\#1) named", lambda r: r.get("found_4_vs_1") == "y")
row("Up+down conflict (\\#4 vs \\#16) named", lambda r: r.get("found_4_vs_16") == "y")
row("Both conflicts named", lambda r: r["both_conflicts"])
row("Vacuity named (runs with the permission reading)", lambda r: r["read4"] == "permission" and r.get("found_vacuity") == "y",
    den=lambda sub: sum(1 for r in sub if r["read4"] == "permission"))
row("Final contract requires lowering", lambda r: r["final_requires_lowering"])
row("Good final contract", lambda r: r["good_final"])
med = []
for c, _ in cells:
    mins = [r["minutes"] for r in rows if r["cell"] == c and not (r["run_id"] == "M05")]
    med.append(f"{statistics.median(mins):.0f}")
L.append("Median duration in minutes & " + " & ".join(med) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(T + "tab_cells.tex", "w").write("\n".join(L) + "\n")
# --- per model and cell: both conflicts named / good final
L = ["\\begin{tabular}{l" + "c" * 4 + "}", "\\toprule", "Model & " + " & ".join(l for _, l in cells) + " \\\\", "\\midrule"]
for m in models:
    vals = []
    for c, _ in cells:
        sub = [r for r in rows if r["cell"] == c and r["model"] == m]
        vals.append(f"{n(sub, lambda r: r['both_conflicts'])}/3 \\,$\\mid$\\, {n(sub, lambda r: r['good_final'])}/3")
    L.append(m + " & " + " & ".join(vals) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(T + "tab_models.tex", "w").write("\n".join(L) + "\n")
# --- arm C tool use
L = ["\\begin{tabular}{llcllc}", "\\toprule", "Run & Model & Kind 2 runs & Verdicts in order & Final contract & Good final \\\\", "\\midrule"]
fs = {"tested": "last tested one", "equivalent to tested": "same rules as run 1", "not run": "not run by the model"}
abbr = {"realizable": "R", "unrealizable": "U", "syntax error": "S"}
for r in sorted([r for r in rows if r["arm"] == "C"], key=lambda r: (models.index(r["model"]), int(r["run_id"][1:]))):
    seq = " ".join(abbr[v] for v in r["run_verdicts"].split(" > "))
    L.append(f"{r['run_id']} & {r['model']} & {r['kind2_runs']} & {seq} & {fs[r['final_status']]} & {'yes' if r['good_final'] else 'no'} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(T + "tab_toolC.tex", "w").write("\n".join(L) + "\n")
# --- per-run appendix table
code = {"y": "yes", "n": "no", "implicit": "impl.", "n.a.": "n.a.", "?": "?"}
r4s = {"permission": "perm.", "obligation": "oblig.", "obligation, both exceptions": "oblig.*", "obligation, E-stop exception": "oblig.+"}
L = ["\\begin{longtable}{llllllllllll}", "\\caption{All 48 main runs. Reading of \\#4 and \\#16 in the first translation; claim = the model's verdict on its own translation (ok or conflict); E1 = E-stop conflict named; E16 = up+down conflict named; Vac = vacuity named; Final \\#4 = reading of \\#4 in the final contract; Good = good final contract; Min = minutes. oblig.* = obligation with both exceptions; impl. = handled but not named.}\\label{tab:runs}\\\\",
     "\\toprule", "Run & Model & Arm & Cond. & \\#4 & \\#16 & Claim & E1 & E16 & Vac & Final \\#4 & Good \\\\", "\\midrule", "\\endfirsthead",
     "\\toprule", "Run & Model & Arm & Cond. & \\#4 & \\#16 & Claim & E1 & E16 & Vac & Final \\#4 & Good \\\\", "\\midrule", "\\endhead"]
for r in sorted(rows, key=lambda r: int(r["run_id"][1:])):
    L.append(" & ".join([r["run_id"], r["model"], r["arm"], r["condition"], r4s[r["read4"]], r["read16"], r["claim_verdict"],
                         code[r["found_4_vs_1"]], code[r["found_4_vs_16"]], code[r["found_vacuity"]], r4s[r["final_read4"]],
                         "yes" if r["good_final"] else "no"]) + " \\\\")
L += ["\\bottomrule", "\\end{longtable}"]
open(T + "tab_runs.tex", "w").write("\n".join(L) + "\n")
# --- numbers used in the text
S = {}
S["both_all"] = n(rows, lambda r: r["both_conflicts"]); S["good_all"] = n(rows, lambda r: r["good_final"])
S["claim_all"] = n(rows, lambda r: r["claim_correct"] is True)
S["e1_all"] = n(rows, lambda r: r["found_4_vs_1"] == "y"); S["e16_all"] = n(rows, lambda r: r["found_4_vs_16"] == "y")
S["perm_runs"] = n(rows, lambda r: r["read4"] == "permission"); S["vac_y"] = n(rows, lambda r: r["read4"] == "permission" and r["found_vacuity"] == "y")
S["vac_impl"] = n(rows, lambda r: r["read4"] == "permission" and r["found_vacuity"] == "implicit")
S["uncmd"] = n(rows, lambda r: r["mentions_uncommanded"])
for arm in "BC":
    S[f"min_{arm}"] = statistics.median([r["minutes"] for r in rows if r["arm"] == arm and r["run_id"] != "M05"])
json.dump(S, open("analysis/numbers.json", "w"), indent=1); print(S)
