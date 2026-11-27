import { SPEECH_CODES } from './i18n/strings'

// ---- Text to speech ----
export function speak(text, lang, onEnd) {
  const synth = window.speechSynthesis
  if (!synth) return { ok: false }
  synth.cancel()
  const code = SPEECH_CODES[lang] || 'en-IN'
  const voices = synth.getVoices()
  const voice = voices.find((v) => v.lang === code) || voices.find((v) => v.lang?.startsWith(lang))
  // Chrome stops long utterances, so speak sentence by sentence
  const parts = text.split(/(?<=[.!?।])\s+|\n+/).map((s) => s.trim()).filter(Boolean)
  parts.forEach((p, i) => {
    const u = new SpeechSynthesisUtterance(p)
    u.lang = code
    if (voice) u.voice = voice
    u.rate = 0.95
    if (i === parts.length - 1) u.onend = onEnd
    synth.speak(u)
  })
  return { ok: true, hasVoice: !!voice || voices.length === 0 }
}

export const stopSpeaking = () => window.speechSynthesis?.cancel()

// ---- Speech to text ----
export function listen(lang, { onResult, onEnd, onError }) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return null
  const r = new SR()
  r.lang = SPEECH_CODES[lang] || 'en-IN'
  r.interimResults = true
  r.continuous = false
  r.onresult = (e) => onResult(Array.from(e.results).map((x) => x[0].transcript).join(' '))
  r.onerror = (e) => onError?.(e.error)
  r.onend = onEnd
  r.start()
  return r
}
