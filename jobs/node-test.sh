#!/usr/bin/env bash
# fastify v5.12.7: install its dependencies and run its unit tests, as its own CI does.
source "$(dirname "$0")/lib.sh"
step checkout checkout fastify/fastify 9f400035ebaf572b95989db5040ebb09c01e4e77
cd "$WORK/src"
echo "// $RUN_ID" >> lib/route.js
step install npm install --no-audit --no-fund --loglevel=error
step test npm run unit
