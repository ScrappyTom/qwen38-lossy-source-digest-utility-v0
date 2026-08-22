# Direct transcript audit

## Disposition

The digest altered the first decision but did not avoid exact recovery or
produce task progress. The measured endpoint is
`delayed_same_source_raw_access`.

## Fork packet

The treatment preserved all 52 messages in the exact historical seed-314159
call-12 request and appended one canonical digest message. That message carried:

- the sealed 218-token lossy digest;
- exact source path, commit, blob, content hash, and size;
- explicit non-authoritative/lossy status; and
- the unchanged exact `repo_read` reopen action.

The historical packet was 19,686 prompt tokens. The treated packet was 20,406,
an increment of 720 tokens, leaving 586 tokens beyond the frozen 4,096-token
response reserve.

## Call 1

Raw assistant output:

```json
{"action":"repo_read","path":"experiments/large-world-source-navigation-v0/runs/2026-08-18-sealed-bank-v0/DIRECT_TRANSCRIPT_AUDIT.md"}
```

The action was valid, admitted, an exact receipt-backed reopen, and a duplicate
on the unchanged-candidate basis. It differed from the historical call-12
action by selecting the paired direct audit rather than `RESULTS.md`.

The literal result contained 5,299 exact source bytes. The unreduced next packet
would have been 22,026 prompt tokens, 1,034 over the usable prompt ceiling. The
frozen pressure rule demoted one older exact result body, recovered 1,482
tokens, and delivered the audit to call 2 at 20,544 prompt tokens with 448
tokens of headroom.

## Call 2

Raw assistant output:

```json
{"action":"repo_read","path":"experiments/large-world-source-navigation-v0/runs/2026-08-18-sealed-bank-v0/RESULTS.md"}
```

This is byte-for-byte the action in the historical call-12 response. It was a
valid whole-source exact reopen of the 8,063-byte source represented by the
digest. The result was custodied but, under the frozen stop rule, was not
delivered to another model invocation.

## Action and artifact audit

- Both calls were acquisition actions.
- Both were duplicate exact recoveries on an unchanged-candidate basis.
- Same-source raw access occurred on call 2.
- No mutation or submission occurred.
- No explicit check action existed in the inherited action schema.
- Candidate identity remained
  `19296f821cc2bf7e32384ec88080ba49aedc4afe1f1f9961c31d57c2e1dc24fd`.
- The actor emitted no reasoning prose; motive and semantic uptake cannot be
  inferred from the tool calls.

## Investigator interpretation

The digest appears to have affected what Qwen3.8 sought first, but the first
effect was another exact recovery from the same study. After receiving that
audit, it returned to the exact historical source request. This is not efficient
selective recovery in the measured horizon and is not artifact progress.

The result does not show whether the digest itself prompted a need to verify the
paired audit, whether the source study was simply already salient, or whether a
longer horizon would later reuse the resident semantic content. Those remain
unobserved rather than resolved.
