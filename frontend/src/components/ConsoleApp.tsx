'use client';

import { useEffect, useState } from 'react';
import { api, post } from '../api/client';
import { AuditExplorer } from '../pages/AuditExplorer';
import { Dashboard } from '../pages/Dashboard';
import { ModelRegistry } from '../pages/ModelRegistry';
import { Playground } from '../pages/Playground';
import { PolicyStudio } from '../pages/PolicyStudio';
import { Reviews } from '../pages/Reviews';
import { TrustCenter } from '../pages/TrustCenter';
import type { PageId } from '../types';

const navigation: Array<{ id: PageId; label: string; code: string; group: string }> = [
  { id: 'overview', label: 'Overview', code: 'OV', group: 'Runtime' },
  { id: 'playground', label: 'Live playground', code: 'PG', group: 'Runtime' },
  { id: 'reviews', label: 'Review queue', code: 'RQ', group: 'Runtime' },
  { id: 'policies', label: 'Policy studio', code: 'PS', group: 'Runtime' },
  { id: 'trust', label: 'Trust center', code: 'TC', group: 'Trust operations' },
  { id: 'models', label: 'Model registry', code: 'MR', group: 'Trust operations' },
  { id: 'audit', label: 'Audit explorer', code: 'AE', group: 'Trust operations' },
];

export function ConsoleApp() {
  const [page, setPage] = useState<PageId>('overview');
  const [healthy, setHealthy] = useState(false);
  const [pending, setPending] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [resetting, setResetting] = useState(false);
  const sync = () => {
    void api<{ status: string }>('/health').then(() => setHealthy(true)).catch(() => setHealthy(false));
    void api<Array<{ status: string }>>('/reviews').then(rows => setPending(rows.filter(row => row.status === 'pending').length)).catch(() => setPending(0));
  };
  useEffect(sync, [refreshKey]);
  const completed = () => { setRefreshKey(value => value + 1); };
  const reset = async () => { setResetting(true); try { await post('/demo/reset'); completed(); setPage('overview'); } finally { setResetting(false); } };

  const title = navigation.find(item => item.id === page)?.label || 'Overview';
  return <main className="app-shell">
    <aside className="sidebar">
      <button className="brand" onClick={() => setPage('overview')}><span className="brand-mark">CP</span><span>ControlPlane<span>.ai</span></span></button>
      {['Runtime', 'Trust operations'].map(group => <div className="nav-group" key={group}><p className="nav-label">{group}</p><nav>{navigation.filter(item => item.group === group).map(item => <button className={page === item.id ? 'active' : ''} key={item.id} onClick={() => setPage(item.id)}><span>{item.code}</span>{item.label}{item.id === 'reviews' && pending > 0 && <b>{pending}</b>}</button>)}</nav></div>)}
      <div className="runtime-status"><i className={healthy ? '' : 'offline'} /><div><strong>{healthy ? 'Runtime healthy' : 'Runtime offline'}</strong><span>Demo mode · zero keys</span></div></div>
    </aside>

    <section className="workspace">
      <header className="topbar"><div><p>AI risk operations</p><h1>{title}</h1></div><div className="top-actions"><span className="live"><i className={healthy ? '' : 'offline'} />{healthy ? 'Live telemetry' : 'Awaiting runtime'}</span><button className="reset-button" disabled={resetting || !healthy} onClick={() => void reset()}>{resetting ? 'Resetting…' : 'Reset demo'}</button><button onClick={() => setPage('playground')}>Run scenario</button></div></header>
      <div className="content">
        {page === 'overview' && <Dashboard refreshKey={refreshKey} onOpenPlayground={() => setPage('playground')} />}
        {page === 'playground' && <Playground onCompleted={completed} />}
        {page === 'reviews' && <Reviews refreshKey={refreshKey} onCompleted={completed} />}
        {page === 'policies' && <PolicyStudio onCompleted={completed} />}
        {page === 'trust' && <TrustCenter />}
        {page === 'models' && <ModelRegistry />}
        {page === 'audit' && <AuditExplorer refreshKey={refreshKey} />}
      </div>
    </section>
  </main>;
}
