from apparatus.constants import DIGESTED_SOURCE
from apparatus.treatment import digest_object, historical_request, treated_request, treatment_delta


def test_treatment_adds_exactly_one_message_and_preserves_prefix():
    control = historical_request()
    treatment = treated_request()
    assert treatment["messages"][:-1] == control["messages"]
    assert len(treatment["messages"]) == len(control["messages"]) + 1
    assert treatment_delta()["prefix_messages_byte_equal"] is True
    assert all(treatment[key] == control[key] for key in control if key != "messages")


def test_digest_is_lossy_non_authoritative_and_reopenable():
    value = digest_object()["source_bound_semantic_digest"]
    assert value["lossy_non_authoritative"] is True
    assert value["exact_reopen_available"] is True
    assert value["exact_reopen_action"] == {"action": "repo_read", "path": DIGESTED_SOURCE}
    assert value["digest_binding"]["digest_token_count"] == 218

