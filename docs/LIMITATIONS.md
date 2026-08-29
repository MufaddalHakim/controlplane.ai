# Limitations and Responsible Use

## What this prototype does not prove

- A low score does not guarantee a safe, correct, fair, private, or compliant response.
- An unsupported claim is not proven false; it lacks support in the available knowledge base.
- A contradiction means available evidence conflicts with the claim; the evidence itself may be stale or incomplete.
- A counterfactual output difference is a diagnostic consistency signal, not proof of unlawful discrimination.
- A configurable policy does not certify GDPR, HIPAA, EU AI Act, employment, financial, insurance, or other legal compliance.
- Illustrative rates and budgets are not current-provider price guarantees.

## Detection limitations

### Privacy

Regexes miss obfuscation, multilingual names/addresses, uncommon phone formats, images, audio, and context-dependent identifiers. They can flag public strings that resemble sensitive formats. Luhn checks plausibility, not whether a card is real.

### Confidential leakage

Exact/shingle fingerprints are strongest for direct or near-direct copies. Paraphrase, translation, reordering, and short common phrases reduce reliability. A production corpus needs access controls and tenant separation because fingerprints themselves describe sensitive sources.

### Grounding

The local lexical retriever lacks semantic embeddings and trained entailment. Paraphrases can look unsupported; lexical overlap can appear supported even when relations differ. The 80-case run measured grounding precision 0.526 at recall 1.000, which indicates substantial alert fatigue at the selected threshold. This result is surfaced intentionally.

### Fairness

The controlled pair checks one attribute at a time in synthetic cases. It does not estimate group fairness, historical inequity, intersectional effects, allocation harms, accessibility, or downstream outcomes. Real assessment requires representative data, domain experts, affected-stakeholder input, and legal review.

### Cost

Mock usage is deterministic. External usage is estimated when a provider does not report tokens. Tokenizers, cached inputs, batch discounts, retries, tool calls, and provider price changes affect real cost.

### Safety

The basic signal is deliberately narrow and should not replace a production safety model or domain-specific abuse controls.

### Self-consistency/drift

Consistent false answers can look certain; stylistic variety can look inconsistent. Mean-window drift can trigger on small samples, seasonality, or legitimate mix change. Neither should block traffic without policy and calibration.

## Evaluation limitations

The 80 cases are synthetic and designed around implemented mechanisms. Fairness and cost have five positive cases each, making perfect scores non-generalizable. Evaluation labels are authored fixtures, not independent expert adjudication. Latency is machine/environment-specific and excludes network/provider time. A production pilot needs blinded customer examples, hard negatives, adversarial cases, multi-language coverage, score calibration, and confidence intervals.

## Architecture limitations

- SQLite and automatic table creation are single-node prototype choices.
- BackgroundTasks are process-local and not durable across restart.
- No authentication, tenant isolation, field encryption, KMS, or production RBAC is implemented.
- Policy updates have versions but no multi-party approval/signature workflow.
- No database migration framework or event outbox.
- The OpenAI-compatible adapter is supplementary and not covered by offline tests against a real provider.
- The current frontend is a single console application, not a multi-tenant administration plane.
- Raw retention off masks recognized sensitive spans; unrecognized sensitive content can still remain.

## Appropriate use

Use this prototype for mechanism demonstration, technical evaluation, policy workshops, synthetic testing, and shadow-mode pilots. Do not use it as the sole control for real employment, credit, insurance, medical, legal, safety-critical, or other high-impact decisions. Human accountability, validated data, independent assurance, security review, and jurisdiction-specific legal analysis remain required.

## Recommended pre-production validation

1. Threat model the checker and its privileged access.
2. Build application-specific labeled datasets with independent adjudication.
3. Measure precision/recall and calibration by language, topic, model, geography, and impact.
4. Define fail behavior and reviewer SLOs before HOLD/BLOCK activation.
5. Red-team prompt injection, corpus poisoning, obfuscation, retrieval manipulation, and policy bypass.
6. Validate masking and retention with security/privacy owners.
7. Run shadow mode and compare against incident/override outcomes.
8. Obtain qualified legal and Responsible AI approval.
