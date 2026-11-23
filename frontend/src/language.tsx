import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { translations } from './translations';

export function translate(text: string, language: string): string {
  const result = translations[text.trim()]?.[language as 'hi' | 'te'];
  return language === 'en' || !result
    ? text
    : `${text.startsWith(' ') ? ' ' : ''}${result}${text.endsWith(' ') ? ' ' : ''}`;
}
export const localeFor = (language: string) =>
  ({ en: 'en-IN', hi: 'hi-IN', te: 'te-IN' })[language] || 'en-IN';
export function localizedDate(value: string, language: string) {
  try {
    return new Intl.DateTimeFormat(localeFor(language), {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: 'Asia/Kolkata',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

const en = {
  discover: 'Discover',
  assistant: 'Scheme assistant',
  assistance: 'My assistance',
  tracking: 'Track case',
  doorstep: 'SevaSetu',
  signIn: 'Sign in',
  account: 'My account',
  partial:
    'Draft interface translation. Official evidence and some diagnostics keep their source language.',
  book: 'Request doorstep assistance',
};
type Key = keyof typeof en;
export const dictionaries: Record<string, Record<Key, string>> = {
  en,
  hi: {
    discover: 'योजनाएँ खोजें',
    assistant: 'योजना सहायक',
    assistance: 'मेरी सहायता',
    tracking: 'स्थिति देखें',
    doorstep: 'सेवासेतु',
    signIn: 'साइन इन',
    account: 'मेरा खाता',
    partial: 'इंटरफ़ेस अनुवाद प्रारूप है। आधिकारिक प्रमाण और कुछ संदेश मूल भाषा में रहते हैं।',
    book: 'घर पर सहायता का अनुरोध करें',
  },
  te: {
    discover: 'పథకాలను కనుగొనండి',
    assistant: 'పథకం సహాయకుడు',
    assistance: 'నా సహాయం',
    tracking: 'స్థితిని చూడండి',
    doorstep: 'సేవాసేతు',
    signIn: 'సైన్ ఇన్',
    account: 'నా ఖాతా',
    partial: 'ఇంటర్‌ఫేస్ అనువాదం ముసాయిదా. అధికారిక ఆధారాలు, కొన్ని సందేశాలు మూల భాషలో ఉంటాయి.',
    book: 'ఇంటి వద్ద సహాయాన్ని అభ్యర్థించండి',
  },
};
const Context = createContext({
  language: 'en',
  setLanguage: (value: string) => {
    void value;
  },
  t: (key: Key) => en[key],
  tr: (text: string) => text,
  formatDate: (value: string) => localizedDate(value, 'en'),
  formatNumber: (value: number) => new Intl.NumberFormat('en-IN').format(value),
});
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, set] = useState(() => {
    try {
      const value = localStorage.getItem('yojanasetu-language') || 'en';
      return Object.hasOwn(dictionaries, value) ? value : 'en';
    } catch {
      return 'en';
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem('yojanasetu-language', language);
    } catch {
      /* Storage may be unavailable. */
    }
    document.documentElement.lang = language;
  }, [language]);
  return (
    <Context.Provider
      value={{
        language,
        setLanguage: (value) => {
          if (Object.hasOwn(dictionaries, value)) set(value);
        },
        t: (key) => dictionaries[language]?.[key] || en[key],
        tr: (text) => translate(text, language),
        formatDate: (value) => localizedDate(value, language),
        formatNumber: (value) => new Intl.NumberFormat(localeFor(language)).format(value),
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useLanguage() {
  return useContext(Context);
}
