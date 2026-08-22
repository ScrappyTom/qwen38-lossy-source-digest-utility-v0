from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apparatus.canonical import compact_json, load_json, sha256_bytes, write_json
from apparatus.constants import DIGESTED_SOURCE
from apparatus.runner import parse_bare_action
from apparatus.treatment import treated_request


def replay(run_root: Path) -> dict[str, Any]:
    run = load_json(run_root / "RUN_RESULT.json")
    failures = []
    rows = []
    for call in run["calls"]:
        ordinal = call["call"]
        request_bytes = (run_root / "requests" / f"call-{ordinal:02d}.json").read_bytes()
        response_bytes = (run_root / "responses" / f"call-{ordinal:02d}.json").read_bytes()
        http = load_json(run_root / "raw" / f"call-{ordinal:02d}-http.json")
        if sha256_bytes(request_bytes) != http["request_sha256"]: failures.append(f"call {ordinal} request hash")
        if sha256_bytes(response_bytes) != http["response_sha256"]: failures.append(f"call {ordinal} response hash")
        request = json.loads(request_bytes)
        response = json.loads(response_bytes)
        action = parse_bare_action(response["choices"][0]["message"]["content"])
        action_record = load_json(run_root / "actions" / f"call-{ordinal:02d}.json")
        if compact_json(action) != compact_json(action_record["action"]): failures.append(f"call {ordinal} parsed action")
        if ordinal == 1 and request["messages"] != treated_request()["messages"]: failures.append("call 1 treatment packet")
        result = load_json(run_root / "results" / f"call-{ordinal:02d}.json")
        if action.get("path") == DIGESTED_SOURCE and result["result"].get("content") is not None:
            content = result["result"]["content"].encode("utf-8")
            if len(content) != 8063: failures.append(f"call {ordinal} source bytes")
        rows.append({"call": ordinal, "request_sha256": http["request_sha256"], "response_sha256": http["response_sha256"], "action": action, "result_message_sha256": result["result_message_sha256"]})
    if run["model_calls"] != len(rows): failures.append("model call count")
    result = {"schema_version": "lossy-source-digest-utility-replay-v0", "run_id": run["run_id"], "passed": not failures, "failures": failures, "calls_replayed": len(rows), "rows": rows}
    write_json(run_root / "replay" / "REPLAY.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("run_root", type=Path); args = parser.parse_args()
    result = replay(args.run_root.resolve()); print(json.dumps(result, sort_keys=True)); return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())

