#!/usr/bin/env python3
"""Helpers for next.sh: classify a model reply and extract Lustre code blocks.
Usage: extract.py classify FILE | run FILE | part LETTER FILE | same FILE1 FILE2"""
import re, sys

FENCE = re.compile(r"^\s*```[^\n`]*\n(.*?)^\s*```\s*$", re.S | re.M)
HEAD = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*(?:Part\s+)?([A-E])\s*(?:[\.\):]|\s[-\u2013\u2014])\s", re.M)


def blocks(text):
    """All fenced code blocks as (start, end, code)."""
    return [(m.start(), m.end(), m.group(1)) for m in FENCE.finditer(text)]


UNFENCED = re.compile(r"node\s+imported\s+Hoist\b.*?\*\)", re.S)


def unfenced(text):
    """Contracts written without a code fence, as (start, end, code)."""
    return [(m.start(), m.end(), m.group(0) + "\n") for m in UNFENCED.finditer(text)]


def is_contract(code):
    return re.search(r"node\s+imported\s+Hoist", code) is not None


def last_lines(text, n=3):
    lines = [l.strip().strip("*`_ ").strip() for l in text.strip().splitlines() if l.strip()]
    return lines[-n:]


def asks_for_run(text):
    """True if one of the last 3 non-empty lines is just RUN (also RUN., **RUN**, `RUN`, RUN!)."""
    return any(re.sub(r"[^A-Za-z]", "", l).upper() == "RUN" for l in last_lines(text))


def has_final_heading(text):
    """True if a short line (at most 6 words) contains FINAL REPORT, e.g. '# FINAL REPORT', '**FINAL REPORT**',
    'FINAL REPORT', 'Here is my FINAL REPORT:'. A mention inside a long sentence does not count."""
    for l in text.splitlines():
        if re.search(r"FINAL\s+REPORT", l, re.I):
            words = re.sub(r"[#*_`:>|\-]", " ", l).split()
            if len(words) <= 6:
                return True
    return False


def classify(text):
    if asks_for_run(text):
        return "run"
    if has_final_heading(text):
        return "final"
    return "other"


def run_block(text):
    """The last contract code block before the final RUN line."""
    cands = [b for b in blocks(text) if is_contract(b[2])] or unfenced(text)
    return cands[-1][2] if cands else ""


def part_block(letter, text):
    """The first contract code block after the LAST heading 'X.' (X = letter); '' if none or 'none'."""
    heads = [m for m in HEAD.finditer(text) if m.group(1) == letter]
    if not heads:
        return ""
    start = heads[-1].end()
    nxt = [m.start() for m in HEAD.finditer(text) if m.start() > start and m.group(1) != letter]
    stop = min(nxt) if nxt else len(text)
    for s, e, code in blocks(text):
        if s >= start and s < stop and is_contract(code):
            return code
    for s, e, code in unfenced(text):          # contract written without a code fence
        if s >= start and s < stop:
            return code
    return ""


def norm(code):
    """Contract text without comments and whitespace, for comparing two contracts."""
    code = re.sub(r"--[^\n]*", "", code)
    return re.sub(r"\s+", "", code)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "same":   # extract.py same FILE1 FILE2 -> prints yes/no
        a = open(sys.argv[2], encoding="utf-8", errors="replace").read()
        b = open(sys.argv[3], encoding="utf-8", errors="replace").read()
        print("yes" if norm(a) == norm(b) else "no")
        sys.exit(0)
    text = open(sys.argv[-1], encoding="utf-8", errors="replace").read()
    if mode == "classify":
        print(classify(text))
    elif mode == "run":
        sys.stdout.write(run_block(text))
    elif mode == "part":
        sys.stdout.write(part_block(sys.argv[2], text))
