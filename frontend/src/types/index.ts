export type Decision = 'ALLOW' | 'WARN' | 'EDIT' | 'HOLD' | 'BLOCK';
export type PageId = 'overview' | 'playground' | 'reviews' | 'policies' | 'models' | 'trust' | 'audit';

export interface ApplicationProfile {
  id: string;
  name: string;
  description: string;
  risk_tier: string;
  latency_budget_ms: number;
}

export interface ModelProfile {
  id: string;
  provider: string;
  model_name: string;
  capability_level: string;
  context_length: number | null;
  usage_available: boolean;
  logprobs_available: boolean;
  pricing: { input_per_million_usd: number; output_per_million_usd: number; notice: string };
  calibration: null | {
    timestamp: string;
    prompt_count: number;
    baseline_latency_ms: number;
    baseline_output_tokens: number;
    baseline_cost_usd: number;
    baseline_uncertainty: number | string;
  };
}

export interface Evidence {
  source_id: string;
  source_name: string;
  snippet: string;
  similarity: number;
  metadata?: Record<string, unknown>;
}

export interface Claim {
  claim: string;
  status: string;
  confidence: number;
  source_id: string | null;
  source_name: string | null;
  evidence_snippet: string | null;
  explanation: string;
}

export interface RuntimeResult {
  trace_id: string;
  application: ApplicationProfile;
  model: { id: string; provider: string; capabilities: Record<string, boolean> };
  original_response: string;
  final_response: string;
  decision: Decision;
  overall_risk: number;
  risks: Record<string, number>;
  signals: Array<{ detector: string; risk_type: string; score: number; severity: string; signals: Array<Record<string, unknown>> }>;
  claims: Claim[];
  evidence: Evidence[];
  policy: { name: string; version: number; risk_tier: string };
  triggered_rules: string[];
  session_risk: { rolling_risk: number; previous_turns: number; risky_claim_turns: number; elevated: boolean; explanation: string };
  performance: Record<string, number>;
  cost: Record<string, number | string>;
  deep_check: { status: string; detector: string | null };
  review_case_id: string | null;
}

export interface Incident {
  id: string;
  trace_id: string;
  created_at: string;
  application: string;
  model: string;
  session_id: string;
  prompt: string;
  original_response: string;
  final_response: string;
  policy: { name: string; version: number };
  decision: Decision;
  machine_decision: Decision;
  review_status: string;
  overall_risk: number;
  risks: Record<string, number>;
  tokens: { input: number; output: number };
  cost: { model: number; checker: number; total: number };
  latency: { model: number; tier0: number; tier1: number; total: number };
  deep_check: { status: string; result?: Record<string, unknown> };
  triggered_rules: string[];
}

export interface ReviewCase {
  id: string;
  created_at: string;
  status: string;
  priority: string;
  reason: string;
  proposed_response: string;
  interaction: Incident;
}

export interface DemoScenario {
  id: string;
  name: string;
  application: string;
  model_id: string;
  prompt: string;
  expected: string;
  description: string;
}

export interface PolicyRecord {
  id: string;
  version: number;
  config: Record<string, any>;
  change_note: string;
  created_at: string;
}

export interface Summary {
  requests: number;
  passed: number;
  warned: number;
  edited: number;
  held: number;
  blocked: number;
  review_rate: number;
  average_risk: number;
  p95_controlplane_latency_ms: number;
  ai_spend_usd: number;
  checker_cost_usd: number;
  pending_reviews: number;
  intervention_mix: Record<string, number>;
  application_health: Array<{ application: string; requests: number; average_risk: number; intervention_rate: number }>;
  recent_incidents: Incident[];
}
