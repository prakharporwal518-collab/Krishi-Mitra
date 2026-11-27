import { useRef, useState } from 'react'
import { api } from '../api'
import { addHistory } from '../history'
import { ConfidenceBar, ErrorBox, PageTitle, ReadAloud, Spinner } from '../components/ui'

const SAMPLES = [
  { file: 'tomato_early_blight.jpg', icon: '🍅' },
  { file: 'potato_late_blight.jpg', icon: '🥔' },
  { file: 'tomato_leaf_curl.jpg', icon: '🌀' },
  { file: 'maize_common_rust.jpg', icon: '🌽' },
  { file: 'tomato_healthy.jpg', icon: '🌱' },
]

export default function Scan({ t, lang, go }) {
  const camRef = useRef()
  const fileRef = useRef()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const pick = (f) => {
    if (!f) return
    setFile(f); setResult(null); setError(null)
    setPreview(URL.createObjectURL(f))
  }
  const reset = () => { setFile(null); setPreview(null); setResult(null); setError(null) }

  const loadSample = async (name) => {
    try {
      const blob = await (await fetch(`/samples/${name}`)).blob()
      pick(new File([blob], name, { type: blob.type || 'image/jpeg' }))
    } catch { setError('NETWORK') }
  }

  const diagnose = async () => {
    setLoading(true); setError(null)
    try {
      const r = await api.predict(file, lang)
      setResult(r)
      if (!r.low_confidence) addHistory({ via: 'photo', disease_id: r.disease_id, disease: r.disease, crop: r.crop, crop_name: r.crop_name, confidence: r.confidence })
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const summary = result && (result.is_healthy
    ? `${t('healthyTitle')} ${t('crop')}: ${result.crop_name}. ${t('healthyMsg')}`
    : `${t('crop')}: ${result.crop_name}. ${t('disease')}: ${result.disease}. ${t('confidence')}: ${Math.round(result.confidence)}%.`)

  return (
    <div>
      <PageTitle icon="📷" title={t('scanTitle')} sub={t('scanDesc')} />
      <input ref={camRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => pick(e.target.files[0])} />
      <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => pick(e.target.files[0])} />

      {!preview && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <button className="btn-primary flex-col py-8 text-xl" onClick={() => camRef.current.click()}><span className="text-5xl">📸</span>{t('takePhoto')}</button>
            <button className="btn-light flex-col py-8 text-xl" onClick={() => fileRef.current.click()}><span className="text-5xl">🖼️</span>{t('uploadPhoto')}</button>
          </div>
          <p className="mt-3 text-center text-sm text-gray-600">💡 {t('photoTips')}</p>
          <div className="card mt-5">
            <p className="mb-3 font-semibold text-leaf-800">{t('trySample')}</p>
            <div className="grid grid-cols-5 gap-2">
              {SAMPLES.map((s) => (
                <button key={s.file} onClick={() => loadSample(s.file)} className="relative overflow-hidden rounded-2xl ring-2 ring-leaf-200 active:scale-95">
                  <img src={`/samples/${s.file}`} alt={s.file} className="aspect-square w-full object-cover" />
                  <span className="absolute bottom-1 right-1 text-xl">{s.icon}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {preview && (
        <div className="card">
          <img src={preview} alt="leaf" className="mx-auto max-h-72 rounded-2xl object-contain" />
          {!result && !loading && (
            <div className="mt-4 grid gap-3">
              <button className="btn-primary text-xl" onClick={diagnose}>🔍 {t('diagnose')}</button>
              <button className="btn-light" onClick={reset}>↩️ {t('retake')}</button>
            </div>
          )}
          {loading && <Spinner label={t('analysing')} />}
        </div>
      )}

      <ErrorBox t={t} error={error} onRetry={reset} />

      {result && result.low_confidence && (
        <div className="card mt-4 border-2 border-yellow-300 bg-yellow-50">
          <p className="text-xl font-extrabold text-yellow-800">📷 {t('lowConfTitle')}</p>
          <p className="mt-2 text-yellow-900">{t('lowConfMsg')}</p>
          <p className="mt-3 text-sm text-gray-700">{result.crop_name} – {result.disease} ({Math.round(result.confidence)}%)</p>
          <div className="mt-2"><ConfidenceBar value={result.confidence} /></div>
          <div className="mt-4 grid gap-3">
            <button className="btn-primary" onClick={reset}>📸 {t('retake')}</button>
            <button className="btn-light" onClick={() => go('disease', { id: result.disease_id, crop: result.crop })}>{t('seeTreatment')} →</button>
          </div>
        </div>
      )}

      {result && !result.low_confidence && (
        <div className={`card mt-4 border-2 ${result.is_healthy ? 'border-leaf-500 bg-leaf-100' : 'border-red-200'}`}>
          {result.is_healthy ? (
            <>
              <p className="text-2xl font-extrabold text-leaf-800">✅ {t('healthyTitle')}</p>
              <p className="mt-1 text-leaf-900">{t('healthyMsg')}</p>
            </>
          ) : (
            <p className="text-sm font-bold uppercase tracking-wide text-red-700">🦠 {t('disease')}</p>
          )}
          <dl className="mt-3 space-y-2 text-lg">
            <div className="flex justify-between gap-2"><dt className="text-gray-600">{t('crop')}</dt><dd className="font-bold">{result.crop_name}</dd></div>
            {!result.is_healthy && <div className="flex justify-between gap-2"><dt className="text-gray-600">{t('disease')}</dt><dd className="text-right font-extrabold text-red-700">{result.disease}</dd></div>}
            <div className="flex justify-between"><dt className="text-gray-600">{t('confidence')}</dt><dd className="font-bold">{Math.round(result.confidence)}%</dd></div>
          </dl>
          <div className="mt-2"><ConfidenceBar value={result.confidence} /></div>
          {result.alternatives?.length > 0 && result.alternatives[0].confidence > 5 && (
            <p className="mt-3 text-sm text-gray-600">{t('possibly')}: {result.alternatives.filter((a) => a.confidence > 5).map((a) => `${a.disease} (${Math.round(a.confidence)}%)`).join(', ')}</p>
          )}
          <div className="mt-4 grid gap-3">
            <ReadAloud t={t} text={summary} lang={lang} />
            <button className="btn-primary text-xl" onClick={() => go('disease', { id: result.disease_id, crop: result.crop })}>💊 {t('seeTreatment')} →</button>
            <button className="btn-light" onClick={reset}>📸 {t('retake')}</button>
          </div>
        </div>
      )}
    </div>
  )
}
