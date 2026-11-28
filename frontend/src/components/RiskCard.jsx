import { useEffect, useState } from 'react'
import { api } from '../api'
import { assessRisk, getForecast } from '../weather'

// "Disease risk: next 3 days" card for the home dashboard
export default function RiskCard({ t, lang, region, go }) {
  const [state, setState] = useState({ loading: false })
  useEffect(() => {
    if (!region.state) return
    let live = true
    setState({ loading: true })
    getForecast(region.state)
      .then(async ({ days, offline }) => {
        const risks = assessRisk(days, region.season).slice(0, 6)
        const named = await Promise.all(risks.map(async (r) => {
          const d = await api.disease(r.id, { lang }).catch(() => null)
          return { ...r, name: d?.name || r.id, crop: d?.crop_name || '' }
        }))
        if (live) setState({ days, offline, risks: named })
      })
      .catch(() => live && setState({ error: true }))
    return () => { live = false }
  }, [region.state, region.season, lang])

  return (
    <section className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="h2">🌦️ {t('riskTitle')}{region.state && <span className="text-base font-semibold text-gray-500"> · {region.state}</span>}</h2>
        {state.days && (
          <div className="flex gap-2 text-xs text-gray-600">
            {state.days.map((d) => (
              <span key={d.date} className="rounded-full bg-leaf-50 px-2 py-1">
                {new Date(d.date).toLocaleDateString(lang, { weekday: 'short' })} 🌡️{Math.round(d.tmin)}–{Math.round(d.tmax)}° 💧{Math.round(d.rh)}%{d.rain > 0 ? ` 🌧️${d.rain}mm` : ''}
              </span>
            ))}
          </div>
        )}
      </div>
      {!region.state && <p className="rounded-2xl bg-leaf-50 p-4 text-gray-600">📍 {t('riskSetState')}</p>}
      {state.loading && <p className="animate-pulse rounded-2xl bg-leaf-50 p-4 text-gray-500">🌦️ …</p>}
      {state.error && <p className="rounded-2xl bg-yellow-50 p-4 text-yellow-800">⚠️ {t('riskError')}</p>}
      {state.offline && <p className="mb-2 text-sm text-yellow-800">📴 {t('riskOffline')}</p>}
      {state.risks && !state.risks.length && <p className="rounded-2xl bg-leaf-50 p-4 text-leaf-900">✅ {t('riskNone')}</p>}
      {state.risks?.length > 0 && (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {state.risks.map((r) => (
            <button key={r.id} onClick={() => go('disease', { id: r.id })}
              className={`rounded-2xl p-3 text-left ring-2 transition hover:shadow ${r.level === 'high' ? 'bg-red-50 ring-red-200' : 'bg-yellow-50 ring-yellow-200'}`}>
              <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-bold text-white ${r.level === 'high' ? 'bg-red-600' : 'bg-yellow-600'}`}>
                {r.level === 'high' ? t('riskHigh') : t('riskMedium')}
              </span>
              <span className="mt-1 block font-extrabold text-leaf-900">{r.name}</span>
              <span className="text-xs text-gray-600">{r.crop} · {new Date(r.day.date).toLocaleDateString(lang, { weekday: 'short', day: 'numeric' })}: 🌡️{Math.round(r.day.tmin)}–{Math.round(r.day.tmax)}° 💧{Math.round(r.day.rh)}%{r.day.rain > 0 ? ` 🌧️${r.day.rain}mm` : ''}</span>
            </button>
          ))}
        </div>
      )}
      <p className="mt-2 text-[11px] text-gray-400">{t('riskSource')}</p>
    </section>
  )
}
