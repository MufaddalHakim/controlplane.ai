'use client';

import { useEffect, useMemo, useState } from 'react';
import { api, post, put } from '../api/client';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';
import type { PolicyRecord } from '../types';
import { toYaml } from '../utils/yaml';

export function PolicyStudio({ onCompleted }: { onCompleted: () => void }) {
  const [policies, setPolicies] = useState<PolicyRecord[]>([]);
  const [selected, setSelected] = useState('customer_support');
  const [configText, setConfigText] = useState('');
  const [risks, setRisks] = useState({ privacy: .72, hallucination: .35, bias: .18, safety: .05, cost: .11 });
  const [simulation, setSimulation] = useState<{ decision: string; overall_risk: number; triggered_rules: string[] } | null>(null);
  const [message, setMessage] = useState('');

  const load = async () => {
    const records = await api<PolicyRecord[]>('/policies');
    setPolicies(records);
    const active = records.find(item => item.id === selected) || records[0];
    if (active) setConfigText(JSON.stringify(active.config, null, 2));
  };
  useEffect(() => { void load(); }, []);
  const active = policies.find(item => item.id === selected);
  const parsed = useMemo(() => { try { return JSON.parse(configText); } catch { return null; } }, [configText]);

  const selectPolicy = (id: string) => {
    setSelected(id);
    const record = policies.find(item => item.id === id);
    if (record) setConfigText(JSON.stringify(record.config, null, 2));
    setSimulation(null);
  };
  const save = async () => {
    if (!parsed) return setMessage('Fix JSON syntax before saving.');
    try {
      const updated = await put<PolicyRecord>(`/policies/${selected}`, { config: parsed, change_note: 'Thresholds updated in Policy Studio' });
      setMessage(`Saved ${selected}:v${updated.version}`); await load(); onCompleted();
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : 'Save failed'); }
  };
  const simulate = async () => {
    try { setSimulation(await post('/policies/simulate', { application: selected, risks })); }
    catch (cause) { setMessage(cause instanceof Error ? cause.message : 'Simulation failed'); }
  };

  if (!active) return <EmptyState title="Loading policy registry" copy="Policy versions and thresholds are loading from the backend." />;
  return <div className="page policy-page">
    <section className="page-title"><div><span className="eyebrow">GOVERNANCE AS CODE</span><h2>Policy studio</h2><p>Version application-specific thresholds without coupling governance to a model provider.</p></div><span className="demo-pill">{active.id}:v{active.version}</span></section>
    <div className="policy-tabs">{policies.map(record => <button key={record.id} className={selected === record.id ? 'selected' : ''} onClick={() => selectPolicy(record.id)}><span>{record.config.metadata?.risk_tier}</span>{record.config.display_name || record.id}</button>)}</div>
    <section className="policy-grid">
      <article className="panel policy-editor"><div className="panel-head"><div><span className="eyebrow">EDITABLE CONFIG</span><h3>Versioned policy document</h3></div><button className="primary-button" onClick={() => void save()}>Save new version</button></div><textarea className="code-editor" value={configText} onChange={event => setConfigText(event.target.value)} spellCheck={false} />{message && <p className="message-banner">{message}</p>}</article>
      <div className="policy-side">
        <article className="panel simulator"><div className="panel-head"><div><span className="eyebrow">POLICY SIMULATOR</span><h3>Test a risk vector</h3></div>{simulation && <StatusBadge decision={simulation.decision} />}</div>
          {Object.entries(risks).map(([key, value]) => <label className="range-input" key={key}><span>{key}<b>{value.toFixed(2)}</b></span><input type="range" min="0" max="1" step="0.01" value={value} onChange={event => setRisks(current => ({ ...current, [key]: Number(event.target.value) }))} /></label>)}
          <button className="contrast-button wide" onClick={() => void simulate()}>Evaluate policy</button>
          {simulation && <div className="simulation-result"><strong>Overall risk {simulation.overall_risk.toFixed(2)}</strong>{simulation.triggered_rules.map(rule => <p key={rule}>{rule}</p>)}</div>}
        </article>
        <article className="panel yaml-preview"><div className="panel-head"><div><span className="eyebrow">SOURCE PREVIEW</span><h3>YAML representation</h3></div></div><pre>{parsed ? toYaml(parsed) : 'Invalid JSON'}</pre></article>
      </div>
    </section>
  </div>;
}
