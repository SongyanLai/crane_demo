# Crane requirements verification: feasibility demo (October 2026)

Two small examples taken from Crane_Case_Study.docx. The hoist logic here is
illustrative, written by us from the intents. It is NOT company code.

| Folder                    | What it checks                                                                                                                 | Tool              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| ex1/                      | Intents #1, #3, #4, #16: can ANY controller satisfy them for every operator input? (realizability)                             | Kind 2            |
| ex2/                      | Intents #5, #6, #27, #28 + EN 12077-2:2024 4.6.1.4: does a given hoist logic satisfy them, in closed loop with a sensor fault? | NuSMV             |
| optional_hanfor_reqcheck/ | Example 1 in Hanfor's pattern language, for Ultimate ReqCheck (needs Java 21 + UReqCheck)                                      | Ultimate ReqCheck |
| results/                  | Outputs of my run (Kind 2 v3.0.0 + Z3 4.13.0, NuSMV 2.6.0)                                                                     |                   |

Run everything (kind2, z3, NuSMV and python3 must be on PATH):

    bash run_all.sh

<!-- Your outputs go to results/. Counterexamples of ex2 are also written as CSV test scenarios. -->
