# Qwen3.8 lossy source-digest utility v0

This standalone experiment tests the marginal short-horizon utility of one
already-produced, known-lossy, source-bound semantic digest at an authentic
repeat-reopen boundary.

The exact historical seed-314159 call-12 packet is the behavioral baseline. It
contained a compact exact reopen receipt for an unchanged 8,063-byte source and
historically produced an exact whole-source reopen. The treatment preserves all
52 historical messages and appends one canonical message containing the sealed
218-token digest, exact source/version binding, explicit lossy/non-authoritative
status, and unchanged exact reopen action.

This is not a test of digest completeness, general summarization, or a context
manager. It is one selected within-trajectory intervention. Avoiding a reopen or
choosing a different valid read is not automatically beneficial.

Measured execution is limited to one attempt, zero retries, and at most three
actor calls. Exact model/runtime custody, capacity, response reserve, pressure
reduction, action grammar, and candidate/source bytes remain inherited.

The frozen contract is in
`QWEN38_LOSSY_SOURCE_DIGEST_UTILITY_HANDOFF.md` and `FREEZE.md`.

