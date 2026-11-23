export interface Scheme {
  id: string;
  title: string;
  category: string;
  summary: string;
  eligibility: string[];
  documents: string[];
  guidance: string[];
  is_demo: boolean;
  source_url: string | null;
  department?: string | null;
  geographic_coverage?: string[] | null;
  benefits?: string[] | null;
  application_url?: string | null;
  last_verified_at?: string | null;
  information_completeness?: string;
}
export interface CaseRecord {
  id: string;
  scheme_id: string;
  assistance_type: string;
  status: string;
  created_at: string;
}
export interface DoorstepRecord {
  id: string;
  status: string;
}
export async function api<T>(
  path: string,
  token = '',
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<T> {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}${path}`,
    {
      method: body ? 'POST' : 'GET',
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { 'X-Dev-Token': token } : {}),
        ...headers,
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    },
  );
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === 'string'
        ? error.detail
        : `Request failed (${response.status}). Check your entries and try again.`,
    );
  }
  return response.json();
}
