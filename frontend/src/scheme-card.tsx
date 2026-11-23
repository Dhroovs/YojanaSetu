import { Link } from 'react-router-dom';
import { Scheme } from './api';

export function SchemeCard({ scheme }: { scheme: Scheme }) {
  return (
    <article className="card">
      <div className="eyebrow">
        {scheme.category} · {scheme.is_demo ? 'Fictional demo' : 'Source review required'}
      </div>
      <h2>{scheme.title}</h2>
      <p>{scheme.summary}</p>
      <Link className="text-link" to={`/schemes/${scheme.id}`}>
        Explore scheme <span aria-hidden>↗</span>
      </Link>
    </article>
  );
}
