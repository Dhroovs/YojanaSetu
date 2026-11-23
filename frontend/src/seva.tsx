import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { privateApi, useAuth } from './auth';
import { AccessGate } from './private-cases';

interface Window {
  start: string;
  end: string;
}
interface Booking {
  id: string;
  category: string;
  stage: string;
  revision: number;
  description: string;
  owner_id: string;
  coordinator_id: string | null;
  worker_id: string | null;
  preferred_window: Window;
  appointment: Window | null;
  location: { district: string; mandal: string; village: string; address: string };
  assignment_accepted: boolean;
  outcome: {
    note: string;
    services_performed: string[];
    documents_assisted: string[];
    reviewed_by: string | null;
  } | null;
  citizen_confirmed: boolean;
  feedback: { rating: number; note: string } | null;
  audit: { id: string; action: string; note: string; at: string }[];
  notifications: {
    id: string;
    kind: string;
    message?: string;
    delivered_at: string | null;
    acknowledged_by: string[];
  }[];
  escalations: { id: string; reason: string; status: string }[];
}
interface Worker {
  id: string;
  display_name: string;
  revision: number;
  verification_status: string;
  verification_expires_at: string | null;
  availability: Window[];
  current_workload: number;
  capacity: number;
  verification_label: string;
}
interface Page<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
interface Candidate {
  worker_id: string;
  display_name: string;
  workload: number;
  reasons: string[];
}
const names: Record<string, string> = {
  scheme_guidance: 'Scheme guidance',
  document_assistance: 'Document checklist help',
  digital_assistance: 'Digital service guidance',
  accessibility_support: 'Accessibility support',
};
const readable = (value: string) => value.replaceAll('_', ' ');
const time = (value: string) =>
  new Date(value).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
const iso = (value: string) => new Date(value).toISOString();

