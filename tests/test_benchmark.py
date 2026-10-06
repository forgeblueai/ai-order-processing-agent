from pathlib import Path

from benchmarks.ground_truth_extractor import GroundTruthExtractor
from benchmarks.runner import load_corpus, run_benchmark


CORPUS = Path("benchmarks/corpus.json")


def test_benchmark_control_proves_metric_pipeline() -> None:
    corpus = load_corpus(CORPUS)
    report = run_benchmark(GroundTruthExtractor(corpus), corpus)

    assert report.sample_count == len(corpus)
    assert report.schema_validity == 1.0
    assert report.extraction_accuracy == 1.0
    assert report.product_match_accuracy == 1.0
    assert report.exception_detection_rate == 1.0
    assert report.human_review_count == 4
    assert report.human_review_rate == 0.5
    assert report.mean_processing_ms >= 0
    assert len(report.case_results) == len(corpus)
    assert {case["id"] for case in report.case_results} == {case["id"] for case in corpus}
