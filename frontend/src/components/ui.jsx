import { useEffect, useState } from 'react'
import { speak, stopSpeaking } from '../speech'

export function Spinner({ label }) {
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-leaf-800" role="status">
      <div className="h-14 w-14 animate-spin rounded-full border-[6px] border-leaf-200 border-t-leaf-700" />
      {label && <p className="text-lg font-semibold">{label}</p>}
    </div>
  )
}

export function ErrorBox({ t, error, onRetry }) {
  if (!error) return null
  const msg = error === 'NETWORK' ? t('networkError') : error
  return (
    <div className="card mt-4 border-2 border-red-200 bg-red-50 text-red-800">
      <p className="text-lg font-bold">⚠️ {t('error')}</p>
      <p className="mt-1">{msg}</p>
      {onRetry && <button className="btn-light mt-3" onClick={onRetry}>🔄 {t('retake')}</button>}
    </div>
  )
}

export function ReadAloud({ t, text, lang }) {
  const [on, setOn] = useState(false)
  const [warn, setWarn] = useState(false)
  useEffect(() => () => stopSpeaking(), [])
  useEffect(() => { stopSpeaking(); setOn(false) }, [text])
  const toggle = () => {
    if (on) { stopSpeaking(); setOn(false); return }
    const r = speak(text, lang, () => setOn(false))
    if (!r.ok) { setWarn(true); return }
    setWarn(!r.hasVoice)
    setOn(true)
  }
  return (
    <div>
      <button onClick={toggle} className={`btn w-full ${on ? 'bg-soil-400 text-white' : 'bg-soil-100 text-soil-700 ring-2 ring-soil-400'}`}>
        {on ? '⏹️ ' + t('stop') : '🔊 ' + t('readAloud')}
      </button>
      {warn && <p className="mt-2 text-sm text-soil-700">{t('ttsMissing')}</p>}
    </div>
  )
}

export function ConfidenceBar({ value }) {
  const color = value >= 80 ? 'bg-leaf-600' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="h-4 w-full overflow-hidden rounded-full bg-gray-200">
      <div className={`h-full ${color} transition-all`} style={{ width: `${Math.min(100, value)}%` }} />
    </div>
  )
}

export function PageTitle({ icon, title, sub }) {
  return (
    <div className="mb-4">
      <h1 className="text-2xl font-extrabold text-leaf-900">{icon} {title}</h1>
      {sub && <p className="mt-1 text-gray-600">{sub}</p>}
    </div>
  )
}
