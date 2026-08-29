'use client';

import { useEffect, useState } from 'react';
import { api, post } from '../api/client';
import { EmptyState } from '../components/EmptyState';
import type { ModelProfile } from '../types';

export function ModelRegistry() {
  const [models, setModels] = useState<ModelProfile[]>([]);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const load = async () => { try { setModels(await api('/models')); setError(''); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load models'); } };
  useEffect(() => { void load(); }, []);
  const calibrate = async (id: string) => { setBusy(id); try { await post(`/models/${id}/calibrate`); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Calibration failed'); } finally { setBusy(''); } };
  if (error && !models.length) return <EmptyState title="Model registry unavailable" copy={error} />;
  return <div className="page models-page">
    <section className="page-title"><div><span className="eyebrow">CAPABILITY-AWARE ONBOARDING</span><h2>Model registry</h2><p>ControlPlane adapts to available provider signals and never invents unavailable telemetry.</p></div><span className="demo-pill">{models.length} registered</span></section>
    {error && <p className="error-banner">{error}</p>}
    <section className="model-grid">{models.map(model => <article className="panel model-card" key={model.id}><div className="model-top"><span className={`provider provider-${model.provider}`}>{model.provider}</span><span className="capability">{model.capability_level.replaceAll('_', ' ')}</span></div><h3>{model.model_name}</h3><p>{model.context_length ? `${model.context_length.toLocaleString()} token context` : 'Context length not supplied'}</p><div className="capability-grid"><span>Usage data<b>{model.usage_available ? 'Available' : 'Unavailable'}</b></span><span>Logprobs<b>{model.logprobs_available ? 'Available' : 'Unavailable'}</b></span><span>Input / 1M<b>${model.pricing.input_per_million_usd.toFixed(2)}</b></span><span>Output / 1M<b>${model.pricing.output_per_million_usd.toFixed(2)}</b></span></div>{model.calibration ? <div className="calibration"><span>CALIBRATED · {new Date(model.calibration.timestamp).toLocaleDateString()}</span><div><b>{model.calibration.baseline_latency_ms.toFixed(2)} ms</b><small>baseline latency</small></div><div><b>{model.calibration.baseline_output_tokens.toFixed(1)}</b><small>baseline tokens</small></div><p>Uncertainty: {String(model.calibration.baseline_uncertainty)}</p></div> : <div className="calibration empty"><p>No calibration baseline stored.</p></div>}<button className="ghost-button wide" disabled={busy === model.id || model.provider !== 'mock'} onClick={() => void calibrate(model.id)}>{busy === model.id ? 'Running 10 prompts…' : model.provider === 'mock' ? 'Calibrate adapter' : 'Configure provider to calibrate'}</button></article>)}</section>
    <p className="responsible-note">Pricing is illustrative and configurable. “Unavailable” means the adapter does not expose that signal; ControlPlane does not synthesize entropy, attention, or logprob statistics.</p>
  </div>;
}
