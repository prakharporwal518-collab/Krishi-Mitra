import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { LANGS, STATES, makeT } from './i18n/strings'
import { clearHistory, getHistory } from './history'
import { stopSpeaking } from './speech'
import { PageTitle } from './components/ui'
import Scan from './pages/Scan'
import Symptoms from './pages/Symptoms'
import Disease from './pages/Disease'

const store = {
  get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d } catch { return d } },
  set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* ignore */ } },
}

export default function App() {
  const [lang, setLang] = useState(() => store.get('km_lang', null))
  const [region, setRegion] = useState(() => store.get('km_region', { state: '', season: '' }))
  const [stack, setStack] = useState([{ name: lang ? 'home' : 'language' }])
  const [crops, setCrops] = useState([])
  const t = useMemo(() => makeT(lang || 'en'), [lang])
  const page = stack[stack.length - 1]

  useEffect(() => { if (lang) { store.set('km_lang', lang); document.documentElement.lang = lang } }, [lang])
  useEffect(() => store.set('km_region', region), [region])
  useEffect(() => { if (lang) api.crops(lang).then(setCrops).catch(() => {}) }, [lang])

  const go = (name, params = {}) => {
    stopSpeaking()
    window.scrollTo(0, 0)
    if (name === 'back') return setStack((s) => (s.length > 1 ? s.slice(0, -1) : [{ name: 'home' }]))
    setStack((s) => (['home', 'scan', 'symptoms', 'history', 'help'].includes(name) ? [{ name: 'home' }, { name, params }] : [...s, { name, params }]))
  }
  const regionParams = useMemo(() => ({ state: region.state || undefined, season: region.season || undefined }), [region])

  if (page.name === 'language') {
    return <LanguagePage t={t} lang={lang} onPick={(l) => { setLang(l); setStack([{ name: 'home' }]) }} />
  }

  const props = { t, lang, go, crops, region: regionParams }
  return (
    <div className="mx-auto min-h-screen max-w-xl pb-28">
      <header className="sticky top-0 z-10 flex items-center justify-between bg-leaf-800 px-4 py-3 text-white shadow">
        <button onClick={() => go('home')} className="flex items-center gap-2 text-xl font-extrabold">
          <span className="text-3xl">🌱</span>{t('appName')}
        </button>
        <button onClick={() => setStack((s) => [...s, { name: 'language' }])} className="rounded-full bg-leaf-700 px-3 py-2 text-sm font-bold ring-1 ring-leaf-500">
          🌐 {LANGS.find((l) => l.code === lang)?.native}
        </button>
      </header>
      <main className="px-4 pt-4">
        {page.name === 'home' && <Home {...props} region={region} setRegion={setRegion} />}
        {page.name === 'scan' && <Scan {...props} />}
        {page.name === 'symptoms' && <Symptoms {...props} />}
        {page.name === 'disease' && <Disease {...props} params={page.params} />}
        {page.name === 'history' && <History {...props} />}
        {page.name === 'help' && <Help t={t} />}
      </main>
      <BottomNav t={t} current={stack.find((p) => p.name !== 'home')?.name || 'home'} go={go} />
    </div>
  )
}

