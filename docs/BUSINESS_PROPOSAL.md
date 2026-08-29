# ControlPlane.ai Business Proposal

## 1. Executive summary

ControlPlane.ai is a runtime risk gateway that sits between enterprise AI applications and their users. It evaluates model responses for performance, responsibility, and cost risk, then enforces application-specific policy in real time. The same output may be allowed with a warning in customer service and held for human review in high-risk decision support. This is the product’s central thesis: enterprise AI governance must be contextual and enforceable at runtime, not reduced to a universal offline scorecard.

The working prototype demonstrates three applications, five enforcement outcomes, evidence-backed grounding, privacy redaction, secret blocking, controlled fairness diagnostics, cost budgets, review workflow, audit, feedback, calibration, and measured evaluation—all offline using synthetic data.

## 2. Problem

Enterprises consume multiple foundation models through APIs while deploying AI into workflows with materially different impact. Existing controls are often fragmented among model evaluation notebooks, provider safety filters, observability dashboards, data-loss prevention, and manual approvals. This creates gaps:

- pre-launch evaluation does not enforce behavior on each production output;
- provider controls rarely understand enterprise documents, workflow impact, jurisdiction, or risk appetite;
- one threshold over-flags benign traffic or under-protects high-impact decisions;
- audit evidence is separated from the delivered response and human override;
- cost governance is measured after spend rather than evaluated per request;
- teams cannot quantify false positives, missed cases, or reviewer volume.

## 3. Target enterprise users

- **AI platform and engineering teams:** one integration point across applications/models.
- **Responsible AI and model risk teams:** configurable thresholds, evidence, calibration, and evaluation.
- **Security/privacy teams:** PII/secret/confidential-data controls with masked telemetry.
- **Business owners:** explicit risk appetite and latency/cost budgets per workflow.
- **Human reviewers:** prioritized cases with model output, evidence, policy rationale, and safe proposal.
- **Audit/legal/compliance stakeholders:** traceability and jurisdiction-specific policy packs, subject to legal review.

Initial adoption should focus on internal copilots and customer-service AI where output is text, intervention is feasible, and owners can label review outcomes. High-risk decision support follows after governance, validation, and reviewer operating models mature.

## 4. Why current approaches fail

### Offline benchmarks are necessary but insufficient

They measure a test distribution, not the exact prompt, retrieved context, model version, session history, and downstream impact of a live response.

### Provider guardrails are not enterprise policy

They cannot reliably know which internal phrase is confidential, which document is authoritative, or when an application legally/operationally requires human review.

### Observability without enforcement is post-hoc

A dashboard may show a leak after delivery. ControlPlane places a policy decision before delivery while preserving the same event for analytics.

### Universal thresholds ignore asymmetric harm

A conservative checker can overwhelm customer-service reviewers; a permissive checker can create liability in decision support. The tradeoff must be visible and configurable.

## 5. ControlPlane solution

ControlPlane receives normalized model output, runs cheap deterministic checks and contextual evidence verification, preserves risk dimensions, aggregates co-occurring risk, and applies a versioned application policy. Safe automated transformations are span- or claim-specific. Held cases enter a review queue. Every machine and human decision is auditable.

The runtime works at the input/output layer and degrades gracefully when only text is available. Provider usage/logprobs improve signals when exposed but are not prerequisites.

## 6. Product architecture

The prototype contains:

1. application/model registry;
2. adapter gateway;
3. Tier 0, Tier 1, and asynchronous Tier 2 detectors;
4. dimension risk and weighted noisy-OR aggregator;
5. YAML/SQL versioned policy engine;
6. safe editor and delivery gate;
7. review/feedback service;
8. masked audit/telemetry store;
9. evaluation, threshold simulation, calibration, and drift views.

Production separates gateway, risk workers, policy decision point, audit stream, review service, and analytics storage while preserving the API contracts.

## 7. Use cases

### Customer support

Low latency, high privacy, medium hallucination/cost sensitivity. PII is automatically redacted, weak grounding warns, severe secrets block, and review is reserved for unusually high risk.

### Internal knowledge copilot

High grounding/confidentiality needs with a larger latency budget. Claims cite internal sources, unsupported facts are hedged, and confidential material can be redacted, held, or blocked.

### Synthetic high-risk decision support

Strict grounding/fairness thresholds and human review. Paired counterfactual differences are shown as diagnostics. The environment never makes real financial, employment, or insurance decisions.

## 8. Differentiation

- **Runtime enforcement, not only evaluation.** Decisions affect delivered output.
- **Policy contextualization.** Same detector vector, different governed result.
- **Model independence.** Text-only API models remain governable.
- **Evidence and scientific restraint.** Unsupported and contradicted are distinct.
- **Unified responsibility and FinOps.** Privacy, grounding, fairness, safety, and cost share one policy/audit envelope.
- **Measurable reviewer tradeoff.** Threshold analysis links precision/recall to escalation volume.
- **Checker privacy.** Sensitive data is masked within the governance layer itself.

## 9. Business impact

ControlPlane can reduce avoidable leakage, unsupported-answer exposure, manual sampling, reviewer effort, and unnecessary inference cost. Value must be estimated transparently rather than promised from invented benchmarks.

