#!/usr/bin/env python3
"""Write results/github.jsonl from the repository's Bench runs, through gh.

queue: from the run being created to the job starting on a runner.
run:   the job on its runner, from its start to its end, cache restore and save included.
"""
import datetime, io, json, pathlib, subprocess, sys, zipfile

REPO = sys.argv[1] if len(sys.argv) > 1 else "zmf/ci-runner-benchmark"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True).stdout


def ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


runs = json.loads(gh("api", f"repos/{REPO}/actions/runs?per_page=100"))["workflow_runs"]
runs = sorted((r for r in runs if r["status"] == "completed"), key=lambda r: r["created_at"])
seeded = False
out = []
for r in runs:
    mode = r["display_title"]
    # The first warm run fills the caches and is not a sample of a warm run.
    seed = mode == "warm" and not seeded
    seeded = seeded or mode == "warm"
    jobs = json.loads(gh("api", f"repos/{REPO}/actions/runs/{r['id']}/jobs"))["jobs"]
    arts = json.loads(gh("api", f"repos/{REPO}/actions/runs/{r['id']}/artifacts"))["artifacts"]
    steps = {}
    for a in arts:
        z = zipfile.ZipFile(io.BytesIO(gh("api", a["archive_download_url"])))
        steps[a["name"]] = [json.loads(l) for n in z.namelist() for l in z.read(n).decode().splitlines() if l]
    for j in jobs:
        out.append({"platform": "github", "size": "ubuntu-latest", "job": j["name"], "mode": "seed" if seed else mode,
                    "run_id": r["id"], "status": j["conclusion"],
                    "queue": round(ts(j["started_at"]) - ts(r["created_at"]), 1),
                    "run": round(ts(j["completed_at"]) - ts(j["started_at"]), 1),
                    "steps": steps.get(j["name"], [])})
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results" / "github.jsonl").write_text("".join(json.dumps(o) + "\n" for o in out))
print(f"{len(out)} samples")
