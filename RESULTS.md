# Results, 1 November 2026

Median of three runs per row, end to end. GitHub: time in the queue plus the job on its
runner, cache restore and save included. agental: getting the machine (a create when cold, a
start of the stopped sandbox when warm), the job, and stopping it, timed from the API's caller.

Cost is each run billed at list price: GitHub's Linux 4-core runner at $0.012 a minute, each job
rounded up to a whole minute and its queue not billed; agental's medium at $0.054 an hour, by
the second, from the create or start to the stop. Prices read on 1 November 2026.

| Job | Cache | GitHub | agental | Faster | GitHub, 1,000 runs | agental, 1,000 runs | Cheaper |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `node-test` | cold | 1m 11s | 45s | 1.6× | $24.00 | $0.67 | 36× |
| `node-test` | warm | 49s | 35s | 1.4× | $12.00 | $0.53 | 23× |
| `rust-build` | cold | 27s | 15s | 1.8× | $12.00 | $0.23 | 53× |
| `rust-build` | warm | 20s | 14s | 1.4× | $12.00 | $0.21 | 58× |
| `docker-build` | cold | 3m 03s | 1m 29s | 2.1× | $36.00 | $1.33 | 27× |
| `docker-build` | warm | 4m 32s | 56s | 4.9× | $48.00 | $0.84 | 57× |

- **GitHub**: `ubuntu-latest` in a public repository, 4 vCPU and 16 GB. **agental**: a `medium` sandbox, 4 vCPU and 8 GB.
- Every run changes one source file, so warm runs rebuild what a push would.
- GitHub's warm Docker build is slower than its cold one: exporting buildx's `type=gha` cache (`mode=max`) costs more than the cache saves on this build. On agental the layers are already on the disk.
- On agental, a warm run spends about 10 s starting the stopped sandbox; a cold one got a machine made in advance in about 0.5 s.
- Steps alone, warm: `npm install` 2.4 s on GitHub, 0.6 s on agental; ripgrep's build 4.3 s and 0.55 s; umami's image 3m 33s and 45 s.
- The agental times are polled every 2 s, so each is up to 2 s long. GitHub's are whole seconds, from its API.
- Three samples per row. End to end, GitHub's times varied by up to 55% between runs (the warm Docker build, 3m 23s to 5m 16s); agental's by up to 20% (ripgrep cold, 13 s to 15 s), the rest under 5%.
- Most of the cost gap is the price of a minute: $0.012 on GitHub against $0.0009 on agental, 13× before speed. GitHub's rounding to a whole minute widens it most on short jobs, such as ripgrep's.
- Not in the agental figures: a warm sandbox costs $0.0027 an hour while stopped between jobs, about $1.97 a month per machine kept, and a medium needs the Fleet plan, $100 a month with $100 of time included. Not in GitHub's: a public repository runs on these runners free, and a private one gets included minutes on its smaller 2-core runner only.

Raw samples: `results/github.jsonl` (from `github/collect.py`) and `results/agental.jsonl` (from `agental/bench.py`).