Illustrative annual value formula:

`prevented loss + reduced review cost + avoided inference cost - ControlPlane operating cost`

Example assumptions, explicitly illustrative:

- 2,000,000 AI interactions/year;
- 2% would otherwise receive manual sampling at 4 minutes each;
- tuned runtime reduces manual reviews by 35% while preserving the selected recall target;
- loaded reviewer cost is $45/hour;
- inference routing experiments identify 8% of $300,000 annual model spend as avoidable;
- annualized ControlPlane platform/operations cost is $90,000.

Review saving: `2,000,000 × 2% × 4/60 × $45 × 35% = $42,000`.

Inference saving: `$300,000 × 8% = $24,000`.

These two operational benefits total $66,000 before prevented-loss value and do not by themselves exceed the illustrative platform cost. A buyer should add probability-weighted incident reduction using its own loss history:

`Σ[(baseline probability - controlled probability) × impact]`.

The example deliberately avoids claiming positive ROI without enterprise evidence. A pilot’s purpose is to measure it.

## 10. Deployment model

- **Developer/pilot:** local or private VPC single-node deployment.
- **Enterprise:** regional Kubernetes service with managed PostgreSQL, Kafka/Redis, object storage, OIDC/SSO, RBAC, secrets management, and observability.
- **Integration:** reverse-proxy gateway, application SDK/middleware, or `/check` for externally generated output.
- **Data posture:** configurable raw retention, tenant encryption, regional residency, and customer-managed keys where required.

## 11. Risk and governance model

Each application owner documents purpose, downstream impact, data sources, model, latency budget, cost budget, jurisdiction, and risk appetite. Responsible AI/security approve the initial policy. Policy changes create new versions and should require production approval. False positives, missed cases, overrides, latency, checker cost, and model drift are monitored.

ControlPlane can encode organization-specific controls; it does not certify GDPR, HIPAA, the EU AI Act, or sector compliance. Qualified counsel and control owners determine obligations.

## 12. Human-in-the-loop design

Review cases show masked original/proposed output, separate risks, detector evidence, application/model/session, policy/rules, and history. Reviewers approve, edit, block, or label false positives. Manual override requires a note. Production adds role separation, queues by SLA/skill, escalation chains, and quality sampling.

## 13. Success metrics

### Detection/trust

Precision, recall, F1, FPR, FNR by detector/application; evidence coverage; contradicted/unsupported rates; calibration by score band.

### Operations

ALLOW/WARN/EDIT/HOLD/BLOCK mix; review volume; reviewer time; overturn rate; backlog age; repeat session risk; drift alerts.

### Runtime

Tier 0/Tier 1/Tier 2 latency, P50/P95/P99 overhead, timeout/failure rate, degraded-mode use.

### Economics

Model/checker cost, budget violations, qualified lower-cost candidates, savings validated through controlled routing tests.

The prototype’s 80-case results are baseline engineering evidence, not production performance claims.

## 14. Scalability

Detectors are independent workers keyed by trace ID. A sparse routing layer can avoid expensive contextual checks when Tier 0 and application policy make them unnecessary. Kafka/outbox ensures durable audit events. PostgreSQL partitions by tenant/time; evidence objects move to governed storage. Reviewer queues scale separately from inline traffic.

## 15. Commercialization and pricing concept

A credible hybrid model:

- platform subscription by environment/region;
- metered protected interactions by detector tier;
- enterprise modules for policy packs, SSO/RBAC, regulated review, and retention;
- professional services for use-case onboarding, evaluation dataset design, and policy calibration.

Pricing should expose checker cost and avoid incentives to run unnecessary deep checks. A pilot can be fixed-fee with agreed success gates: integration latency, coverage, review volume, precision/recall on customer-labeled cases, and measured economic benefit.

## 16. Phased roadmap

1. **Pilot:** text-only gateway, three use cases, customer-specific corpus, shadow mode, labeled feedback.
2. **Controlled production:** version approvals, SSO/RBAC, PostgreSQL, regional retention, reviewer SLAs.
3. **Scale:** Kafka/Redis/Celery, streaming, multi-model routing evaluation, richer drift/calibration.
4. **Advanced research:** learned routing, explainable fairness diagnostics, agent dependency risk, enterprise risk budgets—only after validation.

## 17. Key risks

- detector blind spots and adversarial evasion;
- over-flagging that drives bypass behavior;
- false confidence from simple scores;
- checker becoming a sensitive-data concentration point;
- latency/cost overhead;
- policy sprawl and stale ownership;
- reviewer backlog;
- provider/model/version change;
- legal overclaiming.

## 18. Mitigations

- layered independent detectors and periodic red-team cases;
- per-application thresholds with measured tradeoff;
- dimension scores, evidence, confidence, and limitations in the UI;
- masking, minimal retention, encryption, RBAC, and regional stores;
- fast path, async deep checks, budgeted routing, and SLOs;
- signed/versioned policy packs with owners and review dates;
- queue SLAs, prioritization, sampling, and escalation;
- model registry, calibration, canaries, and drift monitoring;
- explicit language: risk signal, not proof or certification.
