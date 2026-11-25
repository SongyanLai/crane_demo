# Crane case: can LLMs check safety requirements on their own? (analysis of Example 1)

**Status: preliminary, 25 November 2026.** The manual scores were made with the help of an AI rater (Claude).
They have not yet been checked by a person.

## What the study did

We gave four hoist safety requirements of a metallurgical crane (#1, #3, #4 and #16, called Example 1)
to four large language models (LLMs). Every run was a fresh chat session.

| Item | Details |
|---|---|
| Models | GPT-5.6 Sol (Medium), DeepSeek-V4 (DeepThink), Claude Sonnet 5.5 (Medium), Gemini Hydrogen (Medium) |
| Arms | B: the model works alone. C: the model can ask for up to 5 Kind 2 runs. |
| Prompt versions | `orig`: the customer's text. `ground`: plus a short glossary and a note on EN 15011. `shall`: #4 written with "shall". |
| Runs | 48 valid runs: 4 models x 4 combinations (orig-B, orig-C, ground-B, shall-B) x 3 runs |
| Time | 24 November 2026, 22:04 to 25 November 2026, 12:11 (EET) |

Every run was scored in two ways: automatically with the Kind 2 model checker, and manually with a written rubric.
The results were then compared with our earlier human-in-the-loop study of the same example.

## Main results

- In 48 of 48 runs, the model's verdict on its own formal translation matched Kind 2.
- With the original text and no tool, no model read "may" in #4 as an obligation (0 of 12 runs).
- Both hidden conflicts were named in 42 of 48 runs, and 42 of 48 runs proposed a good correction.
  With the domain notes or the "shall" text, all 24 runs did both.
- On this small task, access to Kind 2 did not improve the results.

The full analysis is in the report (see "Related material"). The feasibility demo is in [`../demo/`](../demo/).

## What is in this folder

| File | What it is |
|---|---|
| `analysis/auto_scores.py` | Runs the Kind 2 checks for every run: first and final contract, readings of #4 and #16, tool use |
| `analysis/merge.py` | Joins the automatic and manual scores into `all_runs.json` and prints summaries |
| `analysis/tables.py`, `analysis/figures.py` | Make the LaTeX tables and the figures used in the report |
| `analysis/report_numbers.py` | Prints every number that is quoted in the text of the report |
| `analysis/evidence.py`, `partb.py`, `sect.py`, `minor.py` | Helpers used during manual scoring: they print parts of a transcript |
| `analysis/manual_scores.json` | The manual scores, one entry per run, with a short note on the evidence |
| `analysis/auto_scores.csv`, `auto_scores.json` | The automatic scores |
| `analysis/all_runs.json` | All scores together (the main data file) |
| `analysis/numbers.json` | A few summary numbers |
| `score_ex1.py`, `extract.py` | Scoring and parsing helpers (newer versions than in the study kit) |

## What is not in this folder

The chat transcripts, the model's contract files and the reference contracts are in the study kit
(`crane_ai_study`), which is not public. You can read all scores here, but you need the kit to compute them
again. Please ask Songyan Lai for access.

## How to reproduce the numbers

You need Linux or WSL, `kind2` (v3.0.0) and `z3` on the PATH, and Python 3 with matplotlib and numpy
(`pip install -r requirements.txt`).

1. Copy the content of this folder into the study kit folder `crane_ai_study`.
2. In that folder, run:

        python3 analysis/auto_scores.py
        python3 analysis/merge.py
        python3 analysis/tables.py
        python3 analysis/figures.py
        python3 analysis/report_numbers.py

3. The results are `analysis/all_runs.json`, the tables in `report/tables/` and the figures in `report/figures/`.

## Main fields in `all_runs.json`

| Field | Meaning |
|---|---|
| `run_id`, `model`, `arm`, `condition` | Which run it is |
| `exact_model`, `setting`, `start`, `end` | What was recorded during the run |
| `first_verdict`, `final_verdict` | Kind 2 result for the first and the final contract: realizable, unrealizable or syntax error |
| `first_class`, `final_class` | Which reference contract the model's contract equals: `may`, `shall`, `repaired`, the same three with `_out16`, or `other` |
| `first_enf_I01` ... `final_enf_I16_out` | Whether the contract implies each reference rule (checked by Kind 2) |
| `read4`, `final_read4`, `read16` | Reading of #4 (permission or obligation) and of #16 (joystick rule, output rule or both) |
| `kind2_runs`, `run_verdicts`, `final_status` | Tool use in arm C |
| `claim_verdict`, `found_4_vs_1`, `found_4_vs_16`, `found_vacuity` | Manual scores: y = named, implicit = only built into the correction, n = not named, n.a. = not applicable |
| `good_final` | The final contract is realizable, implies #1, #3, #16 and the repaired #4, and a never-moving controller fails it |
| `main` | true for the 48 main runs, false for the exploratory run M09 |

## Runs left out

- M01 is excluded: a reminder reached the model by mistake. M33 replaces it.
- M09 used GPT-6 instead of GPT-5.6 Sol. It is kept as exploratory data and is not in the main numbers. M34 replaces it.
- The pilot runs R01, R02, R05 and R06 are not included.

## Related material

- Report: "Can Large Language Models Check Crane Safety Requirements on Their Own? A first comparison with a
  human-in-the-loop process", in the Overleaf project of the crane case (ask for access).
- Earlier feasibility demo: [`../demo/`](../demo/) in this repository

## Use of AI assistance

The scripts, the scoring and the analysis were prepared with the help of Claude (Anthropic). Songyan Lai ran all chat
sessions and all Kind 2 commands. Claude Sonnet 5.5 is also one of the tested models, so a person must check the manual
scores before the results are published.

## Licence

Not decided yet. Please ask before you reuse the data or the code.
