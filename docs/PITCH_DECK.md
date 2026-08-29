# ControlPlane.ai Competition Pitch - 12 Slides

## Slide 1 - ControlPlane.ai

**Exact key points**

- Runtime AI Risk Gateway
- The policy and enforcement layer between enterprise AI and the real world
- Round 2 - Problem Track 1

**Suggested visual:** One strong gateway diagram: AI applications on the left, ALLOW/WARN/EDIT/HOLD/BLOCK paths on the right. Use the dark navy/cyan product design; no external branding.

**Speaker notes:** “Enterprises do not need another dashboard that tells them an unsafe response was delivered. They need a runtime that can inspect, explain, and intervene before delivery. That is ControlPlane.”

## Slide 2 - Enterprise AI has many risk signatures

**Exact key points**

- Customer support: low latency, high privacy, moderate factual risk
- Internal copilots: critical confidentiality and grounding
- Decision support: critical hallucination/fairness risk and human review
- The same threshold cannot serve all three

**Suggested visual:** Three application cards with different risk/latency fingerprints.

**Speaker notes:** “One enterprise can operate all three workflows at once. A setting that protects decision support will overwhelm customer service; a customer-service threshold can under-protect a consequential decision.”

## Slide 3 - Existing checks leave an enforcement gap

**Exact key points**

- Offline evaluation does not govern each live response
- Provider guardrails lack enterprise context and authoritative documents
- Observability is often post-hoc
- Fragmented privacy, model-risk, review, and cost controls create audit gaps

**Suggested visual:** Broken toolchain with separate evaluator, DLP, dashboard, review inbox, and spend report; highlight the missing inline policy boundary.

**Speaker notes:** “Every current tool remains useful, but none alone answers: should this exact response reach this exact user in this exact workflow?”

## Slide 4 - The ControlPlane runtime

**Exact key points**

- Model-independent adapter: works with text-only API access
- Tier 0 fast checks + Tier 1 evidence/context + asynchronous Tier 2
- Separate risk dimensions + weighted noisy-OR
- YAML policy decides ALLOW, WARN, EDIT, HOLD, or BLOCK
- Masked audit trail for every machine and human decision

**Suggested visual:** Product architecture flow from ModelResult through detector tiers to enforcement and audit.

**Speaker notes:** “Internal model signals are optional capabilities. Our default path operates entirely at the input/output layer, which reflects how enterprises actually consume foundation models.”

## Slide 5 - Detection with evidence, not overclaiming

**Exact key points**

- PII/secrets: spans, Luhn validation, readable redaction
- Confidential leakage: exact + near-duplicate local fingerprints
- Grounding: claim extraction, retrieval, entity/number consistency
- Distinguishes unsupported from contradicted
- Fairness: controlled paired consistency diagnostic, not a legal conclusion

**Suggested visual:** One response with two claim callouts: March 2024 = CONTRADICTED; $23m = UNSUPPORTED; show the June 2024 source snippet.

**Speaker notes:** “No support in our knowledge base does not prove a statement false. But an approved source with a different launch date is contradictory evidence. The product makes that distinction visible.”

## Slide 6 - Live demo: intervention before delivery

**Exact key points**

- Safe FAQ → ALLOW
- Synthetic customer contact leak → EDIT and redact
- Synthetic token/canary → BLOCK
- Hallucinated date/number → evidence-backed intervention

**Suggested visual:** Four compact before/after output panels with decision colors.

**Speaker notes:** “Every scenario is deterministic and offline. We are demonstrating the runtime mechanism, not hoping an external model hallucinates on cue.”

## Slide 7 - Flagship proof: policy changes the outcome

**Exact key points**

- Same model output
- Same detector scores: hallucination = 0.72
- Customer support policy → WARN
- Decision-support policy → HOLD FOR REVIEW

**Suggested visual:** Split screen using the product’s policy contrast panel. Center equation: SAME OUTPUT + SAME SCORES + DIFFERENT POLICY = DIFFERENT ENFORCEMENT.

**Speaker notes:** “This is why ControlPlane is not merely an evaluator. Scores describe a signal; policy determines what the enterprise does about it.”

## Slide 8 - Human review completes the control loop

**Exact key points**

- Reviewer sees masked original, safe proposal, risks, evidence, and policy version
- Approve, edit, block, or mark false positive
- Manual overrides require rationale
- Feedback informs threshold simulation—no silent auto-retraining

**Suggested visual:** Review Console case detail and action row.

**Speaker notes:** “The machine decision is immutable evidence. The final human decision is recorded beside it, so governance can measure overturns and tune policy responsibly.”

## Slide 9 - Trust is measured

**Exact key points**

- 80 labeled synthetic cases actually executed
- Privacy: precision 0.929, recall 0.867, F1 0.897
- Grounding: recall 1.000, precision 0.526—a visible conservative false-positive challenge
- Mean 0.381 ms and P95 0.654 ms for the final local evaluation detector suite
- Threshold experiment quantifies review-volume vs missed-case tradeoff

**Suggested visual:** Trust Center metric cards plus privacy threshold table. Add small footnote: environment-specific; controlled fairness/cost subsets are not generalizable.

**Speaker notes:** “We do not hide the weak result. The grounding verifier is intentionally conservative and produces false positives. The platform’s value is that this tradeoff is measured, visible, and tunable per application.”

## Slide 10 - Business value

**Exact key points**

- Prevent costly leakage and unsupported-output exposure
- Reduce indiscriminate manual sampling
- Identify requests suitable for lower-cost route evaluation
- Consolidate evidence across engineering, security, Responsible AI, and audit
- ROI formula uses customer evidence, not invented market claims

**Suggested visual:** Transparent equation: prevented loss + review saving + inference saving - operating cost.

**Speaker notes:** “We propose a measured pilot. It succeeds only if it meets latency and detector targets, reduces reviewer effort at the selected recall, and produces customer-validated economic benefit.”

## Slide 11 - Prototype today, production path tomorrow

**Exact key points**

- Today: FastAPI, SQLite, local KB, in-process background checks, zero-key demo
- Production: PostgreSQL, Kafka/Redis, Celery/Ray, object storage, OIDC/RBAC, Kubernetes
- Regional policy packs and retention controls
- Contracts already separate adapters, detectors, policy, review, and telemetry

**Suggested visual:** Two-column prototype-to-production mapping.

**Speaker notes:** “The prototype is deliberately simple to run. The seams needed to scale—trace IDs, versioned policies, worker-safe detector contracts, and normalized adapters—already exist.”

## Slide 12 - Govern the moment AI meets the world

**Exact key points**

- Model-agnostic
- Evidence-backed
- Policy-driven
- Human-accountable
- Measurably tunable

**Suggested visual:** Return to the gateway, now connecting three applications to five governed outcomes. Closing line: “ControlPlane.ai: runtime trust for enterprise AI.”

**Speaker notes:** “Enterprise AI governance cannot stop at evaluation. ControlPlane turns risk insight into a real-time, explainable, auditable action—adapted to the use case that carries the risk.”
