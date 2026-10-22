"""Integrity-gate tests independent of the frozen benchmark scorer."""
from copy import deepcopy

from benchmarks.check_report_integrity import validate_report


CORPUS = [
    {"id": "needs_review", "expected": {"requires_review": True}},
    {"id": "safe", "expected": {"requires_review": False}},
]


def sample_report():
    return {
        "sample_count": 2,
        "schema_valid_count": 2,
        "review_tp": 1,
        "review_fp": 0,
        "review_fn": 0,
        "review_tn": 1,
        "case_results": [
            {
                "id": "needs_review", "schema_valid": True,
                "expected_review": True, "actual_review": True,
            },
            {
                "id": "safe", "schema_valid": True,
                "expected_review": False, "actual_review": False,
            },
        ],
    }


def test_complete_benchmark_safety_report_is_accepted(capsys):
    assert validate_report(sample_report(), CORPUS) == []
    assert "BENCHMARK SAFETY EVIDENCE PASS" in capsys.readouterr().out


def test_extractor_timeout_never_counts_as_complete_review_safety():
    report = sample_report()
    report["schema_valid_count"] = 1
    report["case_results"][0] = {
        "id": "needs_review", "schema_valid": False, "error_type": "ReadTimeout"
    }
    # Historical scorer can still report 0 review false negatives in this case.
    report["review_tp"] = 0
    assert report["review_fn"] == 0
    errors = validate_report(report, CORPUS)
    assert any("incomplete benchmark" in e and "ReadTimeout" in e for e in errors)


def test_missing_record_or_duplicate_id_blocks_gate():
    report = sample_report()
    report["case_results"].pop()
    assert any("case_results" in e for e in validate_report(report, CORPUS))

    report = sample_report()
    report["case_results"][1]["id"] = "needs_review"
    errors = validate_report(report, CORPUS)
    assert any("duplicate IDs" in e for e in errors)
    assert any("case IDs differ" in e for e in errors)


def test_unreported_review_false_negative_blocks_gate():
    report = sample_report()
    report["case_results"][0]["actual_review"] = False
    errors = validate_report(report, CORPUS)
    assert any("unsafe review false negative" in e for e in errors)
    assert any("review_fn" in e for e in errors)


def test_altered_ground_truth_and_confusion_counts_block_gate():
    report = sample_report()
    report["case_results"][0]["expected_review"] = False
    assert any("frozen corpus" in e for e in validate_report(report, CORPUS))

    report = sample_report()
    report["review_tn"] = 2
    assert any("review_tn" in e for e in validate_report(report, CORPUS))


def test_incomplete_quality_report_cannot_be_fixed_by_faking_valid_count():
    report = deepcopy(sample_report())
    report["case_results"][0] = {
        "id": "needs_review", "schema_valid": False, "error_type": "ReadTimeout"
    }
    assert any("incomplete benchmark" in e for e in validate_report(report, CORPUS))


def test_malformed_case_result_fails_closed_without_crashing():
    report = sample_report()
    report["case_results"][1] = "not-a-benchmark-object"
    messages = validate_report(report, CORPUS)
    assert any("malformed or duplicate IDs" in message for message in messages)
    assert any("case_index_1:malformed_record" in message for message in messages)


def test_non_object_report_and_malformed_corpus_are_rejected():
    assert validate_report([], CORPUS) == ["benchmark report must be a JSON object"]
    assert validate_report(sample_report(), ["invalid"]) == [
        "frozen benchmark corpus has malformed cases"
    ]
    malformed = [{"id": "case", "expected": {"requires_review": "yes"}}]
    assert validate_report(sample_report(), malformed) == [
        "frozen benchmark corpus has malformed cases"
    ]


def test_schema_flag_must_be_literal_true_not_truthy():
    report = sample_report()
    report["case_results"][0]["schema_valid"] = 1
    report["schema_valid_count"] = 1
    errors = validate_report(report, CORPUS)
    assert any("incomplete benchmark" in error for error in errors)
