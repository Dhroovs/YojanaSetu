import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';
import { SchemeCard } from './scheme-card';

test('demo scheme card labels fictional data and navigates to details', () => {
  render(
    <MemoryRouter>
      <Routes>
        <Route
          path="/"
          element={
            <SchemeCard
              scheme={{
                id: 'demo-test',
                title: 'Learning example',
                category: 'Education',
                summary: 'Demo description',
                eligibility: [],
                documents: [],
                guidance: [],
                is_demo: true,
                source_url: null,
              }}
            />
          }
        />
        <Route path="/schemes/demo-test" element={<p>Details destination</p>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText(/Fictional demo/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('link', { name: /Explore scheme/ }));
  expect(screen.getByText('Details destination')).toBeInTheDocument();
});
