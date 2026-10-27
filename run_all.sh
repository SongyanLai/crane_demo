#!/usr/bin/env bash
# Crane feasibility demo: runs every check and stores the full outputs in results/
# Usage:  bash run_all.sh
cd "$(dirname "$0")"
mkdir -p results
for f in ex1a_literal ex1b_fix1 ex1c_fix2; do
  kind2 --color false --enable CONTRACTCK ex1/$f.lus > results/$f.txt 2>&1
done
kind2 --color false ex1/ex1d_never_moves.lus > results/ex1d_never_moves.txt 2>&1
for f in ex2_v1_literal ex2_v2_lockout ex2_v3_shared_sensor; do
  NuSMV ex2/$f.smv > results/$f.txt 2>&1
done
python3 trace_to_csv.py results/ex2_v1_literal.txt results/ex2_v3_shared_sensor.txt
echo "===== SUMMARY ====="
grep -H -E "proven (un)?realizable|Guarantee I|: (in)?valid|is (true|false)" results/*.txt | sed 's#^results/##'
