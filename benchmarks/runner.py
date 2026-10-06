from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from time import perf_counter

from app.ai.extractor import OrderExtractor
from app.schemas.order import OrderProcessRequest
from app.services.order_service import process_order


@dataclass(frozen=True)
class BenchmarkReport:
    sample_count: int
    schema_valid_count: int
    extraction_exact_count: int
    product_match_count: int
    product_expected_count: int
    exception_tp: int
    exception_fp: int
    exception_fn: int
    review_tp: int
    review_fp: int
    review_fn: int
    review_tn: int
    schema_validity: float
    extraction_accuracy: float
    product_match_accuracy: float
    exception_precision: float
    exception_recall: float
    exception_f1: float
    human_review_rate: float
    review_precision: float
    review_recall: float
    review_f1: float
    mean_processing_ms: float
    p50_processing_ms: float
    p95_processing_ms: float
    category_summary: dict[str, dict]
    difficulty_summary: dict[str, dict]
    case_results: list[dict]


def load_corpus(path: Path) -> list[dict]:
    corpus = json.loads(path.read_text())
    ids = [case["id"] for case in corpus]
    if len(ids) != len(set(ids)):
        raise ValueError("benchmark case ids must be unique")
    for case in corpus:
        if not case.get("category") or case.get("difficulty") not in {"easy", "medium", "hard"}:
            raise ValueError(f"benchmark case {case['id']} requires category and easy/medium/hard difficulty")
    return corpus


def _ratio(numerator: int, denominator: int, *, empty: float = 1.0) -> float:
    return numerator / denominator if denominator else empty


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _multiset_product_hits(actual: list[str | None], expected: list[str | None]) -> int:
    return sum((Counter(actual) & Counter(expected)).values())


def run_benchmark(extractor: OrderExtractor, corpus: list[dict]) -> BenchmarkReport:
    schema_ok = exact_ok = product_hits = product_total = 0
    exception_tp = exception_fp = exception_fn = 0
    review_tp = review_fp = review_fn = review_tn = reviews = 0
    latencies: list[float] = []
    case_results: list[dict] = []

    for case in corpus:
        payload = OrderProcessRequest(subject=case["subject"], body=case["body"])
        expected = case["expected"]
        started = perf_counter()
        try:
            extraction = extractor.extract(payload)
        except Exception as exc:
            elapsed = (perf_counter() - started) * 1000
            latencies.append(elapsed)
            case_results.append({
                "id": case["id"], "category": case["category"], "difficulty": case["difficulty"],
                "schema_valid": False, "error_type": type(exc).__name__, "processing_ms": elapsed,
            })
            continue

        schema_ok += 1
        result = process_order(payload, extractor=_FixedExtractor(extraction))
        elapsed = (perf_counter() - started) * 1000
        latencies.append(elapsed)

        actual_pairs = [(item.product_reference, item.quantity) for item in extraction.items]
        expected_pairs = [(item["sku"], item["quantity"]) for item in expected["items"]]
        exact_ok += int(Counter(actual_pairs) == Counter(expected_pairs))

        actual_skus = [sku for sku, _ in actual_pairs]
        expected_skus = [sku for sku, _ in expected_pairs]
        product_total += len(expected_skus)
        product_hits += _multiset_product_hits(actual_skus, expected_skus)

        expected_exceptions = set(expected["exception_types"])
        actual_exceptions = {issue.type for issue in result.issues}
        exception_tp += len(expected_exceptions & actual_exceptions)
        exception_fp += len(actual_exceptions - expected_exceptions)
        exception_fn += len(expected_exceptions - actual_exceptions)

        expected_review = bool(expected["requires_review"])
        actual_review = result.status.value == "requires_review"
        reviews += int(actual_review)
        review_tp += int(expected_review and actual_review)
        review_fp += int(not expected_review and actual_review)
        review_fn += int(expected_review and not actual_review)
        review_tn += int(not expected_review and not actual_review)

        case_results.append({
            "id": case["id"], "category": case["category"], "difficulty": case["difficulty"],
            "schema_valid": True, "expected_items": expected_pairs, "actual_items": actual_pairs,
            "expected_exceptions": sorted(expected_exceptions), "actual_exceptions": sorted(actual_exceptions),
            "expected_review": expected_review, "actual_review": actual_review, "processing_ms": elapsed,
        })

    n = len(corpus)
    exception_precision = _ratio(exception_tp, exception_tp + exception_fp)
    exception_recall = _ratio(exception_tp, exception_tp + exception_fn)
    review_precision = _ratio(review_tp, review_tp + review_fp)
    review_recall = _ratio(review_tp, review_tp + review_fn)

    def summarize(key: str) -> dict[str, dict]:
        values = sorted({case[key] for case in corpus})
        summary = {}
        by_id = {case["id"]: case for case in case_results}
        for value in values:
            ids = [case["id"] for case in corpus if case[key] == value]
            completed = [by_id[i] for i in ids if i in by_id]
            summary[value] = {
                "samples": len(ids),
                "schema_valid": sum(int(case.get("schema_valid", False)) for case in completed),
                "exact_extractions": sum(int(Counter(map(tuple, case.get("actual_items", []))) == Counter(map(tuple, case.get("expected_items", [])))) for case in completed if case.get("schema_valid")),
                "review_matches": sum(int(case.get("actual_review") == case.get("expected_review")) for case in completed if case.get("schema_valid")),
            }
        return summary

    return BenchmarkReport(
        sample_count=n, schema_valid_count=schema_ok, extraction_exact_count=exact_ok,
        product_match_count=product_hits, product_expected_count=product_total,
        exception_tp=exception_tp, exception_fp=exception_fp, exception_fn=exception_fn,
        review_tp=review_tp, review_fp=review_fp, review_fn=review_fn, review_tn=review_tn,
        schema_validity=_ratio(schema_ok, n, empty=0.0),
        extraction_accuracy=_ratio(exact_ok, n, empty=0.0),
        product_match_accuracy=_ratio(product_hits, product_total),
        exception_precision=exception_precision, exception_recall=exception_recall,
        exception_f1=_f1(exception_precision, exception_recall),
        human_review_rate=_ratio(reviews, n, empty=0.0),
        review_precision=review_precision, review_recall=review_recall,
        review_f1=_f1(review_precision, review_recall),
        mean_processing_ms=mean(latencies) if latencies else 0.0,
        p50_processing_ms=median(latencies) if latencies else 0.0,
        p95_processing_ms=_percentile(latencies, 0.95),
        category_summary=summarize("category"), difficulty_summary=summarize("difficulty"),
        case_results=case_results,
    )


class _FixedExtractor:
    def __init__(self, result) -> None:
        self._result = result

    def extract(self, payload: OrderProcessRequest):
        return self._result


def write_report(report: BenchmarkReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n")
