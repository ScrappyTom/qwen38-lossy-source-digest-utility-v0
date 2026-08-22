# Treatment delta

The control is the exact historical seed-314159 call-12 request.

The treatment changes one thing: it appends one user message containing the
sealed digest, exact source/version/digest bindings, explicit
`lossy_non_authoritative: true`, and the unchanged exact reopen action.

It does not:

- edit or remove any historical message;
- reveal the investigator-side known-loss record;
- add the omitted source-study candidate/check facts;
- change task, candidate, sources, tools, action schema, model, seed, sampler,
  reasoning, context size, or response reserve;
- force acquisition, mutation, check, or submission; or
- alter the inherited minimum-necessary pressure rule.

The machine-readable byte/token delta is frozen in `TREATMENT_DELTA.json` and
`DIGEST_RENDER_RECEIPT.json` after exact-token preflight.

