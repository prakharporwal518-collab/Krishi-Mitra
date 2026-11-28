import { useEffect, useState } from 'react'
import { api } from '../api'
import { ErrorBox, ReadAloud, Spinner } from '../components/ui'
import SprayCalculator from '../components/SprayCalculator'

const Section = ({ icon, title, children, tone = 'card' }) => (
  <section className={`${tone} mt-4`}>
    <h2 className="h2 mb-2">{icon} {title}</h2>
    {children}
  </section>
)
const List = ({ items }) => (
  <ul className="space-y-2">{items.map((x, i) => <li key={i} className="flex gap-2"><span className="text-leaf-600">●</span><span>{x}</span></li>)}</ul>
)

export default function Disease({ t, lang, params, region, go }) {
  const [d, setD] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setD(null); setError(null)
    api.disease(params.id, { lang, crop: params.crop, ...region }).then(setD).catch((e) => setError(e.message))
  }, [params.id, params.crop, lang, region])

  if (error) return <ErrorBox t={t} error={error} />
  if (!d) return <Spinner />

  const healthy = d.kind === 'healthy'
  const c = d.chemical
  const speech = [
    d.name, d.about,
    `${t('signs')}: ${d.symptoms.join('. ')}`,
    !healthy && `${t('chemical')}: ${c.product}. ${t('dosage')}: ${c.dosage}. ${t('timing')}: ${c.timing}.`,
    `${t('organic')}: ${d.organic.join('. ')}`,
    `${t('prevention')}: ${d.prevention.join('. ')}`,
    !healthy && `${t('warningTitle')}: ${d.warning}`,
    ...d.region_tips.map((r) => r.tip),
  ].filter(Boolean).join('. ')

  return (
    <div>
      <button className="mb-3 rounded-lg font-bold text-leaf-700 transition-colors duration-300 hover:text-leaf-900 hover:underline" onClick={() => go('back')}>← {t('back')}</button>
      <div className={`card ${healthy ? 'bg-leaf-100' : 'bg-gradient-to-br from-white to-leaf-50'}`}>
        <p className="text-sm font-bold uppercase tracking-wide text-gray-500">{t('crop')}: {d.crop_name}</p>
        <h1 className="mt-1 text-3xl font-extrabold text-leaf-900">{healthy ? '✅' : '🦠'} {d.name}</h1>
        {d.pathogen && <p className="mt-1 text-sm italic text-gray-600">{d.pathogen}</p>}
        <p className="mt-3 inline-block rounded-full bg-leaf-700 px-3 py-1 text-xs font-bold text-white">🏛️ {t('source')}: {d.source}</p>
        {!d.translated && <p className="mt-3 rounded-xl bg-yellow-50 p-2 text-sm text-yellow-800">🌐 {t('notTranslated')}</p>}
        {d.auto_translated && <p className="mt-3 rounded-xl bg-blue-50 p-2 text-sm text-blue-800">🌐 {t('autoTranslated')}</p>}
        <div className="mt-4"><ReadAloud t={t} text={speech} lang={d.translated ? lang : 'en'} /></div>
      </div>

      <div className="lg:grid lg:grid-cols-2 lg:items-start lg:gap-x-4">
      <Section icon="📖" title={t('about')}><p className="text-lg">{d.about}</p></Section>
      <Section icon="🔎" title={t('signs')}><List items={d.symptoms} /></Section>

      {!healthy && (
        <Section icon="🧪" title={t('chemical')} tone="card lg:col-span-2">
          <dl className="space-y-3 text-lg lg:grid lg:grid-cols-3 lg:gap-4 lg:space-y-0">
            <div><dt className="text-sm font-bold text-gray-500">{t('product')}</dt><dd className="font-extrabold text-leaf-900">{c.product}</dd></div>
            <div className="rounded-2xl bg-leaf-50 p-3"><dt className="text-sm font-bold text-gray-500">⚖️ {t('dosage')}</dt><dd className="font-bold">{c.dosage}</dd></div>
            <div><dt className="text-sm font-bold text-gray-500">⏰ {t('timing')}</dt><dd>{c.timing}</dd></div>
          </dl>
          {d.dose_per_litre && <SprayCalculator t={t} dose={d.dose_per_litre} product={c.product} />}
          <div className="mt-4 rounded-2xl bg-orange-50 p-3">
            <p className="mb-2 font-bold text-orange-800">🧤 {t('safety')}</p>
            <List items={c.safety} />
          </div>
        </Section>
      )}

      <Section icon="🌿" title={t('organic')}><List items={d.organic} /></Section>
      <Section icon="🛡️" title={t('prevention')}><List items={d.prevention} /></Section>

      {d.region_tips.length > 0 && (
        <Section icon="📍" title={t('regionTips')} tone="card bg-blue-50 ring-blue-100 lg:col-span-2">
          {d.region_tips.map((r, i) => (
            <div key={i} className="mb-3 last:mb-0">
              <p>{r.tip}</p>
              <p className="mt-1 text-xs text-gray-500">{r.states.join(', ')} · {r.seasons.map((s) => t(s)).join(', ')}</p>
            </div>
          ))}
        </Section>
      )}

      </div>

      {!healthy && (
        <section className="card mt-4 border-2 border-red-300 bg-red-50">
          <h2 className="mb-1 text-xl font-extrabold text-red-800">⚠️ {t('warningTitle')}</h2>
          <p className="text-red-900">{d.warning}</p>
        </section>
      )}

      <button className="btn-light mt-4 w-full" onClick={() => go('help')}>📞 {t('kccTitle')} 1800-180-1551</button>
      <p className="mt-4 text-center text-xs text-gray-500">{t('disclaimer')}</p>
    </div>
  )
}
