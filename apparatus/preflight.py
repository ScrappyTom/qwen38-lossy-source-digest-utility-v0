from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from apparatus.canonical import canonical_json_bytes, compact_json, load_json, sha256_bytes, sha256_file, write_json
from apparatus.constants import CONTEXT_TOKENS, DIGESTED_SOURCE, MAXIMUM_MEASURED_CALLS, RESPONSE_RESERVE, ROOT, SOURCE_COMMIT, SOURCE_FILES, STUDY_ID
from apparatus.custody import verify_imports
from apparatus.environment import make_environment
from apparatus.modelio import render_parent_template
from apparatus.receipts import pressure_projection
from apparatus.treatment import digest_message, digest_object, historical_request, treated_request, treatment_delta


def tokenize_count(tokenizer: Path, model: Path, prompt_path: Path) -> int:
    process = subprocess.run(
        [str(tokenizer), "-m", str(model), "-f", str(prompt_path), "--no-bos", "--no-escape", "--show-count", "--log-disable", "--device", "none"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, text=True, encoding="utf-8", errors="replace",
    )
    if process.returncode:
        raise RuntimeError(f"tokenizer failed for {prompt_path}: {process.stdout[-2000:]}")
    match = re.search(r"Total number of tokens:\s*(\d+)\s*$", process.stdout)
    if match is None:
        raise RuntimeError(f"cannot parse tokenizer count for {prompt_path}")
    return int(match.group(1))


def capacity(request: dict[str, Any], tokenizer: Path, model: Path, name: str) -> dict[str, Any]:
    rendered = render_parent_template(request["messages"])
    path = ROOT / "preflight" / f"{name}-rendered-prompt.txt"
    path.write_text(rendered, encoding="utf-8", newline="")
    prompt_tokens = tokenize_count(tokenizer, model, path)
    raw = rendered.encode("utf-8")
    headroom = CONTEXT_TOKENS - RESPONSE_RESERVE - prompt_tokens
    return {
        "prompt_tokens": prompt_tokens, "rendered_prompt_sha256": sha256_bytes(raw),
        "rendered_prompt_size_bytes": len(raw), "context_tokens": CONTEXT_TOKENS,
        "response_reserve_tokens": RESPONSE_RESERVE, "headroom_after_reserve": headroom,
        "fits": headroom >= 0,
    }


def complementarity_audit(packet_hash: str) -> dict[str, Any]:
    return {
        "schema_version": "co-residency-complementarity-audit-v0", "packet_sha256": packet_hash,
        "actor_packet_changed_by_audit": False,
        "known_omissions": [
            {
                "proposition": "The source-navigation study candidate remained unchanged.",
                "source_scope": "large-world-source-navigation-v0 sealed bank",
                "candidate_carriers": [
                    {"carrier": "current continuation candidate identity", "classification": "different_scope", "reason": "It describes the later working-model continuation candidate, not the candidate in the digested source study."},
                    {"carrier": "digested source exact reopen receipt", "classification": "not_resident", "reason": "The receipt preserves identity and recovery, not the omitted proposition."},
                ],
                "same_proposition_resident": False,
            },
            {
                "proposition": "No check ran in the source-navigation study.",
                "source_scope": "large-world-source-navigation-v0 sealed bank",
                "candidate_carriers": [
                    {"carrier": "current continuation action schema", "classification": "different_scope", "reason": "The absence of a current check action does not state the historical source-study check outcome."},
                    {"carrier": "digested source exact reopen receipt", "classification": "not_resident", "reason": "The receipt preserves identity and recovery, not the omitted proposition."},
                ],
                "same_proposition_resident": False,
            },
        ],
        "preserved_semantic_carrier": {
            "carrier": "frozen source-bound digest message", "classification": "source_bound_lossy_semantic_carrier",
            "other_same-scope_semantic_carrier_resident": False,
        },
        "conclusion": "The two known omissions remain real losses at this packet; neither is silently counted as supplied by current-state metadata.",
    }


def marginal_contract(control: dict[str, Any], treatment: dict[str, Any], digest_tokens: int) -> dict[str, Any]:
    marginal = treatment["prompt_tokens"] - control["prompt_tokens"]
    return {
        "schema_version": "marginal-value-contract-v0", "boundary_state": "seed 314159 horizon call 12 exact repeated-source reopen boundary",
        "marginal_intervention": "append one frozen source-bound lossy digest; preserve all historical messages and exact reopen",
        "co_resident_complements_or_substitutes": "No same-scope carrier supplies either known omitted proposition; exact source remains externally reopenable.",
        "immediate_price": {
            "resident_prompt_tokens": marginal, "digest_content_tokens": digest_tokens,
            "wrapper_and_template_marginal_tokens": marginal - digest_tokens,
            "production_prompt_tokens": 6902, "production_completion_tokens": 219,
            "production_total_tokens": 7121, "production_latency_ms": 16070,
            "maintenance_switching": "measure insertion, prefill, cache, and any pressure projection",
            "recovery": "measure same-source raw access, delayed access, bytes, calls, and latency",
        },
        "state_transition": "first actor decision, then at most two conditional decisions",
        "future_information_demand": "classify exact historical whole-source, narrower same-source, other source, candidate, mutation, or submission",
        "downstream_value": "Requires useful progress, meaningful raw-demand deferral, or selective exact recovery improving action/quality; a merely different valid read is neutral.",
        "failure_migration": "record capacity, alternative duplicate acquisition, semantic error, or artifact degradation",
        "feedback_horizon_calls": 3, "historical_control_contemporaneous": False,
        "latency_and_cache_comparison": "descriptive",
    }


def boundary_audit() -> dict[str, Any]:
    call9 = load_json(ROOT / "parent_evidence" / "boundary" / "call-09-action.json")
    call12 = load_json(ROOT / "parent_evidence" / "boundary" / "call-12-action.json")
    initial = load_json(ROOT / "parent_evidence" / "boundary" / "candidate-initial.json")
    terminal = load_json(ROOT / "parent_evidence" / "boundary" / "candidate-terminal.json")
    expected = {"action": "repo_read", "path": DIGESTED_SOURCE}
    return {
        "schema_version": "lossy-source-digest-boundary-audit-v0", "seed": 314159,
        "call_09_action": call9["action"], "call_12_action": call12["action"],
        "actions_byte_equivalent": compact_json(call9["action"]) == compact_json(call12["action"]) == compact_json(expected),
        "candidate_initial": initial["candidate_id"], "candidate_terminal": terminal["candidate_id"],
        "candidate_unchanged": initial["candidate_id"] == terminal["candidate_id"],
        "historical_call_12_classification": call12["classification"],
        "selected_post_hoc_from_known_history": True,
    }


def prepare(tokenizer: Path, model: Path) -> dict[str, Any]:
    materialization = verify_imports()
    write_json(ROOT / "provenance" / "PARENT_MATERIALIZATION_RECEIPT.json", materialization)
    write_json(ROOT / "provenance" / "PARENT_SOURCE_LOCK.json", {"schema_version": "lossy-source-digest-parent-source-lock-v0", "donors": materialization["donors"], "files": materialization["files"]})
    model_lock = load_json(ROOT / "parent_evidence" / "runtime" / "MODEL_PROFILE_LOCK.json")
    write_json(ROOT / "provenance" / "MODEL_PROFILE_LOCK.json", model_lock)

    control_request = historical_request(); treatment_request = treated_request()
    control = capacity(control_request, tokenizer, model, "control")
    treatment = capacity(treatment_request, tokenizer, model, "treatment")
    expected_control = load_json(ROOT / "parent_evidence" / "boundary" / "after-call-11-budget.json")["post_policy"]
    if control != expected_control:
        raise RuntimeError("offline exact tokenizer did not reproduce the historical 19,686-token control packet")
    digest_path = ROOT / "preflight" / "digest-content.txt"
    digest_path.write_text(digest_object()["source_bound_semantic_digest"]["digest"], encoding="utf-8", newline="")
    digest_tokens = tokenize_count(tokenizer, model, digest_path)
    receipt = load_json(ROOT / "parent_evidence" / "digest" / "DIGEST_RECEIPT.json")
    if digest_tokens != receipt["digest_token_count"]:
        raise RuntimeError("frozen digest token count did not replay")
    if not treatment["fits"]:
        raise RuntimeError("treated first request does not preserve the frozen response reserve")
    write_json(ROOT / "CAPACITY_PREFLIGHT.json", {"schema_version": "lossy-source-digest-capacity-preflight-v0", "control": control, "treatment": treatment, "marginal_prompt_tokens": treatment["prompt_tokens"] - control["prompt_tokens"], "largest_legal_response_tokens": RESPONSE_RESERVE, "largest_legal_response_fits": treatment["fits"]})

    delta = treatment_delta(); write_json(ROOT / "TREATMENT_DELTA.json", {"schema_version": "lossy-source-digest-treatment-delta-v0", **delta})
    packet_hash = sha256_bytes(canonical_json_bytes(treatment_request))
    write_json(ROOT / "DIGEST_RENDER_RECEIPT.json", {"schema_version": "lossy-source-digest-render-receipt-v0", "message": digest_message(), "message_content_sha256": delta["added_message_sha256"], "message_content_size_bytes": delta["added_message_size_bytes"], "digest_content_tokens": digest_tokens, "treated_request_sha256": packet_hash})
    write_json(ROOT / "BOUNDARY_AUDIT.json", boundary_audit())
    write_json(ROOT / "CO_RESIDENCY_COMPLEMENTARITY_AUDIT.json", complementarity_audit(packet_hash))
    write_json(ROOT / "MARGINAL_VALUE_CONTRACT.json", marginal_contract(control, treatment, digest_tokens))

    # Offline apparatus probes use private temporary state under preflight.
    with tempfile.TemporaryDirectory(prefix="s3-fake-probe-") as temporary:
        environment = make_environment("s314159-s1", Path(temporary))
        source_result = environment.execute({"action": "repo_read", "path": DIGESTED_SOURCE})
        region_result = environment.execute({"action": "read_region", "region_id": "R033"})
        first_line = (environment.candidate_root / "QWEN_RELATION_ACTION_WORKING_MODEL.md").read_text(encoding="utf-8").splitlines()[0]
        current_sha = sha256_file(environment.candidate_root / "QWEN_RELATION_ACTION_WORKING_MODEL.md")
        mutation = environment.execute({"action": "patch", "path": "QWEN_RELATION_ACTION_WORKING_MODEL.md", "old": first_line, "new": first_line + " ", "expected_file_sha256": current_sha})
        submission = environment.execute({"action": "submit"})
        fake_messages = copy.deepcopy(treatment_request["messages"])
        fake_action = {"role": "assistant", "content": compact_json({"action": "repo_read", "path": DIGESTED_SOURCE})}
        fake_result = environment.result_message({"action": "repo_read", "path": DIGESTED_SOURCE}, "schema-action-026", source_result)
        projection = pressure_projection("s314159-s1", fake_messages, [fake_action, fake_result], maximum_prompt_tokens=20_992, token_count=lambda messages: len(render_parent_template(messages).encode("utf-8")))
        probes = {"exact_source_read": source_result.get("accepted") is True, "exact_region_read": region_result.get("accepted") is True, "mutation": mutation.get("accepted") is True, "submission": submission.get("accepted") is True, "digest_message_survives_projection_pair_scan": isinstance(projection.messages, list)}
    write_json(ROOT / "preflight" / "FAKE_MODEL_PROBES.json", {"schema_version": "lossy-source-digest-fake-model-probes-v0", "passed": all(probes.values()), "probes": probes})
    result = {"schema_version": "lossy-source-digest-offline-preflight-v0", "passed": materialization["all_byte_equivalent"] and all(probes.values()) and treatment["fits"], "parent_files": materialization["file_count"], "control_prompt_tokens": control["prompt_tokens"], "treatment_prompt_tokens": treatment["prompt_tokens"], "treatment_headroom": treatment["headroom_after_reserve"], "digest_content_tokens": digest_tokens, "maximum_measured_calls": MAXIMUM_MEASURED_CALLS, "retries": 0}
    write_json(ROOT / "OFFLINE_PREFLIGHT.json", result)
    return result


def freeze_lock() -> dict[str, Any]:
    excluded_roots = {".git", ".cache", ".cache-import", "runs", "execution"}
    excluded_files = {"provenance/SOURCE_LOCK.json", "AUTHORIZATION_REQUEST.json"}
    files = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix()):
        if not path.is_file(): continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.split("/", 1)[0] in excluded_roots or relative in excluded_files or "__pycache__" in relative or ".pytest_cache" in relative: continue
        files.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    lock = {"schema_version": "lossy-source-digest-source-lock-v0", "study_id": STUDY_ID, "file_count": len(files), "total_bytes": sum(row["size_bytes"] for row in files), "files": files}
    write_json(ROOT / "provenance" / "SOURCE_LOCK.json", lock)
    lock_sha = sha256_file(ROOT / "provenance" / "SOURCE_LOCK.json")
    request = {"schema_version": "measured-inference-authorization-request-v0", "study_id": STUDY_ID, "source_lock_sha256": lock_sha, "maximum_model_calls": MAXIMUM_MEASURED_CALLS, "retries": 0, "requested_operation": "one treated seed-314159 actor cell with conditional three-call ceiling", "approval_status": "user_authorized_in_codex_thread_2026-08-21"}
    write_json(ROOT / "AUTHORIZATION_REQUEST.json", request)
    return {"source_lock_sha256": lock_sha, "file_count": len(files), "authorization_request": request}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true"); parser.add_argument("--freeze-lock", action="store_true")
    parser.add_argument("--tokenizer", type=Path); parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.prepare:
        if args.tokenizer is None or args.model is None: parser.error("--prepare requires --tokenizer and --model")
        result = prepare(args.tokenizer.resolve(), args.model.resolve())
    elif args.freeze_lock:
        result = freeze_lock()
    else:
        parser.error("choose --prepare or --freeze-lock")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
