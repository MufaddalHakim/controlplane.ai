function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function toYaml(value: unknown, indent = 0): string {
  const pad = ' '.repeat(indent);
  if (Array.isArray(value)) {
    return value.map(item => `${pad}- ${isRecord(item) || Array.isArray(item) ? `\n${toYaml(item, indent + 2)}` : String(item)}`).join('\n');
  }
  if (isRecord(value)) {
    return Object.entries(value).map(([key, item]) => isRecord(item) || Array.isArray(item)
      ? `${pad}${key}:\n${toYaml(item, indent + 2)}`
      : `${pad}${key}: ${String(item)}`).join('\n');
  }
  return `${pad}${String(value)}`;
}
