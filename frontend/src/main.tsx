import React, { FormEvent, useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Link, NavLink, Route, Routes, useParams } from 'react-router-dom';
import { api, CaseRecord, DoorstepRecord, Scheme } from './api';
import './styles.css';
import { SchemeCard } from './scheme-card';
import { Assistant, Match, MatchCard } from './assistant';
import { SourceCoverage, SourceList } from './source-list';
import { AuthProvider, Register, SignIn, useAuth } from './auth';
import { Administration } from './admin';
import { AccessGate, PrivateCasePage, PrivateDashboard } from './private-cases';
import {
  SevaDashboard,
  SevaRequestDetail,
  SevaRequestForm,
  SevaWorkerProfile,
  SevaWorkers,
} from './seva';
import { LanguageProvider, useLanguage } from './language';
import { useSessionResults } from './session-results';

function Home() {
  const { tr } = useLanguage();

  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">{tr('INFORMATION. ASSISTANCE. POSSIBILITY.')}</div>
          <h1>
            {tr('A little guidance.')}
            <br />
            {tr('A world of')}
            <br />
            <em>{tr('possibilities.')}</em>
          </h1>
          <p>
            {tr(
              'Find your way to welfare support, understand the next step, and get help closer to home.',
            )}
          </p>
          <Link className="button" to="/schemes">
            {tr('Explore demo schemes ')}
            <span aria-hidden>↗</span>
          </Link>
          <p className="small">{tr('Made for citizens. Built around care.')}</p>
        </div>
        <aside className="hero-art" aria-label={tr('Three simple steps')}>
          <div className="sun" />
          <div className="path" />
          <div className="step">
            <span>01</span>
            <strong>{tr('Discover support')}</strong>
            <p>{tr('Understand your options')}</p>
          </div>
          <div className="step">
            <span>02</span>
            <strong>{tr('Take the next step')}</strong>
            <p>{tr('Ask for application guidance')}</p>
          </div>
          <div className="step">
            <span>03</span>
            <strong>{tr('Stay connected')}</strong>
            <p>{tr('Follow your assistance case')}</p>
          </div>
        </aside>
      </section>
      <section>
        <div className="section-heading">
          <div>
            <div className="eyebrow">{tr('TWO BRIDGES. ONE PURPOSE.')}</div>
            <h2>{tr('Support, wherever you are.')}</h2>
          </div>
          <p>{tr('Simple steps towards a more accessible tomorrow.')}</p>
        </div>
        <div className="grid">
          <article className="card">
            <span className="symbol">↗</span>
            <h2>YojanaSetu</h2>
            <p>
              {tr('A clearer path through scheme information, documents, and assistance tracking.')}
            </p>
            <Link className="text-link" to="/schemes">
              {tr('Find your starting point →')}
            </Link>
          </article>
          <article className="card teal">
            <span className="symbol">⌂</span>
            <h2>SevaSetu</h2>
            <p>
              {tr(
                'Request local doorstep support when navigating digital services feels difficult.',
              )}
            </p>
            <Link className="text-link" to="/doorstep">
              {tr('Explore doorstep assistance →')}
            </Link>
          </article>
        </div>
      </section>
    </>
  );
}
function Schemes() {
  const { tr } = useLanguage();

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
        title={tr('Discover support')}
        text="Browse reviewed official sources and clearly labelled fictional demos. The scheme assistant checks documented conditions with citations."
      />
      <form
        className="search"
        onSubmit={(e) => {
          e.preventDefault();
          setSearch(query);
        }}
      >
        <label htmlFor="search">{tr('Search by topic or category')}</label>
        <div className="row">
          <input
            id="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={tr('Try education, agriculture, wellbeing…')}
            maxLength={100}
          />
          <button>{tr('Search schemes')}</button>
        </div>
      </form>
      <div className="profile-grid">
        <label>
          {tr('Source type')}
          <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
            <option value="all">{tr('All sources')}</option>
            <option value="verified">{tr('Official reviewed sources')}</option>
            <option value="demo">{tr('Fictional demos')}</option>
          </select>
        </label>
        <label>
          {tr('Category')}
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">{tr('All categories')}</option>
            {[...new Set(schemes.map((s) => s.category))].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      {loading ? (
        <p role="status">{tr('Loading schemes…')}</p>
      ) : error ? (
        <ErrorMessage message={error} />
      ) : visible.length ? (
        <div className="grid">
          {visible.map((s) => (
            <SchemeCard key={s.id} scheme={s} />
          ))}
        </div>
      ) : (
        <p>{tr('No schemes found. Try another topic.')}</p>
      )}
    </>
  );
}
function PageTitle({ tag, title, text }: { tag: string; title: string; text: string }) {
  const { tr } = useLanguage();
  return (
    <header className="page-title">
      <div className="eyebrow">{tag}</div>
      <h1>{tr(title)}</h1>
      <p>{tr(text)}</p>
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
  const { tr } = useLanguage();

  return (
    <label>
      {tr('Local development token')}
      <input
        type="password"
        autoComplete="off"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        required
      />
      <small>
        {tr('For local demo use only. Not a citizen login. Token stays in this page’s memory.')}
      </small>
    </label>
  );
}
function Detail() {
  const { tr } = useLanguage();

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
        <p role="status">{error ? tr('Scheme could not be loaded.') : tr('Loading scheme…')}</p>
      ) : (
        <>
          <PageTitle
            tag={scheme.is_demo ? tr('FICTIONAL DEMO SCHEME') : tr('SCHEME INFORMATION')}
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
                    <li>
                      {tr('Not available in the indexed information. Confirm with the department.')}
                    </li>
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
              <h2>{tr('Request private case assistance')}</h2>
              <p>{tr('Create an assistance case owned by your signed-in account.')}</p>
              <Link className="button" to={`/dashboard?scheme=${scheme.id}`}>
                {tr('Begin private assistance →')}
              </Link>
            </section>
          ) : (
            <form className="panel" onSubmit={submit}>
              <h2>{tr('Request assistance')}</h2>
              <p>
                {tr(
                  'Creates a local demo case. No official application, approval or KYC is performed. Do not enter personal information.',
                )}
              </p>
              <TokenField token={token} setToken={setToken} />
              <label>
                {tr('Type of assistance')}
                <select name="assistance">
                  <option value="Understand eligibility">{tr('Understand eligibility')}</option>
                  <option value="Document checklist guidance">
                    {tr('Document checklist guidance')}
                  </option>
                  <option value="Application process guidance">
                    {tr('Application process guidance')}
                  </option>
                </select>
              </label>
              <button disabled={busy}>{busy ? tr('Creating…') : tr('Create demo case')}</button>
              {result && (
                <p role="status">
                  {tr('Case created. Save this reference: ')}
                  <strong>{result}</strong>.{' '}
                  <Link to={`/tracking?case=${result}`}>{tr('Track case →')}</Link>
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
  const { tr } = useLanguage();

  const { user } = useAuth();
  if (user)
    return (
      <>
        <PrivateDashboard />
        <section className="matched-dashboard">
          <h2>{tr('Scheme matches in this session')}</h2>
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
        title={tr('Citizen assistance')}
        text="Sign in to view cases owned by your account, upload documents privately and request internal human assistance."
      />
      <p>
        <Link className="button" to="/login">
          {tr('Sign in to private case assistance')}
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
              {tr('Get started →')}
            </Link>
          </article>
        ))}
      </div>
      <section className="matched-dashboard">
        <h2>{tr('Matches from this session')}</h2>
        <p>
          {tr(
            'Results stay in this tab’s memory. No account or cross-device history is connected.',
          )}
        </p>
        <Link className="text-link" to="/assistant">
          {tr('Ask the scheme assistant →')}
        </Link>
        {matches.length ? (
          matches.map((m, i) => <MatchCard key={`${m.scheme_id}-${i}`} match={m} />)
        ) : (
          <p>{tr('No matches in this active session yet.')}</p>
        )}
      </section>
    </>
  );
}
function Tracking() {
  const { tr, formatDate } = useLanguage();
  const session = useAuth();

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
      setRecord(
        await api<CaseRecord>(
          `/cases/${encodeURIComponent(id.trim())}`,
          token,
          undefined,
          session.user ? { Authorization: `Bearer ${session.token}` } : {},
        ),
      );
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
        title={tr('Track your assistance case')}
        text="Status reflects a local assistance record, not a government application."
      />
      <form className="panel" onSubmit={submit}>
        <label>
          {tr('Case reference')}
          <input
            name="case"
            required
            defaultValue={new URLSearchParams(window.location.search).get('case') || ''}
          />
        </label>
        {!session.user && <TokenField token={token} setToken={setToken} />}
        <button disabled={busy}>{busy ? tr('Checking…') : tr('Check status')}</button>
        {error && <ErrorMessage message={error} />}
      </form>
      {record && (
        <article className="card" role="status">
          <div className="eyebrow">{record.status.replaceAll('_', ' ')}</div>
          <h2>{record.assistance_type}</h2>
          <p>
            {tr('Reference: ')}
            {record.id}
          </p>
          <p>
            {tr('Received: ')}
            {formatDate(record.created_at)}
          </p>
          {session.user ? (
            <Link to={`/my-cases/${record.id}`}>{tr('Open authorized case')}</Link>
          ) : (
            <p>{tr('Human review and automatic updates are not connected.')}</p>
          )}
        </article>
      )}
    </>
  );
}
function Doorstep() {
  const { tr } = useLanguage();

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
        title={tr('Help begins at your doorstep.')}
        text="Explore requesting in-person guidance. Worker assignment and real visits are not available in Phase 1."
      />
      <form className="panel" onSubmit={submit}>
        <p>
          {tr(
            'Use a fictional district. Do not enter a name, phone number, address or identity details.',
          )}
        </p>
        <label>
          {tr('Demo district')}
          <input
            name="district"
            minLength={2}
            maxLength={80}
            required
            placeholder={tr('Example district')}
          />
        </label>
        <label>
          {tr('Support needed')}
          <select name="service_type">
            <option value="Scheme information guidance">{tr('Scheme information guidance')}</option>
            <option value="Digital service guidance">{tr('Digital service guidance')}</option>
            <option value="Document checklist guidance">{tr('Document checklist guidance')}</option>
          </select>
        </label>
        <label>
          {tr('Preferred date')}
          <input type="date" name="preferred_date" min={minDate} required />
        </label>
        <TokenField token={token} setToken={setToken} />
        <button disabled={busy}>{busy ? tr('Saving…') : tr('Save demo request')}</button>
        {error && <ErrorMessage message={error} />}{' '}
        {result && (
          <p role="status">
            {tr('Demo request received: ')}
            <strong>{result}</strong>
            {tr('. This does not book a visit.')}
          </p>
        )}
      </form>
    </>
  );
}
function App() {
  const { tr } = useLanguage();

  const { user, token } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [matches, setMatches] = useSessionResults<Match>(token);
  return (
    <>
      <a className="skip" href="#main">
        {tr('Skip to content')}
      </a>
      <div className="demo-bar">
        {tr(
          'DEVELOPMENT PREVIEW · Demo and official sources are labelled · No government affiliation',
        )}
      </div>
      <header className="site-header">
        <Link className="brand" to="/">
          <span className="brand-icon" aria-hidden>
            ↗
          </span>
          Yojana<span>Setu</span>
        </Link>
        <nav aria-label={tr('Main navigation')}>
          <NavLink to="/schemes">{t('discover')}</NavLink>
          <NavLink to="/assistant">{t('assistant')}</NavLink>
          <NavLink to="/dashboard">{t('assistance')}</NavLink>
          <NavLink to="/tracking">{t('tracking')}</NavLink>
          <NavLink to="/doorstep">{t('doorstep')}</NavLink>
          <NavLink to="/login">{user ? t('account') : t('signIn')}</NavLink>
        </nav>
        <label className="language">
          <span className="sr-only">{tr('Language preview')}</span>
          <select
            data-testid="language-switcher"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
          </select>
        </label>
      </header>
      {language !== 'en' && (
        <p className="language-note" role="status">
          {t('partial')} {tr(' Scheme explanations use English fallback.')}
        </p>
      )}
      <main id="main" lang={language} tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/schemes" element={<Schemes />} />
          <Route path="/sources" element={<SourceCoverage />} />
          <Route path="/schemes/:id" element={<Detail />} />
          <Route
            path="/dashboard"
            element={import.meta.env.PROD ? <PrivateDashboard /> : <Dashboard matches={matches} />}
          />
          <Route path="/assistant" element={<Assistant onMatches={setMatches} />} />
          <Route path="/tracking" element={<Tracking />} />
          <Route
            path="/doorstep"
            element={
              user ? <SevaDashboard /> : import.meta.env.PROD ? <AccessGate /> : <Doorstep />
            }
          />
          <Route path="/seva" element={<SevaDashboard />} />
          <Route path="/seva/new" element={<SevaRequestForm />} />
          <Route path="/seva/requests/:id" element={<SevaRequestDetail />} />
          <Route path="/seva/profile" element={<SevaWorkerProfile />} />
          <Route path="/seva/workers" element={<SevaWorkers />} />
          <Route path="/login" element={<SignIn />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin" element={<Administration />} />
          <Route path="/my-cases/:id" element={<PrivateCasePage />} />
          <Route path="/coordinator" element={<PrivateDashboard coordinator />} />
          <Route
            path="*"
            element={
              <>
                <h1>{tr('Page not found')}</h1>
                <Link to="/">{tr('Return home')}</Link>
              </>
            }
          />
        </Routes>
      </main>
      <footer>
        <Link className="brand" to="/">
          YojanaSetu
        </Link>
        <p>{tr('A bridge to information. A step towards support.')}</p>
        <Link to="/coordinator">{tr('Coordinator workspace →')}</Link>
        <p className="small">
          {tr(
            'Development prototype. No official approvals or submissions. Scheme matching requires local configuration. Document, follow-up and escalation assistance require a signed-in account. SevaSetu visits require coordinator approval and worker acceptance.',
          )}
        </p>
      </footer>
    </>
  );
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
