from __future__ import annotations

import copy
from typing import Any

from apparatus.canonical import compact_json, load_json, sha256_bytes
from apparatus.constants import DIGESTED_SOURCE, ROOT, SOURCE_COMMIT, SOURCE_FILES


SCHEMA = "source-bound-semantic-digest-residency-v0"


def digest_object() -> dict[str, Any]:
    receipt = load_json(ROOT / "parent_evidence" / "digest" / "DIGEST_RECEIPT.json")
    digest = receipt["digest"]
    digest_bytes = digest.encode("utf-8")
    source = SOURCE_FILES[DIGESTED_SOURCE]
    return {
        "schema_version": SCHEMA,
        "source_bound_semantic_digest": {
            "source_binding": {
                "path": DIGESTED_SOURCE,
                "source_commit": SOURCE_COMMIT,
                "git_blob_sha": source["git_blob_sha"],
                "source_content_sha256": source["sha256"],
                "source_size_bytes": (ROOT / source["path"]).stat().st_size,
            },
            "digest_binding": {
                "digest_sha256": sha256_bytes(digest_bytes),
                "digest_size_bytes": len(digest_bytes),
                "digest_token_count": receipt["digest_token_count"],
                "digest_token_ids_sha256": receipt["digest_token_ids_sha256"],
                "provider_response_sha256": receipt["provider_response_sha256"],
            },
            "lossy_non_authoritative": True,
            "exact_reopen_available": True,
            "exact_reopen_action": {"action": "repo_read", "path": DIGESTED_SOURCE},
            "digest": digest,
        },
    }


def digest_message() -> dict[str, str]:
    return {"role": "user", "content": compact_json(digest_object())}


def historical_request() -> dict[str, Any]:
    return load_json(ROOT / "parent_evidence" / "boundary" / "call-12-request.json")


def treated_request() -> dict[str, Any]:
    request = copy.deepcopy(historical_request())
    request["messages"].append(digest_message())
    return request


def treatment_delta() -> dict[str, Any]:
    control = historical_request()
    treatment = treated_request()
    return {
        "control_message_count": len(control["messages"]),
        "treatment_message_count": len(treatment["messages"]),
        "prefix_messages_byte_equal": treatment["messages"][:-1] == control["messages"],
        "added_message": treatment["messages"][-1],
        "added_message_sha256": sha256_bytes(treatment["messages"][-1]["content"].encode("utf-8")),
        "added_message_size_bytes": len(treatment["messages"][-1]["content"].encode("utf-8")),
        "non_message_request_fields_equal": {
            key: treatment[key] == control[key]
            for key in sorted(set(control) | set(treatment))
            if key != "messages"
        },
    }
