from apparatus.custody import verify_imports


def test_all_imported_parent_files_are_byte_exact():
    receipt = verify_imports()
    assert receipt["all_byte_equivalent"] is True
    assert receipt["file_count"] == 23

