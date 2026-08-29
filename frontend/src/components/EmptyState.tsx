export function EmptyState({ title, copy }: { title: string; copy: string }) {
  return <div className="empty-state"><span>CP</span><h3>{title}</h3><p>{copy}</p></div>;
}