export function SevaDashboard() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [rows, setRows] = useState<Page<Booking>>();
  const [page, setPage] = useState(1);
  const [unassigned, setUnassigned] = useState(false);
  const [stage, setStage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    if (!user) return;
    let active = true;
    setRows(undefined);
    privateApi<Page<Booking>>(
      token,
      `/seva/requests?page=${page}&unassigned=${unassigned}&stage=${encodeURIComponent(stage)}`,
    )
      .then((v) => {
        if (active) setRows(v);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [user, token, page, unassigned, stage, refresh]);
  if (!user) return <AccessGate />;
  const staff = user.role === 'coordinator' || user.role === 'admin';
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">SEVASETU · AUTHORIZED IN-PERSON ASSISTANCE</div>
        <h1>
          {user.role === 'worker'
            ? 'My assigned visits'
            : staff
              ? 'Doorstep coordination'
              : 'Help closer to home'}
        </h1>
        <p>
          No government affiliation, MeeSeva authorization or scheme approval is implied.
          Appointments require worker acceptance.
        </p>
      </header>
      <div className="quick-actions">
        {user.role === 'citizen' && (
          <Link className="button" to="/seva/new">
            Request doorstep assistance
          </Link>
        )}
        {user.role === 'worker' && (
          <Link className="button" to="/seva/profile">
            My worker profile & availability
          </Link>
        )}
        {staff && (
          <Link className="button" to="/seva/workers">
            Worker verification & availability
          </Link>
        )}
      </div>
      <div className="profile-grid">
        <label>
          Status filter
          <select
            value={stage}
            onChange={(e) => {
              setStage(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All authorized requests</option>
            {[
              'pending_coordinator_review',
              'approved_for_assignment',
              'worker_assigned',
              'visit_scheduled',
              'visit_in_progress',
              'completion_pending_review',
              'visit_completed',
              'follow_up_required',
              'no_worker_available',
              'no_show',
              'escalated',
              'closed',
              'cancelled',
            ].map((s) => (
              <option key={s} value={s}>
                {readable(s)}
              </option>
            ))}
          </select>
        </label>
        {staff && (
          <label className="check-label">
            <input
              type="checkbox"
              checked={unassigned}
              onChange={(e) => {
                setUnassigned(e.target.checked);
                setPage(1);
              }}
            />
            Show minimal unclaimed request queue
          </label>
        )}
      </div>
      <button
        className="secondary"
        onClick={() => {
          setError('');
          setRefresh((v) => v + 1);
        }}
      >
        Refresh visits
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!rows && !error && <p role="status">Loading authorized requests…</p>}
      {rows && (
        <>
          <p>{rows.total} request(s)</p>
          <div className="grid">
            {rows.items.map((b) => (
              <article className="card" key={b.id}>
                <div className="eyebrow">{readable(b.stage)}</div>
                <h2>{names[b.category]}</h2>
                {b.appointment && (
                  <p>
                    {time(b.appointment.start)}–{time(b.appointment.end)} IST
                  </p>
                )}
                {unassigned ? (
                  <button
                    disabled={busy}
                    onClick={async () => {
                      if (!window.confirm('Confirm taking responsibility for this request?'))
                        return;
                      setBusy(true);
                      try {
                        await privateApi(token, `/seva/requests/${b.id}/actions`, {
                          action: 'claim',
                          confirmed: true,
                          revision: b.revision,
                          note: 'Coordinator self-claim',
                        });
                        setRefresh((v) => v + 1);
                        setUnassigned(false);
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Claim request with confirmation
                  </button>
                ) : (
                  <Link className="text-link" to={`/seva/requests/${b.id}`}>
                    Open visit request →
                  </Link>
                )}
              </article>
            ))}
          </div>
          {rows.total === 0 && (
            <p>No requests in this queue. No availability or booking is assumed.</p>
          )}
          <div className="row pagination">
            <button disabled={page === 1} onClick={() => setPage((v) => v - 1)}>
              Previous
            </button>
            <span>Page {page}</span>
            <button disabled={page * 20 >= rows.total} onClick={() => setPage((v) => v + 1)}>
              Next
            </button>
          </div>
        </>
      )}
      {staff && (
        <p>
          <button className="secondary" onClick={() => navigate('/coordinator')}>
            Open case assistance queue
          </button>
        </p>
      )}
    </>
  );
}

export function SevaRequestForm() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const key = useRef(crypto.randomUUID());
  if (!user) return <AccessGate />;
  if (user.role !== 'citizen')
    return <p role="alert">Citizens submit requests owned by their own account.</p>;
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">SEVASETU</div>
        <h1>Request in-person guidance</h1>
        <p>
          Use synthetic details during development. Never enter Aadhaar, OTPs, bank credentials or
          identity images.
        </p>
      </header>
      <form
        className="panel"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError('');
          const data = new FormData(e.currentTarget);
          try {
            const result = await privateApi<Booking>(
              token,
              '/seva/requests',
              {
                category: data.get('category'),
                scheme_id: data.get('scheme') || null,
                case_id: data.get('case') || null,
                description: data.get('description'),
                preferred_window: {
                  start: iso(String(data.get('start'))),
                  end: iso(String(data.get('end'))),
                },
                location: {
                  district: data.get('district'),
                  mandal: data.get('mandal'),
                  village: data.get('village'),
                  address: data.get('address'),
                },
                accessibility: data.getAll('accessibility'),
                language: data.get('language'),
                caregiver_present:
                  data.get('caregiver') === '' ? null : data.get('caregiver') === 'true',
                contact_preference: 'in_app',
                share_with_assigned_worker: data.get('consent') === 'on',
              },
              key.current,
            );
            navigate(`/seva/requests/${result.id}`);
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Assistance category
          <select name="category">
            {Object.entries(names).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label>
          Known scheme identifier (optional)
          <input
            name="scheme"
            maxLength={80}
            defaultValue={new URLSearchParams(location.search).get('scheme') || ''}
          />
        </label>
        <label>
          My related case reference (optional)
          <input
            name="case"
            maxLength={80}
            defaultValue={new URLSearchParams(location.search).get('case') || ''}
          />
        </label>
        <label>
          What help is needed?
          <textarea name="description" minLength={5} maxLength={600} required />
        </label>
        <div className="profile-grid">
          <label>
            Preferred start (your local time)
            <input type="datetime-local" name="start" required />
          </label>
          <label>
            Preferred end (15 minutes–4 hours later)
            <input type="datetime-local" name="end" required />
          </label>
          {['district', 'mandal', 'village'].map((field) => (
            <label key={field}>
              {readable(field)}
              <input name={field} minLength={2} maxLength={80} required />
            </label>
          ))}
        </div>
        <label>
          Address details for the assigned worker
          <input name="address" minLength={5} maxLength={300} required />
        </label>
        <p>
          Map coordinates are optional through the API with separate explicit consent; this form
          does not request or track your device location.
        </p>
        <label>
          Preferred service language
          <select name="language">
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
          </select>
        </label>
        <p>
          Worker language matching is supported; the interface and scheme explanations remain
          primarily English.
        </p>
        <fieldset>
          <legend>Accessibility support (optional)</legend>
          {['wheelchair_access', 'hearing_support', 'reading_help', 'caregiver_support'].map(
            (a) => (
              <label className="check-label" key={a}>
                <input type="checkbox" name="accessibility" value={a} />
                {readable(a)}
              </label>
            ),
          )}
        </fieldset>
        <label>
          Will a caregiver or family member be present?
          <select name="caregiver">
            <option value="">Not specified</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
        <p>Contact preference: in-app only. No paid messaging is connected.</p>
        <label className="check-label">
          <input type="checkbox" name="consent" required />I consent to sharing necessary booking
          details with the assigned worker.
        </label>
        <button disabled={busy}>{busy ? 'Saving…' : 'Submit doorstep request'}</button>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </form>
    </>
  );
}

export function SevaRequestDetail() {
  const { id } = useParams();
  const { user, token } = useAuth();
  const [booking, setBooking] = useState<Booking>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [rating, setRating] = useState(5);
  const [followup, setFollowup] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState('');
  const [agent, setAgent] = useState('');
  const [performedTask, setPerformedTask] = useState('');
  async function refresh() {
    setBooking(await privateApi<Booking>(token, `/seva/requests/${id}`));
  }
  useEffect(() => {
    let active = true;
    if (user)
      privateApi<Booking>(token, `/seva/requests/${id}`)
        .then((b) => {
          if (active) setBooking(b);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [user, token, id]);
  async function action(action: string, extra: Record<string, unknown> = {}) {
    if (!booking) return;
    setBusy(true);
    setError('');
    try {
      setBooking(
        await privateApi<Booking>(token, `/seva/requests/${id}/actions`, {
          revision: booking.revision,
          action,
          note,
          confirmed,
          ...extra,
        }),
      );
      setConfirmed(false);
      setNote('');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!user) return <AccessGate />;
  if (!booking)
    return error ? (
      <p role="alert" className="error">
        {error}
      </p>
    ) : (
      <p role="status">Loading authorized visit…</p>
    );
  const b = booking,
    staff = user.role === 'admin' || user.role === 'coordinator',
    owner = user.role === 'citizen',
    worker = user.role === 'worker';
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">SEVASETU · INTERNAL ASSISTANCE</div>
        <h1>{names[b.category]}</h1>
        <p className="status-chip">{readable(b.stage)}</p>
        <p>Reference {b.id}. A visit completion is not government approval or KYC.</p>
      </header>
      <button
        className="secondary"
        onClick={() => void refresh().catch((e) => setError(e.message))}
      >
        Refresh visit
      </button>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <section className="panel">
        <h2>Booking details</h2>
        <p>{b.description}</p>
        <p>
          {b.location.district} · {b.location.mandal} · {b.location.village}
        </p>
        <p>{b.location.address}</p>
        <p>
          Preferred: {time(b.preferred_window.start)}–{time(b.preferred_window.end)} IST
        </p>
        {b.appointment && (
          <p>
            {b.assignment_accepted
              ? 'Confirmed appointment'
              : 'Proposed appointment — worker acceptance pending'}
            : {time(b.appointment.start)}–{time(b.appointment.end)} IST
          </p>
        )}
        {b.worker_id && (
          <p>
            Assigned worker reference: {b.worker_id}. Internal verification is not government
            certification.
          </p>
        )}
        <button
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              const result = await privateApi<{
                candidates: Candidate[];
                next_action: string;
                escalation_recommendations: string[];
              }>(token, `/seva/requests/${id}/agent`, null);
              setCandidates(result.candidates);
              setAgent([result.next_action, ...result.escalation_recommendations].join(' '));
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          Get grounded coordination guidance
        </button>
        <p aria-live="polite">{agent}</p>
      </section>
      <section className="panel">
        <h2>Authorized actions</h2>
        <label>
          Visit / review / problem note
          <textarea maxLength={600} value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I explicitly confirm this cancellation, rescheduling, assignment or completion review.
        </label>
        <div className="quick-actions">
          {staff && (
            <>
              <button disabled={busy} onClick={() => void action('approve')}>
                Approve for internal assignment
              </button>
              <button disabled={busy || !note} onClick={() => void action('reject')}>
                Reject with reason
              </button>
              <button
                disabled={busy || !note || !confirmed}
                onClick={() => void action('confirm_completion')}
              >
                Confirm reviewed visit completion
              </button>
              <button
                disabled={busy || !note || !confirmed}
                onClick={() => void action('resolve_escalation')}
              >
                Resolve internal escalation
              </button>
              <button disabled={busy || !confirmed || !note} onClick={() => void action('close')}>
                Close reviewed visit
              </button>
            </>
          )}
          {worker && (
            <>
              <button disabled={busy} onClick={() => void action('accept')}>
                Accept proposed assignment
              </button>
              <button disabled={busy} onClick={() => void action('decline')}>
                Decline assignment
              </button>
              <button disabled={busy} onClick={() => void action('en_route')}>
                Mark en route (no tracking)
              </button>
              <button disabled={busy} onClick={() => void action('check_in')}>
                Check in
              </button>
              <label>
                Tasks actually performed (required for outcome)
                <input maxLength={200} value={performedTask} onChange={(e) => setPerformedTask(e.target.value)} />
              </label>
              <button
                disabled={busy || !note || !performedTask.trim()}
                onClick={() =>
                  void action('submit_outcome', {
                    services_performed: [b.category],
                    documents_assisted: [],
                    task_checklist: [performedTask.trim()],
                  })
                }
              >
                Submit performed-service outcome for review
              </button>
            </>
          )}
          {owner && (
            <>
              <button disabled={busy || !confirmed} onClick={() => void action('cancel')}>
                Cancel my request
              </button>
              <button disabled={busy} onClick={() => void action('citizen_confirm')}>
                Confirm I received this assistance
              </button>
            </>
          )}
          <button disabled={busy || !note} onClick={() => void action('report_problem')}>
            Report a problem internally
          </button>
        </div>
        {(owner || staff) && (
          <>
            <div className="profile-grid">
              <label>
                New proposed start (local time)
                <input
                  type="datetime-local"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                />
              </label>
              <label>
                New proposed end
                <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
              </label>
            </div>
            <button
              disabled={busy || !start || !end || !confirmed}
              onClick={() =>
                void action('reschedule', { window: { start: iso(start), end: iso(end) } })
              }
            >
              Request rescheduling; require acceptance again
            </button>
          </>
        )}
        {staff && (
          <>
            <h3>Eligible-worker shortlist</h3>
            <p>
              Use the guidance button to load actual candidates for the preferred window. No
              candidate is automatically booked.
            </p>
            {candidates.map((c) => (
              <p key={c.worker_id}>
                {c.display_name} · {c.workload} active reservations. {c.reasons.join('; ')}
              </p>
            ))}
            <label>
              Choose eligible worker
              <select value={selected} onChange={(e) => setSelected(e.target.value)}>
                <option value="">Select a candidate</option>
                {candidates.map((c) => (
                  <option key={c.worker_id} value={c.worker_id}>
                    {c.display_name}
                  </option>
                ))}
              </select>
            </label>
            <button
              disabled={busy || !selected || !confirmed}
              onClick={async () => {
                setBusy(true);
                try {
                  setBooking(
                    await privateApi<Booking>(token, `/seva/requests/${id}/assignment`, {
                      revision: b.revision,
                      worker_id: selected,
                      window: b.preferred_window,
                      confirmed,
                      note,
                    }),
                  );
                  setConfirmed(false);
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              Confirm assignment proposal
            </button>
          </>
        )}
      </section>
      {b.outcome && (
        <section className="panel">
          <h2>Recorded visit outcome</h2>
          <p>{b.outcome.note}</p>
          <p>Performed: {b.outcome.services_performed.map((c) => names[c]).join(', ')}</p>
          <p>
            {b.outcome.reviewed_by
              ? 'Reviewed internally by coordinator'
              : 'Awaiting coordinator review'}
          </p>
          <p>
            {b.citizen_confirmed
              ? 'Citizen reported receiving assistance'
              : 'Citizen confirmation not recorded'}
          </p>
        </section>
      )}
      {owner && (
        <section className="panel">
          <h2>Feedback & follow-up</h2>
          <label>
            Rating (1–5)
            <input
              type="number"
              min={1}
              max={5}
              value={rating}
              onChange={(e) => setRating(Number(e.target.value))}
            />
          </label>
          <button disabled={busy} onClick={() => void action('feedback', { rating })}>
            Save feedback for reviewed visit
          </button>
          <label>
            Requested follow-up time
            <input
              type="datetime-local"
              value={followup}
              onChange={(e) => setFollowup(e.target.value)}
            />
          </label>
          <button
            disabled={busy || !followup}
            onClick={() => void action('request_followup', { followup_at: iso(followup) })}
          >
            Request follow-up after completion
          </button>
        </section>
      )}
      <section className="panel">
        <h2>In-app updates</h2>
        {b.notifications
          .filter((n) => n.delivered_at)
          .map((n) => (
            <div className="notice" key={n.id}>
              <p>{n.message}</p>
              <button
                disabled={busy || n.acknowledged_by.includes(user.id)}
                onClick={async () => {
                  try {
                    setBooking(
                      await privateApi<Booking>(
                        token,
                        `/seva/requests/${id}/notifications/${n.id}/acknowledge`,
                        { revision: b.revision, note: '' },
                      ),
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                {n.acknowledged_by.includes(user.id) ? 'Acknowledged' : 'Acknowledge update'}
              </button>
            </div>
          ))}
      </section>
      <section className="panel">
        <h2>Request activity timeline</h2>
        <ol>
          {[...b.audit].reverse().map((e) => (
            <li key={e.id}>
              <strong>{readable(e.action)}</strong>
              <small>{time(e.at)} IST</small>
              <p>{e.note}</p>
            </li>
          ))}
        </ol>
        {b.escalations.map((e) => (
          <p key={e.id}>
            {readable(e.reason)} · {e.status}
          </p>
        ))}
      </section>
    </>
  );
}

export function SevaWorkerProfile() {
  const { user, token } = useAuth();
  const [profile, setProfile] = useState<Worker>();
  const [missing, setMissing] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  useEffect(() => {
    if (user)
      void privateApi<Worker>(token, `/seva/workers/${user.id}`)
        .then(setProfile)
        .catch((e) => {
          setMissing(true);
          setError(e.message);
        });
  }, [user, token]);
  if (!user) return <AccessGate />;
  return (
    <>
      <header className="page-title">
        <h1>Worker profile & calendar</h1>
        <p>
          Declared availability is not a confirmed appointment. Only administrators verify worker
          eligibility.
        </p>
      </header>
      {error && (
        <p className="notice" role="alert">
          {error}
        </p>
      )}
      {profile ? (
        <section className="panel">
          <h2>{profile.display_name}</h2>
          <p>
            {readable(profile.verification_status)} · {profile.verification_label}
          </p>
          <p>
            {profile.current_workload} active reservations / capacity {profile.capacity}
          </p>
          <h3>Declared calendar windows (IST)</h3>
          {profile.availability.map((s, i) => (
            <p key={i}>
              {time(s.start)}–{time(s.end)}
            </p>
          ))}
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              try {
                setProfile(
                  await privateApi<Worker>(token, `/seva/workers/${user.id}/availability`, {
                    revision: profile.revision,
                    slots: [...profile.availability, { start: iso(start), end: iso(end) }],
                    note: '',
                  }),
                );
                setError('');
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              Available start (local time)
              <input
                type="datetime-local"
                required
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </label>
            <label>
              Available end (up to 4 hours)
              <input
                type="datetime-local"
                required
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
            <button disabled={busy}>Add declared availability window</button>
          </form>
        </section>
      ) : (
        missing && (
          <form
            className="panel"
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              const d = new FormData(e.currentTarget);
              try {
                setProfile(
                  await privateApi<Worker>(token, `/seva/workers/${user.id}`, {
                    display_name: d.get('name'),
                    kind: d.get('kind'),
                    categories: d.getAll('category'),
                    languages: d.getAll('language'),
                    districts: String(d.get('districts'))
                      .split(',')
                      .map((v) => v.trim())
                      .filter(Boolean),
                    capabilities: d.getAll('capability'),
                    capacity: Number(d.get('capacity')),
                  }),
                );
                setError('');
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              Display name
              <input name="name" minLength={2} maxLength={80} required />
            </label>
            <label>
              Service role
              <select name="kind">
                <option value="field_worker">Field worker</option>
                <option value="ngo_volunteer">NGO volunteer</option>
                <option value="service_partner">
                  Service partner (no official affiliation implied)
                </option>
              </select>
            </label>
            <label>
              Service districts (comma-separated)
              <input name="districts" required />
            </label>
            <label>
              Assignment capacity
              <input type="number" name="capacity" min={1} max={20} defaultValue={5} />
            </label>
            <fieldset>
              <legend>Service categories</legend>
              {Object.entries(names).map(([k, v]) => (
                <label className="check-label" key={k}>
                  <input name="category" type="checkbox" value={k} />
                  {v}
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>Languages</legend>
              {['en', 'hi', 'te'].map((l) => (
                <label className="check-label" key={l}>
                  <input name="language" type="checkbox" value={l} />
                  {l}
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>Accessibility capabilities</legend>
              {['reading_help', 'wheelchair_access', 'hearing_support', 'caregiver_support'].map(
                (l) => (
                  <label className="check-label" key={l}>
                    <input name="capability" type="checkbox" value={l} />
                    {readable(l)}
                  </label>
                ),
              )}
            </fieldset>
            <button disabled={busy}>Submit profile for internal verification</button>
          </form>
        )
      )}
    </>
  );
}

export function SevaWorkers() {
  const { user, token } = useAuth();
  const [rows, setRows] = useState<Worker[]>([]);
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  const [expiry, setExpiry] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  useEffect(() => {
    if (user)
      void privateApi<Page<Worker>>(token, '/seva/workers')
        .then((r) => setRows(r.items))
        .catch((e) => setError(e.message));
  }, [user, token]);
  if (!user) return <AccessGate />;
  return (
    <>
      <header className="page-title">
        <h1>Worker verification & workload</h1>
        <p>
          Internal verification is not MeeSeva authorization or government certification. Only
          administrators can approve verification.
        </p>
      </header>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {user.role === 'admin' && (
        <section className="panel">
          <label>
            Verification review note
            <textarea value={note} maxLength={600} onChange={(e) => setNote(e.target.value)} />
          </label>
          <label>
            Verification expiry (local time)
            <input
              type="datetime-local"
              value={expiry}
              onChange={(e) => setExpiry(e.target.value)}
            />
          </label>
          <label className="check-label">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            I confirm this internal verification review.
          </label>
        </section>
      )}
      <div className="grid">
        {rows.map((w) => (
          <article className="card" key={w.id}>
            <h2>{w.display_name}</h2>
            <p>
              {readable(w.verification_status)} · {w.current_workload}/{w.capacity} reservations
            </p>
            {w.availability.map((s, i) => (
              <p key={i}>
                {time(s.start)}–{time(s.end)} IST
              </p>
            ))}
            {user.role === 'admin' && (
              <div className="quick-actions">
                {['verified_internally', 'suspended', 'expired'].map((status) => (
                  <button
                    disabled={!note || !confirmed || (status === 'verified_internally' && !expiry)}
                    key={status}
                    onClick={async () => {
                      try {
                        const updated = await privateApi<Worker>(
                          token,
                          `/seva/workers/${w.id}/verification`,
                          {
                            revision: w.revision,
                            status,
                            note,
                            confirmed,
                            expires_at: expiry ? iso(expiry) : null,
                          },
                        );
                        setRows((r) => r.map((old) => (old.id === w.id ? updated : old)));
                        setConfirmed(false);
                      } catch (e) {
                        setError((e as Error).message);
                      }
                    }}
                  >
                    {readable(status)}
                  </button>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
      {rows.length === 0 && (
        <p>No worker profiles available. Workers must submit their profiles before verification.</p>
      )}
    </>
  );
}
