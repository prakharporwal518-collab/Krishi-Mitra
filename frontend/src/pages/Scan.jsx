import { useRef, useState } from 'react'
import { api } from '../api'
import { addHistory } from '../history'
import Heatmap from '../components/Heatmap'
import { ConfidenceBar, ErrorBox, PageTitle, ReadAloud, Spinner } from '../components/ui'

const SAMPLES = [
  { file: 'tomato_early_blight.jpg', icon: '🍅' },
  { file: 'potato_late_blight.jpg', icon: '🥔' },
  { file: 'rice_blast.jpg', icon: '🌾' },
  { file: 'wheat_yellow_rust.jpg', icon: '🌿' },
  { file: 'cotton_wilt.jpg', icon: '☁️' },
  { file: 'tomato_leaf_curl.jpg', icon: '🌀' },
  { file: 'maize_common_rust.jpg', icon: '🌽' },
  { file: 'tomato_healthy.jpg', icon: '🌱' },
]

// Below MIN_CONFIDENCE (60%) the result is uncertain. Between POSSIBLE_MIN and 60% we still show the
// likely disease and its treatment, clearly marked as unconfirmed; below POSSIBLE_MIN we only ask for a retake.
const POSSIBLE_MIN = 35

const loadHint = () => { try { return localStorage.getItem('km_scan_crop') || '' } catch { return '' } }

