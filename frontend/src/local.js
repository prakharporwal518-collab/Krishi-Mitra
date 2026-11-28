// In-browser implementation of the Krishi Mitra API (used for the static Netlify deploy).
// Mirrors backend/app/main.py: ONNX model inference, symptom matching and knowledge-base lookup.
import * as ort from 'onnxruntime-web'
import kb from './data/diseases.json'
import classMap from './data/class_map.json'
import cropData from './data/crops.json'
import symData from './data/symptoms.json'
// Imported through Vite so the built file names contain a content hash: a new model always gets a new URL,
// and browsers can never pair new code with a stale cached model.
import modelUrl from './model/plant_disease.onnx?url'
import labels from './model/labels.json'

ort.env.wasm.numThreads = 1 // avoids needing cross-origin isolation headers

const MIN_CONFIDENCE = 60
// With a crop chosen: below CROP_MASS_FULL of the model's belief on that crop, confidence is scaled down;
// below CROP_MISMATCH the photo is reported as not looking like that crop. (Tuned on PlantDoc field photos.)
const CROP_MASS_FULL = 0.3
const CROP_MISMATCH = 0.12
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

let session
async function loadModel() {
  if (!session) session = await ort.InferenceSession.create(modelUrl, { executionProviders: ['wasm'] })
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

async function toBitmap(file) {
  try { return await createImageBitmap(file) } catch { fail('This file is not a valid image (use JPG or PNG).') }
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
      .map((c) => ({ id: c.id, icon: c.icon, name: cropName(c.id, lang), main: c.main, diseases: kb.diseases.filter((d) => d.crop === c.id).length }))
  },

  async symptomList(lang, crop) {
    lang = L(lang)
    const rel = new Set(kb.diseases.filter((d) => d.crop === crop).flatMap((d) => [...uiTags(d)]))
    return symData.symptoms.filter((s) => rel.has(s.id)).map((s) => ({ id: s.id, icon: s.icon, name: symName(s.id, lang) }))
  },

  // crop (optional): the crop the farmer says this is. Then only that crop's diseases are ranked, and
  // confidence = probability within that crop, scaled down when the photo doesn't look much like the crop.
  async predict(file, lang, crop) {
    lang = L(lang)
    if (file.size > 8 * 1024 * 1024) fail('Image too large (max 8 MB).')
    const [s, views] = await Promise.all([loadModel(), toTensors(file)])
    const probs = new Float32Array(labels.length)
    for (const x of views) (await s.run({ pixel_values: x })).probs.data.forEach((p, i) => { probs[i] += p / views.length })
    const make = (i, conf) => {
      const m = classMap[labels[i]]
      return { label: labels[i], crop: m.crop, crop_name: cropName(m.crop, lang), disease_id: m.disease_id,
        disease: m.disease_id === 'invalid' ? 'Not a plant leaf' : diseaseName(m.disease_id, lang), confidence: Math.round(conf * 1000) / 10 }
    }
    const order = [...probs.keys()].sort((a, b) => probs[b] - probs[a])
    const notLeaf = classMap[labels[order[0]]].disease_id === 'invalid' // model's "Not a Plant Leaf" class
    let top, cropMass = null
    if (crop && !notLeaf && order.some((i) => classMap[labels[i]].crop === crop)) {
      const mine = order.filter((i) => classMap[labels[i]].crop === crop)
      cropMass = mine.reduce((t, i) => t + probs[i], 0)
      const factor = Math.min(1, cropMass / CROP_MASS_FULL)
      top = mine.slice(0, 3).map((i) => make(i, (probs[i] / cropMass) * factor))
    } else {
      top = order.slice(0, 4).map((i) => make(i, probs[i]))
    }
    const mismatch = cropMass !== null && cropMass < CROP_MISMATCH
    return { ...top[0], is_healthy: top[0].disease_id === 'healthy', not_leaf: notLeaf, crop_hint: crop || null,
      crop_mismatch: mismatch, crop_match: cropMass === null ? null : Math.round(cropMass * 100),
      low_confidence: notLeaf || mismatch || top[0].confidence < MIN_CONFIDENCE,
      alternatives: top.slice(1).filter((x) => x.disease_id !== 'invalid').slice(0, 2), engine: 'onnx-browser' }
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
    return { id, crop: cropId, crop_name: cropName(cropId, lang), kind: d.kind, pathogen: d.pathogen, source: d.source, dose_per_litre: d.dose_per_litre,
      lang: translated ? lang : 'en', translated, ...content, region_tips: tips, region_match: !!(state || season) && tips.length > 0 }
  },

  // Explainability by occlusion: grey out one patch at a time and measure how much the
  // predicted class's probability drops. Big drop = the model relied on that area.
  async explain(file, label, grid = 7) {
    const [s, bmp] = await Promise.all([loadModel(), toBitmap(file)])
    const k = labels.indexOf(label)
    const base = view(bmp, 256, false)
    const run = async (data) => (await s.run({ pixel_values: new ort.Tensor('float32', data, [1, 3, 224, 224]) })).probs.data[k]
    const p0 = await run(base.data)
    const cell = 224 / grid, heat = []
    for (let gy = 0; gy < grid; gy++) {
      for (let gx = 0; gx < grid; gx++) {
        const data = base.data.slice()
        for (let c = 0; c < 3; c++) for (let y = gy * cell; y < (gy + 1) * cell; y++) data.fill(0, c * 50176 + y * 224 + gx * cell, c * 50176 + y * 224 + (gx + 1) * cell)
        heat.push(Math.max(0, p0 - (await run(data))))
      }
    }
    const max = Math.max(...heat) || 1
    // the exact 224x224 view the model saw, so the overlay lines up
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = 224
    const kk = 256 / Math.min(bmp.width, bmp.height), w = Math.round(bmp.width * kk), h = Math.round(bmp.height * kk)
    canvas.getContext('2d').drawImage(bmp, -Math.floor((w - 224) / 2), -Math.floor((h - 224) / 2), w, h)
    return { grid, heat: heat.map((v) => v / max), image: canvas.toDataURL('image/jpeg', 0.9) }
  },
}

