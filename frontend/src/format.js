const inrFmt = new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const inr0 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })
const num2 = new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const flt = (v, p = 2) => {
  const n = Number(v)
  if (!isFinite(n)) return 0
  const f = Math.pow(10, p)
  return Math.round(n * f + (n >= 0 ? 1e-9 : -1e-9)) / f
}
export const inr = (v, whole = false) => '₹ ' + (whole ? inr0 : inrFmt).format(Number(v) || 0)
export const signedInr = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) < 0.005) return '₹ 0.00'
  return (n < 0 ? '−' : '+') + '₹ ' + inrFmt.format(Math.abs(n))
}
export const litres = (v, dec = 2) =>
  (dec ? num2 : inr0).format(Number(v) || 0) + ' L'
export const num = (v, dec = 2) =>
  new Intl.NumberFormat('en-IN', { minimumFractionDigits: dec, maximumFractionDigits: dec }).format(Number(v) || 0)
export const compactInr = (v) => {
  const n = Number(v) || 0
  const a = Math.abs(n)
  const s = n < 0 ? '−' : ''
  if (a >= 1e7) return `${s}₹ ${(a / 1e7).toFixed(2)} Cr`
  if (a >= 1e5) return `${s}₹ ${(a / 1e5).toFixed(2)} lakh`
  return `${s}₹ ${inr0.format(a)}`
}
export const dateFmt = (d) => {
  if (!d) return ''
  const [y, m, day] = String(d).slice(0, 10).split('-')
  return `${day}-${m}-${y}`
}
export const timeFmt = (t) => {
  if (!t) return ''
  const [h, m] = String(t).split(':')
  return `${String(h).padStart(2, '0')}:${String(m || '00').padStart(2, '0')}`
}
export const dateTimeFmt = (d) => (d ? `${dateFmt(d)} ${timeFmt(String(d).slice(11))}` : '')
export const today = () => {
  const d = new Date()
  const p = (x) => String(x).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
export const addDays = (d, n) => {
  const x = new Date(String(d).slice(0, 10) + 'T00:00:00')
  x.setDate(x.getDate() + n)
  const p = (v) => String(v).padStart(2, '0')
  return `${x.getFullYear()}-${p(x.getMonth() + 1)}-${p(x.getDate())}`
}
export const relTime = (d) => {
  if (!d) return ''
  const diff = (Date.now() - new Date(String(d).replace(' ', 'T')).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`
  return `${Math.floor(diff / 86400)} d ago`
}
export const fuelClass = (item) => {
  const k = String(item || '').toUpperCase()
  if (k.startsWith('MS') || k.includes('PETROL')) return k.includes('XP') ? 'xp' : 'ms'
  if (k.includes('HSD') || k.includes('DIESEL')) return 'hsd'
  if (k.includes('XP') || k.includes('PREMIUM') || k.includes('POWER') || k.includes('SPEED')) return 'xp'
  return 'lube'
}
export const FUEL_COLORS = { ms: '#16A34A', hsd: '#D97706', xp: '#7C3AED', lube: '#64748B' }
