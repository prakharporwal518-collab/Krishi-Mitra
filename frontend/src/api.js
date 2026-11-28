async function req(path, opts) {
  let res
  try {
    res = await fetch(path, opts)
  } catch {
    throw new Error('NETWORK')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
  return data
}

const serverApi = {
  explain: () => Promise.reject(new Error('Heatmap is only available in browser mode')),
  crops: (lang) => req(`/api/crops?lang=${lang}`),
  symptomList: (lang, crop) => req(`/api/symptom-list?lang=${lang}&crop=${crop}`),
  predict: (file, lang, crop) => {
    const fd = new FormData()
    fd.append('file', file)
    return req(`/api/predict?lang=${lang}${crop ? `&crop=${crop}` : ''}`, { method: 'POST', body: fd })
  },
  symptoms: (body) => req('/api/symptoms', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  disease: (id, { lang, state, season, crop }) => {
    const p = new URLSearchParams({ lang })
    if (state) p.set('state', state)
    if (season) p.set('season', season)
    if (crop) p.set('crop', crop)
    return req(`/api/disease/${id}?${p}`)
  },
}

// VITE_API_MODE=server uses the FastAPI backend; anything else runs fully in the browser.
const local = () => import('./local.js').then((m) => m.localApi) // lazy: loads ONNX Runtime only when needed
export const api = import.meta.env.VITE_API_MODE === 'server'
  ? serverApi
  : Object.fromEntries(Object.keys(serverApi).map((k) => [k, (...a) => local().then((l) => l[k](...a))]))
