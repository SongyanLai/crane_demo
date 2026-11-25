# Crane safety requirements: formal checks and an LLM study

This repository collects the work on the safety requirements of an operator-controlled metallurgical overhead
crane that transports molten metal. The requirements are the 33 requirement intents in `Crane_Case_Study.docx`.

It has two parts:

| Folder | What it is | Period | Status |
|---|---|---|---|
| [`demo/`](demo/) | **Feasibility demo.** Four small examples checked with model checkers (Kind 2, NuSMV, optionally Ultimate ReqCheck): conflicts, missing priorities and too-weak rules in the requirement text, and a suggested new wording | October–November 2026 | Complete; all outputs in `demo/results/` |
| [`llm_study/`](llm_study/) | **LLM study.** Can large language models find the same problems on their own? Analysis of 48 runs of four LLMs on Example 1 of the demo | November 2026 | Preliminary (25 November 2026): manual scores not yet checked by a person |

The two parts build on each other. The demo is the human-in-the-loop process: the author translated the
requirements into formal rules and used the tools to find the problems. The LLM study gives the same Example 1
(intents #1, #3, #4 and #16) to LLMs and compares their findings with the results of the demo.

Author: Songyan Lai, Aalto University

## Repository layout

    .
    ├── README.md                  this file
    ├── demo/                      feasibility demo (formal checks)
    │   ├── README.md              details, full table of results
    │   ├── ex1/ … ex4/            Lustre (.lus) and NuSMV (.smv) models of the four examples
    │   ├── optional_hanfor_reqcheck/   Example 1 in Hanfor's pattern language
    │   ├── results/               outputs of the run on 9 November 2026
    │   ├── run_all.sh             runs every check and prints a summary
    │   └── trace_to_csv.py        NuSMV counterexamples -> CSV test scenarios
    └── llm_study/                 analysis of the LLM study
        ├── README.md              study design, fields of the data files, runs left out
        ├── analysis/              scoring scripts, tables, figures, and the score data
        ├── score_ex1.py, extract.py    scoring and parsing helpers
        └── requirements.txt       Python packages (matplotlib, numpy)

Each folder has its own README with the full details. This page gives only an overview.

## Part 1: feasibility demo (`demo/`)

Four examples, each taken from a few requirement intents:

| Example | Intents | Question | Tool |
|---|---|---|---|
| 1 | #1, #3, #4, #16 (E-stop, primary upper limit) | Can any controller satisfy the rules for every operator input? (realizability) | Kind 2 |
| 2 | #5, #6, #27, #28 + EN 12077-2:2024 4.6.1.4 (backup upper limit) | Does a given hoist logic satisfy them, also with a sensor fault? | NuSMV |
| 3 | #7, #8, #9 with #1 and #16 (overload) | Can any controller satisfy them? | Kind 2 |
| 4 | Suggested wording of the report (Table 12) | Is it realizable, is each condition needed, can a design meet it? | Kind 2, NuSMV |

Main findings:

- **Example 1:** the literal text is unrealizable (#4 conflicts with #16, then with #1). It becomes realizable
  once the E-stop has priority. If #4 is read as "may", a crane that never moves satisfies the rules.
- **Example 2:** a hoist program written word by word from the intents breaks the lock-out rule of
  EN 12077-2:2024 4.6.1.4. With a shared sensor, all signal-level rules pass but the hook can hit the trolley,
  which shows why #28 is needed.
- **Example 3:** the overload rules have the same "should remain available" problem as #4. Three added
  conditions make them realizable.
- **Example 4:** the suggested wording is realizable, its backup-limit condition is needed, and a design
  can meet all 8 rules.

Run all checks (Linux or WSL, with `kind2` v3.0.0, `z3`, `NuSMV` 2.6.0 or 2.5.4 and `python3` on the PATH):

    cd demo
    bash run_all.sh

Each check takes less than one second. See [`demo/README.md`](demo/README.md) for single checks and notes.

## Part 2: LLM study (`llm_study/`)

Example 1 was given to four LLMs (GPT-5.6 Sol, DeepSeek-V4, Claude Sonnet 5.5, Gemini Hydrogen) in fresh chat
sessions: with and without access to Kind 2, and with three versions of the prompt (original text, text with
domain notes, #4 written with "shall"). 48 valid runs were scored automatically with Kind 2 and manually with
a written rubric.

Preliminary findings:

- In 48 of 48 runs, the model's verdict on its own formal translation matched Kind 2.
- With the original text and no tool, no model read "may" in #4 as an obligation (0 of 12 runs).
- Both hidden conflicts were named, and a good correction was proposed, in 42 of 48 runs; with the domain
  notes or the "shall" text, in all 24 runs.
- On this small task, access to Kind 2 did not improve the results.

All scores are in `llm_study/analysis/all_runs.json`. The chat transcripts and the reference contracts are in
the study kit (`crane_ai_study`), which is not public, so the scores can be read here but not recomputed
without the kit. See [`llm_study/README.md`](llm_study/README.md) for how to reproduce the numbers.

## Important notes

- The translations from the requirement intents to formal rules are the author's. They still need to be
  confirmed by the company.
- The hoist logic in the demo (Examples 2 and 4) is illustrative and written from the intents. It is not
  company code.
- Standard clauses are paraphrased. The standards and `Crane_Case_Study.docx` are not included.
- The results of the LLM study are preliminary. Claude Sonnet 5.5 is one of the tested models and the manual
  scores were made with the help of Claude, so a person must check them before the results are published.

## Use of AI assistance

The first versions of the demo models, and the scripts, scoring and analysis of the LLM study, were prepared
with the help of Claude (Anthropic). The author ran all chat sessions and all tool runs, and reviewed the
results. The details are in the README of each folder.

## Licence

Not decided yet. Please ask the author before you reuse the data or the code.
