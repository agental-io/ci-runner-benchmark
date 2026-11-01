# CI runner benchmark

The same three CI jobs, timed on GitHub's standard runner and on an agental sandbox.

| Job | What it does |
| --- | --- |
| `node-test` | fastify v5.12.7: `npm install`, then its unit tests |
| `rust-build` | ripgrep 15.2.0: `cargo build`, then `cargo test` |
| `docker-build` | umami v3.4.1: its own Dockerfile, built with buildx |

Every run appends a line to one source file, so each build sees a changed tree, as after a push.

- **cold**: nothing kept from before.
- **warm**: on GitHub, `actions/cache` and buildx's `type=gha` cache, restored and saved as GitHub's docs suggest. On agental, the sandbox's own disk, kept while it is stopped between jobs; the time includes starting and stopping it.

`jobs/*.sh` are the jobs, and run unchanged on both. `.github/workflows/bench.yml` runs them on GitHub.
