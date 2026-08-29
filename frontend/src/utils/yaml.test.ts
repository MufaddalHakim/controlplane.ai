import { describe, expect, it } from 'vitest';
import { toYaml } from './yaml';

describe('toYaml', () => {
  it('renders nested policy thresholds deterministically', () => {
    const rendered = toYaml({ application: 'decision_support', rules: { privacy: { review: 0.65 } } });
    expect(rendered).toContain('application: decision_support');
    expect(rendered).toContain('review: 0.65');
  });
});
