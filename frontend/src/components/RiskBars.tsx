const labels: Record<string, string> = { hallucination: 'Hallucination', privacy: 'Privacy', bias: 'Bias / fairness', safety: 'Safety', cost: 'Cost' };

export function RiskBars({ risks, compact = false }: { risks: Record<string, number>; compact?: boolean }) {
  return <div className={`risk-bars ${compact ? 'compact' : ''}`}>
    {Object.entries(labels).map(([key, label]) => {
      const value = risks[key] || 0;
      return <div className="risk-line" key={key}>
        <div><span>{label}</span><strong>{Math.round(value * 100)}%</strong></div>
        <div className="risk-track"><i className={value >= .8 ? 'critical' : value >= .5 ? 'elevated' : ''} style={{ width: `${Math.max(1, value * 100)}%` }} /></div>
      </div>;
    })}
  </div>;
}
