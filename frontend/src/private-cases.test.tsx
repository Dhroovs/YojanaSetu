import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { PrivateCasePage, PrivateDashboard, PrivateCase } from './private-cases';
import { privateApi, uploadDocument, useAuth } from './auth';
import { api } from './api';

vi.mock('./auth', () => ({
  useAuth: vi.fn(),
  useOptionalAuth: () => null,
  privateApi: vi.fn(),
  downloadDocument: vi.fn(),
  uploadDocument: vi.fn(),
}));
vi.mock('./api', () => ({ api: vi.fn() }));
const user = { id: 'citizen-a', username: 'synthetic-citizen', role: 'citizen' as const };
const record: PrivateCase = {
  id: 'case-a',
  scheme_id: 'synthetic-test',
  stage: 'documents_pending',
  status: 'awaiting_information',
  revision: 3,
  is_demo: true,
  checklist_verified: false,
  checklist: [
    {
      id: 'item-a',
      label: 'Synthetic household record',
      source_ids: ['test-source'],
      is_demo: true,
    },
  ],
  documents: [],
  followups: [],
  reminders: [],
  escalations: [],
  activity: [],
  missing_information: ['Source checklist requires review'],
  coordinator_id: null,
  worker_ids: [],
  preferences: { in_app: true, quiet_start: 21, quiet_end: 8 },
  scheme_source_versions: {},
};
beforeEach(() => {
  vi.mocked(useAuth).mockReturnValue({
    user,
    token: 'private-session',
    signIn: vi.fn(),
    signOut: vi.fn(),
  });
  vi.mocked(api).mockResolvedValue([]);
  vi.mocked(privateApi).mockResolvedValue(record);
});
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
function mountCase() {
  render(
    <MemoryRouter initialEntries={['/my-cases/case-a']}>
      <Routes>
        <Route path="/my-cases/:id" element={<PrivateCasePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

test('citizen sees authorized checklist and can request a bounded human referral', async () => {
  vi.mocked(privateApi).mockImplementation(async (_t, path) =>
    path.endsWith('/assist')
      ? { result: { next_action: 'Refer to an authorized internal coordinator.' }, revision: 4 }
      : record,
  );
  mountCase();
  expect(await screen.findByRole('heading', { name: 'synthetic-test' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Synthetic household record' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Update internal stage' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Request human assistance' }));
  expect(
    await screen.findByText('Refer to an authorized internal coordinator.'),
  ).toBeInTheDocument();
  expect(privateApi).toHaveBeenCalledWith(
    'private-session',
    '/cases/case-a/assist',
    expect.objectContaining({ intent: 'escalation', apply_changes: true, revision: 3 }),
  );
});

test('cross-user denial shows no case contents', async () => {
  vi.mocked(privateApi).mockRejectedValue(new Error('Case not found for this account.'));
  mountCase();
  expect(await screen.findByRole('alert')).toHaveTextContent('Case not found for this account.');
  expect(
    screen.queryByRole('heading', { name: 'Synthetic household record' }),
  ).not.toBeInTheDocument();
});

test('unsupported upload is rejected before sending file contents', async () => {
  mountCase();
  await screen.findByRole('heading', { name: 'synthetic-test' });
  fireEvent.change(screen.getByLabelText('Checklist item'), { target: { value: 'item-a' } });
  fireEvent.change(screen.getByLabelText('Synthetic or redacted file'), {
    target: { files: [new File(['test'], 'bad.exe', { type: 'application/x-msdownload' })] },
  });
  fireEvent.submit(
    screen.getByRole('button', { name: 'Upload securely / retry' }).closest('form')!,
  );
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Choose a PDF, PNG or JPEG under 10 MB.',
  );
  expect(uploadDocument).not.toHaveBeenCalled();
});

test('coordinator must confirm before claiming minimal unassigned queue', async () => {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 'coord-a', username: 'synthetic-coordinator', role: 'coordinator' },
    token: 'staff-session',
    signIn: vi.fn(),
    signOut: vi.fn(),
  });
  vi.mocked(privateApi).mockResolvedValue({ items: [record], total: 1, page: 1, limit: 20 });
  vi.spyOn(window, 'confirm').mockReturnValue(false);
  render(
    <MemoryRouter>
      <PrivateDashboard coordinator />
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText('Queue'), { target: { value: 'unassigned' } });
  const button = await screen.findByRole('button', { name: 'Claim case with confirmation' });
  fireEvent.click(button);
  expect(vi.mocked(privateApi).mock.calls.some((c) => c[1].endsWith('/assignment'))).toBe(false);
  vi.mocked(window.confirm).mockReturnValue(true);
  fireEvent.click(button);
  await waitFor(() =>
    expect(privateApi).toHaveBeenCalledWith(
      'staff-session',
      '/cases/case-a/assignment',
      expect.objectContaining({ confirmed: true, coordinator_id: 'coord-a' }),
    ),
  );
  vi.mocked(window.confirm).mockRestore();
});
