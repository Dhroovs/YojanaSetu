import { useLanguage } from './language';
import { createContext, ReactNode, useContext, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

export interface User {
  id: string;
  username: string;
  role: 'citizen' | 'worker' | 'coordinator' | 'admin';
}
const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function privateApi<T>(
  token: string,
  path: string,
  body?: unknown,
  key?: string,
): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined
        ? {}
        : { 'Content-Type': 'application/json', 'Idempotency-Key': key || crypto.randomUUID() }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === 'string'
        ? error.detail
        : `Request failed (${response.status}). Check the form and try again.`,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
interface Session {
  user: User | null;
  token: string;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}
const Context = createContext<Session | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const { setLanguage } = useLanguage();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState('');
  async function signIn(username: string, password: string) {
    const response = await privateApi<{ access_token: string; user: User; language?: string }>(
      '',
      '/auth/login',
      {
        username,
        password,
      },
    );
    setToken(response.access_token);
    setUser(response.user);
    if (response.language) setLanguage(response.language);
  }
  async function signOut() {
    try {
      await privateApi(token, '/auth/logout', {});
    } finally {
      setToken('');
      setUser(null);
    }
  }
  return <Context.Provider value={{ user, token, signIn, signOut }}>{children}</Context.Provider>;
}
export function useAuth() {
  const value = useContext(Context);
  if (!value) throw new Error('AuthProvider is required');
  return value;
}
export function useOptionalAuth() {
  return useContext(Context);
}
export function SignIn() {
  const location = useLocation();
  const { tr } = useLanguage();

  const { user, token, signIn, signOut } = useAuth();
  const { language } = useLanguage();
  const [preferenceStatus, setPreferenceStatus] = useState('');
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <>
      <header className="page-title">
        <div className="eyebrow">{tr('PRIVATE ASSISTANCE')}</div>
        <h1>{user ? tr('Your session') : tr('Sign in')}</h1>
        <p>
          {tr(
            'Use a citizen account or a provisioned staff account. No government identity verification is performed.',
          )}
        </p>
        {!user && <Link to="/register">{tr('Create a citizen account')}</Link>}
        {!user && new URLSearchParams(location.search).has('registered') && (
          <p role="status">{tr('Account created. Sign in with your alias.')}</p>
        )}
        {user?.role === 'admin' && <Link to="/admin">{tr('Administration')}</Link>}
      </header>
      {user ? (
        <section className="panel">
          <p>
            {tr('Signed in as ')}
            {user.username} · {user.role}
          </p>
          <Link to="/dashboard">{tr('Open my assistance →')}</Link>
          <p>
            {tr(
              'Navigation language is saved on this device. Save it to your account for future sign-ins.',
            )}
          </p>
          <button
            onClick={async () => {
              try {
                await privateApi(token, '/auth/preferences', { language });
                setPreferenceStatus('Account language saved.');
              } catch (e) {
                setPreferenceStatus((e as Error).message);
              }
            }}
          >
            {tr('Save account language')}
          </button>
          <p role="status">{tr(preferenceStatus)}</p>
          <button
            onClick={() => {
              void signOut().then(() => navigate('/login'));
            }}
          >
            {tr('Sign out')}
          </button>
        </section>
      ) : (
        <form
          className="panel"
          onSubmit={async (e) => {
            e.preventDefault();
            setError('');
            setBusy(true);
            try {
              await signIn(username, password);
              setPassword('');
              navigate('/dashboard');
            } catch (e) {
              setError((e as Error).message);
              setPassword('');
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            {tr('Account alias')}
            <input
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={50}
            />
          </label>
          <label>
            {tr('Password')}
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={12}
              maxLength={128}
            />
          </label>
          <button disabled={busy}>{busy ? tr('Signing in…') : tr('Sign in securely')}</button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <p className="small">
            {tr(
              'Sessions stay in this tab’s memory and expire. Never use real citizen documents in this development preview.',
            )}
          </p>
        </form>
      )}
    </>
  );
}

export function Register() {
  const { tr } = useLanguage();

  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <section className="panel">
      <h1>{tr('Create a citizen account')}</h1>
      <p>
        {tr(
          'Choose an alias instead of your name or contact details. Staff accounts require administrator approval. No Aadhaar or government identity verification is performed.',
        )}
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const d = new FormData(e.currentTarget);
          setBusy(true);
          setError('');
          if (d.get('password') !== d.get('confirmation')) {
            setError('Passwords must match.');
            setBusy(false);
            return;
          }
          try {
            await privateApi('', '/auth/register', {
              username: d.get('alias'),
              password: d.get('password'),
              consent: d.get('consent') === 'on',
              language: d.get('language'),
            });
            navigate('/login?registered=true');
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          {tr('Account alias')}
          <input
            name="alias"
            autoComplete="username"
            minLength={3}
            maxLength={50}
            pattern="[a-zA-Z0-9_-]+"
            required
          />
        </label>
        <label>
          {tr('Password')}
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            minLength={12}
            maxLength={128}
            required
          />
        </label>
        <label>
          {tr('Confirm password')}
          <input
            type="password"
            name="confirmation"
            autoComplete="new-password"
            minLength={12}
            maxLength={128}
            required
          />
        </label>
        <label>
          {tr('Preferred language')}
          <select name="language">
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
          </select>
        </label>
        <label className="check-label">
          <input type="checkbox" name="consent" required />
          {tr(
            'I understand this service stores my assistance records and is not a government approval service. I will use synthetic data during development.',
          )}
        </label>
        <button disabled={busy}>{tr('Create citizen account')}</button>
        {error && <p role="alert">{error}</p>}
      </form>
      <Link to="/login">{tr('Sign in')}</Link>
    </section>
  );
}

export async function downloadDocument(token: string, path: string) {
  const response = await fetch(`${base}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error('Document unavailable, expired or not authorized.');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `assistance-document.${blob.type === 'application/pdf' ? 'pdf' : blob.type === 'image/png' ? 'png' : 'jpg'}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function uploadDocument(
  token: string,
  path: string,
  file: File,
  key: string,
  onProgress: (n: number) => void,
) {
  return new Promise<unknown>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${base}${path}`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.setRequestHeader('Idempotency-Key', key);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.timeout = 120000;
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      let body;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        reject(new Error('Upload response could not be read.'));
        return;
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body);
      else
        reject(
          new Error(
            typeof body.detail === 'string' ? body.detail : `Upload failed (${xhr.status}).`,
          ),
        );
    };
    xhr.onerror = () => reject(new Error('Upload connection failed. You can retry the same file.'));
    xhr.ontimeout = () => reject(new Error('Upload timed out. Refresh and retry.'));
    xhr.send(file);
  });
}
