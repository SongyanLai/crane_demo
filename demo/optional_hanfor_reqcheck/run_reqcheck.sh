#!/usr/bin/env bash
# Run Ultimate ReqCheck (the analysis engine behind Hanfor) on one .req file.
# Usage: ./run_reqcheck.sh <path/to/file.req>   (set UREQ to the unpacked UReqCheck-linux folder)
set -e
REQ="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
UREQ="${UREQ:-/opt/tools/ureqcheck/UReqCheck-linux}"
DUMP="$(mktemp -d)"
cd "$UREQ"
java -Dosgi.configuration.area=config/ -Xmx4G -Xss4m \
  -jar plugins/org.eclipse.equinox.launcher_*.jar \
  -tc config/ReqCheck.xml -s config/ReqCheck-nonlin.epf -i "$REQ" \
  --core.print.statistic.results false \
  --traceabstraction.limit.analysis.time 300 \
  --traceabstraction.dump.smt.script.to.file false \
  --pea2boogie.always.use.all.invariants.during.rt-inconsistency.checks true \
  --pea2boogie.check.vacuity true \
  --pea2boogie.check.consistency true \
  --pea2boogie.report.trivial.rt-consistency false \
  --pea2boogie.use.epsilon.transformation.during.rt-inconsistency.check false \
  --pea2boogie.rt-inconsistency.range ${RANGE:-2} \
  --rcfgbuilder.size.of.a.code.block LoopFreeBlock \
  --pea2boogie.check.rt-inconsistency true 2>&1 \
| grep -E "ReqCheck|Inconsistent|inconsistent|vacuous|Vacuous|RESULT|Requirements set|rt-|consistent" \
| grep -vE "Executing the observer|PluginConnector|initialized|Starting" 
