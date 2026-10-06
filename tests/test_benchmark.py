from pathlib import Path

import pytest

from benchmarks.ground_truth_extractor import GroundTruthExtractor
from benchmarks.runner import load_corpus, run_benchmark


CORPUS = Path("benchmarks/corpus.json")


def test_benchmark_control_proves_metric_pipeline() -> None:
    corpus = load_corpus(CORPUS)
    report = run_benchmark(GroundTruthExtractor(corpus), corpus)

    assert report.sample_count == 85
    assert report.schema_validity == 1.0
    assert report.extraction_accuracy == 1.0
    assert report.product_match_accuracy == 1.0
    assert report.exception_precision == 1.0
    assert report.exception_recall == 1.0
    assert report.exception_f1 == 1.0
    assert report.review_precision == 1.0
    assert report.review_recall == 1.0
    assert report.review_f1 == 1.0
    assert report.review_fp == 0
    assert report.review_fn == 0
    assert report.p50_processing_ms >= 0
    assert report.p95_processing_ms >= report.p50_processing_ms
    assert len(report.case_results) == len(corpus)
    assert {case["id"] for case in report.case_results} == {case["id"] for case in corpus}
    assert set(report.difficulty_summary) == {"easy", "medium", "hard"}
    assert "prompt_injection" in report.category_summary


def test_corpus_ids_and_metadata_are_validated(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('[{"id":"x","subject":"s","body":"b","expected":{}},{"id":"x","subject":"s","body":"b","expected":{}}]')
    with pytest.raises(ValueError):
        load_corpus(bad)
