# G5 pre-implementation audit: contracts, failure modes and bounded rollout

**Status:** REVIEW DRAFT — code inspection / specification only. **Not a statement that G5 has been implemented.**  
**Snapshot date:** 2026-10-23  
**Baseline:** `main` at `ab1481147c33388b8a952d0b71d4e821eaecc80e`; G3 unmerged `feat/private-demo-runtime` at `d86f09224bca7449aaaa8a6bf1110d6ce793dbe3` (PR #25).  
**Related:** [ADR-001](adr/0001-evidence-grounded-order-extraction.md), [acceptance plan](GROUNDED_EXTRACTION_ACCEPTANCE.md), [G5 issue #26](https://github.com/forgeblueai/ai-order-processing-agent/issues/26), [benchmark issue #23](https://github.com/forgeblueai/ai-order-processing-agent/issues/23).

## Audited contract map (on G3 head unless otherwise noted)

| Module | Observed behavior | Required change / gate |
| --- | --- | --- |
| `app/ai/evidence_first.py` | Fully bounded English `quantity SKU` grammar, duplicate and extra-clause abstention, direct Ollama fallback | G5-A: preserve strict grammar, emit verified offsets for each quantity/SKU and route provenance, keep unsupported text out of automatic readiness |
| `app/ai/provider.py` | Calls Ollama for `ExtractionResult` then `require_source_evidence` | G5-A: separate model proposal from evidence-verification decision; never accept self-reported spans without independent source comparison |
| `app/ai/source_evidence.py` | Case-insensitive literal SKU presence and quantity within a 32-character window; checks explicit SKU coverage | G5-A: **proximity is not semantic binding**; reject negation, hypothetical/quoted cases, cross-item quantity links, stale evidence and partial source coverage before any auto-ready state |
| `app/schemas/extraction.py` | `ExtractedItem` has reference, description, nullable quantity and confidence; no source span | G5-A: internal candidate/span types; avoid breaking frozen model-only benchmark or changing model output schema prematurely |
| `app/services/order_service.py` | Looks up `inventory_service.get_product`, produces server-owned price/stock/subtotal/issues and `READY_FOR_APPROVAL` only when no issue | G5-B: canonical resolver contract. G5-C: shared server-side revalidation for **every** corrected revision, not simply cached item replacement |
| `app/services/inventory_service.py` | In-memory three-product demo catalog with float prices and stock | G5-B: versioned catalog identity/alias provider, deterministic Top-3 suggestions. For production-grade amounts migrate to Decimal/minor currency units in a separate reviewed gate |
| `app/domain/order.py`, `app/schemas/order.py` | Immutable dataclass + Pydantic response; fields include status, items, issues, subtotal, original source; no revision/correction audit | G5-C: immutable original, monotonic revision and separate immutable correction-event history; explicit issue state and author |
| `app/ports/order_repository.py` | `save/get/list` only | G5-C: transactional compare-and-swap save and append-audit, with explicit atomic Unit of Work; do not assume `save` alone protects concurrency |
| `app/adapters/sqlalchemy_order_repository.py` | `save` reads and writes then commits; JSON items/issues, float subtotal, no version or CAS | G5-C: Alembic-backed revision constraint, unique audit/idempotency keys and same-transaction correction+event; concurrency tested on real PostgreSQL |
| `app/services/order_application_service.py` | Rejects `REVIEWED -> READY_FOR_APPROVAL` if persisted issues remain | G5-C: correction must rebuild issues and subtotal from authoritative service; no direct issue-clear API |
| `app/services/order_lifecycle.py` | Allowed transitions are explicit; correction is not an existing transition | G5-C: define allowed correction statuses, no mutation after approval or terminal states |
| `app/api/security.py`, `app/api/orders.py` | Hashed bearer tokens, server roles, route guards; no individual-principal identity contract and no correction endpoint | G5-C: reviewer-only correction, separate approver, actor attribution with explicit identity limits; no multitenant claims |
| `benchmarks/runner.py` | Provider exceptions record schema invalid and `continue` without review/exception confusion entries | Benchmark v2: count provider failures in denominator and score observed fail-closed behavior, leaving frozen v1 untouched |

**Readiness gap:** `app/ai/source_evidence.py` currently confirms nearby numeric tokens, **not** whether the sentence actually orders the product. Example: a fabricated high-confidence proposal for `Do not send 2 F-200.` could pass literal proximity and lead to server-side pricing/auto-ready if no separate semantic blocker fires. This is a **code-path risk identified by inspection**, not a claimed observed exploit of the real Qwen model. Add a deterministic adversarial fixture proving fail-closed behavior before promoting G5-A.

## Minimal proposed internal data contracts — not live schemas

```python
SourceSpan = {
    "source_field": "subject|body",
    "start": "int (inclusive, original Python Unicode code-point index)",
    "end": "int (exclusive, original Python Unicode code-point index)",
}
GroundedCandidateLine = {
    "proposed_reference": "str|None",
    "proposed_quantity": "int|None",
    "reference_span": "SourceSpan|None",
    "quantity_span": "SourceSpan|None",
    "extraction_method": "deterministic|llm",
    "evidence_issues": "list[reason_code]",
}
CatalogSuggestion = {
    "canonical_sku": "str",
    "catalog_version": "str",
    "match_type": "exact|approved_alias|fuzzy_suggestion",
    "rank": "int|None",
}
```

Do not let caller-provided `extraction_method`, confidence, numeric offsets, `catalog_version` or `resolver_status` grant authority. The server determines the route, checks spans on **the original source field**, and computes a stable, unambiguous source fingerprint (for example, SHA-256 over a documented length-delimited subject/body encoding). Only a byte-for-byte or code-point-exact source match with verified *quantity-to-SKU association* is valid evidence. For UI display, convert Python code-point offsets to JavaScript UTF-16 offsets explicitly when necessary.

### Resolution algorithm — implementation obligations

1. Normalize SKU only with a documented conservative rule (e.g. trim outer whitespace, ASCII case folding); exact active canonical SKU may bind.
2. Resolve through an approved, versioned alias map **only if one alias maps to exactly one active SKU and current policy allows it**; alias collision/expiry abstains.
3. For other names, generate at most three deterministic ranked **suggestions** (stable tie-break by canonical SKU), never binding the top scorer automatically.
4. Reject unknown/inactive records and duplicate/contradictory quantities into review. No SKU from customer message or LLM may insert/update catalog data.
5. Retrieve price, inventory, policy and catalog snapshot/version from trusted backend after canonical identity is established. Re-check before approval; no implicit stock reservation.

A small standard-library string similarity routine may be sufficient for a demo-sized catalog. Benchmark latency and ranking quality before adding a third-party fuzzy-search dependency.

### Correction API proposal (requires separate G5-C review)

`PATCH /api/v1/orders/{order_id}/correction`, reviewer only:

```json
{
  "expected_revision": 2,
  "idempotency_key": "client-generated-opaque-request-id",
  "reason": "Corrected requested quantity after reading original order",
  "items": [
    {"sku": "F-200", "quantity": 2}
  ]
}
```

No `unit_price`, `subtotal`, `stock`, `issues`, `status`, `approved`, `actor_role` or `sent_at` fields are writable; reject unknown fields. The server reads reviewer identity from trusted auth, validates the state and `expected_revision`, resolves each canonical SKU, recalculates quantity/stock/price/issues, and atomically appends an audit event with old/new canonical values, reason, timestamp, source fingerprint, catalog version and principal-identity scope.

Transaction order: lock or conditional-update the current order version; detect stale revision (409); validate request/revalidation; insert immutable event; update order+revision; store idempotency response digest; commit once. If any step fails, all writes roll back. Repeated key+same request returns the stored result with no new event; repeated key+different payload conflicts. Distinct concurrent requests with the same revision cannot both succeed. `REQUIRES_REVIEW` and `REVIEWED` are the only eligible pre-approval correction states, to be decided in G5-C; correction is **never approval**. Static demo bearer role keys can identify the credential, not a named human: no individual-attribution claim without explicit principal binding.

## Independent benchmark v2 implementation plan

Create **new** `benchmarks/v2/` corpus, labels, scorer and report schema. Do not edit `benchmarks/corpus.json`, `benchmarks/runner.py`, its baseline, or its historical Qwen-only headline. Initially target 200 unique synthetic cases with 120 grouped development and 80 locked holdout samples (group near-duplicate templates and semantic siblings into the same split). Include true newlines, mixed languages, missing quantity, negation, quotation, stock shortage, unknown/ambiguous catalog names, contradictory lines, prompt injection, malformed provider results and timeouts.

Run the same v2 cases through: (1) model-only baseline, (2) strict G3 hybrid, (3) G5 grounded hybrid; later separately measure human correction with real authorized operator actions. Record every case including provider errors, with `route`, `schema_valid`, `provider_error`, `expected_review`, `actual_review`, `auto_ready`, `exact_order`, `sku_coverage`, `quantity_binding`, `span_validity`, `catalog_resolution_type`, `latency_ms`. Count a provider failure as an incorrect extraction and **a fail-closed review** if the actual service routes it there, rather than omitting its TP/FN/FP/TN effects. Report both raw counts and rates; denominator must always equal unique expected cases for appropriate metrics.

Required integrity gates: unique IDs and normalized inputs; independent split and templates; exact complete result cardinality; true multiline test; fixed seed and versioned ground truth; artifact hash; explicit error categories; no vanished failed cases; safety-critical auto-ready FN=0 on the frozen negative gate fixtures; report p50/p95 and model/provider/version; keep any human labels separate from model guesses. Zero observed unsafe cases in synthetic data is not proof of production safety.

## Gate discipline

- **G3 / PR #25:** still needs genuine owner-operated approval/draft/simulated confirmation and final-head acceptance; never merge without owner authorization.
- **ADR / PR #27:** documentation only. Draft review; no code or feature effectiveness claim.
- **G5-A:** implement source spans + verifier and negative semantic counterexamples on an independent PR after approving ADR and resolving G3 dependency.
- **G5-B:** exact/alias/fuzzy read-only catalog resolver.
- **G5-C:** revisioned human correction and real PostgreSQL transaction/concurrency tests.
- **G5-D:** independently scored hybrid study, no benchmark conflation.

No release, public deployment, external email delivery, or automatic merge is authorized by this audit.
