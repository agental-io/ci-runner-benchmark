# Shared by every job. Sourced, not run.
#
# WORK   where the job keeps its checkout (kept between runs on a machine that keeps its disk)
# OUT    a file each timed step appends one JSON line to
# RUN_ID a value that differs from run to run, written into one source file so each run
#        builds a changed tree, as a push does
set -euo pipefail
: "${WORK:?}" "${OUT:?}" "${RUN_ID:?}"
JOB=$(basename "$0" .sh)
mkdir -p "$WORK" "$(dirname "$OUT")"

step() {
  local name=$1; shift
  local t0 t1
  t0=$(date +%s.%N)
  "$@"
  t1=$(date +%s.%N)
  printf '{"job":"%s","step":"%s","seconds":%.2f}\n' "$JOB" "$name" "$(awk "BEGIN{print $t1 - $t0}")" | tee -a "$OUT"
}

# Check out REPO at SHA in $WORK/src. A checkout already there is reset to SHA, untracked
# build output kept, so a kept disk keeps its node_modules and target.
checkout() {
  local repo=$1 sha=$2
  if [ -d "$WORK/src/.git" ]; then
    git -C "$WORK/src" checkout -q -f "$sha"
  else
    git init -q "$WORK/src"
    git -C "$WORK/src" fetch -q --depth 1 "https://github.com/$repo" "$sha"
    git -C "$WORK/src" checkout -q -f FETCH_HEAD
  fi
}
