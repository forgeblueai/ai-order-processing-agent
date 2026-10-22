"""Fail-closed CI *integrity* check for an unchanged frozen-v1 Qwen report.

This checker does NOT modify the benchmark corpus, scorer or confidence
threshold. It rejects incomplete run evidence that the historical scorer
can otherwise summarize as high review recall despite skipped exceptions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def validate_report(report: dict, corpus: list[dict]) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["benchmark report must be a JSON object"]
    if not isinstance(corpus, list) or any(
        not isinstance(case, dict)
        or not isinstance(case.get("id"), str)
        or not isinstance(case.get("expected"), dict)
        or not isinstance(case["expected"].get("requires_review"), bool)
        for case in corpus
    ):
        return ["frozen benchmark corpus has malformed cases"]
    expected_by_id = {case["id"]: case for case in corpus}
    expected_ids = set(expected_by_id)
    if len(expected_by_id) != len(corpus):
        errors.append("benchmark corpus has duplicate case IDs")

    sample_count = report.get("sample_count")
    if sample_count != len(corpus):
        errors.append(f"sample_count={sample_count!r}; corpus has {len(corpus)} cases")

    cases = report.get("case_results")
    if not isinstance(cases, list):
        return errors + ["case_results must be a list"]

    actual_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(cases) != len(corpus):
        errors.append(f"case_results has {len(cases)} records, expected {len(corpus)}")
    if len(actual_ids) != len(cases) or len(set(actual_ids)) != len(actual_ids):
        errors.append("case_results has malformed or duplicate IDs")
    if set(actual_ids) != expected_ids:
        errors.append("case IDs differ from the frozen corpus")

    # A malformed JSON record is *failed evidence*, never an uncaught crash.
    invalid = [
        (
            f"{case.get('id', 'unknown')}:{case.get('error_type', 'invalid_schema')}"
            if isinstance(case, dict)
            else f"case_index_{i}:malformed_record"
        )
        for i, case in enumerate(cases)
        if not isinstance(case, dict) or case.get("schema_valid") is not True
    ]
    reported_valid = report.get("schema_valid_count")
    observed_valid = len(cases) - len(invalid)
    if reported_valid != observed_valid:
        errors.append(
            f"schema_valid_count={reported_valid!r} disagrees with actual {observed_valid}"
        )
    if invalid or observed_valid != len(corpus):
        errors.append(
            "incomplete benchmark: every frozen-v1 case must be schema-valid; failures: "
            + (", ".join(invalid) if invalid else "count mismatch")
        )

    # Reconcile review evidence against ground truth only for completed cases.
    # The historical v1 scorer omits failed-extraction cases from confusion counts.
    tp = fp = fn = tn = 0
    for case in cases:
        if not isinstance(case, dict) or case.get("schema_valid") is not True:
            continue
        case_id = case["id"]
        expected = expected_by_id.get(case_id)
        if expected is None:
            continue
        expected_review = expected["expected"]["requires_review"]
        actual_review = case.get("actual_review")
        if not isinstance(expected_review, bool) or not isinstance(actual_review, bool):
            errors.append(f"{case_id}: missing/invalid expected_review or actual_review")
            continue
        if case.get("expected_review") is not expected_review:
            errors.append(f"{case_id}: reported expected_review differs from frozen corpus")
        if expected_review:
            if actual_review:
                tp += 1
            else:
                fn += 1
                errors.append(f"{case_id}: unsafe review false negative")
        elif actual_review:
            fp += 1
        else:
            tn += 1

    for key, count in (
        ("review_tp", tp), ("review_fp", fp), ("review_fn", fn), ("review_tn", tn)
    ):
        if report.get(key) != count:
            errors.append(f"{key}={report.get(key)!r}, but case evidence totals {count}")

    if errors:
        return errors

    print(
        f"BENCHMARK SAFETY EVIDENCE PASS: {len(corpus)} complete cases; "
        f"review FN=0, TP={tp}, FP={fp}, TN={tn}. "
        "Quality/latency still require independent review."
    )
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("benchmark-results/qwen-report.json"))
    parser.add_argument("--corpus", type=Path, default=Path("benchmarks/corpus.json"))
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
        errors = validate_report(report, corpus)
    except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
        print(f"BENCHMARK SAFETY EVIDENCE BLOCKED: {type(exc).__name__}", file=sys.stderr)
        return 1
    if errors:
        for message in errors:
            print(f"BENCHMARK SAFETY EVIDENCE BLOCKED: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
