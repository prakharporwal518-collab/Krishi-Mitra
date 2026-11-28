import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Spinner } from './ui'

// "Where the AI looked": occlusion heatmap drawn over the exact view the model saw
export default function Heatmap({ t, file, label }) {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const ref = useRef()

  useEffect(() => {
    if (!data || !ref.current) return
    const ctx = ref.current.getContext('2d')
    const img = new Image()
    img.onload = () => {
      ctx.drawImage(img, 0, 0, 224, 224)
      const small = document.createElement('canvas')
      small.width = small.height = data.grid
      const sctx = small.getContext('2d')
      data.heat.forEach((v, i) => {
        sctx.fillStyle = `rgba(239, 68, 68, ${(v * 0.75).toFixed(3)})` // red, stronger = more important
        sctx.fillRect(i % data.grid, Math.floor(i / data.grid), 1, 1)
      })
      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(small, 0, 0, 224, 224) // smooth upscale into a soft heatmap
    }
    img.src = data.image
  }, [data])

  const run = async () => {
    setBusy(true); setError(null)
    try { setData(await api.explain(file, label)) } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  if (import.meta.env.VITE_API_MODE === 'server') return null
  return (
    <div>
      {!data && !busy && <button className="btn-light w-full" onClick={run}>🔥 {t('explainBtn')}</button>}
      {busy && <Spinner label={t('explaining')} />}
      {error && <p className="text-sm text-red-700">{error}</p>}
      {data && (
        <div className="rounded-2xl bg-leaf-50 p-3">
          <p className="mb-2 font-extrabold text-leaf-900">🔥 {t('explainTitle')}</p>
          <canvas ref={ref} width={224} height={224} className="mx-auto w-full max-w-[18rem] rounded-xl" />
          <p className="mt-2 text-sm text-gray-600">{t('explainHelp')}</p>
        </div>
      )}
    </div>
  )
}
