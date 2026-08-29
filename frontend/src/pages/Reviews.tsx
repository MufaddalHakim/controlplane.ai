'use client';

import { useEffect, useState } from 'react';
import { api, post } from '../api/client';
import { EmptyState } from '../components/EmptyState';
import { RiskBars } from '../components/RiskBars';
import { StatusBadge } from '../components/StatusBadge';
import type { ReviewCase } from '../types';

const actions = ['APPROVE_ORIGINAL', 'APPROVE_EDITED', 'MANUALLY_EDIT', 'BLOCK', 'MARK_FALSE_POSITIVE'];

export function Reviews({ refreshKey = 0, onCompleted }: { refreshKey?: number; onCompleted: () => void }) {
  const [cases, setCases] = useState<ReviewCase[]>([]);
  const [selected, setSelected] = useState<ReviewCase | null>(null);
  const [note, setNote] = useState('Reviewed in synthetic demonstration.');
  const [edited, setEdited] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const result = await api<ReviewCase[]>('/reviews');
      setCases(result);
      setSelected(current => result.find(item => item.id === current?.id) || result[0] || null);
      setError('');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load reviews'); }
  };
  useEffect(() => { void load(); }, [refreshKey]);

  const decide = async (action: string) => {
    if (!selected) return;
    try {
      await post(`/reviews/${selected.id}/decision`, { action, note, edited_response: action === 'MANUALLY_EDIT' ? edited : null, reviewer: 'demo.reviewer' });
      await load(); onCompleted();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Review action failed'); }
  };

  return <div className="page review-page">
    <section className="page-title"><div><span className="eyebrow">HUMAN-IN-THE-LOOP</span><h2>Review console</h2><p>Resolve held outputs with a policy-versioned audit trail and structured feedback.</p></div><span className="demo-pill">{cases.filter(item => item.status === 'pending').length} pending</span></section>
    {error && <p className="error-banner">{error}</p>}
    <section className="review-layout">
      <article className="panel queue-panel"><div className="panel-head"><div><span className="eyebrow">QUEUE</span><h3>Escalated cases</h3></div><button className="ghost-button" onClick={() => void load()}>Refresh</button></div>
        {cases.length ? cases.map(item => <button className={`queue-item ${selected?.id === item.id ? 'selected' : ''}`} key={item.id} onClick={() => { setSelected(item); setEdited(item.proposed_response); }}><div><span className={`priority priority-${item.priority}`}>{item.priority}</span><StatusBadge decision={item.interaction.machine_decision} /></div><strong>{item.interaction.application.replaceAll('_', ' ')}</strong><p>{item.reason}</p><small>{item.id} · {item.status}</small></button>) : <EmptyState title="No review cases" copy="Run the bias or high-risk hallucination scenario in the playground." />}
      </article>
      <article className="panel review-detail">
        {!selected ? <EmptyState title="Select a case" copy="Machine rationale, evidence, and reviewer controls will appear here." /> : <>
          <div className="panel-head"><div><span className="eyebrow">CASE · {selected.id}</span><h3>{selected.interaction.application.replaceAll('_', ' ')}</h3></div><span className={`case-state state-${selected.status}`}>{selected.status}</span></div>
          <div className="review-meta"><span>Policy <b>{selected.interaction.policy.name}:v{selected.interaction.policy.version}</b></span><span>Model <b>{selected.interaction.model}</b></span><span>Session <b>{selected.interaction.session_id}</b></span></div>
          <RiskBars risks={selected.interaction.risks} compact />
          <div className="response-block"><span>MASKED ORIGINAL RESPONSE</span><p>{selected.interaction.original_response}</p></div>
          <div className="response-block delivered"><span>PROPOSED SAFE RESPONSE</span><p>{selected.proposed_response}</p></div>
          <div className="rules"><span>POLICY EXPLANATION</span>{selected.interaction.triggered_rules.map(rule => <p key={rule}>{rule}</p>)}</div>
          {selected.status === 'pending' ? <div className="review-controls"><label>Reviewer note<textarea rows={3} value={note} onChange={event => setNote(event.target.value)} /></label><label>Manual edit<textarea rows={4} value={edited || selected.proposed_response} onChange={event => setEdited(event.target.value)} /></label><div className="review-actions">{actions.map(action => <button className={action === 'BLOCK' ? 'danger-button' : 'ghost-button'} key={action} onClick={() => void decide(action)}>{action.replaceAll('_', ' ')}</button>)}</div></div> : <p className="resolved-banner">This case has been resolved. The machine and final decisions remain in the audit log.</p>}
        </>}
      </article>
    </section>
  </div>;
}
