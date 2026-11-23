import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { AuthProvider, SignIn, useAuth } from './auth';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function Account() {
  const { user, signOut } = useAuth();
  return (
    <>
      <p>{user?.username || 'Signed out'}</p>
      <button onClick={() => void signOut()}>End session</button>
    </>
  );
}
test('session stays in memory and logout clears the authenticated account', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: 'synthetic-session-secret',
        user: { id: 'test', username: 'synthetic-citizen', role: 'citizen' },
      }),
    })
    .mockResolvedValueOnce({ ok: true, status: 204 });
  vi.stubGlobal('fetch', fetchMock);
  render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<SignIn />} />
          <Route path="/dashboard" element={<Account />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText('Account alias'), {
    target: { value: 'synthetic-citizen' },
  });
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'synthetic-password-for-tests' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in securely' }));
  expect(await screen.findByText('synthetic-citizen')).toBeInTheDocument();
  expect(localStorage.getItem('token')).toBeNull();
  expect(sessionStorage.getItem('token')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'End session' }));
  expect(await screen.findByText('Signed out')).toBeInTheDocument();
  expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe('Bearer synthetic-session-secret');
});
