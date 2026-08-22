import copy

from apparatus.receipts import pair_indices, pressure_projection
from apparatus.treatment import treated_request


def test_added_digest_message_is_not_misparsed_as_action_result():
    messages = treated_request()["messages"]
    pairs = pair_indices(messages)
    assert pairs
    assert all(messages[a]["role"] == "assistant" and messages[r]["role"] == "user" for a, r in pairs)
    assert len(messages) - 1 not in {index for pair in pairs for index in pair}


def test_pressure_projection_accepts_tail_after_digest_message():
    messages = copy.deepcopy(treated_request()["messages"])
    tail = [
        {"role": "assistant", "content": '{"action":"tree","path":"."}'},
        {"role": "user", "content": '{"action":"tree","action_id":"schema-action-026","result":{"accepted":true}}'},
    ]
    projection = pressure_projection("s314159-s1", messages, tail, maximum_prompt_tokens=10**9, token_count=lambda rows: len(rows))
    assert projection.fits is True
    assert projection.messages[-2:] == tail

