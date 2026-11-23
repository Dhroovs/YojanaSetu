import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import { dictionaries, LanguageProvider, useLanguage } from './language';

afterEach(() => { cleanup(); localStorage.clear(); });
function Preview() {
  const { language, setLanguage, t } = useLanguage();
  return <><p>{language}</p><p>{t('partial')}</p><button onClick={() => setLanguage('te')}>Telugu</button></>;
}
test('all supported dictionaries have every English key', () => {
  for (const language of ['hi', 'te']) {
    expect(Object.keys(dictionaries[language]).sort()).toEqual(Object.keys(dictionaries.en).sort());
    expect(Object.values(dictionaries[language]).every(Boolean)).toBe(true);
  }
});
test('invalid stored language falls back safely and a selection persists', () => {
  localStorage.setItem('yojanasetu-language', '__proto__');
  render(<LanguageProvider><Preview /></LanguageProvider>);
  expect(screen.getByText('en')).toBeTruthy();
  fireEvent.click(screen.getByText('Telugu'));
  expect(document.documentElement.lang).toBe('te');
  expect(localStorage.getItem('yojanasetu-language')).toBe('te');
  expect(screen.getByText(dictionaries.te.partial)).toBeTruthy();
});
