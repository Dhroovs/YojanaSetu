import { afterEach, expect, test, vi } from 'vitest';
import { api } from './api';

afterEach(() => vi.unstubAllGlobals());

test('case submission sends token in a header and serializes the request', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 'case' }) });
  vi.stubGlobal('fetch', fetchMock);
  expect(await api('/cases', 'local-token', { scheme_id: 'demo' })).toEqual({ id: 'case' });
  const [url, options] = fetchMock.mock.calls[0];
  expect(url).not.toContain('local-token');
  expect(options.method).toBe('POST');
  expect(options.headers['X-Dev-Token']).toBe('local-token');
  expect(JSON.parse(options.body)).toEqual({ scheme_id: 'demo' });
});

test('API access errors are shown without reporting success', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Case services disabled' }),
    }),
  );
  await expect(api('/cases/example')).rejects.toThrow('Case services disabled');
});

test('non-JSON gateway errors use a readable fallback', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => {
        throw new Error('not JSON');
      },
    }),
  );
  await expect(api('/schemes')).rejects.toThrow('Request failed (503)');
});
