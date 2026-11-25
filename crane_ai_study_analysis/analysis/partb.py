#!/usr/bin/env python3
"""Print the headings and the start of part B (problems) of the last FINAL REPORT of each run."""
import re, sys
sys.path.insert(0, '.')
import extract as X
SEP = re.compile(r"^========== (USER|MODEL) ==========$", re.M)
HEAD = X.HEAD
for rid in sys.argv[1:]:
    t = open(f"runs/{rid}/transcript.md", encoding="utf-8").read()
    parts = SEP.split(t)
    models = [parts[i + 1] for i in range(1, len(parts), 2) if parts[i] == "MODEL"]
    f = models[-1]
    heads = [m for m in HEAD.finditer(f)]
    hb = [m for m in heads if m.group(1) == "B"]
    if not hb:
        print(f"===== {rid}: no part B heading found; start: {' '.join(f[:500].split())}"); continue
    s = hb[-1].start()
    nxt = [m.start() for m in heads if m.start() > s and m.group(1) == "C"]
    body = f[s: nxt[0] if nxt else len(f)]
    body = re.sub(r"```.*?```", "[CODE]", body, flags=re.S)
    sub = [" ".join(l.split())[:110] for l in body.splitlines() if re.match(r"^\s*(#{1,6}|\*\*|B\.\d|\d+\.\s+\*\*|[-*]\s+\*\*)", l)]
    print(f"===== {rid}: part B {len(body)} chars | sub-headings: " + " || ".join(sub[:9]))
    print("  start: " + " ".join(body.split())[:650])
