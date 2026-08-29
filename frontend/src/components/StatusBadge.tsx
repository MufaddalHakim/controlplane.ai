import type { Decision } from '../types';

export function StatusBadge({ decision }: { decision: Decision | string }) {
  return <span className={`status-badge status-${decision.toLowerCase()}`}>{decision === 'HOLD' ? 'Hold for review' : decision}</span>;
}
