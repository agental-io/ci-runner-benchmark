#!/usr/bin/env bash
# ripgrep 15.2.0: build it and run its tests.
source "$(dirname "$0")/lib.sh"
step checkout checkout BurntSushi/ripgrep e89fff89ac9af12e8d4ce9d5fd07beb408ca730f
cd "$WORK/src"
echo "// $RUN_ID" >> crates/core/main.rs
step build cargo build --locked --quiet
step test cargo test --locked --quiet
