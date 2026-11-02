#!/usr/bin/env bash
# Run only the approved UIE dev20 / support4 sanity pair on the cloned instance.
set -euo pipefail
pilot_root=${1:?new pilot directory required}
case "$pilot_root" in
  /root/autodl-tmp/round2_uie_nocard_20261010/future_pilot/20261012_*) ;;
  *) printf 'Unexpected pilot directory\n' >&2; exit 2 ;;
esac
test -f "$pilot_root/configs/zero_shot.json"
test -f "$pilot_root/configs/support4_sanity.json"
test ! -e "$pilot_root/controller.started"
date -u +%FT%TZ > "$pilot_root/controller.started"
monitor_pid=''
cleanup() {
  if [[ -n "$monitor_pid" ]]; then kill "$monitor_pid" 2>/dev/null || true; wait "$monitor_pid" 2>/dev/null || true; fi
  date -u +%FT%TZ > "$pilot_root/controller.ended"
}
trap cleanup EXIT
(
  while true; do
    nvidia-smi --query-gpu=timestamp,memory.used,memory.free,utilization.gpu --format=csv,noheader
    sleep 2
  done
) > "$pilot_root/gpu_monitor.csv" 2>&1 &
monitor_pid=$!
for phase in zero_shot support4_sanity; do
  date -u +%FT%TZ > "$pilot_root/$phase.started"
  set +e
  timeout --signal=TERM --kill-after=30s 1200 \
    bash /root/project/scripts/round2_uie_gpu_python.sh \
    /root/project/scripts/run_round2_uie.py --config "$pilot_root/configs/$phase.json" \
    > "$pilot_root/$phase.log" 2>&1
  exit_code=$?
  set -e
  printf '%s\n' "$exit_code" > "$pilot_root/$phase.exit_code"
  date -u +%FT%TZ > "$pilot_root/$phase.ended"
  if [[ "$exit_code" -ne 0 ]]; then
    printf '%s\n' "$phase" > "$pilot_root/controller.failed_phase"
    exit "$exit_code"
  fi
done
date -u +%FT%TZ > "$pilot_root/controller.completed"
