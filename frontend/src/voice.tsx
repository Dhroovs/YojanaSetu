import { useEffect, useRef, useState } from 'react';
import { useLanguage } from './language';

interface Recognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
type SpeechWindow = {
  SpeechRecognition?: new () => Recognition;
  webkitSpeechRecognition?: new () => Recognition;
};

export function VoiceAssistance({
  onQuestion,
  response,
}: {
  onQuestion: (value: string) => void;
  response: string;
}) {
  const { tr } = useLanguage();

  const { language } = useLanguage();
  const [consent, setConsent] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const recognition = useRef<Recognition>();
  const speech = window as unknown as SpeechWindow;
  const Engine = speech.SpeechRecognition || speech.webkitSpeechRecognition;
  const synthesis = window.speechSynthesis;
  const locale = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN' }[language] || 'en-IN';
  const voice =
    voices.find((v) => v.lang.toLowerCase() === locale.toLowerCase()) ||
    voices.find((v) => v.lang.toLowerCase().startsWith(language));
  useEffect(() => {
    if (!synthesis) return;
    const refresh = () => setVoices(synthesis.getVoices());
    refresh();
    synthesis.addEventListener?.('voiceschanged', refresh);
    return () => {
      synthesis.removeEventListener?.('voiceschanged', refresh);
      synthesis.cancel();
    };
  }, [synthesis]);
  useEffect(() => {
    setRecording(false);
    return () => {
      if (recognition.current) {
        recognition.current.onresult = null;
        recognition.current.onerror = null;
        recognition.current.onend = null;
        recognition.current.abort();
      }
      synthesis?.cancel();
    };
  }, [language, synthesis]);
  function start() {
    if (!Engine || !consent) return;
    setError('');
    const engine = new Engine();
    recognition.current = engine;
    engine.lang = locale;
    engine.continuous = false;
    engine.interimResults = true;
    engine.onresult = (event) =>
      setTranscript(
        Array.from(event.results)
          .map((result) => result[0].transcript)
          .join(' ')
          .slice(0, 1500),
      );
    engine.onerror = (event) => {
      setRecording(false);
      setError(
        event.error === 'not-allowed'
          ? 'Microphone permission was denied. You can type your question.'
          : event.error === 'language-not-supported'
            ? 'Speech recognition does not support this language here. Use text instead.'
            : 'Speech recognition failed. You can type your question.',
      );
    };
    engine.onend = () => setRecording(false);
    try {
      engine.start();
      setRecording(true);
    } catch {
      setRecording(false);
      setError('Microphone could not start. You can type your question.');
    }
  }
  return (
    <section className="panel" aria-label={tr('Voice assistance')}>
      <h2>{tr('Voice assistance')}</h2>
      <p>
        {tr(
          'Your browser may send speech to its external speech service. This application does not store audio. Language support depends on your browser and installed voices. Text is always available.',
        )}
      </p>
      <label className="check-label">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => {
            setConsent(e.target.checked);
            if (!e.target.checked) {
              recognition.current?.abort();
              synthesis?.cancel();
              setRecording(false);
            }
          }}
        />
        {tr('I consent to browser speech processing, which may use an external service.')}
      </label>
      {!Engine && (
        <p role="status">
          {tr('Speech recognition is unavailable in this browser. Type your question instead.')}
        </p>
      )}
      <div className="row">
        <button type="button" disabled={!Engine || !consent || recording} onClick={start}>
          {tr('Start recording')}
        </button>
        <button
          type="button"
          disabled={!recording}
          onClick={() => {
            recognition.current?.stop();
            setRecording(false);
          }}
        >
          {tr('Stop recording')}
        </button>
      </div>
      <p role="status">{recording ? tr('Listening…') : tr('Microphone stopped')}</p>
      <label>
        {tr('Transcript preview (editable)')}
        <textarea
          value={transcript}
          maxLength={1500}
          onChange={(e) => setTranscript(e.target.value)}
        />
      </label>
      <button
        type="button"
        disabled={!transcript.trim() || recording}
        onClick={() => onQuestion(transcript)}
      >
        {tr('Use transcript as question')}
      </button>
      {!voice && <p>{tr('No installed voice for this language. Text remains available.')}</p>}
      <div className="row">
        <button
          type="button"
          disabled={!synthesis || !voice || !response || !consent}
          onClick={() => {
            synthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(response.slice(0, 5000));
            utterance.lang = locale;
            utterance.voice = voice!;
            utterance.onerror = () =>
              setError('Speech playback failed. Read the text response instead.');
            synthesis.speak(utterance);
          }}
        >
          {tr('Replay response')}
        </button>
        <button type="button" disabled={!synthesis} onClick={() => synthesis?.cancel()}>
          {tr('Stop speaking')}
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
