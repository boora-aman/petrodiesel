import { reactive } from 'vue'
import { call } from 'frappe-ui'
import { api } from './api'

export const session = reactive({
  ready: false,
  loggedIn: false,
  boot: null,
  station: null,
})

export async function loadBoot() {
  try {
    const b = await api('boot')
    session.boot = b
    session.loggedIn = true
    session.station = b.station?.name
  } catch (e) {
    session.loggedIn = false
    session.boot = null
  } finally {
    session.ready = true
  }
  return session.loggedIn
}

export async function refreshCounts() {
  if (!session.loggedIn) return
  try { session.boot.counts = await api('counts') } catch (e) { /* ignore */ }
}

export async function login(usr, pwd) {
  await call('login', { usr, pwd })
  // a new CSRF token is issued for the logged-in session; reload to pick it up
  window.location.href = '/petrodesk'
}

export async function logout() {
  await call('logout')
  window.location.href = '/petrodesk/login'
}

export const hasRole = (...roles) =>
  !!session.boot && session.boot.roles.some((r) => roles.includes(r) || r === 'System Manager')
export const can = (doctype, perm = 'create') => !!session.boot?.can?.[doctype]?.[perm]
