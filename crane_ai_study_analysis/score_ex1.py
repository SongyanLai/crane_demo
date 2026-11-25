#!/usr/bin/env python3
"""Score one AI run of Example 1 (intents #1, #3, #4, #16) against the reference.

Usage:
    python3 score_ex1.py R01           automatic checks, then a few questions
    python3 score_ex1.py R01 --auto    automatic checks only
    python3 score_ex1.py R01 --manual  automatic checks + manual scores from runs/R01/manual.json (rater's file)

The run folder runs/R01/ must contain attempt1.lus (the AI's first contract)
and, if there are more, attempt2.lus, attempt3.lus, ... (the last one = final).
Needs kind2 and z3 on PATH.
"""
import csv, datetime, glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "run_log.csv")

# Reference rules of Example 1 (see reference/ and assumption_sheet.md)
REF_RULES = {
    "I01": "(estop => (not up_cmd and not down_cmd))",
    "I03": "(upper_limit => not up_cmd)",
    "I04_shall": "((upper_limit and joy_down) => down_cmd)",
    "I04_repaired": "((upper_limit and joy_down and not joy_up and not estop) => down_cmd)",
    "I16": "((joy_up and joy_down) => (not up_cmd and not down_cmd))",
    # alternative readings seen in the pilot (v0.4)
    "I16_out": "(not (up_cmd and down_cmd))",                                   # #16 read as: never both output commands
    "I04_estop_only": "((upper_limit and joy_down and not estop) => down_cmd)",  # #4 repaired for the E-stop only
}
REF_SETS = {
    "shall": ["I01", "I03", "I04_shall", "I16"],        # #4 read as "shall", no exceptions
    "may": ["I01", "I03", "I16"],                        # #4 read as "may" = no obligation
    "repaired": ["I01", "I03", "I04_repaired", "I16"],   # #4 with the two missing conditions
    # the same three readings of #4 with #16 read as an output exclusion
    "may_out16": ["I01", "I03", "I16_out"],
    "shall_out16": ["I01", "I03", "I04_shall", "I16_out"],
    "repaired_out16": ["I01", "I03", "I04_estop_only", "I16_out"],
}
CLASS_TEXT = {
    "shall": "same as reference 'shall' (literal #4 as an obligation)",
    "may": "same as reference 'may' (#4 left out: no obligation)",
    "repaired": "same as reference 'repaired' (#4 with E-stop priority and no up+down)",
    "may_out16": "like 'may', but #16 read as 'never both output commands'",
    "shall_out16": "like 'shall', but #16 read as 'never both output commands'",
    "repaired_out16": "#4 repaired for the E-stop only, #16 read as 'never both output commands'",
    "other": "different from all six references",
}


