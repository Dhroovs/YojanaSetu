import { useEffect, useState } from 'react';
import { api } from './api';

interface Source {
  source_id: string;
  document_title: string;
  official_url: string;
  reviewed_at: string;
  published_at: string | null;
  content_hash: string;
  completeness: string;
}
export function SourceList({ schemeId }: { schemeId: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api<Source[]>(`/ai/schemes/${encodeURIComponent(schemeId)}/sources`)
      .then((data) => {
        if (active) setSources(data);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [schemeId]);
  return (
    <article className="card">
      <h2>Official sources & verification</h2>
      {error && <p role="alert">{error}</p>}
      {sources.map((s) => (
        <div key={s.source_id}>
          <a href={s.official_url} target="_blank" rel="noopener noreferrer">
            {s.document_title} ↗
          </a>
          <p>
            Reviewed {s.reviewed_at} · {s.completeness} information
          </p>
          <p>Publication/update date: {s.published_at || 'unknown'}</p>
          <small>Document SHA-256: {s.content_hash}</small>
        </div>
      ))}
      <p>
        Unknown conditions and required documents need confirmation with the department. A source
        review is not an eligibility approval.
      </p>
    </article>
  );
}