function LanguagePage({ t, lang, onPick }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-leaf-700 to-leaf-900 px-5 py-10 text-white">
      <div className="text-7xl">🌱</div>
      <h1 className="mt-2 text-4xl font-extrabold">Krishi Mitra</h1>
      <p className="mt-1 text-leaf-100">कृषि मित्र · కృషి మిత్ర · কৃষি মিত্র</p>
      <p className="mt-8 text-lg font-semibold">🌐 Choose language / भाषा चुनें</p>
      <div className="mt-4 grid w-full max-w-md grid-cols-2 gap-3">
        {LANGS.map((l) => (
          <button key={l.code} onClick={() => onPick(l.code)}
            className={`rounded-3xl p-5 text-center shadow-lg transition active:scale-95 ${lang === l.code ? 'bg-soil-100 text-leaf-900 ring-4 ring-soil-400' : 'bg-white text-leaf-900'}`}>
            <span className="block text-2xl font-extrabold">{l.native}</span>
            <span className="text-sm text-gray-500">{l.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function Home({ t, go, region, setRegion }) {
  const Action = ({ icon, title, desc, to, primary }) => (
    <button onClick={() => go(to)} className={`flex w-full items-center gap-4 rounded-3xl p-5 text-left shadow-sm transition active:scale-[.98] ${primary ? 'bg-leaf-700 text-white' : 'bg-white ring-1 ring-leaf-100'}`}>
      <span className="text-5xl">{icon}</span>
      <span><span className="block text-xl font-extrabold">{title}</span><span className={primary ? 'text-leaf-100' : 'text-gray-600'}>{desc}</span></span>
    </button>
  )
  return (
    <div>
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-leaf-600 to-leaf-900 p-6 text-white shadow">
        <div className="absolute -right-6 -top-6 text-[9rem] opacity-20">🌾</div>
        <h1 className="text-4xl font-extrabold">{t('appName')}</h1>
        <p className="mt-2 text-lg text-leaf-100">{t('tagline')}</p>
        <p className="mt-4 inline-block rounded-full bg-white/15 px-3 py-1 text-sm">🏛️ ICAR · KVK · SAU</p>
      </section>

      <div className="mt-5 space-y-3">
        <Action icon="📷" title={t('scanTitle')} desc={t('scanDesc')} to="scan" primary />
        <Action icon="📝" title={t('symTitle')} desc={t('symDesc')} to="symptoms" />
        <div className="grid grid-cols-2 gap-3">
          <button onClick={() => go('history')} className="card text-left active:scale-95"><span className="text-4xl">🕘</span><p className="mt-1 text-lg font-extrabold">{t('history')}</p><p className="text-sm text-gray-600">{t('histDesc')}</p></button>
          <button onClick={() => go('help')} className="card text-left active:scale-95"><span className="text-4xl">📞</span><p className="mt-1 text-lg font-extrabold">{t('help')}</p><p className="text-sm text-gray-600">{t('helpDesc')}</p></button>
        </div>
      </div>

      <section className="card mt-5">
        <h2 className="h2 mb-3">📍 {t('region')}</h2>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm font-semibold text-gray-600">{t('state')}
            <select value={region.state} onChange={(e) => setRegion({ ...region, state: e.target.value })} className="mt-1 w-full rounded-xl border-2 border-leaf-200 bg-white p-3 text-base text-gray-900">
              <option value="">{t('selectState')}</option>
              {STATES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label className="text-sm font-semibold text-gray-600">{t('season')}
            <select value={region.season} onChange={(e) => setRegion({ ...region, season: e.target.value })} className="mt-1 w-full rounded-xl border-2 border-leaf-200 bg-white p-3 text-base text-gray-900">
              <option value="">{t('anySeason')}</option>
              {['kharif', 'rabi', 'zaid'].map((s) => <option key={s} value={s}>{t(s)}</option>)}
            </select>
          </label>
        </div>
      </section>

      <section className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="card bg-red-50 ring-red-100">
          <h2 className="mb-2 text-xl font-extrabold text-red-800">😟 {t('problemTitle')}</h2>
          <ul className="space-y-2 text-red-900">{['problem1', 'problem2', 'problem3'].map((k) => <li key={k}>✖ {t(k)}</li>)}</ul>
        </div>
        <div className="card bg-leaf-100 ring-leaf-200">
          <h2 className="mb-2 text-xl font-extrabold text-leaf-800">💡 {t('solutionTitle')}</h2>
          <ul className="space-y-2 text-leaf-900">{['solution1', 'solution2', 'solution3', 'solution4'].map((k) => <li key={k}>✔ {t(k)}</li>)}</ul>
        </div>
      </section>
      <p className="mt-5 text-center text-xs text-gray-500">{t('disclaimer')}</p>
    </div>
  )
}

function History({ t, go }) {
  const [items, setItems] = useState(getHistory)
  return (
    <div>
      <PageTitle icon="🕘" title={t('history')} sub={t('histDesc')} />
      {!items.length && <p className="card text-center text-gray-600">{t('noHistory')}</p>}
      <div className="space-y-3">
        {items.map((h, i) => (
          <button key={i} onClick={() => go('disease', { id: h.disease_id, crop: h.crop })} className="card flex w-full items-center justify-between gap-3 text-left active:scale-[.98]">
            <div>
              <p className="text-lg font-extrabold text-leaf-900">{h.disease}</p>
              <p className="text-sm text-gray-600">{h.crop_name} · {h.via === 'photo' ? '📷 ' + t('viaPhoto') : '📝 ' + t('viaSymptoms')} · {Math.round(h.confidence)}%</p>
              <p className="text-xs text-gray-400">{new Date(h.at).toLocaleString()}</p>
            </div>
            <span className="text-2xl text-leaf-700">›</span>
          </button>
        ))}
      </div>
      {items.length > 0 && <button className="btn-light mt-5 w-full" onClick={() => { clearHistory(); setItems([]) }}>🗑️ {t('clearHistory')}</button>}
    </div>
  )
}

function Help({ t }) {
  return (
    <div>
      <PageTitle icon="📞" title={t('help')} sub={t('helpDesc')} />
      <section className="card bg-leaf-700 text-white">
        <h2 className="text-2xl font-extrabold">☎️ {t('kccTitle')}</h2>
        <p className="mt-2 text-4xl font-extrabold tracking-wide">1800-180-1551</p>
        <p className="mt-2 text-leaf-100">{t('kccDesc')}</p>
        <a href="tel:18001801551" className="btn mt-4 w-full bg-white text-leaf-800">📞 {t('callNow')}</a>
      </section>
      <section className="card mt-4">
        <h2 className="h2">🏫 {t('kvkTitle')}</h2>
        <p className="mt-2 text-lg">{t('kvkDesc')}</p>
        <a href="https://kvk.icar.gov.in" target="_blank" rel="noreferrer" className="btn-light mt-4 w-full">🔗 kvk.icar.gov.in</a>
      </section>
      <p className="mt-4 text-center text-xs text-gray-500">{t('disclaimer')}</p>
    </div>
  )
}

function BottomNav({ t, current, go }) {
  const items = [['home', '🏠'], ['scan', '📷'], ['symptoms', '📝'], ['history', '🕘'], ['help', '📞']]
  return (
    <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-leaf-100 bg-white/95 backdrop-blur">
      <div className="mx-auto grid max-w-xl grid-cols-5">
        {items.map(([k, icon]) => (
          <button key={k} onClick={() => go(k)} className={`flex flex-col items-center py-2 text-xs font-bold ${current === k ? 'text-leaf-700' : 'text-gray-500'}`}>
            <span className={`text-2xl ${current === k ? 'scale-110' : ''}`}>{icon}</span>{t(k)}
          </button>
        ))}
      </div>
    </nav>
  )
}
