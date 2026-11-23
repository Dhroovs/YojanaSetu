import { useLanguage } from './language';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { privateApi, useAuth, User } from './auth';

interface Account extends User {
  active: boolean;
  revision: number;
}
export function Administration() {
  const { tr } = useLanguage();

  const { user, token } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [operations, setOperations] = useState<Record<string, unknown>>();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (user?.role !== 'admin') return;
    void Promise.all([
      privateApi<{ items: Account[]; total: number }>(token, `/admin/users?page=${page}`),
      privateApi<Record<string, unknown>>(token, '/admin/operations'),
    ])
      .then(([listing, ops]) => {
        setAccounts(listing.items);
        setTotal(listing.total);
        setOperations(ops);
      })
      .catch((e) => setError(e.message));
  }, [user, token, page]);
  if (user?.role !== 'admin') return <p role="alert">{tr('Administrator access is required.')}</p>;
  return (
    <>
      <header className="page-title">
        <h1>{tr('Administration')}</h1>
        <p>
          {tr(
            'Role changes revoke existing sessions. Configuration and credentials are managed through the operator environment.',
          )}
        </p>
      </header>
      <nav aria-label={tr('Administration')}>
        <Link to="/seva/workers">{tr('Worker verification & service areas')}</Link> ·{' '}
        <Link to="/sources">{tr('Official source coverage')}</Link> ·{' '}
        <Link to="/coordinator">{tr('Case audit and review')}</Link>
      </nav>
      {error && <p role="alert">{error}</p>}
      <section className="panel">
        <h2>{tr('Operational status')}</h2>
        {operations ? (
          <dl>
            {Object.entries(operations).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll('_', ' ')}</dt>
                <dd>{String(value)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p role="status">{tr('Loading status…')}</p>
        )}
      </section>
      <h2>{tr('User and role management')}</h2>
      <p>
        {tr(
          'Existing administrator accounts cannot be disabled or demoted here; an operator-controlled change is required.',
        )}
      </p>
      {accounts.map((account) => (
        <form
          key={`${account.id}:${account.revision}`}
          className="panel"
          onSubmit={async (e) => {
            e.preventDefault();
            const d = new FormData(e.currentTarget);
            setBusy(true);
            try {
              await privateApi(token, `/admin/users/${account.id}`, {
                revision: account.revision,
                role: d.get('role'),
                active: d.get('active') === 'on',
                confirmed: d.get('confirmed') === 'on',
                note: d.get('note'),
              });
              setAccounts((old) =>
                old.map((a) =>
                  a.id === account.id
                    ? {
                        ...a,
                        role: String(d.get('role')) as User['role'],
                        active: d.get('active') === 'on',
                        revision: a.revision + 1,
                      }
                    : a,
                ),
              );
              setError('');
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <h3>{account.username}</h3>
          <p>{account.id}</p>
          <label>
            {tr('Account role')}
            <select name="role" defaultValue={account.role} disabled={account.role === 'admin'}>
              {['citizen', 'worker', 'coordinator', 'admin'].map((role) => (
                <option key={role} value={role}>
                  {tr(role)}
                </option>
              ))}
            </select>
          </label>
          <label className="check-label">
            <input
              type="checkbox"
              name="active"
              defaultChecked={account.active}
              disabled={account.role === 'admin'}
            />
            {tr('Account active')}
          </label>
          {account.role !== 'admin' && (
            <>
              <label>
                {tr('Account review note')}
                <textarea name="note" required maxLength={600} />
              </label>
              <label className="check-label">
                <input type="checkbox" name="confirmed" required />
                {tr('I confirm this account change')}
              </label>
              <button disabled={busy}>{tr('Save account change')}</button>
            </>
          )}
        </form>
      ))}
      <div className="row">
        <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
          {tr('Previous accounts')}
        </button>
        <span>
          {tr('Page ')}
          {page} · {total} {tr(' accounts')}
        </span>
        <button disabled={page * 20 >= total} onClick={() => setPage((p) => p + 1)}>
          {tr('Next accounts')}
        </button>
      </div>
    </>
  );
}
