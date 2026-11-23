import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { Assistant } from './assistant';
import { api } from './api';

vi.mock('./api', () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const response = {
  conversation_id: 'c'.repeat(43),
  profile: { age: 60, state: null },
  message: 'Source evidence is available.',
  mode: 'evidence-only RAG (no LLM)',
  warnings: [],
  follow_up_questions: ['What is your age in years?'],
  disclaimer: 'Preliminary guidance only.',
  recommendations: [
    {
      scheme_id: 'synthetic-test',
      scheme_name: 'Synthetic test scheme',
      status: 'Unable to determine',
      completeness: 'partial',
      conditions: [],
      warnings: [],
      evidence: [
        {
          chunk_id: 'chunk',
          source_id: 'test',
          document_title: 'Synthetic test document',
          official_url: 'https://example.invalid/test.pdf',
          page: 2,
          quote: 'Test condition evidence.',
          retrieved_at: '2026-11-16T00:00:00Z',
          published_at: null,
          verification_status: 'synthetic',
          content_hash: 'hash',
        },
      ],
    },
  ],
};

function mount() {
  const onMatches = vi.fn();
  render(
    <MemoryRouter>
      <Assistant onMatches={onMatches} />
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText('Local development token'), {
    target: { value: 'local-token' },
  });
  fireEvent.change(screen.getByLabelText('Your question'), {
    target: { value: 'What support might help?' },
  });
  return onMatches;
}

test('shows grounded cards, citations, honest mode and follow-up with session isolation header', async () => {
  vi.mocked(api).mockResolvedValue(response);
  const onMatches = mount();
  fireEvent.click(screen.getByRole('button', { name: 'Find relevant schemes' }));
  expect(await screen.findByText('Unable to determine')).toBeInTheDocument();
  expect(screen.getByText('evidence-only RAG (no LLM)')).toBeInTheDocument();
  expect(screen.getByText('Synthetic test document · page 2')).toBeInTheDocument();
  expect(
    screen.getByText(/Synthetic test document — not government information/),
  ).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Read official source/ })).toHaveAttribute(
    'href',
    'https://example.invalid/test.pdf',
  );
  expect(onMatches).toHaveBeenCalledWith(response.recommendations);
  expect(vi.mocked(api).mock.calls[0][3]?.['X-Session-Key']).toMatch(/^[a-zA-Z0-9_-]{32,128}$/);
  fireEvent.change(screen.getByLabelText('Your question'), {
    target: { value: 'I am 55 years old' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Ask follow-up' }));
  await waitFor(() => expect(api).toHaveBeenCalledTimes(2));
  expect(vi.mocked(api).mock.calls[1][0]).toBe('/ai/scheme-chat');
  // Prior parsed form values must not override a correction in a new question.
  expect(vi.mocked(api).mock.calls[1][2]).toEqual({
    question: 'I am 55 years old',
    profile: {},
    conversation_id: response.conversation_id,
  });
  expect(screen.getByLabelText('State of residence')).toHaveValue('');
});

test('reports API failures and allows retry without fabricating matches', async () => {
  vi.mocked(api).mockRejectedValue(new Error('Knowledge base unavailable'));
  const onMatches = mount();
  fireEvent.click(screen.getByRole('button', { name: 'Find relevant schemes' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Knowledge base unavailable');
  expect(onMatches).not.toHaveBeenCalled();
  expect(screen.getByRole('button', { name: 'Find relevant schemes' })).toBeEnabled();
});

test('empty results and reset preserve the distinction between missing evidence and ineligibility', async () => {
  vi.mocked(api).mockResolvedValue({
    ...response,
    recommendations: [],
    message: 'Information cannot currently be verified.',
  });
  const onMatches = mount();
  fireEvent.click(screen.getByRole('button', { name: 'Find relevant schemes' }));
  expect(await screen.findByText('Information cannot currently be verified.')).toBeInTheDocument();
  expect(screen.queryByText('Unable to determine')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Start new conversation' }));
  expect(screen.queryByRole('region', { name: 'Conversation' })).not.toBeInTheDocument();
  expect(onMatches).toHaveBeenLastCalledWith([]);
});
