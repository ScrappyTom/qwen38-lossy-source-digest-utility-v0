# Post-run apparatus note

The exact runtime/profile lock passed: Qwen3.8 27B AD IQ2_S, llama.cpp b10434,
25,088-token context, q8 KV, 66/66 GPU layers, reasoning off, seed 314159, and
the inherited sampler and response reserve. Two calls ran with zero retries.
The server stopped cleanly, the port closed, and GPU memory returned to the
pre-run level.

One inherited implementation assumption required correction before freeze.
The predecessor pressure reducer inferred action/result pairs from fixed message
parity. Appending a digest message would have shifted that parity and made the
reducer unsafe. The standalone apparatus instead identifies adjacent structural
assistant-action/user-result pairs. Focused tests proved that the digest message
cannot be selected as an exact result body and that the inherited pressure rule
still reconstructs deterministically.

During the measured run, pressure relief operated once. It demoted a previously
resident navigation-continuity direct-audit result, recovered 1,482 prompt
tokens, and allowed the new 5,299-byte source-navigation audit result to cross a
model decision boundary. This was expected treatment-environment behavior, not
a second semantic context mechanism.

Replay reconstructed both requests, parsed actions, and literal result messages
exactly. The run contains raw provider exchanges, exact requests/responses,
actions, results, projections, candidate custody, budget receipts, runtime
custody, and analysis. The result seal and final verification bind these files.

The actor never received an explicit check capability in the inherited schema.
Accordingly, zero checks is an apparatus qualification rather than evidence that
the model declined to verify.
