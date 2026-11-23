import { useLanguage } from './language';
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, Scheme } from './api';
import { downloadDocument, privateApi, uploadDocument, useAuth } from './auth';
import { MatchCard, Match } from './assistant';

interface Doc {
  id: string;
  item_id: string;
  technical_status: string;
  review_status: string;
  technical_notes: string[];
  review_note: string | null;
  expires_at: string;
  deleted_at: string | null;
}
interface Follow {
  id: string;
  reason: string;
  due_at: string;
  status: string;
  note: string;
}
interface Referral {
  id: string;
  reason: string;
  severity: string;
  status: string;
  resolution_note: string | null;
  owner_coordinator_id: string | null;
}
export interface PrivateCase {
  id: string;
  scheme_id: string;
  stage: string;
  status: string;
  revision: number;
  is_demo: boolean;
  checklist_verified: boolean;
  checklist: { id: string; label: string; source_ids: string[]; is_demo: boolean }[];
  documents: Doc[];
  followups: Follow[];
  reminders: {
    id: string;
    message: string;
    reason: string;
    acknowledged_by: string[];
    created_at: string;
  }[];
  notices?: {
    id: string;
    action: string;
    message: string | null;
    delivered_at: string | null;
    acknowledged_by: string[];
  }[];
  escalations: Referral[];
  activity: { id: string; action: string; note: string; at: string }[];
  missing_information: string[];
  coordinator_id: string | null;
  worker_ids: string[];
  preferences: { in_app: boolean; quiet_start: number; quiet_end: number; language?: string };
  scheme_source_versions: Record<string, string>;
}
interface Page<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
const human = (value: string) => value.replaceAll('_', ' ');
const stages = [
  'draft',
  'documents_pending',
  'ready_for_human_review',
  'assistance_in_progress',
  'waiting_for_external_update',
  'completed',
  'on_hold',
  'escalated',
  'closed',
];

export function AccessGate() {
  const { tr } = useLanguage();

  return (
    <section className="panel">
      <h1>{tr('Private assistance workspace')}</h1>
      <p>
        {tr(
          'Sign in with a provisioned account to access your authorized cases. Official government status integrations are not connected.',
        )}
      </p>
      <Link className="button" to="/login">
        {tr('Sign in')}
      </Link>
    </section>
  );
}

