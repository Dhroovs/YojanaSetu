import { useLanguage } from './language';
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
  worker_display_name?: string | null;
  language: string;
  share_with_assigned_worker: boolean;
  preferences: { in_app: boolean; quiet_start: number; quiet_end: number };
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
  organization_id: string | null;
  kind: string;
  categories: string[];
  languages: string[];
  districts: string[];
  areas: string[];
  capabilities: string[];
  qualifications: string[];
  active: boolean;
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
const iso = (value: string) => new Date(value).toISOString();

function BookingPreferenceForm({
  booking,
  onSave,
}: {
  booking: Booking;
  onSave: (b: Booking) => void;
}) {
  const { tr } = useLanguage();

  const { token } = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <form
      className="panel"
      key={booking.revision}
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        const d = new FormData(e.currentTarget);
        try {
          onSave(
            await privateApi<Booking>(token, `/seva/requests/${booking.id}/preferences`, {
              revision: booking.revision,
              confirmed: d.get('confirm') === 'on',
              language: d.get('language'),
              share_with_assigned_worker: d.get('share') === 'on',
              preferences: {
                in_app: d.get('notify') === 'on',
                quiet_start: Number(d.get('quietStart')),
                quiet_end: Number(d.get('quietEnd')),
              },
              note: 'Citizen updated communication and sharing preferences',
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
      <h2>{tr('Sharing & notification preferences')}</h2>
      <p>
        {tr(
          'Withdrawing sharing consent cancels an active assignment. Quiet hours use India time; equal start/end disables quiet hours.',
        )}
      </p>
      <label>
        {tr('Notification language')}
        <select name="language" defaultValue={booking.language}>
          {['en', 'hi', 'te'].map((l) => (
            <option key={l}>{l}</option>
          ))}
        </select>
      </label>
      <label className="check-label">
        <input type="checkbox" name="share" defaultChecked={booking.share_with_assigned_worker} />
        {tr('Share necessary details with the assigned worker')}
      </label>
      <label className="check-label">
        <input type="checkbox" name="notify" defaultChecked={booking.preferences.in_app} />
        {tr('Deliver in-app notices')}
      </label>
      <label>
        {tr('Quiet hours start (0–23 IST)')}
        <input
          type="number"
          min={0}
          max={23}
          name="quietStart"
          defaultValue={booking.preferences.quiet_start}
        />
      </label>
      <label>
        {tr('Quiet hours end (0–23 IST)')}
        <input
          type="number"
          min={0}
          max={23}
          name="quietEnd"
          defaultValue={booking.preferences.quiet_end}
        />
      </label>
      <label className="check-label">
        <input type="checkbox" name="confirm" required />
        {tr('I confirm these preference changes')}
      </label>
      <button disabled={busy}>{tr('Save sharing & notification preferences')}</button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}

function WorkerProfileEditor({
  profile,
  onSave,
}: {
  profile: Worker;
  onSave: (w: Worker) => void;
}) {
  const { tr } = useLanguage();

  const { token } = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const fields = {
    display_name: 'Worker display name',
    organization_id: 'Organization reference (optional)',
    districts: 'Service districts',
    areas: 'Service mandals or villages (optional)',
    qualifications: 'Training or qualifications (optional)',
  };
  return (
    <details>
      <summary>{tr('Edit profile and request reverification')}</summary>
      <form
        key={profile.revision}
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          const d = new FormData(e.currentTarget);
          const split = (key: string) =>
            String(d.get(key) || '')
              .split(',')
              .map((v) => v.trim())
              .filter(Boolean);
          try {
            onSave(
              await privateApi<Worker>(token, `/seva/workers/${profile.id}/profile`, {
                revision: profile.revision,
                confirmed: true,
                note: d.get('note'),
                active: d.get('active') === 'on',
                profile: {
                  display_name: d.get('display_name'),
                  organization_id: d.get('organization_id') || null,
                  kind: profile.kind,
                  categories: d.getAll('categories'),
                  languages: d.getAll('languages'),
                  districts: split('districts'),
                  areas: split('areas'),
                  qualifications: split('qualifications'),
                  capabilities: d.getAll('capabilities'),
                  capacity: Number(d.get('capacity')),
                },
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
        <p>{tr('Material changes reset verification. Resolve reserved visits before editing.')}</p>
        {Object.entries(fields).map(([key, label]) => (
          <label key={key}>
            {tr(label)}
            <input
              name={key}
              maxLength={1000}
              defaultValue={
                Array.isArray(profile[key as keyof Worker])
                  ? (profile[key as keyof Worker] as string[]).join(', ')
                  : String(profile[key as keyof Worker] || '')
              }
            />
          </label>
        ))}
        <label>
          {tr('Capacity')}
          <input name="capacity" type="number" min={1} max={20} defaultValue={profile.capacity} />
        </label>
        {Object.entries({
          categories: Object.keys(names),
          languages: ['en', 'hi', 'te'],
          capabilities: [
            'reading_help',
            'wheelchair_access',
            'hearing_support',
            'caregiver_support',
          ],
        }).map(([key, values]) => (
          <fieldset key={key}>
            <legend>{tr(readable(key))}</legend>
            {values.map((v) => (
              <label className="check-label" key={v}>
                <input
                  type="checkbox"
                  name={key}
                  value={v}
                  defaultChecked={(profile[key as keyof Worker] as string[]).includes(v)}
                />
                {tr(names[v] || readable(v))}
              </label>
            ))}
          </fieldset>
        ))}
        <label className="check-label">
          <input type="checkbox" name="active" defaultChecked={profile.active} />
          {tr('Active for assignments after verification')}
        </label>
        <label>
          {tr('Reason for profile change')}
          <textarea name="note" maxLength={600} required />
        </label>
        <label className="check-label">
          <input type="checkbox" required />
          {tr('I confirm these changes and the need for reverification')}
        </label>
        <button disabled={busy}>{tr('Save profile for reverification')}</button>
        {error && <p role="alert">{error}</p>}
      </form>
    </details>
  );
}

interface Organization {
  id: string;
  display_name: string;
  kind: string;
  active: boolean;
  verified_internally: boolean;
  revision: number;
}
function OrganizationManager() {
  const { tr } = useLanguage();

  const { user, token } = useAuth();
  const [rows, setRows] = useState<Organization[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (user)
      void privateApi<Organization[]>(token, '/seva/organizations')
        .then(setRows)
        .catch((e) => setError(e.message));
  }, [user, token]);
  return (
    <section className="panel">
      <h2>{tr('Service organizations')}</h2>
      <p>{tr('Internal records do not establish government partnership.')}</p>
      {rows.map((o) => (
        <p key={o.id}>
          {o.display_name} · {o.id} · {o.active ? tr('Active') : tr('Inactive')} ·{' '}
          {o.verified_internally ? tr('Internally reviewed') : tr('Unverified')}{' '}
          {user?.role === 'admin' && (
            <button
              disabled={busy}
              onClick={async () => {
                if (!window.confirm('Confirm this organization status change?')) return;
                setBusy(true);
                try {
                  const updated = await privateApi<Organization>(
                    token,
                    `/seva/organizations/${o.id}?revision=${o.revision}`,
                    {
                      display_name: o.display_name,
                      kind: o.kind,
                      verified_internally: o.verified_internally,
                      confirmed: true,
                      active: !o.active,
                    },
                  );
                  setRows((r) => r.map((old) => (old.id === o.id ? updated : old)));
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              {o.active ? tr('Deactivate organization') : tr('Activate organization')}
            </button>
          )}
        </p>
      ))}
      {rows.length === 0 && <p>{tr('No organizations recorded.')}</p>}
      {user?.role === 'admin' && (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = e.currentTarget;
            const d = new FormData(form);
            setBusy(true);
            try {
              const created = await privateApi<Organization>(token, '/seva/organizations', {
                display_name: d.get('name'),
                kind: d.get('kind'),
                active: true,
                verified_internally: d.get('verified') === 'on',
                confirmed: true,
              });
              setRows((r) => [...r, created]);
              form.reset();
              setError('');
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            {tr('Organization name')}
            <input name="name" required minLength={2} maxLength={100} />
          </label>
          <label>
            {tr('Organization type')}
            <select name="kind">
              <option value="ngo">{tr('NGO')}</option>
              <option value="service_partner">{tr('Service partner')}</option>
              <option value="field_team">{tr('Field team')}</option>
            </select>
          </label>
          <label className="check-label">
            <input type="checkbox" name="verified" />
            {tr('Internal review completed')}
          </label>
          <label className="check-label">
            <input type="checkbox" required />
            {tr('I confirm the organization record')}
          </label>
          <button disabled={busy}>{tr('Create organization')}</button>
        </form>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

export function SevaDashboard() {
  const { tr, formatDate } = useLanguage();

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
        <div className="eyebrow">{tr('SEVASETU · AUTHORIZED IN-PERSON ASSISTANCE')}</div>
        <h1>
          {user.role === 'worker'
            ? tr('My assigned visits')
            : staff
              ? 'Doorstep coordination'
              : 'Help closer to home'}
        </h1>
        <p>
          {tr(
            'No government affiliation, MeeSeva authorization or scheme approval is implied. Appointments require worker acceptance.',
          )}
        </p>
      </header>
      <div className="quick-actions">
        {user.role === 'citizen' && (
          <Link className="button" to="/seva/new">
            {tr('Request doorstep assistance')}
          </Link>
        )}
        {user.role === 'worker' && (
          <Link className="button" to="/seva/profile">
            {tr('My worker profile & availability')}
          </Link>
        )}
        {staff && (
          <Link className="button" to="/seva/workers">
            {tr('Worker verification & availability')}
          </Link>
        )}
      </div>
      <div className="profile-grid">
        <label>
          {tr('Status filter')}
          <select
            value={stage}
            onChange={(e) => {
              setStage(e.target.value);
              setPage(1);
            }}
          >
            <option value="">{tr('All authorized requests')}</option>
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
                {tr(readable(s))}
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
            {tr('Show minimal unclaimed request queue')}
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
        {tr('Refresh visits')}
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!rows && !error && <p role="status">{tr('Loading authorized requests…')}</p>}
      {rows && (
        <>
          <p>
            {rows.total} {tr(' request(s)')}
          </p>
          {!unassigned && (
            <section className="panel" aria-label={tr('Appointment agenda')}>
              <h2>{tr('Appointment agenda (current page, IST)')}</h2>
              {rows.items
                .filter((b) => b.appointment)
                .sort((a, b) => a.appointment!.start.localeCompare(b.appointment!.start))
                .map((b) => (
                  <p key={b.id}>
                    {formatDate(b.appointment!.start)}–{formatDate(b.appointment!.end)} ·{' '}
                    {tr(names[b.category])} · {tr(readable(b.stage))}
                  </p>
                ))}
              {!rows.items.some((b) => b.appointment) && (
                <p>{tr('No appointment windows on this page.')}</p>
              )}
            </section>
          )}
          <div className="grid">
            {rows.items.map((b) => (
              <article className="card" key={b.id}>
                <div className="eyebrow">{tr(readable(b.stage))}</div>
                <h2>{tr(names[b.category])}</h2>
                {b.appointment && (
                  <p>
                    {formatDate(b.appointment.start)}–{formatDate(b.appointment.end)} {tr(' IST')}
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
                    {tr('Claim request with confirmation')}
                  </button>
                ) : (
                  <Link className="text-link" to={`/seva/requests/${b.id}`}>
                    {tr('Open visit request →')}
                  </Link>
                )}
              </article>
            ))}
          </div>
          {rows.total === 0 && (
            <p>{tr('No requests in this queue. No availability or booking is assumed.')}</p>
          )}
          <div className="row pagination">
            <button disabled={page === 1} onClick={() => setPage((v) => v - 1)}>
              {tr('Previous')}
            </button>
            <span>
              {tr('Page ')}
              {page}
            </span>
            <button disabled={page * 20 >= rows.total} onClick={() => setPage((v) => v + 1)}>
              {tr('Next')}
            </button>
          </div>
        </>
      )}
      {staff && (
        <p>
          <button className="secondary" onClick={() => navigate('/coordinator')}>
            {tr('Open case assistance queue')}
          </button>
        </p>
      )}
    </>
  );
}

export function SevaRequestForm() {
  const { tr } = useLanguage();

  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const key = useRef(crypto.randomUUID());
  if (!user) return <AccessGate />;
  if (user.role !== 'citizen')
    return <p role="alert">{tr('Citizens submit requests owned by their own account.')}</p>;
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">{tr('SEVASETU')}</div>
        <h1>{tr('Request in-person guidance')}</h1>
        <p>
          {tr(
            'Use synthetic details during development. Never enter Aadhaar, OTPs, bank credentials or identity images.',
          )}
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
          {tr('Assistance category')}
          <select name="category">
            {Object.entries(names).map(([k, v]) => (
              <option key={k} value={k}>
                {tr(v)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr('Known scheme identifier (optional)')}
          <input
            name="scheme"
            maxLength={80}
            defaultValue={new URLSearchParams(location.search).get('scheme') || ''}
          />
        </label>
        <label>
          {tr('My related case reference (optional)')}
          <input
            name="case"
            maxLength={80}
            defaultValue={new URLSearchParams(location.search).get('case') || ''}
          />
        </label>
        <label>
          {tr('What help is needed?')}
          <textarea name="description" minLength={5} maxLength={600} required />
        </label>
        <div className="profile-grid">
          <label>
            {tr('Preferred start (your local time)')}
            <input type="datetime-local" name="start" required />
          </label>
          <label>
            {tr('Preferred end (15 minutes–4 hours later)')}
            <input type="datetime-local" name="end" required />
          </label>
          {['district', 'mandal', 'village'].map((field) => (
            <label key={field}>
              {tr(readable(field))}
              <input name={field} minLength={2} maxLength={80} required />
            </label>
          ))}
        </div>
        <label>
          {tr('Address details for the assigned worker')}
          <input name="address" minLength={5} maxLength={300} required />
        </label>
        <p>
          {tr(
            'Map coordinates are optional through the API with separate explicit consent; this form does not request or track your device location.',
          )}
        </p>
        <label>
          {tr('Preferred service language')}
          <select name="language">
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
          </select>
        </label>
        <p>
          {tr(
            'Worker language matching is supported; the interface and scheme explanations remain primarily English.',
          )}
        </p>
        <fieldset>
          <legend>{tr('Accessibility support (optional)')}</legend>
          {['wheelchair_access', 'hearing_support', 'reading_help', 'caregiver_support'].map(
            (a) => (
              <label className="check-label" key={a}>
                <input type="checkbox" name="accessibility" value={a} />
                {tr(readable(a))}
              </label>
            ),
          )}
        </fieldset>
        <label>
          {tr('Will a caregiver or family member be present?')}
          <select name="caregiver">
            <option value="">{tr('Not specified')}</option>
            <option value="true">{tr('Yes')}</option>
            <option value="false">{tr('No')}</option>
          </select>
        </label>
        <p>{tr('Contact preference: in-app only. No paid messaging is connected.')}</p>
        <label className="check-label">
          <input type="checkbox" name="consent" required />
          {tr('I consent to sharing necessary booking details with the assigned worker.')}
        </label>
        <button disabled={busy}>{busy ? tr('Saving…') : tr('Submit doorstep request')}</button>
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
  const { tr, formatDate } = useLanguage();

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
  const [performedServices, setPerformedServices] = useState<string[]>([]);
  const [documentsAssisted, setDocumentsAssisted] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
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
      <p role="status">{tr('Loading authorized visit…')}</p>
    );
  const b = booking,
    staff = user.role === 'admin' || user.role === 'coordinator',
    owner = user.role === 'citizen',
    worker = user.role === 'worker';
  const canChangeSchedule =
    [
      'pending_coordinator_review',
      'approved_for_assignment',
      'worker_assigned',
      'visit_scheduled',
      'worker_en_route',
      'rescheduling_requested',
      'no_worker_available',
      'no_show',
      'escalated',
    ].includes(b.stage) && !b.outcome;
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">{tr('SEVASETU · INTERNAL ASSISTANCE')}</div>
        <h1>{tr(names[b.category])}</h1>
        <p className="status-chip">{tr(readable(b.stage))}</p>
        <p>
          {tr('Reference ')}
          {b.id}
          {tr('. A visit completion is not government approval or KYC.')}
        </p>
      </header>
      <button
        className="secondary"
        onClick={() => void refresh().catch((e) => setError(e.message))}
      >
        {tr('Refresh visit')}
      </button>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <section className="panel">
        <h2>{tr('Booking details')}</h2>
        {b.worker_display_name && (
          <p>
            {tr('Assigned worker: ')}
            {b.worker_display_name} {tr(' (internal verification only)')}
          </p>
        )}
        <p>{b.description}</p>
        <p>
          {b.location.district} · {b.location.mandal} · {b.location.village}
        </p>
        <p>{b.location.address}</p>
        <p>
          {tr('Preferred: ')}
          {formatDate(b.preferred_window.start)}–{formatDate(b.preferred_window.end)} {tr(' IST')}
        </p>
        {b.appointment && (
          <p>
            {b.assignment_accepted
              ? tr('Confirmed appointment')
              : tr('Proposed appointment — worker acceptance pending')}
            : {formatDate(b.appointment.start)}–{formatDate(b.appointment.end)} {tr(' IST')}
          </p>
        )}
        {b.worker_id && (
          <p>
            {tr('Assigned worker reference: ')}
            {b.worker_id}
            {tr('. Internal verification is not government certification.')}
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
          {tr('Get grounded coordination guidance')}
        </button>
        <p aria-live="polite">{agent}</p>
      </section>
      <section className="panel">
        <h2>{tr('Authorized actions')}</h2>
        <label>
          {tr('Visit / review / problem note')}
          <textarea maxLength={600} value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          {tr(
            'I explicitly confirm this cancellation, rescheduling, assignment or completion review.',
          )}
        </label>
        <div className="quick-actions">
          {staff && (
            <>
              <button disabled={busy} onClick={() => void action('no_worker_available')}>
                {tr('Record no eligible worker available')}
              </button>
              <button disabled={busy} onClick={() => void action('approve')}>
                {tr('Approve for internal assignment')}
              </button>
              <button disabled={busy || !note} onClick={() => void action('reject')}>
                {tr('Reject with reason')}
              </button>
              <button
                disabled={busy || !note || !confirmed}
                onClick={() => void action('confirm_completion')}
              >
                {tr('Confirm reviewed visit completion')}
              </button>
              <button
                disabled={busy || !note || !confirmed}
                onClick={() => void action('resolve_escalation')}
              >
                {tr('Resolve internal escalation')}
              </button>
              <button disabled={busy || !confirmed || !note} onClick={() => void action('close')}>
                {tr('Close reviewed visit')}
              </button>
            </>
          )}
          {worker && (
            <>
              <button disabled={busy} onClick={() => void action('accept')}>
                {tr('Accept proposed assignment')}
              </button>
              <button disabled={busy} onClick={() => void action('decline')}>
                {tr('Decline assignment')}
              </button>
              <button disabled={busy} onClick={() => void action('en_route')}>
                {tr('Mark en route (no tracking)')}
              </button>
              <button disabled={busy} onClick={() => void action('check_in')}>
                {tr('Check in')}
              </button>
              <label>
                {tr('Tasks actually performed (required for outcome)')}
                <input
                  maxLength={200}
                  value={performedTask}
                  onChange={(e) => setPerformedTask(e.target.value)}
                />
              </label>
              <fieldset>
                <legend>{tr('Services actually performed')}</legend>
                {Object.entries(names).map(([key, label]) => (
                  <label className="check-label" key={key}>
                    <input
                      type="checkbox"
                      checked={performedServices.includes(key)}
                      onChange={(e) =>
                        setPerformedServices((old) =>
                          e.target.checked ? [...old, key] : old.filter((v) => v !== key),
                        )
                      }
                    />
                    {tr(label)}
                  </label>
                ))}
              </fieldset>
              <label>
                {tr('Documents assisted with (names only, comma-separated)')}
                <input
                  maxLength={500}
                  value={documentsAssisted}
                  onChange={(e) => setDocumentsAssisted(e.target.value)}
                />
              </label>
              <button
                disabled={busy || !note || !performedTask.trim() || !performedServices.length}
                onClick={() =>
                  void action('submit_outcome', {
                    services_performed: performedServices,
                    documents_assisted: documentsAssisted
                      .split(',')
                      .map((v) => v.trim())
                      .filter(Boolean),
                    task_checklist: [performedTask.trim()],
                  })
                }
              >
                {tr('Submit performed-service outcome for review')}
              </button>
            </>
          )}
          {owner && (
            <>
              <button
                disabled={busy || !confirmed || !canChangeSchedule}
                onClick={() => void action('cancel')}
              >
                {tr('Cancel my request')}
              </button>
              <button
                disabled={
                  busy || !['completion_pending_review', 'visit_completed'].includes(b.stage)
                }
                onClick={() => void action('citizen_confirm')}
              >
                {tr('Confirm I received this assistance')}
              </button>
            </>
          )}
          <button disabled={busy || !note} onClick={() => void action('report_problem')}>
            {tr('Report a problem internally')}
          </button>
        </div>
        {(owner || staff) && (
          <>
            <div className="profile-grid">
              <label>
                {tr('New proposed start (local time)')}
                <input
                  type="datetime-local"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                />
              </label>
              <label>
                {tr('New proposed end')}
                <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
              </label>
            </div>
            <button
              disabled={busy || !start || !end || !confirmed || !canChangeSchedule}
              onClick={() =>
                void action('reschedule', { window: { start: iso(start), end: iso(end) } })
              }
            >
              {tr('Request rescheduling; require acceptance again')}
            </button>
          </>
        )}
        {staff && (
          <>
            <h3>{tr('Eligible-worker shortlist')}</h3>
            <label>
              {tr('Reason for choosing a lower ranked eligible worker (if applicable)')}
              <input
                maxLength={400}
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
              />
            </label>
            <p>
              {tr(
                'Use the guidance button to load actual candidates for the preferred window. No candidate is automatically booked.',
              )}
            </p>
            {candidates.map((c) => (
              <p key={c.worker_id}>
                {c.display_name} · {c.workload} {tr(' active reservations. ')}
                {c.reasons.join('; ')}
              </p>
            ))}
            <label>
              {tr('Choose eligible worker')}
              <select value={selected} onChange={(e) => setSelected(e.target.value)}>
                <option value="">{tr('Select a candidate')}</option>
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
                      override_reason: overrideReason,
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
              {tr('Confirm assignment proposal')}
            </button>
          </>
        )}
      </section>
      {b.outcome && (
        <section className="panel">
          <h2>{tr('Recorded visit outcome')}</h2>
          <p>{b.outcome.note}</p>
          <p>
            {tr('Performed: ')}
            {b.outcome.services_performed.map((c) => names[c]).join(', ')}
          </p>
          <p>
            {b.outcome.reviewed_by
              ? tr('Reviewed internally by coordinator')
              : tr('Awaiting coordinator review')}
          </p>
          <p>
            {b.citizen_confirmed
              ? tr('Citizen reported receiving assistance')
              : tr('Citizen confirmation not recorded')}
          </p>
        </section>
      )}
      {owner && ['visit_completed', 'follow_up_required', 'closed'].includes(b.stage) && (
        <section className="panel">
          <h2>{tr('Feedback & follow-up')}</h2>
          <label>
            {tr('Rating (1–5)')}
            <input
              type="number"
              min={1}
              max={5}
              value={rating}
              onChange={(e) => setRating(Number(e.target.value))}
            />
          </label>
          <button disabled={busy} onClick={() => void action('feedback', { rating })}>
            {tr('Save feedback for reviewed visit')}
          </button>
          <label>
            {tr('Requested follow-up time')}
            <input
              type="datetime-local"
              value={followup}
              onChange={(e) => setFollowup(e.target.value)}
            />
          </label>
          <button
            disabled={busy || !followup || b.stage !== 'visit_completed'}
            onClick={() => void action('request_followup', { followup_at: iso(followup) })}
          >
            {tr('Request follow-up after completion')}
          </button>
        </section>
      )}
      <section className="panel">
        <h2>{tr('In-app updates')}</h2>
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
                {n.acknowledged_by.includes(user.id)
                  ? tr('Acknowledged')
                  : tr('Acknowledge update')}
              </button>
            </div>
          ))}
      </section>
      {owner && <BookingPreferenceForm booking={b} onSave={setBooking} />}
      <section className="panel">
        <h2>{tr('Request activity timeline')}</h2>
        <ol>
          {[...b.audit].reverse().map((e) => (
            <li key={e.id}>
              <strong>{tr(readable(e.action))}</strong>
              <small>
                {formatDate(e.at)} {tr(' IST')}
              </small>
              <p>{e.note}</p>
            </li>
          ))}
        </ol>
        {b.escalations.map((e) => (
          <p key={e.id}>
            {tr(readable(e.reason))} · {e.status}
          </p>
        ))}
      </section>
    </>
  );
}

export function SevaWorkerProfile() {
  const { tr, formatDate } = useLanguage();

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
        <h1>{tr('Worker profile & calendar')}</h1>
        <p>
          {tr(
            'Declared availability is not a confirmed appointment. Only administrators verify worker eligibility.',
          )}
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
            {tr(readable(profile.verification_status))} · {profile.verification_label}
          </p>
          <p>
            {profile.current_workload} {tr(' active reservations / capacity ')}
            {profile.capacity}
          </p>
          <h3>{tr('Declared calendar windows (IST)')}</h3>
          {profile.availability.map((s, i) => (
            <p key={i}>
              {formatDate(s.start)}–{formatDate(s.end)}
              <button
                disabled={busy}
                onClick={async () => {
                  if (
                    !window.confirm(
                      'Remove this declared availability window? Reserved visits must be resolved first.',
                    )
                  )
                    return;
                  setBusy(true);
                  try {
                    setProfile(
                      await privateApi<Worker>(token, `/seva/workers/${user.id}/availability`, {
                        revision: profile.revision,
                        slots: profile.availability.filter((_, index) => index !== i),
                        note: 'Worker removed declared availability',
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
                {tr('Remove availability window')}
              </button>
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
              {tr('Available start (local time)')}
              <input
                type="datetime-local"
                required
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </label>
            <label>
              {tr('Available end (up to 4 hours)')}
              <input
                type="datetime-local"
                required
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
            <button disabled={busy}>{tr('Add declared availability window')}</button>
          </form>
          <WorkerProfileEditor profile={profile} onSave={setProfile} />
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
              {tr('Display name')}
              <input name="name" minLength={2} maxLength={80} required />
            </label>
            <label>
              {tr('Service role')}
              <select name="kind">
                <option value="field_worker">{tr('Field worker')}</option>
                <option value="ngo_volunteer">{tr('NGO volunteer')}</option>
                <option value="service_partner">
                  {tr('Service partner (no official affiliation implied)')}
                </option>
              </select>
            </label>
            <label>
              {tr('Service districts (comma-separated)')}
              <input name="districts" required />
            </label>
            <label>
              {tr('Assignment capacity')}
              <input type="number" name="capacity" min={1} max={20} defaultValue={5} />
            </label>
            <fieldset>
              <legend>{tr('Service categories')}</legend>
              {Object.entries(names).map(([k, v]) => (
                <label className="check-label" key={k}>
                  <input name="category" type="checkbox" value={k} />
                  {tr(v)}
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>{tr('Languages')}</legend>
              {['en', 'hi', 'te'].map((l) => (
                <label className="check-label" key={l}>
                  <input name="language" type="checkbox" value={l} />
                  {l}
                </label>
              ))}
            </fieldset>
            <fieldset>
              <legend>{tr('Accessibility capabilities')}</legend>
              {['reading_help', 'wheelchair_access', 'hearing_support', 'caregiver_support'].map(
                (l) => (
                  <label className="check-label" key={l}>
                    <input name="capability" type="checkbox" value={l} />
                    {tr(readable(l))}
                  </label>
                ),
              )}
            </fieldset>
            <button disabled={busy}>{tr('Submit profile for internal verification')}</button>
          </form>
        )
      )}
    </>
  );
}

export function SevaWorkers() {
  const { tr, formatDate } = useLanguage();

  const { user, token } = useAuth();
  const [rows, setRows] = useState<Worker[]>([]);
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  const [expiry, setExpiry] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [evidence, setEvidence] = useState('');
  useEffect(() => {
    if (user)
      void privateApi<Page<Worker>>(token, `/seva/workers?page=${page}&status=${statusFilter}`)
        .then((r) => {
          setRows(r.items);
          setTotal(r.total);
        })
        .catch((e) => setError(e.message));
  }, [user, token, page, statusFilter]);
  if (!user) return <AccessGate />;
  return (
    <>
      <header className="page-title">
        <h1>{tr('Worker verification & workload')}</h1>
        <p>
          {tr(
            'Internal verification is not MeeSeva authorization or government certification. Only administrators can approve verification.',
          )}
        </p>
      </header>
      <label>
        {tr('Verification filter')}
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          {[
            '',
            'pending_verification',
            'verified_internally',
            'authorization_confirmed',
            'suspended',
            'expired',
          ].map((s) => (
            <option key={s} value={s}>
              {s ? readable(s) : tr('All workers')}
            </option>
          ))}
        </select>
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {user.role === 'admin' && (
        <section className="panel">
          <label>
            {tr('Verification review note')}
            <textarea value={note} maxLength={600} onChange={(e) => setNote(e.target.value)} />
          </label>
          <label>
            {tr('Reviewed authorization evidence URL (required for authorization confirmed)')}
            <input type="url" value={evidence} onChange={(e) => setEvidence(e.target.value)} />
          </label>
          <label>
            {tr('Verification expiry (local time)')}
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
            {tr('I confirm this internal verification review.')}
          </label>
        </section>
      )}
      <div className="grid">
        {rows.map((w) => (
          <article className="card" key={w.id}>
            <h2>{w.display_name}</h2>
            <p>
              {tr(readable(w.verification_status))} · {w.current_workload}/{w.capacity}{' '}
              {tr(' reservations')}
            </p>
            {w.availability.map((s, i) => (
              <p key={i}>
                {formatDate(s.start)}–{formatDate(s.end)} {tr(' IST')}
              </p>
            ))}
            {user.role === 'admin' && (
              <div className="quick-actions">
                {['verified_internally', 'authorization_confirmed', 'suspended', 'expired'].map(
                  (status) => (
                    <button
                      disabled={
                        !note || !confirmed || (status === 'verified_internally' && !expiry)
                      }
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
                              evidence_url: evidence || null,
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
                      {tr(readable(status))}
                    </button>
                  ),
                )}
              </div>
            )}
          </article>
        ))}
      </div>
      {rows.length === 0 && (
        <p>
          {tr(
            'No worker profiles available. Workers must submit their profiles before verification.',
          )}
        </p>
      )}
      <div className="row">
        <button disabled={page === 1} onClick={() => setPage((v) => v - 1)}>
          {tr('Previous workers')}
        </button>
        <span>
          {tr('Page ')}
          {page}, {total} {tr(' workers')}
        </span>
        <button disabled={page * 20 >= total} onClick={() => setPage((v) => v + 1)}>
          {tr('Next workers')}
        </button>
      </div>
      <OrganizationManager />
    </>
  );
}
