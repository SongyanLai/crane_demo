# Crane requirements verification: feasibility demo (October–November 2026)

Formal checks of safety requirements for an operator-controlled metallurgical overhead crane that
transports molten metal. Four small examples are taken from the 33 requirement intents in
Crane_Case_Study.docx. The hoist logic in ex2 and ex4 is illustrative, written by us from the intents.
It is NOT company code.

Author: Songyan Lai, Aalto University

## What is in this repository

| Folder / file             | What it checks                                                                                                                                         | Tool              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| ex1/                      | Intents #1, #3, #4, #16 (E-stop and primary upper limit): can ANY controller satisfy them for every operator input? (realizability)                     | Kind 2            |
| ex2/                      | Intents #5, #6, #27, #28 + EN 12077-2:2024 4.6.1.4 (backup upper limit): does a given hoist logic satisfy them, in closed loop with a sensor fault?     | NuSMV             |
| ex3/                      | Overload intents #7, #8, #9 with #1 and #16: can any controller satisfy them? (realizability)                                                           | Kind 2            |
| ex4/                      | The suggested wording of the report (Table 12): is it realizable (4a), is each condition needed (4c), and can a design meet it (4b)?                    | Kind 2, NuSMV     |
| optional_hanfor_reqcheck/ | Example 1 in Hanfor's pattern language, for Ultimate ReqCheck (needs Java 21 + UReqCheck)                                                               | Ultimate ReqCheck |
| results/                  | Outputs of our run on 9 November 2026 (Kind 2 v3.0.0 + Z3 4.13.0, NuSMV 2.6.0)                                                                         |                   |
| run_all.sh                | Runs every check and prints a short summary                                                                                                            |                   |
| trace_to_csv.py           | Turns NuSMV counterexamples into CSV test scenarios (one row per PLC scan)                                                                              |                   |

## Main results

| Example | File                              | Result                                       | What it means                                                                                 |
| ------- | --------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 1       | ex1a_literal.lus                  | Unrealizable: #4 vs #16                      | Hook at the upper limit, joystick up and down at the same time                                |
| 1       | ex1b_fix1.lus                     | Unrealizable: #1 vs #4                       | Hook at the upper limit, E-stop pressed, operator asks for lowering: no priority is stated     |
| 1       | ex1c_fix2.lus                     | Realizable                                   | The conflict is gone once the E-stop has priority                                             |
| 1       | ex1d_never_moves.lus              | A crane that never moves meets #1, #3, #16   | With #4 read as "may", the rules are too weak                                                 |
| 2       | ex2_v1_literal.smv                | P3 (lock-out) fails                          | A program written word by word from the intents breaks EN 12077-2:2024 4.6.1.4                |
| 2       | ex2_v2_lockout.smv                | All rules hold                               | Adding the lock-out fixes it                                                                  |
| 2       | ex2_v3_shared_sensor.smv          | P1 fails: the hook hits the trolley          | All signal-level rules still pass; this shows why #28 is needed                               |
| 3       | ex3a, ex3b, ex3c                  | Unrealizable: #9 vs #7, then #16, then #1    | Same "should remain available" pattern as #4, plus a conflict with the lower limit            |
| 3       | ex3d_fix3.lus                     | Realizable                                   | After three added conditions                                                                  |
| 4       | ex4a_suggested_wording.lus        | Realizable                                   | The suggested wording has no conflicts                                                        |
| 4       | ex4c_without_backup_condition.lus | Unrealizable: suggested #4 vs lock-out rule  | The backup-limit condition in the suggested #4 is needed                                      |
| 4       | ex4b_suggested_design.smv         | All 8 rules hold                             | A design can meet the suggested wording                                                       |

## How to run

You need Linux, or WSL on Windows, with `kind2` (v3.0.0), `z3`, `NuSMV` (2.6.0 or 2.5.4) and `python3` on PATH.
Run everything:

    bash run_all.sh

Each check takes less than one second. The full outputs go to `results/`, and the two counterexamples of
ex2 are also written as CSV test scenarios.

Run a single check:

    kind2 --enable CONTRACTCK ex1/ex1a_literal.lus     # realizability of a requirement set
    kind2 ex1/ex1d_never_moves.lus                     # check concrete programs against their rules
    NuSMV ex2/ex2_v1_literal.smv                       # model checking of a design

On Windows, if bash reports `$'\r': command not found`, remove the Windows line endings first:

    sed -i 's/\r$//' run_all.sh

## Notes

- One step in all models is one PLC scan cycle. The crane model in ex2 and ex4 is simplified: the hook
  height has four zones, and there is no speed or braking distance.
- The translations from the intents to formal rules are ours. They still need to be confirmed by the company.
- Standard clauses are paraphrased. The standards themselves are not included in this repository.
- The same verdicts were obtained on two machines with different tool versions (Z3 4.13.0 and 5.3.1;
  NuSMV 2.6.0 and 2.5.4). Only run times and Kind 2's internal proof depth (`k=`) can differ.
- The first versions of the model files were drafted with help from an AI assistant (Claude).
  All checks were re-run and reviewed by the author.
