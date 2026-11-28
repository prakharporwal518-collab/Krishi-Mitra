import { useState } from 'react'

const store = {
  get: () => { try { return JSON.parse(localStorage.getItem('km_spray')) } catch { return null } },
  set: (v) => { try { localStorage.setItem('km_spray', JSON.stringify(v)) } catch { /* ignore */ } },
}
const fmt = (n) => (n >= 100 ? Math.round(n) : n >= 10 ? Math.round(n * 10) / 10 : Math.round(n * 100) / 100).toLocaleString()

// Turns "2.5 g per litre" into exact amounts for the farmer's own sprayer and field.
export default function SprayCalculator({ t, dose, product }) {
  const [v, setV] = useState(() => store.get() || { acres: 1, tank: 16, water: 200 })
  const set = (k) => (e) => { const n = { ...v, [k]: e.target.value }; setV(n); store.set(n) }
  const acres = Math.max(0, parseFloat(v.acres) || 0), tank = Math.max(1, parseFloat(v.tank) || 1), water = Math.max(1, parseFloat(v.water) || 1)
  const totalWater = acres * water
  const big = dose.unit === 'g' ? ['g', 'kg'] : ['ml', 'L']
  const total = totalWater * dose.amount
  const Field = ({ k, label, step }) => (
    <label className="text-sm font-semibold text-gray-600">{label}
      <input type="number" inputMode="decimal" min="0" step={step} value={v[k]} onChange={set(k)}
        className="mt-1 w-full rounded-xl border-2 border-leaf-200 bg-white p-3 text-lg font-bold text-gray-900" />
    </label>
  )
  return (
    <div className="mt-4 rounded-2xl border-2 border-leaf-200 bg-leaf-50 p-4">
      <p className="mb-3 text-lg font-extrabold text-leaf-900">🧮 {t('calcTitle')} <span className="text-sm font-semibold text-gray-500">· {product}</span></p>
      <div className="grid grid-cols-3 gap-2">
        {Field({ k: 'acres', label: t('calcAcres'), step: '0.5' })}
        {Field({ k: 'tank', label: t('calcTank'), step: '1' })}
        {Field({ k: 'water', label: t('calcWater'), step: '10' })}
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        <div className="rounded-xl bg-leaf-700 p-3 text-white"><p className="text-xs font-bold uppercase opacity-80">{t('calcPerTank')}</p><p className="text-2xl font-extrabold">{fmt(tank * dose.amount)} {dose.unit}</p></div>
        <div className="rounded-xl bg-white p-3"><p className="text-xs font-bold uppercase text-gray-500">{t('calcTanks')}</p><p className="text-2xl font-extrabold text-leaf-900">{Math.ceil(totalWater / tank)}</p></div>
        <div className="rounded-xl bg-white p-3"><p className="text-xs font-bold uppercase text-gray-500">{t('calcTotal')}</p><p className="text-2xl font-extrabold text-leaf-900">{total >= 1000 ? `${fmt(total / 1000)} ${big[1]}` : `${fmt(total)} ${big[0]}`}</p></div>
      </div>
      <p className="mt-2 text-xs text-gray-600">⚖️ {dose.amount} {dose.unit}/L · {t('calcNote')}</p>
    </div>
  )
}
