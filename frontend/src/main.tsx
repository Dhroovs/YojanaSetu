import React, { FormEvent, useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Link, NavLink, Route, Routes, useParams } from 'react-router-dom';
import { api, CaseRecord, DoorstepRecord, Scheme } from './api';
import './styles.css';
import { SchemeCard } from './scheme-card';
import { Assistant, Match, MatchCard } from './assistant';
import { SourceList } from './source-list';
import { AuthProvider, SignIn, useAuth } from './auth';
import { PrivateCasePage, PrivateDashboard } from './private-cases';

function Home() {
  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">INFORMATION. ASSISTANCE. POSSIBILITY.</div>
          <h1>
            A little guidance.
            <br />A world of
            <br />
            <em>possibilities.</em>
          </h1>
          <p>
            Find your way to welfare support, understand the next step, and get help closer to home.
          </p>
          <Link className="button" to="/schemes">
            Explore demo schemes <span aria-hidden>↗</span>
          </Link>
          <p className="small">Made for citizens. Built around care.</p>
        </div>
        <aside className="hero-art" aria-label="Three simple steps">
          <div className="sun" />
          <div className="path" />
          <div className="step">
            <span>01</span>
            <strong>Discover support</strong>
            <p>Understand your options</p>
          </div>
          <div className="step">
            <span>02</span>
            <strong>Take the next step</strong>
            <p>Ask for application guidance</p>
          </div>
          <div className="step">
            <span>03</span>
            <strong>Stay connected</strong>
            <p>Follow your assistance case</p>
          </div>
        </aside>
      </section>
      <section>
        <div className="section-heading">
          <div>
            <div className="eyebrow">TWO BRIDGES. ONE PURPOSE.</div>
            <h2>Support, wherever you are.</h2>
          </div>
          <p>Simple steps towards a more accessible tomorrow.</p>
        </div>
        <div className="grid">
          <article className="card">
            <span className="symbol">↗</span>
            <h2>YojanaSetu</h2>
            <p>A clearer path through scheme information, documents, and assistance tracking.</p>
            <Link className="text-link" to="/schemes">
              Find your starting point →
            </Link>
          </article>
          <article className="card teal">
            <span className="symbol">⌂</span>
            <h2>SevaSetu</h2>
            <p>Request local doorstep support when navigating digital services feels difficult.</p>
            <Link className="text-link" to="/doorstep">
              Explore doorstep assistance →
            </Link>
          </article>
        </div>
      </section>
    </>
  );
}
function Schemes() {
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [dataset, setDataset] = useState('all');
  const [category, setCategory] = useState('');
  const visible = schemes.filter(
    (s) =>
      (dataset === 'all' || (dataset === 'demo' ? s.is_demo : !s.is_demo)) &&
      (!category || s.category === category),
  );
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    api<Scheme[]>(`/schemes?q=${encodeURIComponent(search)}`)
      .then((data) => {
        if (active) setSchemes(data);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [search]);
  return (
    <>
      <PageTitle
        tag="FIND YOUR STARTING POINT"
        title="Discover support"
        text="Browse reviewed official sources and clearly labelled fictional demos. The scheme assistant checks documented conditions with citations."
      />
      <form
        className="search"
        onSubmit={(e) => {
          e.preventDefault();
          setSearch(query);
        }}
      >
        <label htmlFor="search">Search by topic or category</label>
        <div className="row">
          <input
            id="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Try education, agriculture, wellbeing…"
            maxLength={100}
          />
          <button>Search schemes</button>
        </div>
      </form>
      <div className="profile-grid">
        <label>
          Source type
          <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
            <option value="all">All sources</option>
            <option value="verified">Official reviewed sources</option>
            <option value="demo">Fictional demos</option>
          </select>
        </label>
        <label>
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {[...new Set(schemes.map((s) => s.category))].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      {loading ? (
        <p role="status">Loading schemes…</p>
      ) : error ? (
        <ErrorMessage message={error} />
      ) : visible.length ? (
        <div className="grid">
          {visible.map((s) => (
            <SchemeCard key={s.id} scheme={s} />
          ))}
        </div>
      ) : (
        <p>No schemes found. Try another topic.</p>
      )}
    </>
  );
}
function PageTitle({ tag, title, text }: { tag: string; title: string; text: string }) {
  return (
    <header className="page-title">
      <div className="eyebrow">{tag}</div>
      <h1>{title}</h1>
      <p>{text}</p>
    </header>
  );
}
function ErrorMessage({ message }: { message: string }) {
  return (
    <p className="error" role="alert">
      {message}
    </p>
  );
}
function TokenField({ token, setToken }: { token: string; setToken: (s: string) => void }) {
  return (
    <label>
      Local development token
      <input
        type="password"
        autoComplete="off"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        required
      />
      <small>
        For local demo use only. Not a citizen login. Token stays in this page’s memory.
      </small>
    </label>
  );
}
function Detail() {
  const { user } = useAuth();
  const { id } = useParams();
  const [scheme, setScheme] = useState<Scheme>();
  const [error, setError] = useState('');
  const [token, setToken] = useState('');
  const [result, setResult] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    setScheme(undefined);
    setError('');
    api<Scheme>(`/schemes/${encodeURIComponent(id || '')}`)
      .then((s) => {
        if (active) setScheme(s);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id]);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    setResult('');
    const data = new FormData(e.currentTarget);
    try {
      const r = await api<CaseRecord>('/cases', token, {
        scheme_id: id,
        assistance_type: data.get('assistance'),
      });
      setResult(r.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      {error && <ErrorMessage message={error} />}{' '}
      {!scheme ? (
        <p role="status">{error ? 'Scheme could not be loaded.' : 'Loading scheme…'}</p>
      ) : (
        <>
          <PageTitle
            tag={scheme.is_demo ? 'FICTIONAL DEMO SCHEME' : 'SCHEME INFORMATION'}
            title={scheme.title}
            text={scheme.summary}
          />
          {!scheme.is_demo && <SourceList schemeId={scheme.id} />}
          <div className="grid">
            {[
              [
                scheme.is_demo ? 'Example eligibility' : 'Documented conditions',
                scheme.eligibility,
              ],
              [
                scheme.is_demo ? 'Example documents' : 'Required documents (known)',
                scheme.documents,
              ],
              ['How to get started', scheme.guidance],
            ].map(([title, items]) => (
              <article className="card" key={title as string}>
                <h2>{title}</h2>
                <ul>
                  {(items as string[]).length === 0 && (
                    <li>Not available in the indexed information. Confirm with the department.</li>
                  )}
                  {(items as string[]).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
          {user ? (
            <section className="panel">
              <h2>Request private case assistance</h2>
              <p>Create an assistance case owned by your signed-in account.</p>
              <Link className="button" to={`/dashboard?scheme=${scheme.id}`}>
                Begin private assistance →
              </Link>
            </section>
          ) : (
            <form className="panel" onSubmit={submit}>
              <h2>Request assistance</h2>
              <p>
                Creates a local demo case. No official application, approval or KYC is performed. Do
                not enter personal information.
              </p>
              <TokenField token={token} setToken={setToken} />
              <label>
                Type of assistance
                <select name="assistance">
                  <option>Understand eligibility</option>
                  <option>Document checklist guidance</option>
                  <option>Application process guidance</option>
                </select>
              </label>
              <button disabled={busy}>{busy ? 'Creating…' : 'Create demo case'}</button>
              {result && (
                <p role="status">
                  Case created. Save this reference: <strong>{result}</strong>.{' '}
                  <Link to={`/tracking?case=${result}`}>Track case →</Link>
                </p>
              )}
            </form>
          )}
        </>
      )}
    </>
  );
}
function Dashboard({ matches }: { matches: Match[] }) {
  const { user } = useAuth();
  if (user)
    return (
      <>
        <PrivateDashboard />
        <section className="matched-dashboard">
          <h2>Scheme matches in this session</h2>
          {matches.map((m, i) => (
            <MatchCard key={`${m.scheme_id}-${i}`} match={m} />
          ))}
        </section>
      </>
    );
  return (
    <>
      <PageTitle
        tag="YOUR NEXT STEP"
        title="Citizen assistance"
        text="Sign in to view cases owned by your account, upload documents privately and request internal human assistance."
      />
      <p>
        <Link className="button" to="/login">
          Sign in to private case assistance
        </Link>
      </p>
      <div className="grid">
        {[
          ['Discover schemes', 'Read example eligibility and document checklists.', '/schemes'],
          ['Track a case', 'Use your case reference and local development token.', '/tracking'],
          ['Help at your doorstep', 'Try the SevaSetu request workflow.', '/doorstep'],
        ].map(([title, text, url]) => (
          <article className="card" key={url}>
            <h2>{title}</h2>
            <p>{text}</p>
            <Link className="text-link" to={url}>
              Get started →
            </Link>
          </article>
        ))}
      </div>
      <section className="matched-dashboard">
        <h2>Matches from this session</h2>
        <p>Results stay in this tab’s memory. No account or cross-device history is connected.</p>
        <Link className="text-link" to="/assistant">
          Ask the scheme assistant →
        </Link>
        {matches.length ? (
          matches.map((m, i) => <MatchCard key={`${m.scheme_id}-${i}`} match={m} />)
        ) : (
          <p>No matches in this active session yet.</p>
        )}
      </section>
    </>
  );
}
function Tracking() {
  const [token, setToken] = useState('');
  const [record, setRecord] = useState<CaseRecord>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setRecord(undefined);
    setError('');
    const id = new FormData(e.currentTarget).get('case') as string;
    try {
      setRecord(await api<CaseRecord>(`/cases/${encodeURIComponent(id.trim())}`, token));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        tag="STAY CONNECTED"
        title="Track your assistance case"
        text="Status reflects a local assistance record, not a government application."
      />
      <form className="panel" onSubmit={submit}>
        <label>
          Case reference
          <input
            name="case"
            required
            defaultValue={new URLSearchParams(window.location.search).get('case') || ''}
          />
        </label>
        <TokenField token={token} setToken={setToken} />
        <button disabled={busy}>{busy ? 'Checking…' : 'Check status'}</button>
        {error && <ErrorMessage message={error} />}
      </form>
      {record && (
        <article className="card" role="status">
          <div className="eyebrow">{record.status.replaceAll('_', ' ')}</div>
          <h2>{record.assistance_type}</h2>
          <p>Reference: {record.id}</p>
          <p>Received: {new Date(record.created_at).toLocaleString()}</p>
          <p>Human review and automatic updates are not connected.</p>
        </article>
      )}
    </>
  );
}
function Doorstep() {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    setError('');
    setResult('');
    try {
      const r = await api<DoorstepRecord>(
        '/doorstep-requests',
        token,
        Object.fromEntries(
          ['district', 'service_type', 'preferred_date'].map((k) => [k, data.get(k)]),
        ),
      );
      setResult(r.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const today = new Date();
  const minDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  return (
    <>
      <PageTitle
        tag="SEVASETU · CLOSER TO HOME"
        title="Help begins at your doorstep."
        text="Explore requesting in-person guidance. Worker assignment and real visits are not available in Phase 1."
      />
      <form className="panel" onSubmit={submit}>
        <p>
          Use a fictional district. Do not enter a name, phone number, address or identity details.
        </p>
        <label>
          Demo district
          <input
            name="district"
            minLength={2}
            maxLength={80}
            required
            placeholder="Example district"
          />
        </label>
        <label>
          Support needed
          <select name="service_type">
            <option>Scheme information guidance</option>
            <option>Digital service guidance</option>
            <option>Document checklist guidance</option>
          </select>
        </label>
        <label>
          Preferred date
          <input type="date" name="preferred_date" min={minDate} required />
        </label>
        <TokenField token={token} setToken={setToken} />
        <button disabled={busy}>{busy ? 'Saving…' : 'Save demo request'}</button>
        {error && <ErrorMessage message={error} />}{' '}
        {result && (
          <p role="status">
            Demo request received: <strong>{result}</strong>. This does not book a visit.
          </p>
        )}
      </form>
    </>
  );
}
function App() {
  const { user } = useAuth();
  const [language, setLanguage] = useState('en');
  const [matches, setMatches] = useState<Match[]>([]);
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <div className="demo-bar">
        DEVELOPMENT PREVIEW · Demo and official sources are labelled · No government affiliation
      </div>
      <header className="site-header">
        <Link className="brand" to="/">
          <span className="brand-icon" aria-hidden>
            ↗
          </span>
          Yojana<span>Setu</span>
        </Link>
        <nav aria-label="Main navigation">
          <NavLink to="/schemes">Discover</NavLink>
          <NavLink to="/assistant">Scheme assistant</NavLink>
          <NavLink to="/dashboard">My assistance</NavLink>
          <NavLink to="/tracking">Track case</NavLink>
          <NavLink to="/doorstep">SevaSetu</NavLink>
          <NavLink to="/login">{user ? 'My account' : 'Sign in'}</NavLink>
        </nav>
        <label className="language">
          <span className="sr-only">Language preview</span>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
          </select>
        </label>
      </header>
      {language !== 'en' && (
        <p className="language-note" role="status">
          {language === 'hi' ? 'हिन्दी अनुवाद अभी उपलब्ध नहीं है।' : 'తెలుగు అనువాదం ఇంకా అందుబాటులో లేదు.'}{' '}
          Translation is not connected; content remains in English.
        </p>
      )}
      <main id="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/schemes" element={<Schemes />} />
          <Route path="/schemes/:id" element={<Detail />} />
          <Route path="/dashboard" element={<Dashboard matches={matches} />} />
          <Route path="/assistant" element={<Assistant onMatches={setMatches} />} />
          <Route path="/tracking" element={<Tracking />} />
          <Route path="/doorstep" element={<Doorstep />} />
          <Route path="/login" element={<SignIn />} />
          <Route path="/my-cases/:id" element={<PrivateCasePage />} />
          <Route path="/coordinator" element={<PrivateDashboard coordinator />} />
          <Route
            path="*"
            element={
              <>
                <h1>Page not found</h1>
                <Link to="/">Return home</Link>
              </>
            }
          />
        </Routes>
      </main>
      <footer>
        <Link className="brand" to="/">
          YojanaSetu
        </Link>
        <p>A bridge to information. A step towards support.</p>
        <Link to="/coordinator">Coordinator workspace →</Link>
        <p className="small">
          Development prototype. No official approvals or submissions. Scheme matching requires
          local configuration. Document, follow-up and escalation assistance require a signed-in
          account. Doorstep coordination is not connected.
        </p>
      </footer>
    </>
  );
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
