import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { LANGS, STATES, makeT } from './i18n/strings'
import { clearHistory, getHistory } from './history'
import { stopSpeaking } from './speech'
import { PageTitle } from './components/ui'
import Scan from './pages/Scan'
import Symptoms from './pages/Symptoms'
import Disease from './pages/Disease'
import RiskCard from './components/RiskCard'

const store = {
  get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d } catch { return d } },
  set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* ignore */ } },
}
function useOnline() {
  const [online, setOnline] = useState(navigator.onLine)
  useEffect(() => {
    const on = () => setOnline(true), off = () => setOnline(false)
    window.addEventListener('online', on); window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])
  return online
}

// Browser "install app" prompt (Chrome/Edge/Android); hidden where not supported or already installed
function useInstall() {
  const [evt, setEvt] = useState(null)
  useEffect(() => {
    const h = (e) => { e.preventDefault(); setEvt(e) }
    window.addEventListener('beforeinstallprompt', h)
    return () => window.removeEventListener('beforeinstallprompt', h)
  }, [])
  return evt && (() => { evt.prompt(); setEvt(null) })
}

const NAV = [['home', '🏠'], ['scan', '📷'], ['symptoms', '📝'], ['history', '🕘'], ['help', '📞']]

export default function App() {
  const [lang, setLang] = useState(() => store.get('km_lang', null))
  const [region, setRegion] = useState(() => store.get('km_region', { state: '', season: '' }))
  const [stack, setStack] = useState([{ name: lang ? 'home' : 'language' }])
  const [crops, setCrops] = useState([])
  const [navKey, setNavKey] = useState(0) // remounts the page on every navigation, so it always starts fresh
  const t = useMemo(() => makeT(lang || 'en'), [lang])
  const page = stack[stack.length - 1]
  const online = useOnline()
  const install = useInstall()

  useEffect(() => { if (lang) { store.set('km_lang', lang); document.documentElement.lang = lang } }, [lang])
  useEffect(() => store.set('km_region', region), [region])
  useEffect(() => { if (lang) api.crops(lang).then(setCrops).catch(() => {}) }, [lang])

  const go = (name, params = {}) => {
    stopSpeaking()
    window.scrollTo(0, 0)
    setNavKey((k) => k + 1)
    if (name === 'back') return setStack((s) => (s.length > 1 ? s.slice(0, -1) : [{ name: 'home' }]))
    setStack((s) => (NAV.some(([k]) => k === name) ? [{ name: 'home' }, { name, params }] : [...s, { name, params }]))
  }
  const regionParams = useMemo(() => ({ state: region.state || undefined, season: region.season || undefined }), [region])
  const openLanguage = () => setStack((s) => [...s, { name: 'language' }])

  if (page.name === 'language') {
    return <LanguagePage t={t} lang={lang} onPick={(l) => { setLang(l); setStack([{ name: 'home' }]) }} />
  }

  const current = stack.find((p) => p.name !== 'home')?.name || 'home'
  const props = { t, lang, go, crops, region: regionParams }
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[17rem_1fr]">
      <Sidebar t={t} lang={lang} current={current} go={go} region={region} setRegion={setRegion} openLanguage={openLanguage} install={install} />

      <div className="min-w-0 pb-28 lg:pb-10">
        {/* Mobile header (the sidebar replaces it on large screens) */}
        <header className="sticky top-0 z-10 flex items-center justify-between bg-leaf-800 px-4 py-3 text-white shadow lg:hidden">
          <button onClick={() => go('home')} className="flex items-center gap-2 text-xl font-extrabold">
            <span className="text-3xl">🌱</span>{t('appName')}
          </button>
          <span className="flex gap-2">
            {install && <button onClick={install} className="rounded-full bg-soil-100 px-3 py-2 text-sm font-bold text-leaf-900 transition-colors duration-300 hover:bg-white">⬇️</button>}
            <button onClick={openLanguage} className="rounded-full bg-leaf-700 px-3 py-2 text-sm font-bold ring-1 ring-leaf-500 transition-colors duration-300 hover:bg-leaf-600 active:scale-95">
              🌐 {LANGS.find((l) => l.code === lang)?.native}
            </button>
          </span>
        </header>
        {!online && <p className="bg-yellow-100 px-4 py-2 text-center text-sm font-bold text-yellow-900">📴 {t('offlineBanner')}</p>}
        <main key={navKey} className="mx-auto max-w-xl px-4 pt-4 lg:max-w-6xl lg:px-8 lg:pt-8">
          {page.name === 'home' && <Home {...props} region={region} setRegion={setRegion} />}
          {page.name === 'scan' && <Scan {...props} />}
          {page.name === 'symptoms' && <Symptoms {...props} />}
          {page.name === 'disease' && <Disease {...props} params={page.params} />}
          {page.name === 'history' && <History {...props} />}
          {page.name === 'help' && <Help t={t} />}
        </main>
      </div>

      <BottomNav t={t} current={current} go={go} />
    </div>
  )
}

