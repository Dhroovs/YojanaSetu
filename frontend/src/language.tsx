import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

const en = {
  discover: 'Discover',
  assistant: 'Scheme assistant',
  assistance: 'My assistance',
  tracking: 'Track case',
  doorstep: 'SevaSetu',
  signIn: 'Sign in',
  account: 'My account',
  partial:
    'Partial interface translation. Scheme rules, legal conditions and most forms use English fallback.',
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
    partial: 'इंटरफ़ेस का आंशिक अनुवाद। योजना नियम, कानूनी शर्तें और अधिकांश फ़ॉर्म अंग्रेज़ी में उपलब्ध हैं।',
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
    partial: 'ఇంటర్‌ఫేస్ పాక్షిక అనువాదం. పథకం నియమాలు, చట్టపరమైన షరతులు మరియు చాలా ఫారమ్‌లు ఆంగ్లంలో ఉంటాయి.',
    book: 'ఇంటి వద్ద సహాయాన్ని అభ్యర్థించండి',
  },
};
const Context = createContext({
  language: 'en',
  setLanguage: (value: string) => { void value; },
  t: (key: Key) => en[key],
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
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useLanguage() {
  return useContext(Context);
}