export default function Scan({ t, lang, go, crops = [] }) {
  const camRef = useRef()
  const fileRef = useRef()
  const [file, setFile] = useState(null)
  const [hint, setHint] = useState(loadHint) // crop the farmer says this is ('' = detect automatically)
  const chooseHint = (c) => { setHint(c); setResult(null); try { localStorage.setItem('km_scan_crop', c) } catch { /* ignore */ } }
  const hintName = crops.find((c) => c.id === hint)?.name || hint
  // 7 main field crops by default; "More crops" adds the fruit and vegetable crops the photo AI also knows
  const [showMore, setShowMore] = useState(() => !!hint && !['tomato', 'potato', 'rice', 'wheat', 'cotton', 'maize', 'chilli'].includes(hint))
  const visibleCrops = showMore ? crops : crops.filter((c) => c.main)
  const moreToggle = crops.some((c) => !c.main) && (
    <button onClick={() => setShowMore((v) => !v)} aria-expanded={showMore}
      className="lift rounded-full bg-leaf-50 px-3 py-1.5 text-sm font-bold text-leaf-800 ring-2 ring-leaf-200 hover:ring-leaf-500">
      {showMore ? '➖ ' + t('fewerCrops') : '➕ ' + t('moreCrops')}
    </button>
  )
  // On an uncertain automatic result, let the farmer name the crop and re-check the same photo in one tap
  const cropRetry = !hint && (
    <div className="mt-3 rounded-xl bg-white/80 p-3">
      <p className="mb-2 text-sm font-bold text-leaf-900">🌱 {t('pickCropRetry')}</p>
      <div className="flex flex-wrap gap-2">
        {visibleCrops.map((c) => (
          <button key={c.id} onClick={() => { chooseHint(c.id); diagnose(c.id) }}
            className="lift rounded-full bg-white px-3 py-1.5 text-sm font-bold text-leaf-900 ring-2 ring-leaf-200 hover:ring-leaf-500">
            {c.icon} {c.name}
          </button>
        ))}
        {moreToggle}
      </div>
    </div>
  )
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

  const diagnose = async (cropOverride) => {
    const crop = typeof cropOverride === 'string' ? cropOverride : hint // onClick passes an event
    setLoading(true); setError(null)
    try {
      const r = await api.predict(file, lang, crop || undefined)
      setResult(r)
      if (!r.not_leaf && !r.crop_mismatch && (!r.low_confidence || r.confidence >= POSSIBLE_MIN)) addHistory({ via: 'photo', disease_id: r.disease_id, disease: r.disease, crop: r.crop, crop_name: r.crop_name, confidence: r.confidence })
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

      <div className="lg:grid lg:grid-cols-2 lg:items-start lg:gap-6">
      <div>
      <section className="card mb-4" aria-label={t('cropQuestion')}>
        <p className="font-extrabold text-leaf-900">🌱 {t('cropQuestion')}</p>
        <p className="mb-3 text-sm text-gray-600">{t('cropOptional')}</p>
        <div className="flex flex-wrap gap-2">
          {[{ id: '', icon: '✨', name: t('autoDetect') }, ...visibleCrops].map((c) => (
            <button key={c.id || 'auto'} onClick={() => chooseHint(c.id)} aria-pressed={hint === c.id}
              className={`lift rounded-full px-3 py-2 text-sm font-bold ring-2 ${hint === c.id ? 'bg-leaf-700 text-white ring-leaf-700' : 'bg-white text-leaf-900 ring-leaf-100 hover:ring-leaf-200'}`}>
              {c.icon} {c.name}
            </button>
          ))}
          {moreToggle}
        </div>
      </section>
      {!preview && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <button className="btn-primary flex-col py-8 lg:py-12 text-xl" onClick={() => camRef.current.click()}><span className="text-5xl">📸</span>{t('takePhoto')}</button>
            <button className="btn-light flex-col py-8 text-xl lg:py-12" onClick={() => fileRef.current.click()}><span className="text-5xl">🖼️</span>{t('uploadPhoto')}</button>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-sm font-semibold sm:grid-cols-4">
            <span className="rounded-xl bg-leaf-100 px-3 py-2 text-leaf-900">✅ {t('leafDo')}</span>
            <span className="rounded-xl bg-red-50 px-3 py-2 text-red-800">❌ {t('leafDont1')}</span>
            <span className="rounded-xl bg-red-50 px-3 py-2 text-red-800">❌ {t('leafDont2')}</span>
            <span className="rounded-xl bg-red-50 px-3 py-2 text-red-800">❌ {t('leafDont3')}</span>
          </div>
          <p className="mt-2 text-center text-sm text-gray-600">💡 {t('photoTips')}</p>
          <div className="card mt-5">
            <p className="mb-3 font-semibold text-leaf-800">{t('trySample')}</p>
            <div className="grid grid-cols-4 gap-2">
              {SAMPLES.map((s) => (
                <button key={s.file} onClick={() => loadSample(s.file)} className="tile relative overflow-hidden rounded-2xl ring-2 ring-leaf-200">
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
          <img src={preview} alt="leaf" className="mx-auto max-h-72 rounded-2xl object-contain lg:max-h-[26rem]" />
          {!result && !loading && (
            <div className="mt-4 grid gap-3">
              <button className="btn-primary text-xl" onClick={diagnose}>🔍 {t('diagnose')}</button>
              <button className="btn-light" onClick={reset}>↩️ {t('retake')}</button>
            </div>
          )}
          {loading && <Spinner label={t('analysing')} />}
        </div>
      )}
      </div>

      <div className="lg:sticky lg:top-8 [&>.card]:lg:mt-0">
      {!result && !error && (
        <div className="card card-flat hidden min-h-[16rem] flex-col items-center justify-center border-2 border-dashed border-leaf-200 text-center text-gray-500 lg:flex">
          <span className="text-6xl opacity-60">🔬</span>
          <p className="mt-3 text-lg font-semibold">{t('resultHere')}</p>
        </div>
      )}
      <ErrorBox t={t} error={error} onRetry={reset} />

      {result && result.low_confidence && !result.not_leaf && !result.crop_mismatch && result.confidence >= POSSIBLE_MIN && (
        <div className="card mt-4 border-2 border-yellow-300 bg-yellow-50">
          <p className="text-sm font-bold uppercase tracking-wide text-yellow-800">⚠️ {t('possibleTitle')}</p>
          <p className="mt-1 text-2xl font-extrabold text-red-700">{result.is_healthy ? t('healthyTitle') : result.disease}</p>
          <p className="text-gray-700">{t('crop')}: <b>{result.crop_name}</b> · {t('confidence')}: <b>{Math.round(result.confidence)}%</b></p>
          <div className="mt-2"><ConfidenceBar value={result.confidence} /></div>
          <p className="mt-3 text-yellow-900">{t('possibleMsg')}</p>
          <p className="mt-2 text-sm text-gray-700">🍃 {t('leafHint')}</p>
          {cropRetry}
          <div className="mt-4 grid gap-3">
            <ReadAloud t={t} text={`${t('possibleTitle')}: ${result.disease}. ${t('possibleMsg')}`} lang={lang} />
            <Heatmap t={t} file={file} label={result.label} />
            <button className="btn-primary text-xl" onClick={() => go('disease', { id: result.disease_id, crop: result.crop })}>💊 {t('seeTreatment')} →</button>
            <button className="btn-light" onClick={reset}>📸 {t('retake')}</button>
            <button className="btn-light" onClick={() => go('symptoms', { crop: hint || result.crop })}>📝 {t('trySymptoms')}</button>
          </div>
        </div>
      )}

      {result && result.low_confidence && (result.not_leaf || result.crop_mismatch || result.confidence < POSSIBLE_MIN) && (
        <div className="card mt-4 border-2 border-yellow-300 bg-yellow-50">
          <p className="text-xl font-extrabold text-yellow-800">📷 {result.crop_mismatch ? t('cropMismatchTitle').replace('{crop}', hintName) : t('lowConfTitle')}</p>
          <p className="mt-2 text-yellow-900">{result.crop_mismatch ? t('cropMismatchMsg') : t('lowConfMsg')}</p>
          <p className="mt-2 text-sm text-gray-700">🍃 {t('leafHint')}</p>
          {cropRetry}
          <p className="mt-3 rounded-xl bg-white/70 p-2 text-sm text-gray-700">🌾 {t('supportedCrops')}</p>
          <div className="mt-4 grid gap-3">
            <button className="btn-primary" onClick={reset}>📸 {t('retake')}</button>
            <button className="btn-light" onClick={() => go('symptoms', { crop: hint || undefined })}>📝 {t('trySymptoms')}</button>
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
            <Heatmap t={t} file={file} label={result.label} />
            <button className="btn-primary text-xl" onClick={() => go('disease', { id: result.disease_id, crop: result.crop })}>💊 {t('seeTreatment')} →</button>
            <button className="btn-light" onClick={reset}>📸 {t('retake')}</button>
          </div>
        </div>
      )}
      </div>
      </div>
    </div>
  )
}
