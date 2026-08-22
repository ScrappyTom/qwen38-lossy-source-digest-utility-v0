from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apparatus.canonical import load_json
from apparatus.runner import verify_source_lock
from apparatus.seal import verify_seal


def verify(run_root: Path) -> dict[str, Any]:
    failures = []
    try: verify_source_lock()
    except Exception as exc: failures.append(f"source lock: {type(exc).__name__}: {exc}")
    replay = load_json(run_root / "replay" / "REPLAY.json")
    if replay.get("passed") is not True: failures.append("replay")
    seal = verify_seal(run_root)
    if not seal["passed"]: failures.extend(seal["failures"])
    lifecycle = load_json(run_root / "model" / "runtime-lifecycle.json")
    if lifecycle.get("port_open_after") is not False: failures.append("port remained open")
    if lifecycle.get("llama_processes_after") not in ([], None): failures.append("llama process remained")
    if lifecycle.get("passed") is not True: failures.append("runtime lifecycle")
    run = load_json(run_root / "RUN_RESULT.json")
    if run.get("apparatus_invariant_failure") is True: failures.append("apparatus invariant failure")
    return {"schema_version": "lossy-source-digest-utility-verification-v0", "run_id": run_root.name, "passed": not failures, "failures": failures, "replay": replay, "seal": seal}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("run_root", type=Path); args = parser.parse_args()
    result = verify(args.run_root.resolve()); print(json.dumps(result, sort_keys=True)); return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
