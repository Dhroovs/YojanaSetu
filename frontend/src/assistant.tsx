import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from './api';
import { useOptionalAuth } from './auth';

export interface Evidence {
  chunk_id: string;
  source_id: string;
  document_title: string;
  official_url: string;
  page: number | null;
  quote: string;
  retrieved_at: string;
  published_at: string | null;
  verification_status: string;
  content_hash: string;
}
export interface Match {
  scheme_id: string;
  scheme_name: string;
  status: string;
  conditions: { field: string; outcome: string; explanation: string; citation: Evidence }[];
  evidence: Evidence[];
  warnings: string[];
  completeness: string;
}
interface Reply {
  conversation_id: string;
  profile: Record<string, string | number | boolean | null>;
  message: string;
  recommendations: Match[];
  follow_up_questions: string[];
  warnings: string[];
  mode: string;
  disclaimer: string;
}
const sessionKey = crypto.randomUUID().replaceAll('-', '');

export function CitationView({ evidence }: { evidence: Evidence }) {
  return (
    <details className="citation">
      <summary>
        {evidence.document_title}
        {evidence.page ? ` · page ${evidence.page}` : ' · web source'}
      </summary>
      <blockquote>{evidence.quote}</blockquote>
      <a href={evidence.official_url} target="_blank" rel="noopener noreferrer">
        Read official source ↗
      </a>
      <small>
        Retrieved {new Date(evidence.retrieved_at).toLocaleDateString()}. Publication/update date:{' '}
        {evidence.published_at || 'unknown'}.
      </small>
      {evidence.verification_status === 'synthetic' && (
        <strong>Synthetic test document — not government information.</strong>
      )}
    </details>
  );
}

export function MatchCard({ match }: { match: Match }) {
  return (
    <article className="card match-card">
      <div className="eyebrow">SOURCE-BASED GUIDANCE · {match.completeness} INFORMATION</div>
      <h2>{match.scheme_name}</h2>
      <p className={`status-chip ${match.status.startsWith('Not eligible') ? 'excluded' : ''}`}>
        {match.status}
      </p>
      {match.warnings.map((w) => (
        <p className="notice" key={w}>
          {w}
        </p>
      ))}
      {match.conditions.map((condition, i) => (
        <div className="condition" key={`${condition.field}-${i}`}>
          <p>{condition.explanation}</p>
          <CitationView evidence={condition.citation} />
        </div>
      ))}
      <h3>Supporting source excerpts</h3>
      {match.evidence.map((e) => (
        <CitationView key={e.chunk_id} evidence={e} />
      ))}
      <Link className="text-link" to={`/schemes/${match.scheme_id}`}>
        View scheme details →
      </Link>
      <p>
        <Link className="text-link" to={`/seva/new?scheme=${match.scheme_id}`}>
          Explore in-person assistance for this scheme →
        </Link>
      </p>
    </article>
  );
}