def kind2(args, timeout=180):
    try:
        p = subprocess.run(["kind2", "-json"] + args, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        sys.exit("ERROR: kind2 was not found. Open a new Ubuntu window and check `kind2 --version`.")
    except subprocess.TimeoutExpired:
        return None, "timeout"
    try:
        return json.loads(p.stdout, strict=False), ""
    except json.JSONDecodeError:
        return None, (p.stdout + p.stderr).strip()[:600]


def errors_of(objs):
    return [o.get("value", "") for o in objs
            if o.get("objectType") == "log" and o.get("level") in ("error", "fatal")]


def realizability(path):
    """Run Kind 2's realizability check on the AI's own file."""
    objs, raw = kind2(["--enable", "CONTRACTCK", path])
    res = {"syntax_ok": False, "result": "", "conflict": "", "inputs": "", "error": ""}
    if objs is None:
        res["error"] = raw
        return res
    checks = [o for o in objs if o.get("objectType") == "realizabilityCheck"]
    if not checks:
        res["error"] = " | ".join(errors_of(objs))[:600] or "no realizability result (is the node 'imported' with a contract?)"
        return res
    c = checks[0]                      # first one = the contract of the node
    res["syntax_ok"] = True
    res["result"] = c.get("result", "")
    names = []
    for node in (c.get("conflictingSet") or {}).get("nodes", []):
        names += [e.get("name", "?") for e in node.get("elements", [])]
    res["conflict"] = " vs ".join(names)
    vals = []
    for blk in c.get("deadlockingTrace") or []:
        for s in blk.get("streams", []):
            if s.get("class") == "input" and s.get("instantValues"):
                vals.append("%s=%s" % (s["name"], ",".join("T" if v[1] else "F" for v in s["instantValues"])))
    res["inputs"] = " ".join(vals)
    return res


def _strip_block_comments(text):
    """Remove (* ... *) comments, allowing nesting (Kind 2 accepts nested comments)."""
    out, depth, i = [], 0, 0
    while i < len(text):
        if text.startswith("(*", i):
            depth += 1; i += 2; continue
        if text.startswith("*)", i) and depth:
            depth -= 1; i += 2; continue
        if depth == 0:
            out.append(text[i])
        i += 1
    return "".join(out)


def _contract_body(text):
    """Body of the (*@contract ... *) annotation, found with proper nesting of comments."""
    k = text.find("(*@contract")
    if k < 0:
        m = re.search(r"/\*@contract(.*?)\*/", text, re.S)
        return m.group(1) if m else None
    i, depth = k + len("(*@contract"), 1
    while i < len(text) and depth:
        if text.startswith("(*", i):
            depth += 1; i += 2
        elif text.startswith("*)", i):
            depth -= 1; i += 2
        else:
            i += 1
    return text[k + len("(*@contract"): i - 2]


def parse_contract(path):
    """Pull the interface, guarantees, assumptions, helper variables and top-level constants out of the file."""
    text = open(path, encoding="utf-8", errors="replace").read()
    text = re.sub(r"--[^\n]*", "", text)                       # line comments
    info = {"guarantees": [], "assumes": [], "ghosts": [], "consts": [], "flags": [], "in_decl": "", "out_decl": ""}
    m = re.search(r"node\s+(?:imported\s+)?\w+\s*\((.*?)\)\s*returns\s*\((.*?)\)\s*;", text, re.S)
    if not m:
        info["flags"].append("no node header found")
        return info
    info["in_decl"] = " ".join(m.group(1).split())
    info["out_decl"] = " ".join(m.group(2).split())
    # top-level constants (outside the node), e.g. const ALLOW_LOWERING : bool = true;
    outside = _strip_block_comments(text[:m.start()])
    for cm in re.finditer(r"\bconst\s+(\w+)\s*(?::\s*(\w+))?\s*=\s*([^;]+);", outside):
        info["consts"].append((cm.group(1), cm.group(2) or "bool", cm.group(3).strip()))
    body = _contract_body(text)
    if body is None:
        info["flags"].append("no (*@contract ... *) block found")
        return info
    body = _strip_block_comments(body)
    for stmt in body.split(";"):
        st = " ".join(stmt.split())
        if not st:
            continue
        g = re.match(r'^guarantee\s+(?:"([^"]*)"\s*)?(.+)$', st)
        a = re.match(r'^assume\s+(?:"([^"]*)"\s*)?(.+)$', st)
        v = re.match(r"^(?:var|const)\s+(\w+)\s*(?::\s*([\w ]+?))?\s*=\s*(.+)$", st)
        if g:
            info["guarantees"].append((g.group(1) or "g%d" % (len(info["guarantees"]) + 1), g.group(2)))
        elif a:
            info["assumes"].append(a.group(2))
        elif v:
            info["ghosts"].append((v.group(1), (v.group(2) or "bool").strip(), v.group(3)))
        elif st.startswith(("mode", "require", "ensure", ")")):
            if "uses modes" not in info["flags"]:
                info["flags"].append("uses modes")
        else:
            info["flags"].append("statement not understood: " + st[:60])
    for name in ["estop", "upper_limit", "joy_up", "joy_down"]:
        if not re.search(r"\b%s\b" % name, info["in_decl"]):
            info["flags"].append("input %s missing in the interface" % name)
    for name in ["up_cmd", "down_cmd"]:
        if not re.search(r"\b%s\b" % name, info["out_decl"]):
            info["flags"].append("output %s missing in the interface" % name)
    return info


def build_miter(info):
    """A Lustre file that asks Kind 2 to compare the AI's rules with the reference rules."""
    ai = " and ".join("(%s)" % e for _, e in info["guarantees"]) or "true"
    ghost_decl = "".join("  %s : %s;\n" % (n, t) for n, t, _ in info["ghosts"])
    ghost_def = "".join("  %s = %s;\n" % (n, e) for n, _, e in info["ghosts"])
    refs = "".join("  r_%s = %s;\n" % (k, " and ".join(REF_RULES[r] for r in v)) for k, v in REF_SETS.items())
    checks = "".join('  check "equiv_%s" ai = r_%s;\n' % (k, k) for k in REF_SETS)
    checks += "".join('  check "enforces_%s" ai => %s;\n' % (k, e) for k, e in REF_RULES.items())
    consts = "".join("const %s : %s = %s;\n" % c for c in info.get("consts", []))
    return (
        consts + "node Miter(%s; %s) returns (ok : bool);\n" % (info["in_decl"], info["out_decl"])
        + "var ai : bool;\n" + "".join("  r_%s : bool;\n" % k for k in REF_SETS) + ghost_decl
        + "let\n" + ghost_def + "  ai = %s;\n" % ai + refs + "  ok = true;\n" + checks + "tel\n\n"
        + "node NeverMoves(%s) returns (ok : bool);\n" % info["in_decl"]
        + "var %s;\n  ai : bool;\n" % info["out_decl"] + ghost_decl
        + "let\n  up_cmd = false;\n  down_cmd = false;\n" + ghost_def + "  ai = %s;\n" % ai
        + '  ok = true;\n  check "never_moving_crane_passes" ai;\ntel\n'
    )


def compare(path):
    info = parse_contract(path)
    out = {"class": "", "enforces": {}, "never_moves_passes": "", "n_guarantees": len(info["guarantees"]),
           "n_assumes": len(info["assumes"]), "assumes": info["assumes"], "flags": info["flags"], "error": ""}
    if not info["guarantees"] or any("missing" in f or "no " in f for f in info["flags"]):
        out["error"] = "cannot compare automatically: " + "; ".join(info["flags"] or ["no guarantees found"])
        return out
    miter = re.sub(r"\.lus$", "", path) + "_compare.lus"
    open(miter, "w", encoding="utf-8").write(build_miter(info))
    objs, raw = kind2([miter])
    if objs is None:
        out["error"] = "comparison file rejected by Kind 2: " + raw
        return out
    props = {o["name"]: o.get("answer", {}).get("value", "")
             for o in objs if o.get("objectType") == "property"}
    if not props:
        out["error"] = "comparison file rejected by Kind 2: " + " | ".join(errors_of(objs))[:400]
        return out
    out["class"] = next((k for k in REF_SETS if props.get("equiv_" + k) == "valid"), "other")
    out["enforces"] = {k: props.get("enforces_" + k) == "valid" for k in REF_RULES}
    out["never_moves_passes"] = props.get("never_moving_crane_passes") == "valid"
    return out


def reading4(c):
    """Which reading of #4 the contract uses, derived from the comparison."""
    k = c.get("class", "")
    return {"may": "permission", "may_out16": "permission", "shall": "obligation", "shall_out16": "obligation",
            "repaired": "repaired", "repaired_out16": "repaired-estop-only"}.get(k, "other" if k else "")


def reading16(c):
    """Which reading of #16 the contract enforces: the joystick (operator) form, the output exclusion, or both."""
    e = c.get("enforces", {})
    if not e:
        return ""
    a, b = e.get("I16"), e.get("I16_out")
    return "both" if a and b else ("operator" if a else ("outputs" if b else "neither"))


ALLOWED = {
    "arm": ["B", "C"], "condition": ["orig", "shall", "ground"], "complete": ["y", "n"],
    "claim_verdict": ["ok", "conflict", "unclear"], "noticed_may": ["y", "n", "?"],
    "found_4_vs_16": ["y", "implicit", "n", "n.a.", "?"], "found_4_vs_1": ["y", "implicit", "n", "n.a.", "?"],
    "found_vacuity": ["y", "implicit", "n", "?"], "said_may_reading": ["y", "n", "?"],
    "said_time_model": ["y", "n", "?"], "invented_output": ["y", "n", "?"], "used_other_tools": ["y", "n", "?"],
    "standards": ["none", "correct", "wrong", "?"],
}


def load_manual(path):
    """Manual scores written by the rater as JSON (non-interactive). Unknown keys are kept; values are checked."""
    m = json.load(open(path, encoding="utf-8"))
    bad = ["%s=%r" % (k, m[k]) for k in ALLOWED if k in m and m[k] not in ALLOWED[k]]
    if bad:
        sys.exit("ERROR in %s: values not allowed: %s" % (path, ", ".join(bad)))
    missing = [k for k in ALLOWED if k not in m]
    if missing:
        sys.exit("ERROR in %s: missing fields: %s" % (path, ", ".join(missing)))
    return {k: v for k, v in m.items() if k != "evidence"}


def ask(question, choices=None):
    """Ask one question. For yes/no questions, '?' means: cannot tell from the transcript."""
    if choices == ["y", "n"]:
        choices = ["y", "n", "?"]
        question = question.replace("(y/n):", "(y/n/?):")
    while True:
        ans = input(question + " ").strip()
        if choices is None or ans.lower() in choices:
            return ans.lower() if choices else ans
        print("   please type one of: " + "/".join(choices))


def yn(b):
    return "" if b == "" else ("yes" if b else "no")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run_id = sys.argv[1]
    auto_only = "--auto" in sys.argv
    folder = os.path.join(HERE, "runs", run_id)
    files = sorted(glob.glob(os.path.join(folder, "attempt*.lus")),
                   key=lambda p: int(re.search(r"attempt(\d+)", os.path.basename(p)).group(1)))
    files = [f for f in files if not f.endswith("_compare.lus")]
    if not files:
        sys.exit("ERROR: no attempt1.lus found in %s" % folder)
    first, final = files[0], files[-1]
    if os.path.exists(os.path.join(folder, "final.lus")):
        final = os.path.join(folder, "final.lus")       # part A of the FINAL REPORT, when it differs from the last run
    row = {"run_id": run_id, "date": datetime.date.today().isoformat(), "n_attempts": len(files)}

    cache = {}
    for tag, path in (("first", first), ("final", final)):
        if path not in cache:
            cache[path] = (realizability(path), compare(path))
        r, c = cache[path]
        print("\n===== %s attempt: %s =====" % (tag.upper(), os.path.basename(path)))
        if tag == "final" and final == first:
            print("(only one attempt: the final contract is the same file as the first)")
        if not r["syntax_ok"]:
            print("Kind 2 could NOT read this file: " + r["error"])
        else:
            print("Kind 2 verdict on the AI's own contract : " + r["result"].upper())
            if r["conflict"]:
                print("  conflicting rules : " + r["conflict"])
                print("  triggering inputs : " + r["inputs"])
        if c["error"]:
            print("Comparison with the reference: " + c["error"])
        else:
            print("Compared with the reference     : " + CLASS_TEXT[c["class"]])
            print("  enforces #1 E-stop            : " + yn(c["enforces"]["I01"]))
            print("  enforces #3 upper limit       : " + yn(c["enforces"]["I03"]))
            print("  enforces #4 as literal 'shall': " + yn(c["enforces"]["I04_shall"]))
            print("  enforces #4 in repaired form  : " + yn(c["enforces"]["I04_repaired"]))
            print("  enforces #16 up+down          : " + yn(c["enforces"]["I16"]))
            print("  enforces #16 as output excl.  : " + yn(c["enforces"]["I16_out"]) + "  (never up_cmd and down_cmd together)")
            print("  a crane that never moves passes: " + yn(c["never_moves_passes"]) + "  (yes = the rules are too weak)")
        if c["n_assumes"]:
            print("  NOTE: the AI added %d environment assumption(s): %s" % (c["n_assumes"], " ; ".join(c["assumes"])))
        for f in c["flags"]:
            print("  NOTE: " + f)
        row.update({
            tag + "_syntax_ok": yn(r["syntax_ok"]), tag + "_verdict": r["result"], tag + "_conflict": r["conflict"],
            tag + "_inputs": r["inputs"], tag + "_class": c["class"], tag + "_n_assumes": c["n_assumes"],
            tag + "_enf_I01": yn(c["enforces"].get("I01", "")), tag + "_enf_I03": yn(c["enforces"].get("I03", "")),
            tag + "_enf_I04_shall": yn(c["enforces"].get("I04_shall", "")),
            tag + "_enf_I04_repaired": yn(c["enforces"].get("I04_repaired", "")),
            tag + "_enf_I16": yn(c["enforces"].get("I16", "")),
            tag + "_enf_I16_out": yn(c["enforces"].get("I16_out", "")),
            tag + "_reading4": reading4(c), tag + "_reading16": reading16(c),
            tag + "_never_moves_passes": yn(c["never_moves_passes"]),
        })

    manual = None
    if "--manual" in sys.argv:
        i = sys.argv.index("--manual")
        manual = sys.argv[i + 1] if i + 1 < len(sys.argv) else os.path.join(folder, "manual.json")
    elif os.path.exists(os.path.join(folder, "manual.json")) and not auto_only:
        manual = os.path.join(folder, "manual.json")
    if manual:
        row.update(load_manual(manual))
        print("\nManual scores read from %s" % os.path.relpath(manual, HERE))
    elif not auto_only:
        print("\n===== Questions about the conversation (read the transcript) / 对照对话记录回答 =====")
        row["model"] = ask("Model name, version and setting, e.g. 'ChatGPT 5.6 Sol, medium' / 模型名称、版本和推理档位:")
        row["arm"] = ask("Arm: b = no tool, c = with Kind 2 / 实验臂 (b/c):", ["b", "c"]).upper()
        row["condition"] = ask("Prompt condition: orig = original text of #4, shall = #4 as an obligation / 提示词条件 (orig/shall):",
                               ["orig", "shall"])
        row["minutes"] = ask("Minutes spent / 用了几分钟:")
        row["complete"] = ask("Did the run end with a FINAL REPORT? / 这次运行是否以 FINAL REPORT 结束 (y/n):", ["y", "n"])
        row["claim_verdict"] = ask("What did the AI conclude about the ORIGINAL four requirements? "
                                   "ok = no conflict, conflict = cannot all be met, unclear / AI 对原始四条的结论 (ok/conflict/unclear):",
                                   ["ok", "conflict", "unclear"])
        row["noticed_may"] = ask("Did it say that 'may' in #4 can be read as a permission OR as an obligation (the may/shall question)? / 指出 #4 的 may 有两种读法了吗 (y/n):", ["y", "n"])
        row["found_4_vs_16"] = ask("Did it name the conflict of #4 with #16 (up+down at the upper limit), as a real conflict OR as what happens if #4 is read as 'shall'? / 指出 #4 与 #16 的冲突了吗（真实的或“若读作 shall”的都算） (y/implicit/n/n.a.):", ["y", "implicit", "n", "n.a.", "?"])
        row["found_4_vs_1"] = ask("Did it name the conflict of #4 with #1 (E-stop against lowering), as a real conflict OR as what happens if #4 is read as 'shall'? / 指出 #4 与 #1 的冲突了吗（真实的或“若读作 shall”的都算） (y/implicit/n/n.a.):", ["y", "implicit", "n", "n.a.", "?"])
        row["found_vacuity"] = ask("Did it say that the rules can be met by a crane that never moves (too weak)? / 指出“永不动作的起重机也满足”了吗 (y/n):", ["y", "n"])
        row["said_may_reading"] = ask("Did it say which reading of 'may' it used for its contract? / 说明它的合同用了哪种读法吗 (y/n):", ["y", "n"])
        row["said_time_model"] = ask("Did it state a time assumption (same PLC cycle / step)? / 说明时间假设了吗 (y/n):", ["y", "n"])
        row["invented_output"] = ask("Did it claim a tool result that it did not get? / 有没有虚构工具运行结果 (y/n):", ["y", "n"])
        row["used_other_tools"] = ask("Did the chat app run any tool on its own (code, canvas, web search)? / 对话里模型自己用了工具吗（代码、画布、联网） (y/n):", ["y", "n"])
        row["standards"] = ask("Standards cited: none, correct, wrong / 引用标准的情况 (none/correct/wrong):", ["none", "correct", "wrong"])
        row["note"] = ask("One-line note (or just press Enter) / 一句话备注:")

    if auto_only:
        print("\n(--auto: nothing saved; the official scores come from the rater's manual.json)")
        return
    json.dump(row, open(os.path.join(folder, "score.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    if run_id.upper().startswith("DEMO"):
        print("\nPractice run: saved runs/%s/score.json only (not added to run_log.csv)." % run_id)
        return
    rows = []
    if os.path.exists(LOG):
        rows = [r for r in csv.DictReader(open(LOG, encoding="utf-8")) if r.get("run_id") != run_id]
    rows.append(row)
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with open(LOG, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("\nSaved: runs/%s/score.json and run_log.csv (%d run(s) so far)" % (run_id, len(rows)))


if __name__ == "__main__":
    main()
