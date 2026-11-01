#!/usr/bin/env python3
"""Print RESULTS.md's table from results/*.jsonl: the median of each job, end to end.

GitHub, end to end: queue + the job on its runner.
agental, end to end: getting the machine (create, or start) + the job + stopping it.
"""
import json, pathlib, statistics

ROOT = pathlib.Path(__file__).resolve().parent
rows = [json.loads(l) for f in ("github.jsonl", "agental.jsonl") for l in open(ROOT / "results" / f)]


def end_to_end(r):
    return r["queue"] + r["run"] if r["platform"] == "github" else r["total"]


def med(platform, job, mode, f=end_to_end):
    xs = [f(r) for r in rows if r["platform"] == platform and r["job"] == job and r["mode"] == mode]
    return statistics.median(xs), len(xs)


def fmt(s):
    s = round(s)
    return f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"


print("| Job | Cache | GitHub | agental | Faster |")
print("| --- | --- | ---: | ---: | ---: |")
for job in ("node-test", "rust-build", "docker-build"):
    for mode in ("cold", "warm"):
        g, gn = med("github", job, mode)
        a, an = med("agental", job, mode)
        print(f"| `{job}` | {mode} | {fmt(g)} | {fmt(a)} | {g / a:.1f}× |")