export function Assistant({ onMatches }: { onMatches: (matches: Match[]) => void }) {
  const session = useOptionalAuth();
  const [question, setQuestion] = useState('');
  const [token, setToken] = useState('');
  const [profile, setProfile] = useState<Record<string, string>>({});
  const [dirtyFields, setDirtyFields] = useState<Set<string>>(new Set());
  const [reply, setReply] = useState<Reply>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [turns, setTurns] = useState<{ question: string; message: string }[]>([]);
  function update(field: string, value: string) {
    setProfile((p) => ({ ...p, [field]: value }));
    setDirtyFields((fields) => new Set(fields).add(field));
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setBusy(true);
    const values = Object.fromEntries(
      Object.entries(profile)
        .filter(([k]) => dirtyFields.has(k))
        .map(([k, v]) => [
          k,
          v === ''
            ? null
            : k === 'age' || k === 'household_income'
              ? Number(v)
              : v === 'true'
                ? true
                : v === 'false'
                  ? false
                  : v,
        ]),
    );
    try {
      const response = await api<Reply>(
        reply ? '/ai/scheme-chat' : '/ai/scheme-match',
        token,
        { question, profile: values, ...(reply ? { conversation_id: reply.conversation_id } : {}) },
        { 'X-Session-Key': sessionKey },
      );
      setReply(response);
      onMatches(response.recommendations);
      setTurns((t) => [...t.slice(-7), { question, message: response.message }]);
      setQuestion('');
      // Parsed values are shown for correction; nothing is written to browser storage.
      setProfile(
        Object.fromEntries(
          Object.entries(response.profile)
            .filter(([, v]) => v !== null)
            .map(([k, v]) => [k, String(v)]),
        ),
      );
      setDirtyFields(new Set());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const optionalBooleans = [
    'student',
    'employed',
    'farming',
    'disability',
    'landholding_family',
    'institutional_landholder',
    'family_income_taxpayer',
  ];
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">YOJANASETU · SCHEME ASSISTANT</div>
        <h1>Let’s find your next step.</h1>
        <p>
          Ask about scheme support and inspect the source evidence. This is preliminary guidance,
          never official approval.
        </p>
      </header>
      <p className="notice">
        Local development only. Do not enter names, Aadhaar numbers, bank details, contact
        information or document images. English is supported; Hindi/Telugu translation is not
        connected.
      </p>
      <section className="panel">
        <h2>Ask about an assistance case</h2>
        <p>
          Document checklists, recorded case progress, follow-ups and human referrals use only your
          authorized case record.
        </p>
        <Link className="text-link" to={session?.user ? '/dashboard' : '/login'}>
          {session?.user
            ? 'Choose my case and ask the case assistant →'
            : 'Sign in for private case assistance →'}
        </Link>
      </section>
      {turns.length > 0 && (
        <section className="conversation" aria-label="Conversation">
          {turns.map((turn, i) => (
            <div key={i}>
              <p>
                <strong>You:</strong> {turn.question}
              </p>
              <p>
                <strong>Assistant:</strong> {turn.message}
              </p>
            </div>
          ))}
        </section>
      )}
      <form className="panel assistant-form" onSubmit={submit}>
        <label>
          Local development token
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="off"
            required
          />
        </label>
        <details>
          <summary>Optional profile · share only what is needed</summary>
          <p>
            Approximate values are enough. Leave unknown fields blank. Documented conditions
            determine which follow-up questions are asked.
          </p>
          <div className="profile-grid">
            <label>
              State of residence
              <input
                value={profile.state || ''}
                maxLength={60}
                onChange={(e) => update('state', e.target.value)}
              />
            </label>
            <label>
              Age
              <input
                type="number"
                min="0"
                max="120"
                value={profile.age || ''}
                onChange={(e) => update('age', e.target.value)}
              />
            </label>
            <label>
              Annual household income (₹)
              <input
                type="number"
                min="0"
                max="1000000000"
                value={profile.household_income || ''}
                onChange={(e) => update('household_income', e.target.value)}
              />
            </label>
            <label>
              Occupation
              <input
                value={profile.occupation || ''}
                maxLength={80}
                onChange={(e) => update('occupation', e.target.value)}
              />
            </label>
            {optionalBooleans.map((field) => (
              <label key={field}>
                {field.replaceAll('_', ' ')}
                {field === 'disability' ? ' (voluntary)' : ''}
                <select
                  value={profile[field] || ''}
                  onChange={(e) => update(field, e.target.value)}
                >
                  <option value="">Not supplied / unknown</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </label>
            ))}
          </div>
        </details>
        <label>
          Your question
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            minLength={3}
            maxLength={1500}
            required
            rows={3}
            placeholder="I am a farmer from Telangana. What support might be relevant?"
          />
        </label>
        <div className="row">
          <button disabled={busy}>
            {busy ? 'Checking source evidence…' : reply ? 'Ask follow-up' : 'Find relevant schemes'}
          </button>
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={() => {
              setReply(undefined);
              setTurns([]);
              setProfile({});
              setDirtyFields(new Set());
              setError('');
              setQuestion('');
              onMatches([]);
            }}
          >
            Start new conversation
          </button>
        </div>
        {busy && <p role="status">Retrieving documents and checking cited conditions…</p>}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </form>
      {reply && (
        <section aria-label="Assistant results" aria-live="polite">
          <p className="eyebrow">{reply.mode}</p>
          <p>{reply.disclaimer}</p>
          {reply.warnings.map((w) => (
            <p className="notice" key={w}>
              {w}
            </p>
          ))}
          {reply.follow_up_questions.length > 0 && (
            <div className="panel">
              <h2>To check the documented conditions</h2>
              <p>Use the profile fields above to answer or correct these details.</p>
              {reply.follow_up_questions.map((q) => (
                <p key={q}>{q}</p>
              ))}
            </div>
          )}
          <div className="match-list">
            {reply.recommendations.map((match, i) => (
              <MatchCard key={`${match.scheme_id}-${i}`} match={match} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}
