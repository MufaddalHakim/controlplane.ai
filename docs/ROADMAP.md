# Roadmap

The roadmap extends a stable runtime; it does not substitute buzzwords for working controls.

## Phase 0 - Submission hardening (now)

- deterministic offline scenarios and reset;
- dimension-preserving detectors and YAML policies;
- review, audit, feedback, registry/calibration, evaluation, Trust Center;
- package/start/test/build documentation.

## Phase 1 - Enterprise pilot

- shadow-mode SDK/gateway integrations;
- customer-specific knowledge/confidential fingerprints;
- PostgreSQL + Alembic, encryption, retention jobs;
- OIDC/SSO and reviewer RBAC;
- signed policy approvals/diff/rollback;
- multilingual PII and optional local semantic retrieval;
- blinded labeled datasets and score-band calibration;
- durable evidence exports and incident reports.

## Phase 2 - Reliable production scale

- Redis for routing/cache and rate budgets;
- Kafka plus transactional outbox for durable interaction/signal/review events;
- Celery/Ray workers for contextual and deep checks;
- Kubernetes autoscaling and regional deployments;
- object storage for governed evidence artifacts;
- OpenTelemetry, SIEM, SLOs, dead-letter/replay, chaos testing;
- policy-specific fail-open/fail-closed/degraded modes;
- reviewer queue forecasting, skills, SLA, and escalation.

## Phase 3 - Higher-fidelity detection

- locally hosted or governed embedding/entailment retriever;
- relation-aware numeric and temporal contradiction checks;
- multilingual/entity-aware privacy extension;
- calibrated provider judge ensemble where approved;
- agent/tool-action envelopes, dependency graph, and reversible action gates;
- correlation analysis across privacy, hallucination, and fairness signals.

## Advanced concepts and how they extend the current architecture

### Bayesian Online Changepoint Detection

Replaces the simple mean-window drift signal with posterior probability of a distribution regime change. It consumes the existing risk/latency/cost time series and remains monitoring-only until validated.

### SHAP bias attribution

Adds feature-level explanation to a validated predictive fairness test. It complements paired counterfactual evidence; it does not turn a consistency diagnostic into legal proof. Requires model/data access and careful causal interpretation.

### Attention pathology analysis

Becomes an optional detector only for adapters declaring attention availability. The capability registry already prevents it from running or fabricating data for API-only models.

### Learned sparse detector routing

Uses request/application features to select necessary checks under latency/cost budgets. It extends the tier router and must be constrained so critical deterministic rules always run and routing false negatives are measured.

### Stackelberg/game-theoretic thresholds

Models adaptive attacker and defender incentives. It can recommend threshold strategies to Policy Studio but should never silently modify production policy.

### VaR-style enterprise risk budgeting

Aggregates probability-weighted loss scenarios across applications. It builds on dimension scores and application impact metadata; it requires calibrated probabilities and enterprise loss data before credible use.

### M/M/c reviewer queue optimization

Estimates staffing/backlog SLA under arrival and service rates. It extends stored review timestamps and threshold simulations. Real queues may violate exponential assumptions, so discrete-event validation is preferable.

### PageRank-style agent dependency risk

Propagates risk through an agent/tool dependency graph so influential upstream outputs receive stricter gates. It extends session IDs into trace-linked graph nodes and must avoid treating graph centrality as harm probability.

### Kafka/Ray/Celery distributed architecture

Turns current detector contracts into independently scalable workers. Kafka carries durable events, Redis coordinates short-lived state, Celery handles standard jobs, and Ray can serve compute-heavy local models. Idempotency, ordering, timeouts, and audit completeness are prerequisites.

## Exit criteria by phase

Each phase requires measured accuracy/calibration, latency/cost SLOs, security review, documented policy ownership, reviewer capacity, rollback, and evidence from realistic application traffic. Advanced research is not promoted while a P0/P1 reliability criterion is broken.
