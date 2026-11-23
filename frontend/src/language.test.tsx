import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import { dictionaries, LanguageProvider, useLanguage } from './language';
import { localizedDate, translate } from './language';
import { translations } from './translations';

afterEach(() => {
  cleanup();
  localStorage.clear();
});
function Preview() {
  const { language, setLanguage, t } = useLanguage();
  return (
    <>
      <p>{language}</p>
      <p>{t('partial')}</p>
      <button onClick={() => setLanguage('te')}>Telugu</button>
    </>
  );
}
test('all supported dictionaries have every English key', () => {
  for (const language of ['hi', 'te']) {
    expect(Object.keys(dictionaries[language]).sort()).toEqual(Object.keys(dictionaries.en).sort());
    expect(Object.values(dictionaries[language]).every(Boolean)).toBe(true);
  }
});

test('static translations are nonempty Unicode and preserve unknown official text', () => {
  for (const [english, values] of Object.entries(translations)) {
    expect(english.trim()).not.toBe('');
    expect(values.hi).toMatch(/[\u0900-\u097f]/);
    expect(values.te).toMatch(/[\u0c00-\u0c7f]/);
    expect(values.hi).not.toContain('\ufffd');
    expect(values.te).not.toContain('\ufffd');
  }
  expect(translate('Account alias', 'hi')).toBe('खाता उपनाम');
  expect(translate('Account alias', 'te')).toBe('ఖాతా మారుపేరు');
  expect(translate('Official condition: 18 to 70', 'te')).toBe('Official condition: 18 to 70');
  expect(localizedDate('2026-11-23T12:00:00Z', 'te')).not.toBe('Invalid Date');
});
test('invalid stored language falls back safely and a selection persists', () => {
  localStorage.setItem('yojanasetu-language', '__proto__');
  render(
    <LanguageProvider>
      <Preview />
    </LanguageProvider>,
  );
  expect(screen.getByText('en')).toBeTruthy();
  fireEvent.click(screen.getByText('Telugu'));
  expect(document.documentElement.lang).toBe('te');
  expect(localStorage.getItem('yojanasetu-language')).toBe('te');
  expect(screen.getByText(dictionaries.te.partial)).toBeTruthy();
});
