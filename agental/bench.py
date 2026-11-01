#!/usr/bin/env python3
"""Time the jobs in ../jobs on agental sandboxes, the way a CI job would use one.

cold: a new sandbox is created, the job runs, the sandbox is stopped.
warm: the sandbox from before is started, the job runs on the disk it kept, it is stopped.

Each line printed (and appended to results/agental.jsonl) is one sample, with the time of
each phase measured from this computer. Needs AGENTAL_API_KEY.

  python3 agental/bench.py --jobs node-test,rust-build,docker-build --cold 3 --warm 3
"""
import argparse, json, os, pathlib, sys, time, urllib.error, urllib.request, uuid

API = os.environ.get("AGENTAL_API_URL", "https://agental.io")
KEY = os.environ.get("AGENTAL_API_KEY") or sys.exit("AGENTAL_API_KEY is not set")
ROOT = pathlib.Path(__file__).resolve().parent.parent


def call(method, path, body=None, headers=None, timeout=200):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", **(headers or {})}
    for attempt in range(6):
        req = urllib.request.Request(API + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                err = json.loads(raw)
            except ValueError:
                err = None
            if e.code in (502, 503, 504) or err is None:
                time.sleep(10)
                continue
            raise RuntimeError(f"{method} {path}: {e.code} {err}") from None
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10)
    raise RuntimeError(f"{method} {path}: gave up")


def wait_running(sid):
    while True:
        _, s = call("GET", f"/v1/sandboxes/{sid}")
        if s["status"] == "running":
            return s
        time.sleep(2)


def run_job(sid, job, run_id):
    for f in sorted((ROOT / "jobs").iterdir()):
        call("PUT", f"/v1/sandboxes/{sid}/files", {"path": f"bench/jobs/{f.name}", "text": f.read_text()})
    out = f"/opt/agental/out/{run_id}.jsonl"
    cmd = (f"mkdir -p /opt/agental/out && chmod +x /opt/agental/bench/jobs/*.sh && cd /opt/agental && "
           f"WORK=/opt/agental/work/{job} OUT={out} RUN_ID={run_id} HOME=/root "
           f"/opt/agental/bench/jobs/{job}.sh > /opt/agental/out/{run_id}.log 2>&1; "
           f"e=$?; cat {out}; exit $e")
    _, c = call("POST", f"/v1/sandboxes/{sid}/commands", {"command": ["sh", "-c", cmd], "timeoutMs": 600000})
    while True:
        time.sleep(2)
        _, s = call("GET", f"/v1/sandboxes/{sid}/commands/{c['id']}")
        if s["status"] != "running":
            break
    steps = [json.loads(l) for l in (s.get("stdout") or "").splitlines() if l.startswith("{")]
    if s.get("exitCode") != 0:
        _, t = call("POST", f"/v1/sandboxes/{sid}/exec", {"command": ["tail", "-n", "40", f"/opt/agental/out/{run_id}.log"]})
        print(t["stdout"], file=sys.stderr)
    return s["status"], s.get("exitCode"), steps


def sample(job, mode, sid, size, n):
    run_id = f"{job}-{mode}-{n}-{int(time.time())}"
    t = {}
    t0 = time.time()
    if mode == "cold":
        st, s = call("POST", "/v1/sandboxes", {"name": f"bench-{job}-{uuid.uuid4().hex[:6]}", "size": size},
                     headers={"Idempotency-Key": f"bench-{run_id}"})
        while st == 202:
            time.sleep(10)
            st, s = call("POST", "/v1/sandboxes", {"name": s["name"], "size": size},
                         headers={"Idempotency-Key": f"bench-{run_id}"})
        sid = s["id"]
        wait_running(sid)
    else:
        st, _ = call("POST", f"/v1/sandboxes/{sid}/start")
        wait_running(sid)
    t["machine"] = time.time() - t0
    t1 = time.time()
    status, code, steps = run_job(sid, job, run_id)
    t["run"] = time.time() - t1
    t2 = time.time()
    call("POST", f"/v1/sandboxes/{sid}/stop")
    t["stop"] = time.time() - t2
    t["total"] = time.time() - t0
    rec = {"platform": "agental", "size": size, "job": job, "mode": mode, "n": n, "sandbox": sid,
           "status": status, "exitCode": code, **{k: round(v, 1) for k, v in t.items()}, "steps": steps}
    print(json.dumps(rec), flush=True)
    (ROOT / "results").mkdir(exist_ok=True)
    with open(ROOT / "results" / "agental.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    return sid


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jobs", default="node-test,rust-build,docker-build")
    p.add_argument("--size", default="medium")
    p.add_argument("--cold", type=int, default=3)
    p.add_argument("--warm", type=int, default=3)
    a = p.parse_args()
    for job in a.jobs.split(","):
        sid = None
        for n in range(1, a.cold + 1):
            sid = sample(job, "cold", None, a.size, n)
        # The last cold run's sandbox is the one the warm runs reuse, as a CI machine is.
        for n in range(1, a.warm + 1):
            sample(job, "warm", sid, a.size, n)


if __name__ == "__main__":
    main()
