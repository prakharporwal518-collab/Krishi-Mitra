// In-browser implementation of the Krishi Mitra API (used for the static Netlify deploy).
// Mirrors backend/app/main.py: ONNX model inference, symptom matching and knowledge-base lookup.
import * as ort from 'onnxruntime-web'
import kb from './data/diseases.json'
import classMap from './data/class_map.json'
import cropData from './data/crops.json'
import symData from './data/symptoms.json'

ort.env.wasm.numThreads = 1 // avoids needing cross-origin isolation headers

const MIN_CONFIDENCE = 60
const KB = Object.fromEntries(kb.diseases.map((d) => [d.id, d]))
const CROPS = Object.fromEntries(cropData.crops.map((c) => [c.id, c]))
const SYM = Object.fromEntries(symData.symptoms.map((s) => [s.id, s]))
const alias = (t) => symData.aliases[t] || t
const L = (lang) => (cropData.languages.some((l) => l.code === lang) ? lang : 'en')
const cropName = (id, lang) => CROPS[id]?.names[lang] || CROPS[id]?.names.en || id
const diseaseName = (id, lang) => (KB[id].content[lang] || KB[id].content.en).name
const symName = (id, lang) => SYM[id].names[lang] || SYM[id].names.en
const uiTags = (d) => new Set(d.symptom_tags.map(alias).filter((t) => SYM[t]))
const fail = (msg) => { throw new Error(msg) }

let session, labels
async function loadModel() {
  if (!session) {
    ;[session, labels] = await Promise.all([
      ort.InferenceSession.create('/model/plant_disease.onnx', { executionProviders: ['wasm'] }),
      fetch('/model/labels.json').then((r) => r.json()),
    ])
  }
  return session
}

// Same preprocessing as MobileNetV2ImageProcessor: resize shortest edge, centre-crop 224, scale to [-1, 1].
// We average 3 views (centre, mirrored, zoomed-in) - test-time augmentation, +2% on field photos.
function view(bmp, short, mirror) {
  const k = short / Math.min(bmp.width, bmp.height)
  const w = Math.round(bmp.width * k), h = Math.round(bmp.height * k)
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 224
  const ctx = canvas.getContext('2d')
  ctx.imageSmoothingQuality = 'high'
  if (mirror) { ctx.translate(224, 0); ctx.scale(-1, 1) }
  ctx.drawImage(bmp, -Math.floor((w - 224) / 2), -Math.floor((h - 224) / 2), w, h)
  const px = ctx.getImageData(0, 0, 224, 224).data
  const data = new Float32Array(3 * 224 * 224)
  for (let i = 0; i < 224 * 224; i++) for (let c = 0; c < 3; c++) data[c * 224 * 224 + i] = px[i * 4 + c] / 127.5 - 1
  return new ort.Tensor('float32', data, [1, 3, 224, 224])
}

async function toTensors(file) {
  let bmp
  try { bmp = await createImageBitmap(file) } catch { fail('This file is not a valid image (use JPG or PNG).') }
  return [view(bmp, 256, false), view(bmp, 256, true), view(bmp, 300, false)]
}

export const localApi = {
  async crops(lang) {
    lang = L(lang)
    return cropData.crops.filter((c) => c.main || kb.diseases.some((d) => d.crop === c.id))
      .map((c) => ({ id: c.id, icon: c.icon, name: cropName(c.id, lang), main: c.main }))
  },

  async symptomList(lang, crop) {
    lang = L(lang)
    const rel = new Set(kb.diseases.filter((d) => d.crop === crop).flatMap((d) => [...uiTags(d)]))
    return symData.symptoms.filter((s) => rel.has(s.id)).map((s) => ({ id: s.id, icon: s.icon, name: symName(s.id, lang) }))
  },

  async predict(file, lang) {
    lang = L(lang)
    if (file.size > 8 * 1024 * 1024) fail('Image too large (max 8 MB).')
    const [s, views] = await Promise.all([loadModel(), toTensors(file)])
    const probs = new Float32Array(labels.length)
    for (const x of views) (await s.run({ pixel_values: x })).probs.data.forEach((p, i) => { probs[i] += p / views.length })
    const top = [...probs].map((p, i) => [p, i]).sort((a, b) => b[0] - a[0]).slice(0, 3).map(([p, i]) => {
      const m = classMap[labels[i]]
      return { label: labels[i], crop: m.crop, crop_name: cropName(m.crop, lang), disease_id: m.disease_id,
        disease: diseaseName(m.disease_id, lang), confidence: Math.round(p * 1000) / 10 }
    })
    return { ...top[0], is_healthy: top[0].disease_id === 'healthy', low_confidence: top[0].confidence < MIN_CONFIDENCE,
      alternatives: top.slice(1), engine: 'onnx-browser' }
  },

  async symptoms({ crop, symptoms = [], text, lang }) {
    lang = L(lang)
    const sel = new Set(symptoms.map(alias).filter((t) => SYM[t]))
    if (text) {
      const tl = text.toLowerCase()
      symData.symptoms.forEach((s) => { if (s.kw.some((k) => tl.includes(k.toLowerCase()))) sel.add(s.id) })
    }
    if (!sel.size) fail('Please select or speak at least one symptom.')
    const matches = kb.diseases.filter((d) => d.crop === crop).map((d) => {
      const tags = uiTags(d)
      const hit = [...sel].filter((s) => tags.has(s)).sort()
      return hit.length && { disease_id: d.id, disease: diseaseName(d.id, lang), crop: d.crop, crop_name: cropName(d.crop, lang),
        score: Math.round((100 * hit.length) / Math.sqrt(sel.size * tags.size)), matched: hit.map((s) => symName(s, lang)) }
    }).filter(Boolean).sort((a, b) => b.score - a.score)
    return { detected_symptoms: [...sel].sort(), matches: matches.slice(0, 3) }
  },

  async disease(id, { lang, state, season, crop }) {
    lang = L(lang)
    const d = KB[id] || fail('Disease not found')
    const translated = !!d.content[lang]
    const content = d.content[lang] || d.content.en
    const tips = d.region_tips.filter((t) => (!state || t.states.includes(state)) && (!season || t.seasons.includes(season)))
      .map((t) => ({ states: t.states, seasons: t.seasons, tip: t.tip[lang] || t.tip.en }))
    const cropId = d.crop === 'any' && crop ? crop : d.crop
    return { id, crop: cropId, crop_name: cropName(cropId, lang), kind: d.kind, pathogen: d.pathogen, source: d.source,
      lang: translated ? lang : 'en', translated, ...content, region_tips: tips, region_match: !!(state || season) && tips.length > 0 }
  },
}
