import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { VoiceAssistance } from './voice';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
test('unsupported speech stays on text fallback and never requests microphone access', () => {
  vi.stubGlobal('webkitSpeechRecognition', undefined);
  vi.stubGlobal('SpeechRecognition', undefined);
  render(<VoiceAssistance onQuestion={vi.fn()} response="" />);
  expect(screen.getByRole('button', { name: 'Start recording' })).toBeDisabled();
  expect(screen.getByText(/Speech recognition is unavailable/)).toBeInTheDocument();
});
test('recording requires consent, transcript remains editable and submits only after review', () => {
  const start = vi.fn(),
    stop = vi.fn(),
    abort = vi.fn(),
    submit = vi.fn();
  const instances: Engine[] = [];
  class Engine {
    lang = '';
    start = start;
    stop = stop;
    abort = abort;
    constructor() {
      instances.push(this);
    }
  }
  vi.stubGlobal('SpeechRecognition', Engine);
  render(<VoiceAssistance onQuestion={submit} response="" />);
  expect(start).not.toHaveBeenCalled();
  fireEvent.click(screen.getByLabelText(/I consent to browser speech processing/));
  fireEvent.click(screen.getByRole('button', { name: 'Start recording' }));
  expect(start).toHaveBeenCalledOnce();
  expect(instances[0].lang).toBe('en-IN');
  fireEvent.click(screen.getByRole('button', { name: 'Stop recording' }));
  expect(stop).toHaveBeenCalledOnce();
  fireEvent.change(screen.getByLabelText('Transcript preview (editable)'), {
    target: { value: 'Edited synthetic question' },
  });
  expect(submit).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Use transcript as question' }));
  expect(submit).toHaveBeenCalledWith('Edited synthetic question');
  fireEvent.click(screen.getByLabelText(/I consent to browser speech processing/));
  expect(abort).toHaveBeenCalled();
});
test('playback requires consent and an installed matching voice', () => {
  const speak = vi.fn(),
    cancel = vi.fn();
  vi.stubGlobal(
    'SpeechSynthesisUtterance',
    class {
      constructor(public text: string) {}
    },
  );
  vi.stubGlobal('speechSynthesis', {
    getVoices: () => [{ lang: 'en-IN', localService: true }],
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    speak,
    cancel,
  });
  render(<VoiceAssistance onQuestion={vi.fn()} response="Source-backed text" />);
  expect(screen.getByRole('button', { name: 'Replay response' })).toBeDisabled();
  fireEvent.click(screen.getByLabelText(/I consent to browser speech processing/));
  fireEvent.click(screen.getByRole('button', { name: 'Replay response' }));
  expect(speak).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole('button', { name: 'Stop speaking' }));
  expect(cancel).toHaveBeenCalled();
});
