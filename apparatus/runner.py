from __future__ import annotations

import copy
import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apparatus.canonical import canonical_json_bytes, compact_json, load_json, sha256_bytes, sha256_file, write_json
from apparatus.constants import CELL, CONTEXT_TOKENS, DIGESTED_SOURCE, EXPECTED_MODEL_SHA256, EXPECTED_MODEL_SIZE, EXPECTED_SERVER_SHA256, INTEGRITY_REJECTION_CODES, MAXIMUM_MEASURED_CALLS, MAXIMUM_PROMPT_TOKENS, MODEL_ALIAS, ROOT, SEED, STUDY_ID
from apparatus.environment import make_environment, validate_action
from apparatus.modelio import ParentTokenEndpoint
from apparatus.receipts import pressure_projection, receipt_from_message
from apparatus.treatment import historical_request, treated_request


ACQUISITION_ACTIONS = {"tree", "search", "read", "read_lines", "read_region", "repo_list", "repo_catalog", "repo_read_lines", "continue_lines", "repo_search", "repo_read", "repo_history"}


@dataclass(frozen=True)
class HttpRecord:
    status_code: int
    headers: dict[str, str]
    body: bytes
    duration_ms: int
    transport_error: str | None

    @property
    def success(self) -> bool:
        return self.transport_error is None and 200 <= self.status_code < 300


def _http(request: urllib.request.Request, timeout_seconds: int = 900) -> HttpRecord:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return HttpRecord(int(response.status), {k.lower(): v for k, v in response.headers.items()}, response.read(), round((time.perf_counter() - started) * 1000), None)
    except urllib.error.HTTPError as exc:
        return HttpRecord(int(exc.code), {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}, exc.read(), round((time.perf_counter() - started) * 1000), None)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return HttpRecord(0, {}, b"", round((time.perf_counter() - started) * 1000), f"{type(exc).__name__}: {exc}")


def get_json(base_url: str, path: str) -> dict[str, Any]:
    response = _http(urllib.request.Request(base_url.rstrip("/") + path, method="GET"), 60)
    if not response.success:
        raise RuntimeError(f"GET {path} failed: status={response.status_code} error={response.transport_error}")
    value = json.loads(response.body)
    if not isinstance(value, dict):
        raise RuntimeError(f"GET {path} returned a non-object")
    return value


def post_chat(base_url: str, body: bytes) -> HttpRecord:
    return _http(urllib.request.Request(base_url.rstrip("/") + "/v1/chat/completions", data=body, method="POST", headers={"Content-Type": "application/json"}))


def current_head() -> str:
    process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
    if process.returncode:
        raise RuntimeError("standalone repository has no committed HEAD")
    return process.stdout.strip()


def require_clean_head() -> str:
    head = current_head()
    process = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
    if process.returncode or process.stdout.strip():
        raise RuntimeError("measured execution requires a clean committed standalone HEAD")
    return head


def verify_source_lock() -> tuple[dict[str, Any], str]:
    lock_path = ROOT / "provenance" / "SOURCE_LOCK.json"
    lock = load_json(lock_path)
    for row in lock["files"]:
        path = ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"source-lock mismatch: {row['path']}")
    return lock, sha256_file(lock_path)


def require_authorization() -> dict[str, Any]:
    lock, lock_sha = verify_source_lock()
    request = load_json(ROOT / "AUTHORIZATION_REQUEST.json")
    authorization = load_json(ROOT / "execution" / "AUTHORIZATION.json")
    expected = {"study_id": STUDY_ID, "approved": True, "source_lock_sha256": lock_sha, "maximum_model_calls": MAXIMUM_MEASURED_CALLS, "retries": 0}
    if request.get("source_lock_sha256") != lock_sha:
        raise RuntimeError("authorization request does not bind the current source lock")
    failures = [f"{key}={authorization.get(key)!r}" for key, value in expected.items() if authorization.get(key) != value]
    if failures:
        raise RuntimeError("authorization mismatch: " + "; ".join(failures))
    return {"authorization": authorization, "source_lock": lock, "source_lock_sha256": lock_sha}


