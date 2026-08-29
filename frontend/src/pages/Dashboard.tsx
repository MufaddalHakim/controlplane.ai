'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import { EmptyState } from '../components/EmptyState';
import { RiskBars } from '../components/RiskBars';
import { StatusBadge } from '../components/StatusBadge';
import type { Summary } from '../types';

const fmt = (value: number, digits = 0) => value.toLocaleString(undefined, { maximumFractionDigits: digits });

export function Dashboard({ refreshKey = 0, onOpenPlayground }: { refreshKey?: number; onOpenPlayground: () => void }) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [riskData, setRiskData] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [summaryResult, risks] = await Promise.all([
        api<Summary>('/analytics/summary'),
        api<Record<string, any>>('/analytics/risks'),
      ]);
      setSummary(summaryResult);
      setRiskData(risks);
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Runtime unavailable');
    }
  }, []);

  useEffect(() => { void load(); }, [load, refreshKey]);

  if (error) return <EmptyState title="Connect the ControlPlane runtime" copy={`${error}. Start the FastAPI service on port 8000, then refresh this page.`} />;
  if (!summary || !riskData) return <div className="loading-panel">Loading protected interaction telemetry…</div>;

  const metrics = [
    ['Requests protected', fmt(summary.requests), 'stored audit traces'],
    ['Pass rate', `${fmt(summary.passed / Math.max(1, summary.requests) * 100, 1)}%`, `${fmt(summary.passed)} allowed`],
    ['Interventions', fmt(summary.requests - summary.passed), `${fmt((summary.requests - summary.passed) / Math.max(1, summary.requests) * 100, 1)}% of traffic`],
    ['P95 overhead', `${fmt(summary.p95_controlplane_latency_ms, 1)} ms`, 'measured locally'],
    ['Review rate', `${fmt(summary.review_rate * 100, 1)}%`, `${fmt(summary.held)} held`],
    ['AI spend', `$${fmt(summary.ai_spend_usd, 4)}`, 'illustrative pricing'],
  ];

  return <div className="page dashboard-page">
    <section className="hero">
      <div><span className="eyebrow">CONTROLPLANE RUNTIME</span><h2>Policy enforcement for<br />enterprise AI, in real time.</h2><p>Inspect, explain, and intervene before model output reaches the real world.</p></div>
      <div className="hero-signal"><span>Current posture</span><strong>All applications protected</strong><p>3 policy profiles · zero-key demo · measured telemetry</p><button className="link-button" onClick={onOpenPlayground}>Run deterministic demo →</button></div>
    </section>

    <section className="metric-grid six">
      {metrics.map(([label, value, detail]) => <article className="metric" key={label}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>)}
    </section>

    <section className="dashboard-grid">
      <article className="panel chart-panel">
        <div className="panel-head"><div><span className="eyebrow">INTERVENTION MIX</span><h3>Runtime decisions</h3></div><span className="data-label">Actual audit data</span></div>
        <div className="decision-chart">
          {(['ALLOW', 'WARN', 'EDIT', 'HOLD', 'BLOCK'] as const).map(decision => {
            const count = summary.intervention_mix[decision] || 0;
            const height = Math.max(5, count / Math.max(1, summary.requests) * 100);
            return <div className="decision-column" key={decision}><span>{count}</span><div><i className={`fill-${decision.toLowerCase()}`} style={{ height: `${height}%` }} /></div><small>{decision}</small></div>;
          })}
        </div>
      </article>

      <article className="panel risk-overview">
        <div className="panel-head"><div><span className="eyebrow">RISK POSTURE</span><h3>Average detector score</h3></div><strong className="score-number">{Math.round(summary.average_risk * 100)}</strong></div>
        <RiskBars risks={riskData.averages || {}} />
      </article>
    </section>

    <section className="dashboard-grid lower">
      <article className="panel incidents-panel">
        <div className="panel-head"><div><span className="eyebrow">RECENT ACTIVITY</span><h3>Protected interactions</h3></div><button className="ghost-button" onClick={() => void load()}>Refresh</button></div>
        <div className="table-wrap"><table><thead><tr><th>Trace</th><th>Application</th><th>Decision</th><th>Risk</th><th>Latency</th></tr></thead><tbody>
          {summary.recent_incidents.map(item => <tr key={item.id}><td><code>{item.trace_id}</code></td><td>{item.application.replaceAll('_', ' ')}</td><td><StatusBadge decision={item.decision} /></td><td>{Math.round(item.overall_risk * 100)}%</td><td>{item.latency.total.toFixed(1)} ms</td></tr>)}
        </tbody></table></div>
      </article>
      <article className="panel app-health">
        <div className="panel-head"><div><span className="eyebrow">APPLICATION HEALTH</span><h3>One runtime, distinct policies</h3></div></div>
        {summary.application_health.map(app => <div className="health-row" key={app.application}><div><strong>{app.application.replaceAll('_', ' ')}</strong><small>{app.requests} requests</small></div><div><span>Avg risk {Math.round(app.average_risk * 100)}%</span><span>Intervene {Math.round(app.intervention_rate * 100)}%</span></div></div>)}
      </article>
    </section>
  </div>;
}
