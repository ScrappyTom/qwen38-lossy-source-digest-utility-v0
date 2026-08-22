from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from apparatus.canonical import sha256_bytes, sha256_file
from apparatus.constants import DIGEST_COMMIT, HISTORICAL_COMMIT, PROGRAM_COMMIT, ROOT


DONORS = {
    "historical": {"repository": "ScrappyTom/qwen38-recurrent-context-reduction-horizon-v0", "local_path": Path(r"E:\qwen38-recurrent-context-reduction-horizon-v0"), "commit": HISTORICAL_COMMIT},
    "digest": {"repository": "ScrappyTom/qwen38-source-digest-actor-utility-v0", "local_path": Path(r"E:\qwen38-source-digest-actor-utility-v0"), "commit": DIGEST_COMMIT},
    "program": {"repository": "ScrappyTom/bounded-context-experimental-program", "local_path": Path(r"E:\bounded-context-experimental-program"), "commit": PROGRAM_COMMIT},
}


IMPORTS = [
    ("digest", "parent_evidence/boundary/after-call-11-budget.json", "parent_evidence/boundary/after-call-11-budget.json"),
    ("digest", "parent_evidence/boundary/after-call-11-projection.json", "parent_evidence/boundary/after-call-11-projection.json"),
    ("digest", "parent_evidence/boundary/call-09-action.json", "parent_evidence/boundary/call-09-action.json"),
    ("digest", "parent_evidence/boundary/call-12-action.json", "parent_evidence/boundary/call-12-action.json"),
    ("digest", "parent_evidence/boundary/call-12-request.json", "parent_evidence/boundary/call-12-request.json"),
    ("digest", "parent_evidence/boundary/call-12-response.json", "parent_evidence/boundary/call-12-response.json"),
    ("digest", "parent_evidence/boundary/candidate-initial.json", "parent_evidence/boundary/candidate-initial.json"),
    ("digest", "parent_evidence/boundary/candidate-terminal.json", "parent_evidence/boundary/candidate-terminal.json"),
    ("digest", "parent_evidence/run/RUN_RESULT.json", "parent_evidence/boundary/historical-RUN_RESULT.json"),
    ("digest", "parent_evidence/run/RESULTS.md", "parent_evidence/boundary/historical-RESULTS.md"),
    ("digest", "parent_evidence/run/DIRECT_TRANSCRIPT_AUDIT.md", "parent_evidence/boundary/historical-DIRECT_TRANSCRIPT_AUDIT.md"),
    ("digest", "parent_evidence/source/call-09-source-result.json", "parent_evidence/source/call-09-source-result.json"),
    ("digest", "runs/2026-08-21-sealed-source-digest-stage-a-s314159-v0/cells/01-digest-source-navigation-results-s314159/response/DIGEST_RECEIPT.json", "parent_evidence/digest/DIGEST_RECEIPT.json"),
    ("digest", "provenance/MODEL_PROFILE_LOCK.json", "parent_evidence/runtime/MODEL_PROFILE_LOCK.json"),
    ("digest", "parent_evidence/run/runtime-custody.json", "parent_evidence/runtime/runtime-custody.json"),
    ("historical", "runs/2026-08-20-sealed-horizon-run-v0/cells/02-s314159-s1-recurrent-oldest-fit-horizon-v0/world/candidate/QWEN_RELATION_ACTION_WORKING_MODEL.md", "parent_evidence/candidate/QWEN_RELATION_ACTION_WORKING_MODEL.md"),
    ("historical", "parent_evidence/predecessor_evidence/evidence/parent/s314159-s1/data/s314159-s1/inputs/action-schema.json", "parent_evidence/schema/action-schema.json"),
    ("historical", "parent_evidence/predecessor_evidence/evidence/parent/s314159-s1/data/s314159-s1/turns/turn-010/request.json", "parent_evidence/schema/historical-turn-010-request.json"),
    ("historical", "parent_evidence/predecessor_evidence/evidence/source/experiments/large-world-source-navigation-v0/runs/2026-08-18-sealed-bank-v0/RESULTS.md", "parent_evidence/source/source-navigation-RESULTS.md"),
    ("historical", "parent_evidence/predecessor_evidence/evidence/source/experiments/large-world-source-navigation-v0/runs/2026-08-18-sealed-bank-v0/DIRECT_TRANSCRIPT_AUDIT.md", "parent_evidence/source/source-navigation-DIRECT_TRANSCRIPT_AUDIT.md"),
    ("historical", "parent_evidence/predecessor_evidence/evidence/source/experiments/large-world-navigation-continuity-v0/runs/2026-08-18-sealed-bank-v0/RESULTS.md", "parent_evidence/source/navigation-continuity-RESULTS.md"),
    ("historical", "parent_evidence/predecessor_evidence/evidence/source/experiments/large-world-navigation-continuity-v0/runs/2026-08-18-sealed-bank-v0/DIRECT_TRANSCRIPT_AUDIT.md", "parent_evidence/source/navigation-continuity-DIRECT_TRANSCRIPT_AUDIT.md"),
    ("program", "NEXT_EXPERIMENT_S3_LOSSY_DIGEST_UTILITY.md", "QWEN38_LOSSY_SOURCE_DIGEST_UTILITY_HANDOFF.md"),
]


def git_object_bytes(repo: Path, commit: str, path: str) -> bytes:
    process = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise RuntimeError(f"cannot read donor object {commit}:{path}: {process.stderr.decode(errors='replace')}")
    return process.stdout


def verify_imports() -> dict[str, Any]:
    donor_rows = []
    for name, donor in DONORS.items():
        process = subprocess.run(["git", "-C", str(donor["local_path"]), "cat-file", "-t", donor["commit"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
        if process.returncode or process.stdout.strip() != "commit":
            raise RuntimeError(f"donor commit unavailable: {name}")
        donor_rows.append({"name": name, "repository": donor["repository"], "local_path": str(donor["local_path"]), "commit": donor["commit"], "commit_available": True})
    files = []
    for donor_name, original_path, copied_path in IMPORTS:
        donor = DONORS[donor_name]
        original = git_object_bytes(donor["local_path"], donor["commit"], original_path)
        copied = ROOT / copied_path
        if not copied.is_file():
            raise RuntimeError(f"copied parent evidence missing: {copied_path}")
        copied_bytes = copied.read_bytes()
        equal = original == copied_bytes
        files.append({
            "donor": donor_name, "donor_repository": donor["repository"], "donor_commit": donor["commit"],
            "original_path": original_path, "original_size_bytes": len(original), "original_sha256": sha256_bytes(original),
            "copied_path": copied_path, "copied_size_bytes": len(copied_bytes), "copied_sha256": sha256_file(copied),
            "byte_equivalent": equal,
        })
        if not equal:
            raise RuntimeError(f"parent materialization mismatch: {copied_path}")
    return {
        "schema_version": "lossy-source-digest-parent-materialization-v0",
        "donors": donor_rows, "file_count": len(files),
        "total_copied_bytes": sum(row["copied_size_bytes"] for row in files),
        "all_byte_equivalent": all(row["byte_equivalent"] for row in files), "files": files,
    }