def verify_runtime_files(server: Path, model: Path) -> dict[str, Any]:
    if not server.is_file() or sha256_file(server) != EXPECTED_SERVER_SHA256:
        raise RuntimeError("llama-server executable does not match the frozen package")
    if not model.is_file() or model.stat().st_size != EXPECTED_MODEL_SIZE or sha256_file(model) != EXPECTED_MODEL_SHA256:
        raise RuntimeError("model does not match the frozen package")
    return {"server_executable": {"path": str(server), "size_bytes": server.stat().st_size, "sha256": EXPECTED_SERVER_SHA256}, "model": {"path": str(model), "size_bytes": model.stat().st_size, "sha256": EXPECTED_MODEL_SHA256}}


def verify_endpoint(base_url: str, model: Path) -> dict[str, Any]:
    health = get_json(base_url, "/health")
    props = get_json(base_url, "/props")
    generation = props.get("default_generation_settings", {})
    failures = []
    if health.get("status") != "ok": failures.append("health")
    if props.get("model_alias") != MODEL_ALIAS: failures.append("alias")
    if props.get("build_info") != "b10434-7e4c0a968": failures.append("build")
    if generation.get("n_ctx") != CONTEXT_TOKENS: failures.append("context")
    reported = props.get("model_path")
    if reported and Path(str(reported)).resolve() != model.resolve(): failures.append("model_path")
    if failures: raise RuntimeError("endpoint identity mismatch: " + ", ".join(failures))
    return props


def parse_bare_action(content: str) -> dict[str, Any]:
    stripped = content.strip()
    decoder = json.JSONDecoder()
    value, end = decoder.raw_decode(stripped)
    if stripped[end:].strip() or not isinstance(value, dict):
        raise ValueError("assistant response is not one bare JSON object")
    return value


def parse_response(response: HttpRecord) -> dict[str, Any]:
    if not response.success:
        return {"valid": False, "error": "provider_http_failure", "details": {"status": response.status_code, "transport": response.transport_error}}
    try:
        payload = json.loads(response.body)
        if not isinstance(payload.get("choices"), list) or len(payload["choices"]) != 1:
            raise ValueError("choice count invalid")
        choice = payload["choices"][0]
        message = choice["message"]
        if choice.get("finish_reason") != "stop" or message.get("role") != "assistant":
            raise ValueError("assistant turn or finish reason invalid")
        if message.get("reasoning_content") not in (None, "") or message.get("tool_calls") not in (None, []):
            raise ValueError("unexpected reasoning or native tool calls")
        content = message["content"]
        action = validate_action(CELL, parse_bare_action(content))
    except Exception as exc:
        return {"valid": False, "error": "invalid_model_response", "details": f"{type(exc).__name__}: {exc}"}
    return {"valid": True, "payload": payload, "assistant_message": {"role": "assistant", "content": content}, "action": action, "usage": payload.get("usage")}


def action_key(action: dict[str, Any]) -> str:
    return compact_json(action)


def historical_action_keys(messages: list[dict[str, Any]]) -> list[str]:
    rows = []
    for message in messages:
        if message.get("role") != "assistant": continue
        try: action = json.loads(message["content"])
        except (KeyError, TypeError, json.JSONDecodeError): continue
        if isinstance(action, dict) and isinstance(action.get("action"), str): rows.append(action_key(action))
    return rows


def same_source_access_class(action: dict[str, Any]) -> str | None:
    if action.get("path") != DIGESTED_SOURCE: return None
    if action == {"action": "repo_read", "path": DIGESTED_SOURCE}: return "exact_historical_whole_source_reopen"
    if action.get("action") == "repo_read_lines": return "narrower_same_source_precision_access"
    if action.get("action") in {"repo_read", "repo_history"}: return "other_same_source_access"
    return None


def receipt_reopen(action: dict[str, Any], messages: list[dict[str, Any]]) -> bool:
    for message in messages:
        receipt = receipt_from_message(message)
        if receipt is not None and action_key(receipt.get("reopen_action", {})) == action_key(action): return True
    return False


def action_class(action: dict[str, Any], messages: list[dict[str, Any]]) -> str:
    if same_source_access_class(action): return "same_source_raw_access"
    if action.get("action") in {"patch", "replace_file"}: return "mutation"
    if action.get("action") == "submit": return "submission"
    if receipt_reopen(action, messages): return "exact_reopen_other_object"
    if action.get("action") in ACQUISITION_ACTIONS: return "other_acquisition"
    return "other"


