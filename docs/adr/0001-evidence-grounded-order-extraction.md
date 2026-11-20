# ADR-001: Evidence-grounded order extraction and human correction

- **Status:** PROPOSED — architecture only; **not implemented/approved**
- **Date:** 2026-10-23
- **Owners:** ForgeBlue AI / AI Order Processing Agent
- **Branch:** `docs/adr-001-grounded-order-correction` (independent, based on merged G2 main)
- **Dependencies:** private G3 runtime in [draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25); [issue #24](https://github.com/forgeblueai/ai-order-processing-agent/issues/24)
- **Related risk:** benchmark v1 methodology tracked by [issue #23](https://github.com/forgeblueai/ai-order-processing-agent/issues/23)

## Context and evidence

A raw small LLM (Qwen3 0.6B) intermittently omits even an explicit SKU or quantity. In G3, a strict `EvidenceFirstOrderExtractor` prototype (PR #25, **not yet merged**) bypasses the LLM only when the **entire** message satisfies a narrow explicit English `quantity SKU` grammar. Ambiguous messages still use an Ollama-backed `LLMOrderExtractor`. The frozen model-only benchmark measures the latter separately. This improves the bounded demo path but does **not** fix the model's accuracy on natural-language, multilingual or catalog-name requests.

Existing business authority: server-side product catalog, quantity validation, stock, pricing and order state machine; roles `operator`, `reviewer`, `approver`, `sender`; an authenticated reviewer **cannot** resolve an issue merely by acknowledging review. G3 adds an unresolved-issue guard (also currently **only on PR #25**). No structured correction endpoint or per-user audit attribution exists. This ADR must not be cited as though these missing features already work.

External design patterns evaluated before this decision:
- [Loxone human-in-the-loop B2B purchase-order extraction study](https://pure.fh-ooe.at/en/studentTheses/design-and-evaluation-of-a-human-in-the-loop-ai-system-for-automa/): catalog resolution and operator correction alongside extraction.
- [invoice2data](https://github.com/invoice-x/invoice2data): template/regex extraction before an AI fallback for unsupported formats.
- [Google LangExtract](https://github.com/google/langextract): source-grounded extracted spans.
- [DocETL](https://github.com/ucbepic/docetl): decompose difficult document tasks and validate intermediate outputs.

These sources motivate the design; reported results from other datasets are **not** performance guarantees for this product.

## Decision

Adopt a **three-lane, evidence-first, human-in-the-loop architecture** with one deterministic business-validation boundary.

```text
Untrusted customer subject + body
                  |
       Preflight, length/encoding, provenance
                  |
       [A] Strict deterministic parser
            | exact complete-grammar match
            | -> candidate with exact source spans
            | abstain
            v
       [B] Grounded LLM candidate extraction
            | tentative SKU, quantity, intent and spans
            | verifier: syntax, source range, semantics,
            | catalog resolution, coverage and missingness
            | abstain / uncertain
            v
       [C] Human correction (reviewer)
            | immutable original + revisioned edits
            | independent server revalidation
            v
      Authoritative validation service
      canonical catalog -> stock -> pricing -> issues
                  |
       REVIEW / READY_FOR_APPROVAL
                  |
         Separate approver role
                  |
          draft / human send confirmation
```

### A. Deterministic lane

- Use only on **full-body, supported grammar**, not a substring/first-match parser. Explicit, positive quantity must bind to an unambiguous SKU and affirmative order intent.
- Reject/admit to next lane: ambiguous quantifier, negation, cancellation, quotations, SKU appearing only in the subject without unambiguous linkage, free-form notes, duplicates, unsupported currency/units, multi-intent/conditional messages and prompt-injection instructions.
- Parse errors do not supply defaults or select catalog products. The implementation can **abstain** rather than pretend coverage.
- Every accepted candidate contains source offsets for the **exact SKU and quantity substrings** and records `extraction_method=deterministic`.

### B. Grounded LLM lane

- LLM output is **untrusted candidate data**, not a command and never the authoritative amount.
- Require typed source provenance **per candidate item and field**, not just document-level confidence. Each source span contains `source_field: subject|body`, half-open `start/end` (Unicode code-point indices against the original *unmodified* Python source), optional displayed excerpt, server-calculated source fingerprint; the server verifies `text[start:end]` matches the claim. Do not rely on a self-reported quote, confidence, or offset without independent checks.
- A matching literal span is **necessary but not sufficient**: verify affirmative order context, quantity-product association, negation, cancellation and scope. E.g. `Do not send 20 PV-10` cannot be accepted as a positive order.
- For every explicit source SKU, check coverage; never allow a model to omit one and still auto-route to READY. A fuzzy or alias candidate must be reviewed if identity is not uniquely proven.
- Missing quantity remains `None`, not 1 or an inferred number. A provider failure, timeout, malformed schema, suspect span, incomplete coverage or contradictory context produces a review issue.
- Never log raw customer text, bearer credentials or sensitive excerpts in CI; retain relevant original content securely in the authorized order store as already required for audit.

### Catalog resolver

A separate deterministic/catalog service resolves product **identities**, not prices from LLM text:

1. Exact canonical SKU match.
2. Explicit, approved, versioned alias map with unique one-to-one mapping (can be auto-resolved only when policy permits and the alias is unambiguous).
3. Normalized name search/fuzzy Top-3 **suggestions only**; a human must choose a canonical SKU. Similarity is never proof of identity.
4. Unknown, inactive, duplicated or ambiguous matches `requires_review`.

Always use server catalog unit price, available stock and policy checks. Treat text mentioning a price as customer-provided untrusted data. Record resolver/catalog version for reproducibility.

### C. Human correction and state-machine boundaries

Create a **separate correction gate/PR**. Do not add this directly to the blocked G3 release scope:

- Proposed endpoint: `PATCH /api/v1/orders/{order_id}/correction`, **reviewer only**, JSON body with `expected_revision`, candidate corrected line items and a non-empty `reason`. Exact API and schema require their own ADR-review during implementation.
- Only `REQUIRES_REVIEW` or `REVIEWED` may be corrected; `APPROVED`, `RESPONSE_DRAFTED`, `RESPONSE_SENT`, `COMPLETED` and `REJECTED` are immutable to this endpoint.
- Human changes are a new **revision**, not edits to the original raw text/LLM extraction. Append an audit event with principal identity, prior/new values, reason, time, order ID and expected/new revision. For the current role-key-only demo, a shared role is **not** an individual identity; do not claim individual attribution until an identity contract is implemented.
- Reject stale `expected_revision` with HTTP **409**; perform compare-and-swap and append revision atomically in the same database transaction. No lost updates; duplicate submissions must not create repeated side effects (idempotency policy to be specified).
- A correction is **not an approval**. Recompute catalog references, quantity validation, fresh inventory, server pricing, subtotal and all issues. If unresolved issues remain, stay under review; only a wholly valid revision can become `READY_FOR_APPROVAL`. The `approver` must still separately approve.
- Reviewer's corrective authority must never permit editing system prices, forcing stock available, changing their own role, suppressing issues or invoking a send operation.
- If inventory/catalog changes between correction and approval, stale assumptions must revalidate at approval; stock reservation is out of scope until a separate transactional design.

### No automatic retry loop

A bounded LLM retry may be evaluated for unsupported syntax **only after** exact reason codes, request budget, timeout handling and rate limits exist. Re-running until a favorable answer or silently choosing the best answer is not acceptable evidence.

## Data boundaries and migration strategy

Current `ExtractionResult` and `OrderRecord` are deliberately kept stable for G3. Future work should use a separate internal `GroundedCandidate` (with `SourceSpan`, `CandidateLine`, `EvidenceIssue`, `extraction_method`) to avoid changing Ollama's existing JSON schema before full compatibility tests.

Suggested evidence contract (design sketch, **not active API/schema**):

```json
{
  "extraction_method": "llm",
  "source_fingerprint": "sha256:...",
  "lines": [
    {
      "proposed_sku": "PV-10",
      "quantity": 20,
      "sku_span": {"source_field": "body", "start": 15, "end": 20},
      "quantity_span": {"source_field": "body", "start": 12, "end": 14},
      "resolver_status": "exact"
    }
  ],
  "issues": []
}
```

These offsets are illustrative only, **not validated** against a particular order string; tests must always compute and verify actual offsets.

Add versioned persistence/DB migration and outward API response fields only in the correction/grounding implementation PR. Retain old record compatibility; migrations must be reversible where feasible and proved in PostgreSQL. Do not put a raw customer transcript into logs or build artifacts.

## Measurable acceptance and test strategy

The first hybrid evaluation should be a **new** versioned dataset (proposed: 200 synthetic cases, balanced across fully explicit/multiline/free-form, ambiguous, negated, bilingual and adversarial cases), with a documented fixed seed and non-overlapping development/holdout subsets. A set of 200 synthetic cases is a *design target*, not proof of production quality.

Required comparisons on **identical inputs**:
- `LLM-only`: frozen v1 remains unchanged and individually labeled; new hybrid corpus must use its own scorer.
- `hybrid-current`: strict deterministic parser + real Ollama fallback.
- `hybrid-grounded`: source-spans + catalog identity resolver; later human correction.

Report **whole-order exact accuracy**, item/SKU/quantity precision and recall, missing-item rate, **unsafe auto-ready** count, case coverage, provider timeout rate, review burden, latency P50/P95 and correction time (when human UI exists). Break down results **by route and language**; never report parser accuracy as LLM accuracy. Emit failing case IDs and explicit provider-failure denominator.

**Non-negotiable acceptance (release blocker):**
- No known unsafe `READY_FOR_APPROVAL` on any negative/adversarial release-gate case; no dropped explicit SKU in a candidate marked ready.
- Every accepted source span is reproducible against the immutable original. Unlinked/ambiguous spans trigger review.
- Reviewer cannot bypass approver, stock, pricing or issue validation; stale revision conflicts are 409; unauthorized actions are 401/403; negative transitions are 409.
- CI tests and PostgreSQL migration/replay on exact SHA green; genuine Ollama fallback smoke with real model and private Compose green; human-confirmation evidence is actual human activity, never impersonated in CI.
- Failing, incomplete, duplicated or timed-out benchmark cases fail the *evidence-integrity gate*; do not rewrite the frozen v1 scorer to hide regressions.

Any numeric quality improvement must be measured on holdout data. `zero unsafe auto-ready in 200 synthetic tests` does **not** imply zero probability in production. Before production, evaluate representative consented data, company policies, identity/tenancy and measured operator workflows.

## Alternatives consciously rejected

| Alternative | Rejection reason |
| --- | --- |
| Swap to Qwen 1.7B/8B for every request | Higher resource cost without proof of stable structured extraction on this workload |
| Make regex permissive enough for all natural language | False order intent, wrong quantity links and unsafe partial substring matches |
| Treat model-provided confidence as calibrated probability | Not independently calibrated; errors may be overconfident |
| Auto-select highest fuzzy catalog match | Product substitutions can cause material business harm |
| Reviewer marks any issue as resolved by clicking `reviewed` | Conflates acknowledgment and data correction; bypasses previously established state invariant |
| Auto retry LLM until a clean output | Cherry-picks uncertain output, increases latency and obscures failure rates |
| Integrate a full ERP/paid Document AI stack into G3 | Violates bounded low-cost private-demo scope; organizational identity/PII boundary not ready |

## Implementation sequence / decisions deferred

- **ADR review (this PR):** approve or amend source-span semantics, correction rights, issue-resolution logic and benchmark categories. Documentation only.
- **G3 closeout (existing PR #25):** final-head CI + real private-stack smoke + genuine owner-operated human approval. This ADR does not loosen its merge or release gates.
- **Gate A / Grounding:** internal types, span verifier, explicit-SKU completeness, negation/quote counterexamples, catalog resolver *suggestion* layer; no public correction mutation.
- **Gate B / Correction:** audit actor identity, versioned schema, PostgreSQL migration, atomic optimistic locking, correction endpoint, revalidation/state tests, UI/operator approval.
- **Gate C / Independent quality evaluation:** new hybrid corpus, holdout audit, latency/review-cost measures and transparent case-study evidence.

**Overall status: PROPOSED.** No new API endpoint, schema, business-state transition, model switch or public release is authorized by merging this document.