export function PrivateDashboard({ coordinator = false }: { coordinator?: boolean }) {
  const { tr } = useLanguage();

  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [kind, setKind] = useState('cases');
  const [result, setResult] = useState<Page<PrivateCase>>();
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [scheme, setScheme] = useState(
    new URLSearchParams(window.location.search).get('scheme') || '',
  );
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const creationKey = useRef(crypto.randomUUID());
  useEffect(() => {
    if (!user) return;
    let active = true;
    setError('');
    setResult(undefined);
    privateApi<Page<PrivateCase>>(
      token,
      coordinator ? `/coordinator/queue?kind=${kind}&page=${page}` : `/cases?page=${page}`,
    )
      .then((r) => {
        if (active) setResult(r);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [user, token, coordinator, kind, page, refresh]);
  useEffect(() => {
    if (user?.role === 'citizen')
      void api<Scheme[]>('/schemes')
        .then(setSchemes)
        .catch((e) => setError(e.message));
  }, [user]);
  if (!user) return <AccessGate />;
  if (coordinator && user.role === 'citizen')
    return (
      <p role="alert">
        {tr('This workspace requires an assigned worker, coordinator or admin account.')}
      </p>
    );
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">
          {user.role} {tr(' WORKSPACE')}
        </div>
        <h1>
          {coordinator ? tr('Coordinator assistance queue') : tr('My private assistance cases')}
        </h1>
        <p>{tr('Internal support tasks only. “Completed” never means government approval.')}</p>
      </header>
      <p>
        <Link className="button" to="/seva">
          {tr('Open SevaSetu doorstep assistance →')}
        </Link>
      </p>
      {user.role === 'citizen' && !coordinator && (
        <form
          className="panel"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError('');
            try {
              const c = await privateApi<PrivateCase>(
                token,
                '/cases',
                {
                  scheme_id: scheme,
                  assistance_type: 'Document and case guidance',
                },
                creationKey.current,
              );
              navigate(`/my-cases/${c.id}`);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <h2>{tr('Begin an assistance case')}</h2>
          <label>
            {tr('Scheme')}
            <select
              required
              value={scheme}
              onChange={(e) => {
                setScheme(e.target.value);
                creationKey.current = crypto.randomUUID();
              }}
            >
              <option value="">{tr('Choose a scheme')}</option>
              {schemes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                  {s.is_demo ? tr(' · fictional demo') : tr(' · reviewed official source')}
                </option>
              ))}
            </select>
          </label>
          <button disabled={busy}>{busy ? tr('Creating…') : tr('Create my case')}</button>
          <p>
            {tr(
              'Missing source requirements remain unknown; the assistant will ask a coordinator to review them.',
            )}
          </p>
        </form>
      )}
      <div className="row">
        {coordinator && (
          <label>
            {tr('Queue')}
            <select
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                setPage(1);
              }}
            >
              {[
                'cases',
                'reviews',
                'followups',
                'escalations',
                ...(user.role === 'worker' ? [] : ['unassigned']),
              ].map((k) => (
                <option key={k} value={k}>
                  {tr(human(k))}
                </option>
              ))}
            </select>
          </label>
        )}
        <button className="secondary" onClick={() => setRefresh((n) => n + 1)}>
          {tr('Refresh cases')}
        </button>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!result && !error && <p role="status">{tr('Loading authorized cases…')}</p>}
      {result && (
        <>
          <p>
            {result.total} {tr(' case(s)')}
          </p>
          <div className="grid">
            {result.items.map((c) => (
              <article className="card" key={c.id}>
                <div className="eyebrow">{tr(human(c.stage))}</div>
                <h2>{c.scheme_id}</h2>
                <p className="small">
                  {tr('Reference ')}
                  {c.id}
                </p>
                {kind === 'unassigned' ? (
                  <button
                    disabled={busy}
                    onClick={async () => {
                      if (
                        !window.confirm(
                          'Confirm taking responsibility for this unassigned assistance case?',
                        )
                      )
                        return;
                      setBusy(true);
                      try {
                        await privateApi(token, `/cases/${c.id}/assignment`, {
                          revision: c.revision,
                          coordinator_id: user.id,
                          worker_ids: [],
                          confirmed: true,
                          note: 'Coordinator self-claim',
                        });
                        setRefresh((n) => n + 1);
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    {tr('Claim case with confirmation')}
                  </button>
                ) : (
                  <Link className="text-link" to={`/my-cases/${c.id}`}>
                    {tr('Open authorized case →')}
                  </Link>
                )}
              </article>
            ))}
          </div>
          {result.items.length === 0 && <p>{tr('No cases in this queue.')}</p>}
          <div className="row pagination">
            <button disabled={page === 1} onClick={() => setPage((n) => n - 1)}>
              {tr('Previous')}
            </button>
            <span>
              {tr('Page ')}
              {page}
            </span>
            <button disabled={page * 20 >= result.total} onClick={() => setPage((n) => n + 1)}>
              {tr('Next')}
            </button>
          </div>
        </>
      )}
    </>
  );
}

export function PrivateCasePage() {
  const { tr } = useLanguage();

  const { id } = useParams();
  const { user, token } = useAuth();
  const [record, setRecord] = useState<PrivateCase>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number>();
  const [file, setFile] = useState<File>();
  const [item, setItem] = useState('');
  const [note, setNote] = useState('');
  const [target, setTarget] = useState('');
  const [date, setDate] = useState('');
  const [reason, setReason] = useState('manual');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Record<string, unknown>>();
  const [confirmed, setConfirmed] = useState(false);
  const [staff, setStaff] = useState<{ id: string; username: string; role: string }[]>([]);
  const [assignment, setAssignment] = useState('');
  const [workers, setWorkers] = useState<string[]>([]);
  const retryKey = useRef(crypto.randomUUID());
  const actionKeys = useRef(new Map<string, string>());
  const schemeConversation = useRef<string | null>(null);
  const reviewer = user?.role === 'coordinator' || user?.role === 'admin';
  async function load() {
    try {
      setRecord(await privateApi<PrivateCase>(token, `/cases/${id}`));
      setError('');
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    let active = true;
    if (user)
      privateApi<PrivateCase>(token, `/cases/${id}`)
        .then((c) => {
          if (active) setRecord(c);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [id, user, token]);
  useEffect(() => {
    if (user?.role === 'admin')
      void privateApi<{ id: string; username: string; role: string }[]>(token, '/coordinator/staff')
        .then(setStaff)
        .catch((e) => setError(e.message));
  }, [user, token]);
  async function action(path: string, body: Record<string, unknown>) {
    if (!record) return;
    setBusy(true);
    setError('');
    const identity = JSON.stringify([id, path, body]);
    const key = actionKeys.current.get(identity) || crypto.randomUUID();
    actionKeys.current.set(identity, key);
    try {
      const c = await privateApi<PrivateCase>(
        token,
        `/cases/${id}${path}`,
        path.startsWith('/preferences') ? body : { revision: record.revision, ...body },
        key,
      );
      actionKeys.current.delete(identity);
      setRecord(c);
      setNote('');
      setConfirmed(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function assist(text: string, intent = 'auto', apply = false) {
    if (!record) return;
    setBusy(true);
    setError('');
    try {
      const r = await privateApi<{ result: Record<string, unknown>; revision: number }>(
        token,
        `/cases/${id}/assist`,
        {
          question: text,
          intent,
          apply_changes: apply,
          revision: record.revision,
          note: '',
          ...(schemeConversation.current
            ? { scheme_conversation_id: schemeConversation.current }
            : {}),
        },
      );
      if (r.result.match && typeof r.result.match === 'object') {
        schemeConversation.current = (
          r.result.match as { conversation_id: string }
        ).conversation_id;
      }
      setAnswer(r.result);
      if (apply) await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!user) return <AccessGate />;
  if (!record || record.id !== id)
    return (
      <>
        {error ? (
          <p role="alert" className="error">
            {error}
          </p>
        ) : (
          <p role="status">{tr('Loading private assistance case…')}</p>
        )}
      </>
    );
  const c = record;
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">
          {tr('PRIVATE ASSISTANCE · ')}
          {c.is_demo ? tr('FICTIONAL DEMO') : tr('SOURCE-BASED CASE')}
        </div>
        <h1>{c.scheme_id}</h1>
        <p>
          {tr('Reference ')}
          {c.id}
        </p>
        <p className="status-chip">{tr(human(c.stage))}</p>
        <p>
          {tr(
            'Internal completion is not official government approval, legal document authentication or KYC.',
          )}
        </p>
      </header>
      <button className="secondary" disabled={busy} onClick={() => void load()}>
        {tr('Refresh case')}
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {busy && <p role="status">{tr('Saving assistance update…')}</p>}
      <section className="panel">
        <h2>{tr('Next steps & case assistant')}</h2>
        <Link className="text-link" to={`/seva/new?case=${c.id}&scheme=${c.scheme_id}`}>
          {tr('Request consent-based doorstep help for this case →')}
        </Link>
        {c.missing_information.map((m) => (
          <p key={m} className="notice">
            {m}
          </p>
        ))}
        <div className="quick-actions">
          {[
            ['What documents do I still need?', 'documents'],
            ['What is happening with my assistance case?', 'status'],
            ['When is my next follow-up?', 'followup'],
          ].map(([q, i]) => (
            <button className="secondary" disabled={busy} key={i} onClick={() => void assist(q, i)}>
              {tr(q)}
            </button>
          ))}
          <button
            disabled={busy}
            onClick={() =>
              void assist('Please request help from a human coordinator', 'escalation', true)
            }
          >
            {tr('Request human assistance')}
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void assist(question);
          }}
        >
          <label>
            {tr('Ask about this authorized case')}
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              minLength={3}
              maxLength={500}
              required
            />
          </label>
          <button disabled={busy}>{tr('Ask case assistant')}</button>
        </form>
        {answer && (
          <div className="case-answer" aria-live="polite">
            <h3>{tr('From your case record')}</h3>
            {typeof answer.next_action === 'string' && <p>{answer.next_action}</p>}
            {typeof answer.stage === 'string' && (
              <p>
                {tr('Stage: ')}
                {tr(human(answer.stage))}
              </p>
            )}
            {typeof answer.official_status === 'string' && <p>{answer.official_status}</p>}
            {Array.isArray(answer.items) &&
              answer.items.map((i: { id: string; label: string; status: string }) => (
                <p key={i.id}>
                  {i.label}: {tr(human(i.status))}
                </p>
              ))}
            {answer.next_follow_up && typeof answer.next_follow_up === 'object' ? (
              <p>
                {tr('Next follow-up:')}{' '}
                {new Date((answer.next_follow_up as Follow).due_at).toLocaleString()}
              </p>
            ) : null}
            {answer.match && typeof answer.match === 'object'
              ? (answer.match as { recommendations: Match[] }).recommendations.map((m) => (
                  <MatchCard key={m.scheme_id} match={m} />
                ))
              : null}
          </div>
        )}
      </section>
      <section>
        <h2>{tr('Document assistance checklist')}</h2>
        <p>
          {tr(
            'Use redacted or synthetic documents only. Technical quality checks never establish identity or authenticity.',
          )}
        </p>
        {!c.checklist_verified && (
          <p className="notice">
            {tr(
              'This checklist is not verified for an official scheme. A coordinator must review the source requirements before accepting it.',
            )}
          </p>
        )}
        <div className="grid">
          {c.checklist.map((i) => (
            <article className="card" key={i.id}>
              <h3>{i.label}</h3>
              <p className="small">
                {i.is_demo ? tr('Fictional demo item') : `Source: ${i.source_ids.join(', ')}`}
              </p>
              {!c.documents.some((d) => d.item_id === i.id && !d.deleted_at) && (
                <p>{tr('Missing')}</p>
              )}
              {c.documents
                .filter((d) => d.item_id === i.id)
                .map((d) => (
                  <div className="document-row" key={d.id}>
                    <p>
                      {d.deleted_at ? tr('Removed') : human(d.review_status)} ·{' '}
                      {tr(human(d.technical_status))}
                    </p>
                    {d.technical_notes.map((n) => (
                      <p key={n} className="small">
                        {n}
                      </p>
                    ))}
                    {d.review_note && (
                      <p>
                        {tr('Review note: ')}
                        {d.review_note}
                      </p>
                    )}
                    <small>
                      {tr('Retention expires ')}
                      {new Date(d.expires_at).toLocaleDateString()}
                    </small>
                    {!d.deleted_at && (
                      <>
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() =>
                            void downloadDocument(
                              token,
                              `/cases/${id}/documents/${d.id}/content`,
                            ).catch((e) => setError(e.message))
                          }
                        >
                          {tr('Download securely')}
                        </button>
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() => {
                            if (
                              window.confirm(
                                'Delete this private file? Its content will become unavailable.',
                              )
                            )
                              void action(`/documents/${d.id}/delete?confirmed=true`, {
                                note: 'Document removed by authorized user',
                              });
                          }}
                        >
                          {tr('Delete file')}
                        </button>
                        {reviewer && (
                          <div className="review-actions">
                            <button
                              disabled={busy || !note}
                              onClick={() =>
                                void action(`/documents/${d.id}/review`, {
                                  status: 'accepted_for_assistance_checklist',
                                  note,
                                })
                              }
                            >
                              {tr('Accept for assistance checklist')}
                            </button>
                            <button
                              className="secondary"
                              disabled={busy || !note}
                              onClick={() =>
                                void action(`/documents/${d.id}/review`, {
                                  status: 'unreadable',
                                  note,
                                })
                              }
                            >
                              {tr('Mark unreadable')}
                            </button>
                            <button
                              className="secondary"
                              disabled={busy || !note}
                              onClick={() =>
                                void action(`/documents/${d.id}/review`, {
                                  status: 'needs_human_review',
                                  note,
                                })
                              }
                            >
                              {tr('Needs human review')}
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
            </article>
          ))}
        </div>
        {c.checklist.length > 0 && (
          <form
            className="panel"
            onSubmit={async (e) => {
              e.preventDefault();
              if (!file) return;
              if (
                file.size > 10000000 ||
                !['application/pdf', 'image/png', 'image/jpeg'].includes(file.type)
              ) {
                setError('Choose a PDF, PNG or JPEG under 10 MB.');
                return;
              }
              setBusy(true);
              setError('');
              setProgress(0);
              try {
                setRecord(
                  (await uploadDocument(
                    token,
                    `/cases/${id}/documents?item_id=${encodeURIComponent(item)}&revision=${c.revision}`,
                    file,
                    retryKey.current,
                    setProgress,
                  )) as PrivateCase,
                );
                retryKey.current = crypto.randomUUID();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              {tr('Checklist item')}
              <select
                value={item}
                onChange={(e) => {
                  setItem(e.target.value);
                  retryKey.current = crypto.randomUUID();
                }}
                required
              >
                <option value="">{tr('Choose an item')}</option>
                {c.checklist.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {tr('Synthetic or redacted file')}
              <input
                type="file"
                accept="application/pdf,image/jpeg,image/png"
                required
                onChange={(e) => {
                  setFile(e.target.files?.[0]);
                  retryKey.current = crypto.randomUUID();
                }}
              />
            </label>
            <button disabled={busy}>
              {busy && progress !== undefined
                ? `Uploading ${progress}%`
                : tr('Upload securely / retry')}
            </button>
            {progress !== undefined && (
              <progress aria-label={tr('Upload progress')} value={progress} max={100} />
            )}
          </form>
        )}
      </section>
      {reviewer && (
        <section className="panel">
          <h2>{tr('Human review controls')}</h2>
          <label>
            {tr('Review / activity note')}
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={600}
              placeholder={tr(
                'No identity numbers, account details or personal contact information.',
              )}
            />
          </label>
          <label>
            {tr('Assistance stage')}
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">{tr('Choose next stage')}</option>
              {stages.map((s) => (
                <option key={s} value={s}>
                  {tr(human(s))}
                </option>
              ))}
            </select>
          </label>
          <label className="check-label">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            {tr('I confirm this closure, reopening or reassignment.')}
          </label>
          <div className="row">
            <button
              disabled={busy || !target}
              onClick={() =>
                void action('/stage', {
                  stage: target,
                  note,
                  confirmed,
                  reported_external_update: false,
                })
              }
            >
              {tr('Update internal stage')}
            </button>
            <button
              className="secondary"
              disabled={busy || !note}
              onClick={() => void action('/flags', { note })}
            >
              {tr('Flag conflicting information')}
            </button>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void action('/checklist/refresh', { note })}
            >
              {tr('Refresh source checklist')}
            </button>
          </div>
          {user.role === 'admin' && (
            <>
              <label>
                {tr('Assigned coordinator')}
                <select value={assignment} onChange={(e) => setAssignment(e.target.value)}>
                  <option value="">{tr('Choose coordinator')}</option>
                  {staff
                    .filter((s) => s.role !== 'worker')
                    .map((s) => (
                      <option value={s.id} key={s.id}>
                        {s.username} · {s.role}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                {tr('Assigned workers')}
                <select
                  multiple
                  value={workers}
                  onChange={(e) => setWorkers([...e.target.selectedOptions].map((o) => o.value))}
                >
                  {staff
                    .filter((s) => s.role === 'worker')
                    .map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.username}
                      </option>
                    ))}
                </select>
              </label>
              <button
                disabled={busy || !assignment || !confirmed}
                onClick={() =>
                  void action('/assignment', {
                    coordinator_id: assignment,
                    worker_ids: workers,
                    confirmed,
                    note,
                  })
                }
              >
                {tr('Confirm assignment')}
              </button>
            </>
          )}
        </section>
      )}
      <section className="panel">
        <h2>{tr('Follow-ups & in-app reminders')}</h2>
        {(c.notices || [])
          .filter((n) => n.delivered_at)
          .map((n) => (
            <div key={n.id}>
              <p>{n.message}</p>
              <small>{human(n.action)}</small>
              <button
                disabled={busy || n.acknowledged_by.includes(user.id)}
                onClick={() => void action(`/notices/${n.id}/acknowledge`, { note: '' })}
              >
                {n.acknowledged_by.includes(user.id)
                  ? tr('Acknowledged')
                  : tr('Acknowledge update')}
              </button>
            </div>
          ))}
        {c.followups.map((f) => (
          <p key={f.id}>
            {tr(human(f.reason))} · {new Date(f.due_at).toLocaleString()} · {f.status}
          </p>
        ))}
        {c.reminders.map((r) => (
          <div key={r.id} className="notice">
            <p>
              {r.message} · {tr(human(r.reason))}
            </p>
            <button
              disabled={busy || r.acknowledged_by.includes(user.id)}
              onClick={() => void action(`/reminders/${r.id}/acknowledge`, { note: '' })}
            >
              {r.acknowledged_by.includes(user.id) ? tr('Acknowledged') : tr('Acknowledge')}
            </button>
          </div>
        ))}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void action('/followups', { reason, due_at: new Date(date).toISOString(), note: '' });
          }}
        >
          <label>
            {tr('Follow-up type')}
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              {['manual', 'appointment', 'missing_documents', 'coordinator_review'].map((r) => (
                <option value={r} key={r}>
                  {tr(human(r))}
                </option>
              ))}
            </select>
          </label>
          <label>
            {tr('Follow-up date and time (your local time)')}
            <input
              type="datetime-local"
              required
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
          <button disabled={busy}>{tr('Schedule in-app follow-up')}</button>
        </form>
        <PreferencesForm
          record={c}
          save={async (prefs) => {
            await action(`/preferences?revision=${c.revision}`, prefs);
          }}
          busy={busy}
        />
      </section>
      <section className="panel">
        <h2>{tr('Internal human referrals')}</h2>
        {c.escalations.length === 0 && <p>{tr('No escalations recorded.')}</p>}
        {c.escalations.map((e) => (
          <div className="escalation-row" key={e.id}>
            <p>
              {tr(human(e.reason))} · {e.severity} · {e.status}
            </p>
            <p>
              {e.owner_coordinator_id
                ? tr('An authorized coordinator owns this referral.')
                : tr('Awaiting coordinator assignment.')}
            </p>
            {e.resolution_note && <p>{e.resolution_note}</p>}
            {reviewer && (
              <div className="row">
                {e.status === 'open' && (
                  <button
                    disabled={busy}
                    onClick={() =>
                      void action(`/escalations/${e.id}`, { action: 'acknowledge', note })
                    }
                  >
                    {tr('Acknowledge referral')}
                  </button>
                )}
                {e.status !== 'resolved' ? (
                  <button
                    disabled={busy || !note}
                    onClick={() => void action(`/escalations/${e.id}`, { action: 'resolve', note })}
                  >
                    {tr('Resolve with note')}
                  </button>
                ) : (
                  <button
                    disabled={busy || !note}
                    onClick={() => void action(`/escalations/${e.id}`, { action: 'reopen', note })}
                  >
                    {tr('Reopen referral')}
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </section>
      <section className="panel">
        <h2>{tr('Case activity timeline')}</h2>
        <ol>
          {[...c.activity]
            .reverse()
            .slice(0, 30)
            .map((e) => (
              <li key={e.id}>
                <strong>{tr(human(e.action))}</strong>
                <small>{new Date(e.at).toLocaleString()}</small>
                {e.note && <p>{e.note}</p>}
              </li>
            ))}
        </ol>
        <p>
          {tr(
            'Showing up to 30 latest events. Full paginated history is available through the authorized activity API.',
          )}
        </p>
        <details>
          <summary>{tr('Scheme source versions')}</summary>
          {Object.entries(c.scheme_source_versions).map(([s, v]) => (
            <p className="small source-hash" key={s}>
              {s}: {v}
            </p>
          ))}
        </details>
      </section>
    </>
  );
}

function PreferencesForm({
  record,
  save,
  busy,
}: {
  record: PrivateCase;
  save: (p: Record<string, unknown>) => Promise<void>;
  busy: boolean;
}) {
  const { tr } = useLanguage();

  const [enabled, setEnabled] = useState(record.preferences.in_app);
  const [start, setStart] = useState(record.preferences.quiet_start);
  const [end, setEnd] = useState(record.preferences.quiet_end);
  const [noticeLanguage, setNoticeLanguage] = useState(record.preferences.language || 'en');
  return (
    <form
      className="preferences"
      onSubmit={(e) => {
        e.preventDefault();
        void save({
          in_app: enabled,
          quiet_start: start,
          quiet_end: end,
          language: noticeLanguage,
        });
      }}
    >
      <h3>{tr('Notification preferences')}</h3>
      <label>
        {tr('Notification language')}
        <select value={noticeLanguage} onChange={(e) => setNoticeLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
          <option value="te">తెలుగు</option>
        </select>
      </label>
      <label className="check-label">
        <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
        {tr('In-app notifications')}
      </label>
      <div className="profile-grid">
        <label>
          {tr('Quiet hours start (IST, 0–23)')}
          <input
            type="number"
            min={0}
            max={23}
            required
            value={start}
            onChange={(e) => setStart(Number(e.target.value))}
          />
        </label>
        <label>
          {tr('Quiet hours end (IST, 0–23)')}
          <input
            type="number"
            min={0}
            max={23}
            required
            value={end}
            onChange={(e) => setEnd(Number(e.target.value))}
          />
        </label>
      </div>
      <button disabled={busy}>{tr('Save reminder preferences')}</button>
      <p>{tr('No SMS or WhatsApp messages are sent.')}</p>
    </form>
  );
}
