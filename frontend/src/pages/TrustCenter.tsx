'use client';

import { useEffect, useState } from 'react';
import { api, post } from '../api/client';
import { EmptyState } from '../components/EmptyState';

interface Evaluation {
  status: string;
  run_id?: string;
  case_count?: number;
  detectors: Record<string, { precision: number; recall: number; f1: number; false_positive_rate: number; false_negative_rate: number; tp: number; tn: number; fp: number; fn: number }>;
  threshold_analysis: Array<{ threshold: number; precision: number; recall: number; false_positive_rate: number; false_negative_rate: number; review_escalation_rate: number }>;
  latency?: { mean_ms: number; p50_ms: number; p95_ms: number };
}

export function TrustCenter() {
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [risks, setRisks] = useState<Record<string, any> | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const load = async () => { try { const [evaluationData, riskData] = await Promise.all([api<Evaluation>('/analytics/evaluation'), api<Record<string, any>>('/analytics/risks')]); setEvaluation(evaluationData); setRisks(riskData); setError(''); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load trust metrics'); } };
  useEffect(() => { void load(); }, []);
  const run = async () => { setRunning(true); try { await post('/evaluation/run'); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Evaluation failed'); } finally { setRunning(false); } };
  if (error && !evaluation) return <EmptyState title="Trust Center unavailable" copy={error} />;
  return <div className="page trust-page">
    <section className="page-title"><div><span className="eyebrow">MEASURABLE TRUST</span><h2>Analytics & Trust Center</h2><p>Actual detector outcomes, latency, drift, and alert-fatigue tradeoffs—not fabricated KPIs.</p></div><button className="primary-button" disabled={running} onClick={() => void run()}>{running ? 'Running 80 cases…' : 'Run evaluation dataset'}</button></section>
    {error && <p className="error-banner">{error}</p>}
    {!evaluation || evaluation.status === 'not_run' ? <EmptyState title="No evaluation run yet" copy="Run the labeled local dataset to calculate TP, TN, FP, FN, precision, recall, F1, and measured latency." /> : <>
      <section className="evaluation-hero"><div><span>RUN</span><strong>{evaluation.run_id}</strong></div><div><span>CASES EXECUTED</span><strong>{evaluation.case_count}</strong></div><div><span>P95 DETECTOR LATENCY</span><strong>{evaluation.latency?.p95_ms.toFixed(3)} ms</strong></div><div><span>METHODOLOGY</span><strong>Actual local runs</strong></div></section>
      <section className="detector-grid">{Object.entries(evaluation.detectors).map(([name, metric]) => <article className="panel detector-card" key={name}><div className="panel-head"><div><span className="eyebrow">DETECTOR</span><h3>{name}</h3></div><strong className="f1-score">{Math.round(metric.f1 * 100)}</strong></div><div className="metric-pairs"><span>Precision<b>{metric.precision.toFixed(3)}</b></span><span>Recall<b>{metric.recall.toFixed(3)}</b></span><span>FPR<b>{metric.false_positive_rate.toFixed(3)}</b></span><span>FNR<b>{metric.false_negative_rate.toFixed(3)}</b></span></div><p>TP {metric.tp} · TN {metric.tn} · FP {metric.fp} · FN {metric.fn}</p></article>)}</section>
      <section className="trust-grid"><article className="panel threshold-card"><div className="panel-head"><div><span className="eyebrow">ALERT FATIGUE EXPERIMENT</span><h3>Privacy threshold tradeoff</h3></div><span className="data-label">Measured</span></div><div className="table-wrap"><table><thead><tr><th>Threshold</th><th>Precision</th><th>Recall</th><th>FPR</th><th>Review volume</th></tr></thead><tbody>{evaluation.threshold_analysis.map(row => <tr key={row.threshold}><td>{row.threshold.toFixed(2)}</td><td>{row.precision.toFixed(3)}</td><td>{row.recall.toFixed(3)}</td><td>{row.false_positive_rate.toFixed(3)}</td><td><div className="mini-bar"><i style={{ width: `${row.review_escalation_rate * 100}%` }} /></div>{Math.round(row.review_escalation_rate * 100)}%</td></tr>)}</tbody></table></div><p className="responsible-note">Lower thresholds catch more labeled risks but can increase reviewer volume. Higher thresholds reduce volume while increasing missed-case risk.</p></article>
      <article className="panel drift-card"><div className="panel-head"><div><span className="eyebrow">ROLLING MONITOR</span><h3>Distribution drift</h3></div></div>{risks?.drift?.length ? risks.drift.map((item: any) => <div className="drift-row" key={item.dimension}><div><strong>{item.dimension}</strong><small>{item.significant ? 'Significant shift' : 'Within baseline range'}</small></div><span className={item.significant ? 'shifted' : ''}>{item.absolute_shift > 0 ? '+' : ''}{item.absolute_shift.toFixed(3)}</span></div>) : <p className="muted-copy">More stored interactions are needed to compare baseline and current windows.</p>}<p className="fine-print">Method: difference in rolling-window means. Monitoring signal only; it does not block traffic.</p></article></section>
    </>}
  </div>;
}
