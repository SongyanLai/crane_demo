#!/usr/bin/env python3
"""Print the text after a heading that matches a regex, in the last FINAL REPORT. Usage: sect.py RUN 'regex' [chars]"""
import re, sys
SEP = re.compile(r"^========== (USER|MODEL) ==========$", re.M)
rid, rx = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 900
t = open(f"runs/{rid}/transcript.md", encoding="utf-8").read()
parts = SEP.split(t)
f = "\n".join(parts[i + 1] for i in range(1, len(parts), 2) if parts[i] == "MODEL")
m = list(re.finditer(rx, f, re.M | re.I))
if not m: print(f"--- {rid}: '{rx}' not found")
else:
    s = m[-1].start(); body = re.sub(r"```.*?```", "[CODE]", f[s:s + n * 2], flags=re.S)
    print(f"--- {rid} [{rx}]: " + " ".join(body.split())[:n])
