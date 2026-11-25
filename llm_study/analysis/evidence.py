#!/usr/bin/env python3
"""Print compact evidence snippets from the MODEL messages of each run, for manual scoring.
Usage: python3 analysis/evidence.py M02 M04 ..."""
import re, sys, os
SEP = re.compile(r"^========== (USER|MODEL) ==========$", re.M)
FENCE = re.compile(r"```.*?```", re.S)
CONTRACT = re.compile(r"node\s+imported\s+Hoist\b.*?\*\)", re.S)
PAT = {
 "estop": (r"(estop|e-stop|emergency|R0?1\b|#1\b)", r"(R0?4\b|#4\b|lower|down_cmd)", r"(conflict|contradict|unrealiz|cannot|impossible|incompatib|deadlock|clash|both true)"),
 "updown": (r"(R16|#16|joy_up\s*(and|∧|&)\s*joy_down|simultaneous|both direction|both joystick|up and down)", r"(R0?4\b|#4\b|lower|down_cmd)", r"(conflict|contradict|unrealiz|cannot|impossible|incompatib|deadlock|clash)"),
 "vacuity": (r"(never move|never moves|do-nothing|does nothing|trivial|vacuous|always false|permanently|no motion at all|never command|never issue|never lower|never hoist|all outputs false|non-?functional|useless|completeness gap|under-?specif)",),
 "may": (r"(\bmay\b|permissi|permissive)", r"(obligation|shall|guarantee|true\b|tautolog|no constraint)"),
 "time": (r"(same scan|same cycle|same PLC|scan cycle|per scan|once per scan|synchronous|pointwise|combinational|instantaneous|no delay|no memory|within the same)",),
 "tools": (r"(\bI ran\b|\bwe ran\b|after running|Kind 2 (reported|returned|proved|confirm|showed|says)|I executed|was executed|verified by Kind|proven (un)?realizable|tool output)",),
 "std": (r"\b(EN|ISO|IEC)\s?\d{3,5}",),
}
def sentences(text):
    text = CONTRACT.sub(" [CONTRACT] ", FENCE.sub(" [CODE] ", text))
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [" ".join(p.split()) for p in parts if len(p.split()) > 3]
for rid in sys.argv[1:]:
    t = open(f"runs/{rid}/transcript.md", encoding="utf-8").read()
    parts = SEP.split(t)
    model_text = "\n".join(parts[i + 1] for i in range(1, len(parts), 2) if parts[i] == "MODEL")
    fr = re.search(r"FINAL\s+REPORT", model_text)
    print(f"########## {rid} ({len(model_text)} chars; FINAL REPORT at {fr.start() if fr else -1})")
    sents = sentences(model_text)
    for key, pats in PAT.items():
        hits = [s for s in sents if all(re.search(p, s, re.I) for p in pats)]
        for h in hits[:2 if key in ('estop', 'updown', 'vacuity') else 1]:
            print(f"  [{key}] {h[:230]}")
        if not hits:
            print(f"  [{key}] -")
