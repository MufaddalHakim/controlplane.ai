'use client';

import { useEffect, useState } from 'react';
import { api, post } from '../api/client';
import { EmptyState } from '../components/EmptyState';
import { RiskBars } from '../components/RiskBars';
import { StatusBadge } from '../components/StatusBadge';
import type { ApplicationProfile, DemoScenario, ModelProfile, RuntimeResult } from '../types';

interface ContrastResult { customer: RuntimeResult; decision: { decision: string; overall_risk: number; risks: Record<string, number>; triggered_rules: string[] } }

export function Playground({ onCompleted }: { onCompleted: () => void }) {
  const [apps, setApps] = useState<ApplicationProfile[]>([]);
  const [models, setModels] = useState<ModelProfile[]>([]);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [application, setApplication] = useState('customer_support');
  const [modelId, setModelId] = useState('mock-standard');
  const [scenario, setScenario] = useState('safe');
  const [prompt, setPrompt] = useState('What warranty comes with NovaPhone X1?');
  const [sessionId, setSessionId] = useState('demo-live-session');
  const [result, setResult] = useState<RuntimeResult | null>(null);
  const [contrast, setContrast] = useState<ContrastResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api<ApplicationProfile[]>('/applications'), api<ModelProfile[]>('/models'), api<DemoScenario[]>('/demo/scenarios')])
      .then(([appData, modelData, scenarioData]) => { setApps(appData); setModels(modelData); setScenarios(scenarioData); })
      .catch(cause => setError(cause instanceof Error ? cause.message : 'Runtime unavailable'));
  }, []);

  const chooseScenario = (item: DemoScenario) => {
    setScenario(item.id === 'policy_contrast' ? 'hallucination' : item.id);
    setApplication(item.application);
    setModelId(item.model_id);
    setPrompt(item.prompt);
    setResult(null);
    setContrast(null);
  };

  const run = async (policyContrast = false) => {
    setRunning(true); setError(''); setContrast(null);
    try {
      const effectiveScenario = policyContrast ? 'hallucination' : scenario;
      const effectiveApplication = policyContrast ? 'customer_support' : application;
      const response = await post<RuntimeResult>('/chat', { prompt, scenario: effectiveScenario, application: effectiveApplication, model_id: modelId, session_id: sessionId, deep_checks: true });
      setResult(response);
      if (policyContrast) {
        const simulated = await post<ContrastResult['decision']>('/policies/simulate', { application: 'decision_support', risks: response.risks });
        setContrast({ customer: response, decision: simulated });
      }
      onCompleted();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Request failed'); }
    finally { setRunning(false); }
  };

  if (error && !scenarios.length) return <EmptyState title="Playground needs the runtime" copy={`${error}. Start the backend and reload.`} />;

  return <div className="page playground-page">
    <section className="page-title"><div><span className="eyebrow">LIVE ENFORCEMENT</span><h2>Runtime playground</h2><p>Generate a deterministic model response, inspect evidence, then apply the selected application policy.</p></div><span className="demo-pill">DEMO_MODE=true</span></section>
    <div className="scenario-strip">
      {scenarios.map(item => <button key={item.id} className={scenario === (item.id === 'policy_contrast' ? 'hallucination' : item.id) && application === item.application ? 'selected' : ''} onClick={() => chooseScenario(item)}><span>{item.expected}</span><strong>{item.name}</strong></button>)}
    </div>

    <section className="playground-grid">
      <article className="panel controls-panel">
        <div className="panel-head"><div><span className="eyebrow">REQUEST</span><h3>AI application envelope</h3></div></div>
        <label>Application profile<select value={application} onChange={event => setApplication(event.target.value)}>{apps.map(app => <option value={app.id} key={app.id}>{app.name} · {app.risk_tier}</option>)}</select></label>
        <label>Model adapter<select value={modelId} onChange={event => setModelId(event.target.value)}>{models.filter(model => model.provider === 'mock').map(model => <option value={model.id} key={model.id}>{model.model_name}</option>)}</select></label>
        <label>Session ID<input value={sessionId} onChange={event => setSessionId(event.target.value)} /></label>
        <label>Prompt<textarea rows={6} value={prompt} onChange={event => setPrompt(event.target.value)} /></label>
        {error && <p className="error-banner">{error}</p>}
        <button className="primary-button wide" disabled={running} onClick={() => void run(false)}>{running ? 'Evaluating response…' : 'Send through ControlPlane'}</button>
        <button className="contrast-button wide" disabled={running} onClick={() => void run(true)}>Run mandatory policy contrast</button>
        <p className="fine-print">All identities, enterprise data, prices, and decisions in this environment are synthetic.</p>
      </article>

      {!result ? <article className="panel result-placeholder"><EmptyState title="Ready to inspect a model response" copy="Choose a scenario or enter a prompt. Every mandatory demo works without internet or API keys." /></article> :
      <article className="result-stack">
        <section className="panel result-hero">
          <div className="panel-head"><div><span className="eyebrow">TRACE · {result.trace_id}</span><h3>{result.application.name}</h3></div><StatusBadge decision={result.decision} /></div>
          <div className="result-summary"><div><span>Overall risk</span><strong>{Math.round(result.overall_risk * 100)}</strong></div><RiskBars risks={result.risks} compact /></div>
          <div className="response-block"><span>ORIGINAL MODEL OUTPUT</span><p>{result.original_response}</p></div>
          {result.final_response !== result.original_response && <div className="response-block delivered"><span>FINAL DELIVERED OUTPUT</span><p>{result.final_response}</p></div>}
          <div className="rules"><span>TRIGGERED POLICY RULES · {result.policy.name}:v{result.policy.version}</span>{result.triggered_rules.map(reason => <p key={reason}>{reason}</p>)}</div>
        </section>

        {contrast && <section className="panel contrast-panel"><div className="panel-head"><div><span className="eyebrow">MANDATORY PROOF</span><h3>Same response + same detector scores</h3></div><span className="data-label">Different policy outcomes</span></div><div className="contrast-columns"><div><span>Customer support</span><StatusBadge decision={contrast.customer.decision} /><p>Hallucination {contrast.customer.risks.hallucination.toFixed(2)}</p></div><i>→</i><div><span>Decision support</span><StatusBadge decision={contrast.decision.decision} /><p>Hallucination {contrast.decision.risks.hallucination.toFixed(2)}</p></div></div></section>}

        <section className="panel evidence-panel"><div className="panel-head"><div><span className="eyebrow">CLAIMS & EVIDENCE</span><h3>Grounding verification</h3></div><span className="data-label">Local knowledge base</span></div>
          {result.claims.length ? result.claims.map((claim, index) => <div className="claim-row" key={`${claim.claim}-${index}`}><span className={`claim-status claim-${claim.status.toLowerCase()}`}>{claim.status.replace('_', ' ')}</span><div><strong>{claim.claim}</strong><p>{claim.explanation}</p><small>{claim.source_name || 'No source'} · confidence {Math.round(claim.confidence * 100)}%</small>{claim.evidence_snippet && <blockquote>{claim.evidence_snippet}</blockquote>}</div></div>) : <p className="muted-copy">No material factual claims required source verification.</p>}
        </section>

        {result.risks.bias > 0 && <section className="panel evidence-panel"><div className="panel-head"><div><span className="eyebrow">FAIRNESS DIAGNOSTIC</span><h3>Paired counterfactual outputs</h3></div></div><p className="responsible-note">This is a diagnostic consistency signal, not proof of unlawful discrimination.</p>{result.evidence.filter(item => item.source_id.startsWith('counterfactual')).map(item => <div className="counterfactual" key={item.source_id}><strong>{item.source_name}</strong><p>{item.snippet}</p></div>)}</section>}

        <section className="panel trace-panel"><div><span>Model</span><strong>{result.performance.model_latency_ms.toFixed(2)} ms</strong></div><div><span>Tier 0</span><strong>{result.performance.tier0_latency_ms.toFixed(2)} ms</strong></div><div><span>Tier 1</span><strong>{result.performance.tier1_latency_ms.toFixed(2)} ms</strong></div><div><span>Total</span><strong>{result.performance.total_latency_ms.toFixed(2)} ms</strong></div><div><span>AI cost</span><strong>${Number(result.cost.total_ai_cost_usd).toFixed(6)}</strong></div><div><span>Deep check</span><strong>{result.deep_check.status}</strong></div></section>
      </article>}
    </section>
  </div>;
}
