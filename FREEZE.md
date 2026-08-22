# Freeze — lossy source-digest utility v0

Date: 2026-08-21

Status: implementation and offline preflight freeze; measured GPU execution
authorized by the user in the active Codex task.

## Question

At seed 314159 horizon call 12, does adding the sealed 218-token, source-bound,
lossy digest change short-horizon information demand or useful work while exact
reopening remains available?

## Boundary

- Historical donor: `ScrappyTom/qwen38-recurrent-context-reduction-horizon-v0`
  at `f52642ec85efdc8f7196515503a0312af7c38d78`.
- Seed: 314159.
- Source first read: call 9.
- Exact repeat reopen: call 12.
- Candidate unchanged.
- Historical packet: 19,686 prompt tokens with 1,306 tokens beyond the frozen
  4,096 response reserve.

## Treatment

Preserve the historical request exactly and append one canonical user message
containing the frozen digest and mechanical bindings. Do not add the two known
omissions, semantic advice, readiness claims, progress state, or any other
context operation.

The added message is an explicitly lossy cache, not authoritative source truth.
The exact source remains externally custodied and accessible through the same
`repo_read` action.

## Outcomes

Primary: exact historical whole-source reopen, narrower same-source access,
other same-source access, or a different valid action.

Utility requires useful progress, meaningful raw-demand deferral, or selective
recovery that improves downstream action/quality. A different duplicate read is
not a lead. Exact recovery is not inherently a failure.

## Horizon and stop

- Maximum actor calls: 3.
- One attempt; zero retries.
- Immediate same-source access stops after the requested action/result is
  custodied; no additional model call is made.
- Otherwise execute and deliver under the inherited minimum-necessary pressure
  rule, stopping at same-source access, submission, call limit, capacity/control
  failure, or apparatus/model integrity failure.

## Claim limit

The digest and boundary were selected from known histories. This is a
hypothesis-generating local intervention, not an independent effect-frequency
estimate, transfer, or architecture promotion. Historical cache and latency are
descriptive rather than a contemporaneous causal control.

