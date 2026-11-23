import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { privateApi, useAuth } from './auth';
import { SevaDashboard, SevaRequestDetail, SevaRequestForm, SevaWorkerProfile } from './seva';

vi.mock('./auth', () => ({ useAuth: vi.fn(), privateApi: vi.fn(), useOptionalAuth: () => null }));
const citizen = { id: 'citizen-a', username: 'Synthetic citizen', role: 'citizen' as const };
const record = {
  id: 'booking-a',
  category: 'document_assistance',
  stage: 'pending_coordinator_review',
  revision: 0,
  description: 'Synthetic assistance',
  owner_id: 'citizen-a',
  worker_id: null,
  coordinator_id: null,
  language: 'en',
  share_with_assigned_worker: true,
  preferences: { in_app: true, quiet_start: 21, quiet_end: 8 },
  preferred_window: { start: '2099-01-01T06:00:00Z', end: '2099-01-01T07:00:00Z' },
  appointment: null,
  location: {
    district: 'Test District',
    mandal: 'Test Mandal',
    village: 'Test Village',
    address: 'Synthetic house',
  },
  assignment_accepted: false,
  outcome: null,
  citizen_confirmed: false,
  feedback: null,
  audit: [],
  notifications: [],
  escalations: [],
};
beforeEach(() => {
  vi.mocked(useAuth).mockReturnValue({
    user: citizen,
    token: 'synthetic-session',
    signIn: vi.fn(),
    signOut: vi.fn(),
  });
  vi.mocked(privateApi).mockResolvedValue(record);
});
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
function detail() {
  render(
    <MemoryRouter initialEntries={['/seva/requests/booking-a']}>
      <Routes>
        <Route path="/seva/requests/:id" element={<SevaRequestDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

test('citizen form submits consented booking with timezone-aware times and stable creation key', async () => {
  render(
    <MemoryRouter>
      <SevaRequestForm />
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText('What help is needed?'), {
    target: { value: 'Synthetic document help' },
  });
  fireEvent.change(screen.getByLabelText('Preferred start (your local time)'), {
    target: { value: '2099-01-01T12:00' },
  });
  fireEvent.change(screen.getByLabelText('Preferred end', { exact: false }), {
    target: { value: '2099-01-01T13:00' },
  });
  for (const label of ['district', 'mandal', 'village'])
    fireEvent.change(screen.getByLabelText(label), { target: { value: 'Synthetic area' } });
  fireEvent.change(screen.getByLabelText('Address details for the assigned worker'), {
    target: { value: 'Synthetic house' },
  });
  fireEvent.click(screen.getByLabelText(/I consent to sharing necessary booking/));
  fireEvent.click(screen.getByRole('button', { name: 'Submit doorstep request' }));
  await waitFor(() =>
    expect(privateApi).toHaveBeenCalledWith(
      'synthetic-session',
      '/seva/requests',
      expect.objectContaining({
        share_with_assigned_worker: true,
        preferred_window: { start: expect.stringMatching(/Z$/), end: expect.stringMatching(/Z$/) },
      }),
      expect.any(String),
    ),
  );
});

test('read-only coordination guidance sends POST null and never creates an assignment', async () => {
  vi.mocked(privateApi).mockImplementation(async (_token, path) =>
    path.endsWith('/agent')
      ? {
          candidates: [],
          next_action: 'Ask a coordinator to review.',
          escalation_recommendations: [],
        }
      : record,
  );
  detail();
  await screen.findByRole('heading', { name: 'Booking details' });
  fireEvent.click(screen.getByRole('button', { name: 'Get grounded coordination guidance' }));
  expect(await screen.findByText('Ask a coordinator to review.')).toBeInTheDocument();
  expect(privateApi).toHaveBeenCalledWith(
    'synthetic-session',
    '/seva/requests/booking-a/agent',
    null,
  );
  expect(
    screen.queryByRole('button', { name: 'Confirm assignment proposal' }),
  ).not.toBeInTheDocument();
});

test('unauthorized request errors display without private details', async () => {
  vi.mocked(privateApi).mockRejectedValue(new Error('Request not found for this account.'));
  detail();
  expect(await screen.findByRole('alert')).toHaveTextContent('Request not found');
  expect(screen.queryByText('Synthetic house')).not.toBeInTheDocument();
});

test('worker dashboard lists actual authorized visits with loading state', async () => {
  vi.mocked(useAuth).mockReturnValue({
    user: { ...citizen, id: 'worker-a', role: 'worker' },
    token: 'synthetic-session',
    signIn: vi.fn(),
    signOut: vi.fn(),
  });
  vi.mocked(privateApi).mockResolvedValue({ items: [record], total: 1, page: 1, limit: 20 });
  render(
    <MemoryRouter>
      <SevaDashboard />
    </MemoryRouter>,
  );
  expect(await screen.findByRole('link', { name: /Open visit request/ })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /My worker profile/ })).toBeInTheDocument();
});

test('coordinator must select a worker and explicitly confirm before assignment', async () => {
  vi.mocked(useAuth).mockReturnValue({
    user: { ...citizen, id: 'coord-a', role: 'coordinator' },
    token: 'synthetic-session',
    signIn: vi.fn(),
    signOut: vi.fn(),
  });
  vi.mocked(privateApi).mockImplementation(async (_token, path) =>
    path.endsWith('/agent')
      ? {
          candidates: [
            {
              worker_id: 'worker-a',
              display_name: 'Synthetic worker',
              workload: 0,
              reasons: ['Verified internally'],
            },
          ],
          next_action: 'Review proposal.',
          escalation_recommendations: [],
        }
      : record,
  );
  detail();
  await screen.findByRole('heading', { name: 'Booking details' });
  const button = screen.getByRole('button', { name: 'Confirm assignment proposal' });
  expect(button).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Get grounded coordination guidance' }));
  await screen.findByRole('option', { name: 'Synthetic worker' });
  fireEvent.change(screen.getByLabelText('Choose eligible worker'), {
    target: { value: 'worker-a' },
  });
  fireEvent.click(screen.getByLabelText(/I explicitly confirm this cancellation/));
  fireEvent.click(button);
  await waitFor(() =>
    expect(privateApi).toHaveBeenCalledWith(
      'synthetic-session',
      '/seva/requests/booking-a/assignment',
      expect.objectContaining({ worker_id: 'worker-a', confirmed: true, revision: 0 }),
    ),
  );
});

test('worker calendar submits declared windows with current revision', async () => {
  vi.mocked(useAuth).mockReturnValue({
    user: { ...citizen, id: 'worker-a', role: 'worker' },
    token: 'synthetic-session',
    signIn: vi.fn(),
    signOut: vi.fn(),
  });
  vi.mocked(privateApi).mockResolvedValue({
    id: 'worker-a',
    display_name: 'Synthetic worker',
    revision: 3,
    verification_status: 'pending_verification',
    verification_label: 'Internal only',
    availability: [],
    current_workload: 0,
    capacity: 5,
    active: true,
    categories: [],
    languages: [],
    districts: [],
    areas: [],
    qualifications: [],
    capabilities: [],
  });
  render(
    <MemoryRouter>
      <SevaWorkerProfile />
    </MemoryRouter>,
  );
  await screen.findByRole('heading', { name: 'Synthetic worker' });
  fireEvent.change(screen.getByLabelText('Available start (local time)'), {
    target: { value: '2099-01-01T12:00' },
  });
  fireEvent.change(screen.getByLabelText('Available end (up to 4 hours)'), {
    target: { value: '2099-01-01T13:00' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Add declared availability window' }));
  await waitFor(() =>
    expect(privateApi).toHaveBeenCalledWith(
      'synthetic-session',
      '/seva/workers/worker-a/availability',
      expect.objectContaining({
        revision: 3,
        slots: [{ start: expect.stringMatching(/Z$/), end: expect.stringMatching(/Z$/) }],
      }),
    ),
  );
});
