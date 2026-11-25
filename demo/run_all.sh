#!/usr/bin/env bash
# Crane feasibility demo: runs every check and stores the full outputs in results/
# Usage:  bash run_all.sh
cd "$(dirname "$0")"
mkdir -p results
# Example 1: E-stop and primary upper limit (#1, #3, #4, #16), realizability with Kind 2
for f in ex1a_literal ex1b_fix1 ex1c_fix2; do
  kind2 --color false --enable CONTRACTCK ex1/$f.lus > results/$f.txt 2>&1
done
kind2 --color false ex1/ex1d_never_moves.lus > results/ex1d_never_moves.txt 2>&1
# Example 2: backup upper limit (#5, #6, #27, #28 + EN 12077-2 4.6.1.4), model checking with NuSMV
for f in ex2_v1_literal ex2_v2_lockout ex2_v3_shared_sensor; do
  NuSMV ex2/$f.smv > results/$f.txt 2>&1
done
# Example 3: overload (#7, #8, #9 with #1, #16), realizability with Kind 2
for f in ex3a_literal ex3b_fix1 ex3c_fix2 ex3d_fix3; do
  kind2 --color false --enable CONTRACTCK ex3/$f.lus > results/$f.txt 2>&1
done
# Example 4: the suggested wording of the report (Table 12)
for f in ex4a_suggested_wording ex4c_without_backup_condition; do
  kind2 --color false --enable CONTRACTCK ex4/$f.lus > results/$f.txt 2>&1
done
NuSMV ex4/ex4b_suggested_design.smv > results/ex4b_suggested_design.txt 2>&1
python3 trace_to_csv.py results/ex2_v1_literal.txt results/ex2_v3_shared_sensor.txt
echo "===== SUMMARY ====="
grep -H -E "proven (un)?realizable|Guarantee [IS]|Guarantee N|: (in)?valid|is (true|false)" results/*.txt | sed 's#^results/##'
