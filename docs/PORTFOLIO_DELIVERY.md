# Portfolio delivery checklist — AI Order Processing Agent

Status: **IN PROGRESS — not production-ready and not released**. This document tracks evidence, acceptance conditions, and remaining work; it is not a promise of deployment readiness.

## Demo acceptance contract

1. A reproducible, zero-paid-service local setup starts the API, persistent database, and a local Ollama model, with setup and manual steps documented.
2. A user submits synthetic B2B orders and can distinguish deterministic extraction of narrowly explicit SKU orders from LLM extraction of unstructured or ambiguous messages.
3. An authenticated **reviewer** can inspect and review an order and mark it ready only when its validation issues are resolved. A separately authorized **approver** can approve or reject. Unauthorized callers cannot read protected order data or invoke role-restricted operations.
4. An authorized human can inspect a safe synthetic order, approve it, and record a simulated send confirmation. The demo must never imply that an external email was transmitted.
5. Python CI, PostgreSQL integration, and private Compose smoke checks pass on the exact candidate head. Real-model evidence is complete, independently reviewable, and labeled with its model, sample count, configuration, limitations, and artifact digest.
6. Any public case study uses synthetic examples only and discloses the limitations below. No customer content, secrets, tokens, or private demo credentials are published.
7. A reviewed README, versioned demo runbook, architecture diagram, walkthrough, and release evidence are available before a tagged demo release is considered.

## Evidence and current gate disposition

| Gate | Required evidence | Current disposition |
| --- | --- | --- |
| G1 Reliability | Frozen v1 benchmark, complete-case integrity, fail-closed extraction evidence | **MERGED** via [PR #19](https://github.com/forgeblueai/ai-order-processing-agent/pull/19), merge SHA `e60cbef5c5ed7aa5853c481e606431b08aa07a5e`. Benchmark v2 and scorer limitations remain tracked in [issue #23](https://github.com/forgeblueai/ai-order-processing-agent/issues/23). Do not present one synthetic run as production reliability. |
| G2 Security | Authenticated roles, denied-action tests, CI and PostgreSQL checks | **MERGED** via [PR #22](https://github.com/forgeblueai/ai-order-processing-agent/pull/22), merge SHA `ab1481147c33388b8a952d0b71d4e821eaecc80e`. Accepted for a bounded private demo only; not production IAM or tenant isolation. |
| G3 Reproducibility | Private Compose, PostgreSQL, Ollama, migrations, real-model smoke, persistence, human acceptance | **VALIDATING** on [draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25). Its implementation head `d86f09224bca7449aaaa8a6bf1110d6ce793dbe3` passed CI #115 (155 Python tests), PostgreSQL #77, and Private Demo #38. Real LLM #51 completed and passed the 85-case report-integrity gate. Actual human approval and simulated-send acceptance remain outstanding. |
| G4 Portfolio | Accurate public README, case study, walkthrough, demo and release evidence | **BLOCKED** until G3 is accepted and the final candidate is reviewed. The public README and versioned release remain unfinished. |

### G3 evidence interpretation

The checks above apply to implementation head `d86f09224bca7449aaaa8a6bf1110d6ce793dbe3`, before this documentation-only synchronization. The documentation commits that update this checklist and the security gate must themselves be checked on the resulting PR head before merge.

- [CI #115](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096747): **SUCCESS**, 155 Python tests, zero failures.
- [PostgreSQL #77](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096864): **SUCCESS**.
- [Private Demo #38](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096835): **SUCCESS**. Explicit single- and multi-SKU cases used the deterministic evidence-first parser; an ambiguous case used the real Ollama fallback and remained under review without priced lines; RBAC and PostgreSQL persistence after API restart passed.
- [Real LLM #51](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096817): **SUCCESS**. The report-integrity checker verified 85 complete cases and review confusion counts of FN=0, TP=40, FP=9, TN=36. This verifies complete benchmark evidence and the zero-review-false-negative condition for that run; it does **not** by itself establish high extraction accuracy or production reliability. The benchmark is model-only and must not be represented as a hybrid-parser accuracy result.
- The Qwen3 1.7B candidate run #6 was cancelled and the candidate remains unselected. The private demo continues to use Qwen3 0.6B for its LLM fallback.

The checks above are not a human sign-off. G3 remains open until a person follows the human acceptance procedure in `docs/DEMO_RUNBOOK.md`, including a safe synthetic order's approval and separate simulated-send confirmation.

## Invariants

- LLM output is **untrusted data**; it is never an authority for pricing, inventory, approval, permissions, tool execution, or outbound sending.
- Deterministic catalog, stock, pricing, and state-machine rules remain authoritative.
- The evidence-first parser accepts only a narrow, fully explicit English SKU grammar. Unsupported, ambiguous, incomplete, or untrusted input must abstain and use the LLM path or fail closed to human review.
- Unknown products, missing quantities, stock shortages, model/schema errors, and unresolved review issues must not silently become approved orders.
- A reviewer acknowledging an issue is not equivalent to resolving it. An order with outstanding validation issues must not become ready for approval.
- The send-confirmation endpoint records a human confirmation only. No external email is sent.
- The demo must remain private and loopback-only. Static role tokens are not production identity management or tenant isolation.
- Mandatory services, models, and CI should remain usable without paid subscriptions or API credits.
- Do not change benchmark thresholds, corpus labels, or scorer logic merely to make a regression disappear. Methodology changes require a versioned benchmark and explicit comparison limits.

## Delivery sequence

1. Preserve the merged G1 and G2 baselines and their documented limitations.
2. Complete G3 on PR #25: run the human acceptance steps using only synthetic data and review the resulting evidence.
3. Re-run Python CI, PostgreSQL integration, private Compose smoke, and benchmark-integrity checks on the exact final PR head.
4. Review all known limitations and residual security risks; keep PR #25 in Draft until the implementation and documentation are ready for owner review.
5. Obtain explicit owner authorization before merging PR #25.
6. Complete G4: update the public README, prepare a bounded case study, architecture diagram, and walkthrough, then review the demo release evidence.
7. Obtain separate explicit owner authorization before tagging or publishing a release.

Completing these gates does not establish production readiness or authorize a public deployment.

## Demonstration scenarios

Use synthetic orders that expose both deterministic and LLM behavior:

- Explicit multi-SKU shortage: `We need 2 F-200 and 20 PV-10.` The narrow evidence-first parser extracts both explicit lines; deterministic stock validation routes the PV-10 shortage to human review.
- Explicit safe order: `Please send 2 F-200.` The API calculates trusted catalog pricing and leaves the order awaiting a human-authorized approval; it is not automatically approved.
- Ambiguous request: `We need PV-10. Please confirm availability.` This must use the real Ollama fallback and remain under review when the quantity is missing. A provider failure is not a successful smoke result.

A human may inspect and approve the safe synthetic order only through the procedure in `docs/DEMO_RUNBOOK.md`. Never present a draft or recorded send confirmation as a delivered external email.

## Release evidence template

- Release tag / SHA:
- PRs and merged SHAs:
- Final Python/API CI run:
- Final PostgreSQL integration run:
- Private Compose smoke run:
- Ollama model/configuration and benchmark run:
- Benchmark artifact ID / digest:
- Benchmark completeness and review confusion counts:
- Authentication/RBAC negative-test evidence:
- Human approval and simulated-send evidence (operator sign-off):
- Persistence-after-restart verification:
- Architecture diagram / walkthrough:
- Known limitations and residual risks:
- Sign-off: **NOT APPROVED until all gates and separate owner authorization are complete**
