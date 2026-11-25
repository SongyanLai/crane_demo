import re, sys
SEP = re.compile(r"^========== (USER|MODEL) ==========$", re.M)
P = {"time": r"(same scan|same cycle|same PLC|scan cycle|per scan|once per scan|synchronous|pointwise|combinational|instantaneous|no delay|no memory|memoryless|within the same|time)",
     "tool": r"(\bI ran\b|\bwe ran\b|after running|Kind 2 (reported|returned|proved|proves|confirm|showed|shows|says|accepted)|I executed|was executed|verified by Kind|verified with Kind|checked with Kind|proven (un)?realizable|tool output|cannot run|did not run|no tool|by hand|manual reasoning)",
     "std": r"\b(EN|ISO|IEC)\s?\d{3,5}[^\s,;.)]*"}
for rid in sys.argv[1:]:
    t = open(f"runs/{rid}/transcript.md", encoding="utf-8").read(); parts = SEP.split(t)
    m = "\n".join(parts[i+1] for i in range(1, len(parts), 2) if parts[i] == "MODEL")
    m = re.sub(r"```.*?```", " ", m, flags=re.S)
    out = []
    for k, p in P.items():
        h = [x.group(0) for x in re.finditer(r"[^.\n]{0,70}" + p + r"[^.\n]{0,50}", m, re.I)]
        out.append(f"{k}: {(' '.join(h[0].split())[:150]) if h else '-'}")
    print(rid, " | ".join(out))
