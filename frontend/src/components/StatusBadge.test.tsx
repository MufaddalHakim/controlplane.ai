import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('uses explicit hold-for-review wording', () => {
    const html = renderToStaticMarkup(<StatusBadge decision="HOLD" />);
    expect(html).toContain('Hold for review');
    expect(html).toContain('status-hold');
  });
});
