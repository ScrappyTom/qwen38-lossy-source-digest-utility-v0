from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "qwen38-lossy-source-digest-utility-v0"
BRANCH = "codex/qwen38-lossy-source-digest-utility-v0"

HISTORICAL_REPOSITORY = "ScrappyTom/qwen38-recurrent-context-reduction-horizon-v0"
HISTORICAL_COMMIT = "f52642ec85efdc8f7196515503a0312af7c38d78"
DIGEST_REPOSITORY = "ScrappyTom/qwen38-source-digest-actor-utility-v0"
DIGEST_COMMIT = "d9336f5681ecffb8d322802c01ebaf8bb480f750"
PROGRAM_REPOSITORY = "ScrappyTom/bounded-context-experimental-program"
PROGRAM_COMMIT = "b433e286f7c172831b34300775c27414266585e0"

SOURCE_COMMIT = "f8c93e5ad33c8dd235c418df6561ba022d9077fb"
CONTEXT_TOKENS = 25_088
RESPONSE_RESERVE = 4_096
MAXIMUM_PROMPT_TOKENS = CONTEXT_TOKENS - RESPONSE_RESERVE
MAXIMUM_MEASURED_CALLS = 3
SEED = 314159
CELL = "s314159-s1"
CELLS = {CELL: {"seed": SEED}}

TARGET = "QWEN_RELATION_ACTION_WORKING_MODEL.md"
TARGET_SHA256 = "899a37f188de42075d5559bcaf6ba4bea96713ba192517021dbcc533c9844387"
TARGET_CANDIDATE_ID = "19296f821cc2bf7e32384ec88080ba49aedc4afe1f1f9961c31d57c2e1dc24fd"

DIGESTED_SOURCE = (
    "experiments/large-world-source-navigation-v0/runs/"
    "2026-08-18-sealed-bank-v0/RESULTS.md"
)

SOURCE_FILES = {
    DIGESTED_SOURCE: {
        "path": "parent_evidence/source/source-navigation-RESULTS.md",
        "sha256": "941d1cc9910e5227c158df6d88e704ab9e5e2cea654910bc5e6b6e7dd05176f7",
        "git_blob_sha": "0f2f2216c4b3d9a0e9d8329c11598e0842d57271",
    },
    "experiments/large-world-source-navigation-v0/runs/2026-08-18-sealed-bank-v0/DIRECT_TRANSCRIPT_AUDIT.md": {
        "path": "parent_evidence/source/source-navigation-DIRECT_TRANSCRIPT_AUDIT.md",
        "sha256": "ad6370ab0c040356a2edcd29f496fef8379d626a5fcda01c9d89f4d9401847b1",
        "git_blob_sha": "417842c826e77d0436de1ca779f87e8672a62e45",
    },
    "experiments/large-world-navigation-continuity-v0/runs/2026-08-18-sealed-bank-v0/RESULTS.md": {
        "path": "parent_evidence/source/navigation-continuity-RESULTS.md",
        "sha256": "daaaf37d3b6e38fb64df7c7a1f6e7d61b9c445f327613b376633fa0a3ce2ea0f",
        "git_blob_sha": "87105a0217f459a20649298d441173954354b743",
    },
    "experiments/large-world-navigation-continuity-v0/runs/2026-08-18-sealed-bank-v0/DIRECT_TRANSCRIPT_AUDIT.md": {
        "path": "parent_evidence/source/navigation-continuity-DIRECT_TRANSCRIPT_AUDIT.md",
        "sha256": "8e199102bd556ef2e76d20e9bb91de7c872025e9c762e0a5145904f79ddbcee6",
        "git_blob_sha": "abd6c275fe6673037ce1893774263bc7ec83c7cd",
    },
}
SOURCE_PATHS = tuple(SOURCE_FILES)

EXPECTED_SERVER_SHA256 = "5f1f831bc21dcbff4ca40e05cb59dbcbc0802d20b2046540bbbf3bd45cd61610"
EXPECTED_MODEL_SHA256 = "d416fa422c9035605c778f60d90a94b288c38b4f9ec2126b58ef938ce8d5f716"
EXPECTED_MODEL_SIZE = 11_141_912_032
MODEL_ALIAS = "qwen38-ad25q8-world-join"

INTEGRITY_REJECTION_CODES = {
    "source_surface_not_materialized",
    "exact_backing_mismatch",
    "unsupported_declared_action",
}
