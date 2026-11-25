#!/usr/bin/env python3
"""Turn each NuSMV counterexample in a result file into a CSV test scenario (one row per PLC scan).
NuSMV prints only the variables that changed; this script carries the other values forward."""
import csv, re, sys

for path in sys.argv[1:]:
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    n = 0
    i = 0
    while i < len(lines):
        if lines[i].startswith("-- specification") and lines[i].rstrip().endswith("is false"):
            spec = lines[i][len("-- specification"):].rsplit("is false", 1)[0].strip()
            n += 1
            rows, state, order, loop_next = [], {}, [], False
            i += 1
            while i < len(lines) and not lines[i].startswith("-- specification"):
                l = lines[i].strip()
                if l.startswith("-- Loop starts here"):
                    loop_next = True
                elif l.startswith("-> State:"):
                    if rows or state:
                        rows.append(dict(state))
                    state["_loop"] = "loop starts here" if loop_next else ""
                    loop_next = False
                else:
                    m = re.match(r"^([A-Za-z_][\w.]*) = (.+)$", l)
                    if m:
                        if m.group(1) not in order:
                            order.append(m.group(1))
                        state[m.group(1)] = m.group(2)
                i += 1
            rows.append(dict(state))
            rows = [r for r in rows if any(k != "_loop" for k in r)]
            out = re.sub(r"\.txt$", "", path) + f"_counterexample{n}.csv"
            with open(out, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["# violated:", spec])
                w.writerow(["scan"] + order + ["note"])
                for k, r in enumerate(rows, 1):
                    w.writerow([k] + [r.get(v, "") for v in order] + [r.get("_loop", "")])
            print(f"wrote {out} ({len(rows)} scans)")
        else:
            i += 1
