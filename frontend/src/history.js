const KEY = 'km_history'
export const getHistory = () => {
  try { return JSON.parse(localStorage.getItem(KEY)) || [] } catch { return [] }
}
export const addHistory = (item) => {
  const h = [{ ...item, at: Date.now() }, ...getHistory()].slice(0, 50)
  try { localStorage.setItem(KEY, JSON.stringify(h)) } catch { /* storage full / blocked */ }
}
export const clearHistory = () => { try { localStorage.removeItem(KEY) } catch { /* ignore */ } }