def _write_http(root: Path, ordinal: int, request_bytes: bytes, response: HttpRecord) -> None:
    for child in ("requests", "responses", "raw"): (root / child).mkdir(parents=True, exist_ok=True)
    (root / "requests" / f"call-{ordinal:02d}.json").write_bytes(request_bytes)
    (root / "responses" / f"call-{ordinal:02d}.json").write_bytes(response.body)
    write_json(root / "raw" / f"call-{ordinal:02d}-http.json", {"request_sha256": sha256_bytes(request_bytes), "request_size_bytes": len(request_bytes), "response_sha256": sha256_bytes(response.body), "response_size_bytes": len(response.body), "status_code": response.status_code, "headers": response.headers, "duration_ms": response.duration_ms, "transport_error": response.transport_error})


def run_experiment(run_id: str, base_url: str, runtime_custody: dict[str, Any]) -> dict[str, Any]:
    run_root = ROOT / "runs" / run_id
    if run_root.exists(): raise RuntimeError(f"run directory already exists: {run_root}")
    head = require_clean_head()
    authorization = require_authorization()
    for child in ("actions", "budget", "candidates", "objects", "projections", "raw", "requests", "responses", "results", "world", "model", "analysis", "replay"): (run_root / child).mkdir(parents=True, exist_ok=True)
    write_json(run_root / "model" / "AUTHORIZATION.json", authorization["authorization"])
    write_json(run_root / "model" / "runtime-custody.json", runtime_custody)
    environment = make_environment(CELL, run_root / "world")
    write_json(run_root / "candidates" / "initial.json", environment.initial_snapshot)
    request = treated_request()
    messages = copy.deepcopy(request["messages"])
    kwargs = request["chat_template_kwargs"]
    token_endpoint = ParentTokenEndpoint(base_url)
    initial = token_endpoint.count(messages, kwargs).as_dict()
    if initial != load_json(ROOT / "CAPACITY_PREFLIGHT.json")["treatment"] or not initial["fits"]:
        raise RuntimeError("live treated packet does not match frozen exact-token preflight")
    history_keys = historical_action_keys(historical_request()["messages"])
    calls, pressure_events = [], []
    endpoint, integrity_failure = "model_call_limit", False

    for ordinal in range(1, MAXIMUM_MEASURED_CALLS + 1):
        capacity = token_endpoint.count(messages, kwargs).as_dict()
        if not capacity["fits"]:
            endpoint, integrity_failure = "capacity_invariant_failed_before_call", True
            break
        call_request = copy.deepcopy(request); call_request["messages"] = copy.deepcopy(messages)
        request_bytes = canonical_json_bytes(call_request)
        response = post_chat(base_url, request_bytes); token_endpoint.chat_completion_calls += 1
        _write_http(run_root, ordinal, request_bytes, response)
        parsed = parse_response(response)
        if not parsed["valid"]:
            write_json(run_root / "actions" / f"call-{ordinal:02d}.json", parsed)
            endpoint, integrity_failure = "model_or_server_integrity_failure", True
            break
        action = parsed["action"]
        classification, same_source = action_class(action, messages), same_source_access_class(action)
        before = environment.snapshot(); result = environment.execute(action); after = environment.snapshot()
        action_id = f"schema-action-{25 + ordinal:03d}"
        result_message = environment.result_message(action, action_id, result)
        result_bytes = result_message["content"].encode("utf-8"); result_sha = sha256_bytes(result_bytes)
        (run_root / "objects" / f"{result_sha}.json").write_bytes(result_bytes)
        environment.exact_reopens[action_key(action)] = copy.deepcopy(result)
        key = action_key(action); duplicate = action.get("action") in ACQUISITION_ACTIONS and key in history_keys; history_keys.append(key)
        action_record = {"call": ordinal, "action": action, "classification": classification, "same_source_access_subclass": same_source, "admitted": result.get("accepted") is True, "candidate_before": before["candidate_id"], "candidate_after": after["candidate_id"], "duplicate_on_unchanged_candidate_basis": duplicate and before["candidate_id"] == after["candidate_id"], "exact_receipt_reopen": receipt_reopen(action, messages)}
        write_json(run_root / "actions" / f"call-{ordinal:02d}.json", action_record)
        write_json(run_root / "results" / f"call-{ordinal:02d}.json", {"action_id": action_id, "action": action, "result": result, "result_message_sha256": result_sha, "result_message_size_bytes": len(result_bytes)})
        calls.append({**action_record, "request_capacity": capacity, "provider_usage": parsed["usage"], "http_duration_ms": response.duration_ms, "result_delivered_to_later_call": False})
        error_code = result.get("error", {}).get("code") if isinstance(result.get("error"), dict) else None
        if error_code in INTEGRITY_REJECTION_CODES:
            endpoint, integrity_failure = "apparatus_invariant_failure", True; break
        if same_source is not None:
            endpoint = "immediate_same_source_raw_access" if ordinal == 1 else "delayed_same_source_raw_access"; break
        if action.get("action") == "submit" and result.get("accepted") is True:
            endpoint = "admitted_submission"; break
        if ordinal == MAXIMUM_MEASURED_CALLS:
            endpoint = "model_call_limit_result_custodied_not_delivered"; break
        tail = [parsed["assistant_message"], result_message]
        raw_capacity = token_endpoint.count(messages + tail, kwargs).as_dict()
        event = {"after_call": ordinal, "raw_post_result": raw_capacity, "pressure_triggered": not raw_capacity["fits"], "result_message_sha256": result_sha, "result_message_size_bytes": len(result_bytes)}
        if raw_capacity["fits"]:
            messages += tail; event.update({"policy_applied": False, "post_policy": raw_capacity, "delivery_status": "delivered_to_next_call"})
        else:
            projection = pressure_projection(CELL, messages, tail, maximum_prompt_tokens=MAXIMUM_PROMPT_TOKENS, token_count=lambda candidate: token_endpoint.count(candidate, kwargs).prompt_tokens, backing_id=lambda index, message: f"{run_id}:message:{sha256_bytes(message['content'].encode('utf-8'))}")
            post = token_endpoint.count(projection.messages, kwargs).as_dict()
            event.update({"policy_applied": True, "policy_id": projection.policy_id, "changes": projection.changes, "selection_trace": projection.selection_trace, "post_policy": post, "delivery_status": "delivered_to_next_call" if projection.fits else "capacity_unrestored"})
            write_json(run_root / "projections" / f"after-call-{ordinal:02d}.json", {"request": {**request, "messages": projection.messages}, **event})
            pressure_events.append(event)
            if not projection.fits:
                endpoint = "capacity_unrestored_before_result_delivery"; write_json(run_root / "budget" / f"after-call-{ordinal:02d}.json", event); break
            messages = projection.messages
        calls[-1]["result_delivered_to_later_call"] = True
        write_json(run_root / "budget" / f"after-call-{ordinal:02d}.json", event)

    terminal = environment.snapshot(); write_json(run_root / "candidates" / "terminal.json", terminal)
    result = {"schema_version": "lossy-source-digest-utility-run-result-v0", "study_id": STUDY_ID, "run_id": run_id, "standalone_commit": head, "source_lock_sha256": authorization["source_lock_sha256"], "seed": SEED, "model_calls": len(calls), "maximum_authorized_model_calls": MAXIMUM_MEASURED_CALLS, "retries": 0, "endpoint": endpoint, "apparatus_invariant_failure": integrity_failure, "initial_treatment_capacity": initial, "calls": calls, "pressure_events": pressure_events, "initial_candidate_id": environment.initial_snapshot["candidate_id"], "final_candidate_id": terminal["candidate_id"], "admitted_mutations": sum(1 for row in calls if row["classification"] == "mutation" and row["admitted"]), "admitted_submissions": sum(1 for row in calls if row["classification"] == "submission" and row["admitted"]), "same_source_raw_accesses": sum(1 for row in calls if row["classification"] == "same_source_raw_access"), "token_endpoint_calls": {"apply_template": token_endpoint.apply_calls, "tokenize": token_endpoint.tokenize_calls, "chat_completions": token_endpoint.chat_completion_calls}}
    write_json(run_root / "RUN_RESULT.json", result)
    return result
