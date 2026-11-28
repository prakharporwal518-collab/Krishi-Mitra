// Weather-based disease risk for the next 3 days.
// Forecast: Open-Meteo (free, no API key). Rules: simple weather conditions that favour each disease,
// summarised from ICAR / State Agricultural University advisories. They warn, they don't diagnose.

// Approximate centre of the main farming area of each state (lat, lon)
export const STATE_COORDS = {
  'Andhra Pradesh': [16.2, 80.6], Assam: [26.2, 92.6], Bihar: [25.6, 85.4], Chhattisgarh: [21.3, 81.6], Gujarat: [22.6, 72.6],
  Haryana: [29.2, 76.3], 'Himachal Pradesh': [31.6, 76.9], 'Jammu and Kashmir': [33.7, 74.9], Jharkhand: [23.6, 85.3],
  Karnataka: [15.3, 75.7], Kerala: [10.5, 76.3], 'Madhya Pradesh': [23.2, 77.4], Maharashtra: [19.3, 75.7], Odisha: [20.5, 85.2],
  Punjab: [30.9, 75.6], Rajasthan: [26.9, 75.0], 'Tamil Nadu': [11.0, 78.7], Telangana: [17.6, 78.6], 'Uttar Pradesh': [26.8, 80.9],
  Uttarakhand: [29.9, 78.1], 'West Bengal': [23.0, 87.9],
}

const between = (x, lo, hi) => x >= lo && x <= hi
// day: { tmin, tmax, rh, rain }  ->  'high' | 'medium' | null
const RULES = [
  { id: 'potato_late_blight', seasons: ['rabi'], f: (d) => (between(d.tmin, 8, 20) && d.tmax <= 25 && d.rh >= 85 ? 'high' : d.tmax <= 27 && d.rh >= 75 && d.rain > 0 ? 'medium' : null) },
  { id: 'tomato_late_blight', seasons: ['rabi', 'kharif'], f: (d) => (between(d.tmin, 10, 20) && d.tmax <= 25 && d.rh >= 85 ? 'high' : d.tmax <= 27 && d.rh >= 80 && d.rain > 0 ? 'medium' : null) },
  { id: 'tomato_early_blight', seasons: ['kharif', 'rabi'], f: (d) => (between(d.tmax, 24, 32) && d.rh >= 80 ? 'high' : between(d.tmax, 22, 34) && d.rh >= 70 ? 'medium' : null) },
  { id: 'rice_blast', seasons: ['kharif'], f: (d) => (between(d.tmin, 18, 26) && d.rh >= 90 ? 'high' : between(d.tmin, 16, 28) && d.rh >= 85 ? 'medium' : null) },
  { id: 'rice_bacterial_leaf_blight', seasons: ['kharif'], f: (d) => (between(d.tmax, 25, 34) && d.rain >= 10 ? 'high' : d.rain >= 5 && d.rh >= 80 ? 'medium' : null) },
  { id: 'wheat_rust', seasons: ['rabi'], f: (d) => (between(d.tmax, 10, 22) && (d.rh >= 80 || d.rain > 0) ? 'high' : between(d.tmax, 15, 25) && d.rh >= 70 ? 'medium' : null) },
  { id: 'maize_common_rust', seasons: ['kharif', 'rabi'], f: (d) => (between(d.tmax, 16, 25) && d.rh >= 85 ? 'high' : between(d.tmax, 16, 27) && d.rh >= 75 ? 'medium' : null) },
  { id: 'chilli_anthracnose', seasons: ['kharif', 'rabi'], f: (d) => (between(d.tmax, 25, 32) && d.rh >= 85 && d.rain > 0 ? 'high' : between(d.tmax, 24, 34) && d.rh >= 80 ? 'medium' : null) },
  { id: 'tomato_leaf_curl', seasons: ['zaid', 'rabi'], f: (d) => (between(d.tmax, 28, 38) && d.rh <= 60 && d.rain === 0 ? 'high' : d.tmax >= 26 && d.rh <= 70 && d.rain === 0 ? 'medium' : null) },
  { id: 'cotton_leaf_curl', seasons: ['kharif'], f: (d) => (between(d.tmax, 28, 38) && d.rh <= 60 && d.rain === 0 ? 'high' : d.tmax >= 26 && d.rh <= 70 && d.rain === 0 ? 'medium' : null) },
  { id: 'tomato_spider_mites', seasons: ['zaid', 'rabi'], f: (d) => (d.tmax >= 32 && d.rh <= 50 && d.rain === 0 ? 'high' : d.tmax >= 30 && d.rh <= 60 ? 'medium' : null) },
  { id: 'wheat_powdery_mildew', seasons: ['rabi'], f: (d) => (between(d.tmax, 15, 22) && d.rh >= 70 && d.rain === 0 ? 'medium' : null) },
]
const RANK = { high: 2, medium: 1 }
const KEY = 'km_weather'

export async function getForecast(state) {
  const [lat, lon] = STATE_COORDS[state]
  let cached = null
  try { cached = JSON.parse(localStorage.getItem(KEY)) } catch { /* ignore */ }
  const fresh = cached && cached.state === state && Date.now() - cached.at < 3 * 3600e3
  if (fresh) return { days: cached.days, offline: false }
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&timezone=Asia%2FKolkata&forecast_days=3` +
      '&daily=temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum'
    const r = await fetch(url)
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const d = (await r.json()).daily
    const days = d.time.map((date, i) => ({ date, tmax: d.temperature_2m_max[i], tmin: d.temperature_2m_min[i], rh: d.relative_humidity_2m_mean[i], rain: d.precipitation_sum[i] }))
    try { localStorage.setItem(KEY, JSON.stringify({ state, at: Date.now(), days })) } catch { /* ignore */ }
    return { days, offline: false }
  } catch (e) {
    if (cached && cached.state === state) return { days: cached.days, offline: true }
    throw e
  }
}

// Returns [{ id, level, day }] sorted by risk, keeping each disease's worst day.
export function assessRisk(days, season) {
  const out = []
  for (const rule of RULES) {
    if (season && !rule.seasons.includes(season)) continue
    let best = null
    for (const day of days) {
      const level = rule.f(day)
      if (level && (!best || RANK[level] > RANK[best.level])) best = { id: rule.id, level, day }
    }
    if (best) out.push(best)
  }
  return out.sort((a, b) => RANK[b.level] - RANK[a.level])
}
