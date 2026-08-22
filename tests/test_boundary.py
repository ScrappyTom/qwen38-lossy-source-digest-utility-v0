from apparatus.constants import DIGESTED_SOURCE
from apparatus.runner import same_source_access_class


def test_same_source_access_taxonomy():
    assert same_source_access_class({"action": "repo_read", "path": DIGESTED_SOURCE}) == "exact_historical_whole_source_reopen"
    assert same_source_access_class({"action": "repo_read_lines", "path": DIGESTED_SOURCE, "start_line": 1, "end_line": 10}) == "narrower_same_source_precision_access"
    assert same_source_access_class({"action": "repo_read", "path": "other.md"}) is None

