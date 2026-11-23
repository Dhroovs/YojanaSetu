import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import { useSessionResults } from './session-results';

afterEach(cleanup);
test('logout/session change clears results and ignores stale responses from the previous user', () => {
  let receive: (values: string[]) => void = () => {};
  function Results({ owner }: { owner: string }) {
    const [values, accept] = useSessionResults<string>(owner);
    receive = accept;
    return <p>{values.join(',') || 'No private results'}</p>;
  }
  const view = render(<Results owner="session-a" />);
  act(() => receive(['Synthetic private result A']));
  const oldResponse = receive;
  expect(screen.getByText('Synthetic private result A')).toBeInTheDocument();
  view.rerender(<Results owner="session-b" />);
  act(() => receive(['Synthetic private result B']));
  act(() => oldResponse(['Late private result A']));
  expect(screen.getByText('Synthetic private result B')).toBeInTheDocument();
  expect(screen.queryByText(/private result A/)).not.toBeInTheDocument();
  view.rerender(<Results owner="signed-out" />);
  expect(screen.getByText('No private results')).toBeInTheDocument();
});
