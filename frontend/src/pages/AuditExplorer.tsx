'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { EmptyState } from '../components/EmptyState';
import { RiskBars } from '../components/RiskBars';
import { StatusBadge } from '../components/StatusBadge';
import type { Incident } from '../types';

export function AuditExplorer({ refreshKey = 0 }: { refreshKey?: number }) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [application, setApplication] = useState('');
  const [decision, setDecision] = useState('');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const load = async () => { try { const rows = await api<Incident[]>('/incidents?limit=250'); setIncidents(rows); setSelected(current => rows.find(row => row.id === current?.id) || rows[0] || null); setError(''); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load audit traces'); } };
  useEffect(() => { void load(); }, [refreshKey]);
  const filtered = useMemo(() => incidents.filter(item => (!application || item.application === application) && (!decision || item.decision === decision) && (!search || `${item.trace_id} ${item.session_id} ${item.model}`.toLowerCase().includes(search.toLowerCase()))), [incidents, application, decision, search]);
  if (error && !incidents.length) return <EmptyState title="Audit explorer unavailable" copy={error} />;
  return <div className="page audit-page">
    <section className="page-title"><div><span className="eyebrow">TRACEABLE BY DEFAULT</span><h2>Audit explorer</h2><p>Masked content, detector execution, policy version, model usage, and final disposition for every request.</p></div><span className="demo-pill">raw retention off</span></section>
    <section className="audit-filters"><input placeholder="Search trace, session, or model" value={search} onChange={event => setSearch(event.target.value)} /><select value={application} onChange={event => setApplication(event.target.value)}><option value="">All applications</option><option value="customer_support">Customer support</option><option value="internal_copilot">Internal copilot</option><option value="decision_support">Decision support</option></select><select value={decision} onChange={event => setDecision(event.target.value)}><option value="">All decisions</option>{['ALLOW','WARN','EDIT','HOLD','BLOCK'].map(value => <option key={value}>{value}</option>)}</select><button className="ghost-button" onClick={() => void load()}>Refresh</button></section>
    <section className="audit-layout"><article className="panel audit-list"><div className="table-wrap"><table><thead><tr><th>Trace</th><th>Application</th><th>Decision</th><th>Risk</th><th>Time</th></tr></thead><tbody>{filtered.map(item => <tr className={selected?.id === item.id ? 'selected' : ''} key={item.id} onClick={() => setSelected(item)}><td><code>{item.trace_id}</code></td><td>{item.application.replaceAll('_',' ')}</td><td><StatusBadge decision={item.decision} /></td><td>{Math.round(item.overall_risk * 100)}%</td><td>{new Date(item.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</td></tr>)}</tbody></table></div></article>
      <article className="panel audit-detail">{!selected ? <EmptyState title="No matching trace" copy="Adjust the filters or run a playground scenario." /> : <><div className="panel-head"><div><span className="eyebrow">{selected.trace_id}</span><h3>{selected.application.replaceAll('_',' ')}</h3></div><StatusBadge decision={selected.decision} /></div><div className="review-meta"><span>Policy <b>{selected.policy.name}:v{selected.policy.version}</b></span><span>Model <b>{selected.model}</b></span><span>Session <b>{selected.session_id}</b></span></div><RiskBars risks={selected.risks} compact /><div className="response-block"><span>MASKED AUDIT RESPONSE</span><p>{selected.original_response}</p></div><div className="trace-grid"><span>Model tokens<b>{selected.tokens.input + selected.tokens.output}</b></span><span>Tier 0<b>{selected.latency.tier0.toFixed(3)} ms</b></span><span>Tier 1<b>{selected.latency.tier1.toFixed(3)} ms</b></span><span>Total<b>{selected.latency.total.toFixed(3)} ms</b></span></div><div className="rules"><span>DECISION EXPLANATION</span>{selected.triggered_rules.map(rule => <p key={rule}>{rule}</p>)}</div><p className="fine-print">Sensitive values are masked in ordinary telemetry. A SHA-256 response hash supports correlation without retaining raw secrets.</p></>}</article>
    </section>
  </div>;
}
