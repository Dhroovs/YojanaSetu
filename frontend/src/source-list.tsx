import { useLanguage } from './language';
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

export function SourceCoverage() {
  const { tr } = useLanguage();

  const [report, setReport] = useState<{
    source_count: number;
    scheme_count: number;
    schemes: {
      scheme_id: string;
      scheme_name: string;
      requires_reconciliation: boolean;
      sources: {
        source_id: string;
        official_url: string;
        department: string;
        last_verified_at: string;
        completeness: string;
        dated: boolean;
        missing_fields: string[];
      }[];
    }[];
  }>();
  const [error, setError] = useState('');
  useEffect(() => {
    void api<NonNullable<typeof report>>('/ai/coverage')
      .then(setReport)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <header className="page-title">
        <h1>{tr('Official source coverage')}</h1>
        <p>
          {tr(
            'Source provenance is reviewed by an operator. Partial information is not complete eligibility.',
          )}
        </p>
      </header>
      {error && <p role="alert">{error}</p>}
      {!report && !error && <p role="status">{tr('Loading sources…')}</p>}
      {report && (
        <>
          <p>
            {report.source_count} {tr(' source(s) · ')}
            {report.scheme_count} {tr(' scheme(s)')}
          </p>
          {report.schemes.map((scheme) => (
            <section key={scheme.scheme_id} className="panel">
              <h2>{scheme.scheme_name}</h2>
              {scheme.requires_reconciliation && (
                <p>{tr('Multiple sources require human reconciliation.')}</p>
              )}
              {scheme.sources.map((source) => (
                <div key={source.source_id}>
                  <a href={source.official_url} target="_blank" rel="noopener noreferrer">
                    {tr('Read official source')}
                  </a>
                  <p>{source.department}</p>
                  <p>
                    {tr('Last reviewed: ')}
                    {source.last_verified_at} · {source.completeness}
                  </p>
                  <p>
                    {source.dated
                      ? tr('Source may be outdated.')
                      : tr('Review date is within the configured freshness window.')}
                  </p>
                  <p>
                    {tr('Missing fields: ')}
                    {source.missing_fields.join(', ') || 'None recorded'}
                  </p>
                </div>
              ))}
            </section>
          ))}
        </>
      )}
    </>
  );
}
export function SourceList({ schemeId }: { schemeId: string }) {
  const { tr } = useLanguage();

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
      <h2>{tr('Official sources & verification')}</h2>
      {error && <p role="alert">{error}</p>}
      {sources.map((s) => (
        <div key={s.source_id}>
          <a href={s.official_url} target="_blank" rel="noopener noreferrer">
            {s.document_title} ↗
          </a>
          <p>
            {tr('Reviewed ')}
            {s.reviewed_at} · {s.completeness} {tr(' information')}
          </p>
          <p>
            {tr('Publication/update date: ')}
            {s.published_at || 'unknown'}
          </p>
          <small>
            {tr('Document SHA-256: ')}
            {s.content_hash}
          </small>
        </div>
      ))}
      <p>
        {tr(
          'Unknown conditions and required documents need confirmation with the department. A source review is not an eligibility approval.',
        )}
      </p>
    </article>
  );
}
