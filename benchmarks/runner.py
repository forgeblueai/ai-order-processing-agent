from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
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
    exception_hit_count: int
    exception_expected_count: int
    human_review_count: int
    schema_validity: float
    extraction_accuracy: float
    product_match_accuracy: float
    exception_detection_rate: float
    human_review_rate: float
    mean_processing_ms: float


def load_corpus(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def run_benchmark(extractor: OrderExtractor, corpus: list[dict]) -> BenchmarkReport:
    schema_ok = exact_ok = product_hits = product_total = exception_hits = exception_total = reviews = 0
    latencies: list[float] = []

    for case in corpus:
        payload = OrderProcessRequest(subject=case["subject"], body=case["body"])
        expected = case["expected"]
        started = perf_counter()
        try:
            extraction = extractor.extract(payload)
        except Exception:
            latencies.append((perf_counter() - started) * 1000)
            continue

        schema_ok += 1
        result = process_order(payload, extractor=_FixedExtractor(extraction))
        latencies.append((perf_counter() - started) * 1000)

        actual_pairs = [(item.product_reference, item.quantity) for item in extraction.items]
        expected_pairs = [(item["sku"], item["quantity"]) for item in expected["items"]]
        exact_ok += int(actual_pairs == expected_pairs)

        actual_skus = [sku for sku, _ in actual_pairs]
        expected_skus = [sku for sku, _ in expected_pairs]
        product_total += len(expected_skus)
        product_hits += sum(1 for index, sku in enumerate(expected_skus) if index < len(actual_skus) and actual_skus[index] == sku)

        expected_exceptions = set(expected["exception_types"])
        actual_exceptions = {issue.type for issue in result.issues}
        exception_total += len(expected_exceptions)
        exception_hits += len(expected_exceptions & actual_exceptions)
        reviews += int(result.status.value == "requires_review")

    n = len(corpus)
    return BenchmarkReport(
        sample_count=n,
        schema_valid_count=schema_ok,
        extraction_exact_count=exact_ok,
        product_match_count=product_hits,
        product_expected_count=product_total,
        exception_hit_count=exception_hits,
        exception_expected_count=exception_total,
        human_review_count=reviews,
        schema_validity=schema_ok / n if n else 0.0,
        extraction_accuracy=exact_ok / n if n else 0.0,
        product_match_accuracy=product_hits / product_total if product_total else 1.0,
        exception_detection_rate=exception_hits / exception_total if exception_total else 1.0,
        human_review_rate=reviews / n if n else 0.0,
        mean_processing_ms=mean(latencies) if latencies else 0.0,
    )


class _FixedExtractor:
    def __init__(self, result) -> None:
        self._result = result

    def extract(self, payload: OrderProcessRequest):
        return self._result


def write_report(report: BenchmarkReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n")
