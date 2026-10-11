# Qwen3 0.6B baseline — Sprint 8.1

This is measured benchmark evidence, not a production claim.

- Source head: `806e1ae1ed856670014e71ad3dd61542490a5459`
- GitHub Actions run: `37504971188` (Real LLM Integration #9)
- Artifact: `qwen-benchmark-report` / ID `11432530955`
- Artifact digest: `sha256:df8cd7bbf75114ea45352b4e25383d45d736dd1c2c3267661cc965a593caf3e9`
- Model: `qwen3:0.6b` via Ollama
- Corpus: 85 deterministic synthetic cases
- Corpus/scorer are held fixed for the post-hardening comparison.

## Aggregate baseline

| Metric | Result |
| --- | ---: |
| Schema validity | 85/85 = 100.0% |
| Exact extraction | 54/85 = 63.5% |
| Product match | 80/95 = 84.2% |
| Exception precision | 26/(26+41) = 38.8% |
| Exception recall | 26/(26+24) = 52.0% |
| Exception F1 | 44.4% |
| Review precision | 35/(35+14) = 71.4% |
| Review recall | 35/(35+5) = 87.5% |
| Review F1 | 78.7% |
| Human review rate | 49/85 = 57.6% |
| Mean latency | 8751.6 ms |
| P50 latency | 8056.3 ms |
| P95 latency | 14181.1 ms |

## Cohorts

Exact extraction / review routing matches:
- easy: 13/15 / 13/15
- medium: 29/40 / 33/40
- hard: 12/30 / 20/30
- ambiguous_reference: 4/10 / 9/10
- clean_multi: 7/10 / 8/10
- clean_single: 13/15 / 13/15
- format_variant: 4/5 / 3/5
- insufficient_stock: 8/10 / 10/10
- missing_quantity: 3/10 / 6/10
- non_product_noise: 2/5 / 2/5
- prompt_injection: 5/10 / 5/10
- unknown_sku: 8/10 / 10/10

## Dominant failure modes

1. Item fragmentation: a single explicit product/quantity pair is sometimes split into separate items, e.g. `(null, 3)` plus `(PV-10, null)`.
2. Unsupported quantity invention: missing quantities are sometimes filled with values such as 1 or 50 instead of remaining null.
3. Ambiguous-reference invention: generic text such as “usual filters” can become `filters` or, in the safety-critical baseline case `ambiguous_reference_09`, an unsupported `F-200`.
4. Non-product/injection text can create extra items or false review exceptions.
5. Confidence calibration causes some false-positive reviews, but thresholds are intentionally not relaxed to improve benchmark scores.

The safety-critical baseline defect is review false negatives: 5/40 expected-review cases were routed without review. Hardening therefore prioritizes ambiguity and missing-fact preservation over automation rate.

No raw customer message bodies or provider error details are stored in this evidence file.