function Sidebar({ t, lang, current, go, region, setRegion, openLanguage, install }) {
  return (
    <aside className="sticky top-0 hidden h-screen flex-col gap-6 overflow-y-auto bg-gradient-to-b from-leaf-800 to-leaf-900 p-5 text-white lg:flex">
      <button onClick={() => go('home')} className="flex items-center gap-3 text-left">
        <span className="text-4xl">🌱</span>
        <span><span className="block text-2xl font-extrabold leading-tight">{t('appName')}</span><span className="text-xs text-leaf-200">{t('tagline')}</span></span>
      </button>

      <nav className="space-y-1" aria-label={t('menu')}>
        {NAV.map(([k, icon]) => (
          <button key={k} onClick={() => go(k)} aria-current={current === k ? 'page' : undefined}
            className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-base font-bold transition duration-300 ease-in-out ${current === k ? 'bg-white text-leaf-800 shadow' : 'text-leaf-50 hover:bg-white/10'}`}>
            <span className="text-2xl">{icon}</span>{t(k)}
          </button>
        ))}
      </nav>

      <div className="rounded-2xl bg-white/10 p-4">
        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-leaf-200">🌐 {t('changeLang')}</p>
        <button onClick={openLanguage} className="w-full rounded-xl bg-white/15 px-3 py-2 text-left font-bold transition-colors duration-300 hover:bg-white/25">
          {LANGS.find((l) => l.code === lang)?.native} ▾
        </button>
        <p className="mb-2 mt-4 text-xs font-bold uppercase tracking-wide text-leaf-200">📍 {t('region')}</p>
        <RegionPicker t={t} region={region} setRegion={setRegion} dark />
      </div>

      {install && <button onClick={install} className="rounded-2xl bg-white/15 px-4 py-3 text-left font-bold transition-colors duration-300 hover:bg-white/25">⬇️ {t('installApp')}</button>}

      <a href="tel:18001801551" className="lift mt-auto rounded-2xl bg-soil-100 p-4 text-leaf-900 hover:bg-white">
        <span className="block text-xs font-bold uppercase tracking-wide text-soil-700">☎️ {t('kccTitle')}</span>
        <span className="block text-2xl font-extrabold">1800-180-1551</span>
      </a>
    </aside>
  )
}

function RegionPicker({ t, region, setRegion, dark }) {
  const cls = dark
    ? 'mt-1 w-full rounded-xl bg-white/15 p-2 text-sm font-semibold text-white [&>option]:text-gray-900'
    : 'mt-1 w-full rounded-xl border-2 border-leaf-200 bg-white p-3 text-base text-gray-900'
  return (
    <div className={dark ? 'space-y-2' : 'grid grid-cols-2 gap-3'}>
      <label className={`block text-sm font-semibold ${dark ? 'text-leaf-100' : 'text-gray-600'}`}>{t('state')}
        <select value={region.state} onChange={(e) => setRegion({ ...region, state: e.target.value })} className={cls}>
          <option value="">{t('selectState')}</option>
          {STATES.map((s) => <option key={s}>{s}</option>)}
        </select>
      </label>
      <label className={`block text-sm font-semibold ${dark ? 'text-leaf-100' : 'text-gray-600'}`}>{t('season')}
        <select value={region.season} onChange={(e) => setRegion({ ...region, season: e.target.value })} className={cls}>
          <option value="">{t('anySeason')}</option>
          {['kharif', 'rabi', 'zaid'].map((s) => <option key={s} value={s}>{t(s)}</option>)}
        </select>
      </label>
    </div>
  )
}

function LanguagePage({ lang, onPick }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-leaf-700 to-leaf-900 px-5 py-10 text-white">
      <div className="text-7xl">🌱</div>
      <h1 className="mt-2 text-4xl font-extrabold">Krishi Mitra</h1>
      <p className="mt-1 text-leaf-100">कृषि मित्र · కృషి మిత్ర · কৃষি মিত্র</p>
      <p className="mt-8 text-lg font-semibold">🌐 Choose language / भाषा चुनें</p>
      <div className="mt-4 grid w-full max-w-md grid-cols-2 gap-3 lg:max-w-3xl lg:grid-cols-3">
        {LANGS.map((l) => (
          <button key={l.code} onClick={() => onPick(l.code)}
            className={`lift rounded-3xl p-5 text-center shadow-lg ${lang === l.code ? 'bg-soil-100 text-leaf-900 ring-4 ring-soil-400' : 'bg-white text-leaf-900 hover:ring-4 hover:ring-leaf-300'}`}>
            <span className="block text-2xl font-extrabold">{l.native}</span>
            <span className="text-sm text-gray-500">{l.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function Stat({ icon, label, value, sub }) {
  return (
    <div className="card flex items-center gap-4">
      <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-leaf-100 text-3xl">{icon}</span>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-gray-500">{label}</p>
        <p className="truncate text-2xl font-extrabold text-leaf-900">{value}</p>
        {sub && <p className="truncate text-xs text-gray-500">{sub}</p>}
      </div>
    </div>
  )
}

function Home({ t, lang, go, crops, region, setRegion }) {
  const history = useMemo(getHistory, [])
  const last = history[0]
  const diseaseCount = crops.reduce((n, c) => n + (c.diseases || 0), 0)
  return (
    <div className="space-y-5 lg:space-y-6">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-leaf-600 to-leaf-900 p-6 text-white shadow lg:p-8">
        <div className="absolute -right-6 -top-6 text-[9rem] opacity-20 lg:text-[12rem]">🌾</div>
        <h1 className="text-4xl font-extrabold lg:text-5xl">{t('appName')}</h1>
        <p className="mt-2 text-lg text-leaf-100">{t('tagline')}</p>
        <p className="mt-4 inline-block rounded-full bg-white/15 px-3 py-1 text-sm">🏛️ ICAR · KVK · SAU</p>
      </section>

      {/* Summary tiles */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
        <Stat icon="🧪" label={t('statDiagnoses')} value={history.length} />
        <Stat icon="🕘" label={t('statLast')} value={last ? last.disease : '—'} sub={last ? `${last.crop_name} · ${Math.round(last.confidence)}%` : ''} />
        <Stat icon="🌾" label={t('statCrops')} value={crops.length || '—'} />
        <Stat icon="📚" label={t('statDiseases')} value={diseaseCount || '—'} />
      </section>

      <RiskCard t={t} lang={lang} region={region} go={go} />

      {/* Main actions */}
      <section>
        <h2 className="h2 mb-3">{t('quickActions')}</h2>
        <div className="grid gap-3 md:grid-cols-2 lg:gap-4">
          <button onClick={() => go('scan')} className="flex items-center gap-4 rounded-3xl bg-leaf-700 p-5 text-left text-white shadow-sm lift hover:bg-leaf-800 lg:p-7">
            <span className="text-5xl lg:text-6xl">📷</span>
            <span><span className="block text-xl font-extrabold lg:text-2xl">{t('scanTitle')}</span><span className="text-leaf-100">{t('scanDesc')}</span></span>
          </button>
          <button onClick={() => go('symptoms')} className="flex items-center gap-4 rounded-3xl bg-white p-5 text-left shadow-sm ring-1 ring-leaf-100 lift hover:ring-leaf-200 lg:p-7">
            <span className="text-5xl lg:text-6xl">📝</span>
            <span><span className="block text-xl font-extrabold lg:text-2xl">{t('symTitle')}</span><span className="text-gray-600">{t('symDesc')}</span></span>
          </button>
        </div>
      </section>

      {/* Region (on large screens it lives in the sidebar) */}
      <section className="card lg:hidden">
        <h2 className="h2 mb-3">📍 {t('region')}</h2>
        <RegionPicker t={t} region={region} setRegion={setRegion} />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="h2">🕘 {t('recent')}</h2>
            {history.length > 0 && <button onClick={() => go('history')} className="text-sm font-bold text-leaf-700 hover:underline">{t('viewAll')} →</button>}
          </div>
          {!history.length && <p className="rounded-2xl bg-leaf-50 p-4 text-center text-gray-600">{t('noHistory')}</p>}
          <div className="divide-y divide-leaf-100">
            {history.slice(0, 4).map((h, i) => (
              <button key={i} onClick={() => go('disease', { id: h.disease_id, crop: h.crop })} className="flex w-full items-center justify-between gap-3 rounded-xl py-3 text-left transition-colors duration-300 ease-in-out hover:bg-leaf-50">
                <span className="min-w-0">
                  <span className="block truncate font-extrabold text-leaf-900">{h.disease}</span>
                  <span className="text-sm text-gray-500">{h.crop_name} · {h.via === 'photo' ? '📷' : '📝'} · {new Date(h.at).toLocaleDateString()}</span>
                </span>
                <span className="shrink-0 rounded-full bg-leaf-100 px-3 py-1 text-sm font-bold text-leaf-800">{Math.round(h.confidence)}%</span>
              </button>
            ))}
          </div>
        </div>
        <div className="card flex flex-col bg-leaf-700 text-white ring-0">
          <h2 className="text-xl font-extrabold">☎️ {t('kccTitle')}</h2>
          <p className="mt-2 text-3xl font-extrabold tracking-wide">1800-180-1551</p>
          <p className="mt-2 text-sm text-leaf-100">{t('kccDesc')}</p>
          <a href="tel:18001801551" className="btn mt-auto w-full bg-white text-leaf-800 lg:mt-4">📞 {t('callNow')}</a>
        </div>
      </section>

      {crops.length > 0 && (
        <section className="card">
          <h2 className="h2 mb-3">🌱 {t('cropsCovered')}</h2>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 lg:grid-cols-7">
            {crops.map((c) => (
              <div key={c.id} className="tile flex flex-col items-center rounded-2xl bg-leaf-50 p-3 text-center">
                <span className="text-3xl">{c.icon}</span>
                <span className="mt-1 text-xs font-bold text-leaf-900">{c.name}</span>
                <span className="text-[11px] text-gray-500">{c.diseases} 🦠</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="grid gap-4 md:grid-cols-2">
        <div className="card bg-red-50 ring-red-100">
          <h2 className="mb-2 text-xl font-extrabold text-red-800">😟 {t('problemTitle')}</h2>
          <ul className="space-y-2 text-red-900">{['problem1', 'problem2', 'problem3'].map((k) => <li key={k}>✖ {t(k)}</li>)}</ul>
        </div>
        <div className="card bg-leaf-100 ring-leaf-200">
          <h2 className="mb-2 text-xl font-extrabold text-leaf-800">💡 {t('solutionTitle')}</h2>
          <ul className="space-y-2 text-leaf-900">{['solution1', 'solution2', 'solution3', 'solution4'].map((k) => <li key={k}>✔ {t(k)}</li>)}</ul>
        </div>
      </section>
      <p className="text-center text-xs text-gray-500">{t('disclaimer')}</p>
    </div>
  )
}

function History({ t, go }) {
  const [items, setItems] = useState(getHistory)
  return (
    <div>
      <PageTitle icon="🕘" title={t('history')} sub={t('histDesc')} />
      {!items.length && <p className="card text-center text-gray-600">{t('noHistory')}</p>}
      <div className="grid gap-3 lg:grid-cols-2">
        {items.map((h, i) => (
          <button key={i} onClick={() => go('disease', { id: h.disease_id, crop: h.crop })} className="card flex w-full items-center justify-between gap-3 text-left">
            <div className="min-w-0">
              <p className="text-lg font-extrabold text-leaf-900">{h.disease}</p>
              <p className="text-sm text-gray-600">{h.crop_name} · {h.via === 'photo' ? '📷 ' + t('viaPhoto') : '📝 ' + t('viaSymptoms')} · {Math.round(h.confidence)}%</p>
              <p className="text-xs text-gray-400">{new Date(h.at).toLocaleString()}</p>
            </div>
            <span className="text-2xl text-leaf-700">›</span>
          </button>
        ))}
      </div>
      {items.length > 0 && <button className="btn-light mt-5 w-full lg:w-auto" onClick={() => { clearHistory(); setItems([]) }}>🗑️ {t('clearHistory')}</button>}
    </div>
  )
}

function Help({ t }) {
  return (
    <div>
      <PageTitle icon="📞" title={t('help')} sub={t('helpDesc')} />
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card bg-leaf-700 text-white">
          <h2 className="text-2xl font-extrabold">☎️ {t('kccTitle')}</h2>
          <p className="mt-2 text-4xl font-extrabold tracking-wide">1800-180-1551</p>
          <p className="mt-2 text-leaf-100">{t('kccDesc')}</p>
          <a href="tel:18001801551" className="btn mt-4 w-full bg-white text-leaf-800">📞 {t('callNow')}</a>
        </section>
        <section className="card">
          <h2 className="h2">🏫 {t('kvkTitle')}</h2>
          <p className="mt-2 text-lg">{t('kvkDesc')}</p>
          <a href="https://kvk.icar.gov.in" target="_blank" rel="noreferrer" className="btn-light mt-4 w-full">🔗 kvk.icar.gov.in</a>
        </section>
      </div>
      <p className="mt-4 text-center text-xs text-gray-500">{t('disclaimer')}</p>
    </div>
  )
}

function BottomNav({ t, current, go }) {
  return (
    <nav className="bottom-nav fixed inset-x-0 bottom-0 z-10 border-t border-leaf-100 bg-white/95 backdrop-blur lg:hidden">
      <div className="mx-auto grid max-w-xl grid-cols-5">
        {NAV.map(([k, icon]) => (
          <button key={k} onClick={() => go(k)} className={`flex flex-col items-center py-2 text-xs font-bold transition-colors duration-300 hover:text-leaf-700 active:scale-95 ${current === k ? 'text-leaf-700' : 'text-gray-500'}`}>
            <span className={`text-2xl ${current === k ? 'scale-110' : ''}`}>{icon}</span>{t(k)}
          </button>
        ))}
      </div>
    </nav>
  )
}
