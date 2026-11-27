import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { addHistory } from '../history'
import { listen } from '../speech'
import { ErrorBox, PageTitle, Spinner } from '../components/ui'

export default function Symptoms({ t, lang, go, crops }) {
  const [crop, setCrop] = useState(null)
  const [list, setList] = useState([])
  const [picked, setPicked] = useState([])
  const [transcript, setTranscript] = useState('')
  const [listening, setListening] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const recRef = useRef()

  useEffect(() => {
    if (!crop) return
    setList([]); setPicked([]); setResult(null)
    api.symptomList(lang, crop).then(setList).catch((e) => setError(e.message))
  }, [crop, lang])

  const toggle = (id) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))

  const mic = () => {
    if (listening) { recRef.current?.stop(); return }
    setError(null)
    const r = listen(lang, {
      onResult: setTranscript,
      onEnd: () => setListening(false),
      onError: (e) => { setListening(false); if (e !== 'no-speech' && e !== 'aborted') setError(e) },
    })
    if (!r) { setError(t('speechUnsupported')); return }
    recRef.current = r
    setListening(true)
  }

  const find = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await api.symptoms({ crop, symptoms: picked, text: transcript || null, lang })
      setResult(r)
      if (r.detected_symptoms?.length) setPicked((p) => [...new Set([...p, ...r.detected_symptoms])])
      const top = r.matches[0]
      if (top) addHistory({ via: 'symptoms', disease_id: top.disease_id, disease: top.disease, crop, crop_name: top.crop_name, confidence: top.score })
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  return (
    <div>
      <PageTitle icon="📝" title={t('symTitle')} sub={t('symDesc')} />
      <h2 className="h2 mb-2">1. {t('selectCrop')}</h2>
      <div className="grid grid-cols-4 gap-2">
        {crops.filter((c) => c.main).map((c) => (
          <button key={c.id} onClick={() => setCrop(c.id)}
            className={`flex flex-col items-center rounded-2xl p-2 text-sm font-semibold ring-2 transition active:scale-95 ${crop === c.id ? 'bg-leaf-700 text-white ring-leaf-700' : 'bg-white ring-leaf-100'}`}>
            <span className="text-3xl">{c.icon}</span>{c.name}
          </button>
        ))}
      </div>

      {crop && (
        <>
          <h2 className="h2 mb-2 mt-6">2. {t('selectSymptoms')}</h2>
          <button onClick={mic} className={`btn mb-3 w-full ${listening ? 'animate-pulse bg-red-600 text-white' : 'bg-soil-100 text-soil-700 ring-2 ring-soil-400'}`}>
            🎤 {listening ? t('listening') : t('speak')}
          </button>
          {transcript && <p className="mb-3 rounded-xl bg-white p-3 text-gray-700">🗣️ {t('youSaid')}: “{transcript}”</p>}
          {!list.length && !error && <Spinner />}
          <div className="grid grid-cols-2 gap-2">
            {list.map((s) => {
              const on = picked.includes(s.id)
              return (
                <button key={s.id} onClick={() => toggle(s.id)} aria-pressed={on}
                  className={`flex items-center gap-2 rounded-2xl p-3 text-left text-sm font-semibold ring-2 transition active:scale-95 ${on ? 'bg-leaf-100 ring-leaf-600' : 'bg-white ring-gray-100'}`}>
                  <span className="text-2xl">{on ? '✅' : s.icon}</span><span>{s.name}</span>
                </button>
              )
            })}
          </div>
          <button className="btn-primary mt-5 w-full text-xl" disabled={loading || (!picked.length && !transcript)} onClick={find}>🔍 {t('findDisease')}</button>
        </>
      )}

      {loading && <Spinner />}
      <ErrorBox t={t} error={error} />

      {result && (
        <div className="mt-5">
          <h2 className="h2 mb-2">{t('topMatches')}</h2>
          {!result.matches.length && <p className="card">{t('noMatch')}</p>}
          <div className="space-y-3">
            {result.matches.map((m, i) => (
              <button key={m.disease_id} onClick={() => go('disease', { id: m.disease_id, crop })} className="card block w-full text-left active:scale-[.98]">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-lg font-extrabold text-leaf-900">{i + 1}. {m.disease}</p>
                  <span className="rounded-full bg-leaf-100 px-3 py-1 text-sm font-bold text-leaf-800">{m.score}% {t('match')}</span>
                </div>
                <p className="mt-1 text-sm text-gray-600">✔ {m.matched.join(' · ')}</p>
                <p className="mt-2 font-bold text-leaf-700">{t('seeTreatment')} →</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
