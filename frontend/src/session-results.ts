import { useEffect, useState } from 'react';

/** Never display another session's results, including late responses after logout. */
export function useSessionResults<T>(owner: string) {
  const [state, setState] = useState<{ owner: string; values: T[] }>({ owner, values: [] });
  useEffect(() => {
    setState({ owner, values: [] });
  }, [owner]);
  const receive = (values: T[]) =>
    setState((current) => (current.owner === owner ? { owner, values } : current));
  return [state.owner === owner ? state.values : [], receive] as const;
}
