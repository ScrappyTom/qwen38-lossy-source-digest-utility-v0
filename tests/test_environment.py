from pathlib import Path

from apparatus.constants import DIGESTED_SOURCE, TARGET_CANDIDATE_ID
from apparatus.environment import make_environment


def test_exact_source_reopen_and_candidate_identity(tmp_path: Path):
    environment = make_environment("s314159-s1", tmp_path)
    assert environment.initial_snapshot["candidate_id"] == TARGET_CANDIDATE_ID
    result = environment.execute({"action": "repo_read", "path": DIGESTED_SOURCE})
    assert result["accepted"] is True
    assert result["size_bytes"] == 8063
    assert result["blob_sha"] == "0f2f2216c4b3d9a0e9d8329c11598e0842d57271"
    assert environment.snapshot()["candidate_id"] == TARGET_CANDIDATE_ID


def test_read_mutation_and_submission_probes(tmp_path: Path):
    environment = make_environment("s314159-s1", tmp_path)
    read = environment.execute({"action": "read_region", "region_id": "R033"})
    assert read["accepted"] is True
    assert read["sha256"] == "eb65724f2ab012d5b739472ebad28a4c79fdcf3cc658913854340bc27f07d4bd"
    path = environment.candidate_root / "QWEN_RELATION_ACTION_WORKING_MODEL.md"
    old = path.read_text(encoding="utf-8").splitlines()[0]
    patch = environment.execute({"action": "patch", "path": path.name, "old": old, "new": old + " ", "expected_file_sha256": read["file_sha256"]})
    assert patch["accepted"] is True
    assert environment.execute({"action": "submit"})["accepted"] is True

