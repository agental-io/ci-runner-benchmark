#!/usr/bin/env bash
# umami v3.4.1: build its Docker image with its own Dockerfile.
# BUILD_ARGS adds to the build command, such as GitHub's cache (--cache-from type=gha ...).
source "$(dirname "$0")/lib.sh"
step checkout checkout umami-software/umami 559e3c607c23d2c72d9bd4f6481bda428255323c
cd "$WORK/src"
echo "// $RUN_ID" >> src/lib/constants.ts
# shellcheck disable=SC2086
step build docker buildx build --load --progress=plain -t umami-bench \
  --build-arg SKIP_BUILD_GEO=1 ${BUILD_ARGS:-} . > "$WORK/docker-build.log" 2>&1
