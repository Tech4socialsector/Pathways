import { toast as frappeToast } from 'frappe-ui'

/**
 * toast({ title, icon, iconClasses }) — the call shape used across the app.
 * frappe-ui's own `toast` is an object (toast.success / toast.error), so
 * calling it directly throws; this maps the old shape onto it. Toasts render
 * through <FrappeUIProvider> in App.vue.
 */
export function toast({ title, message, icon, iconClasses } = {}) {
  const text = title || message || ''
  const isError = icon === 'alert-triangle' || /red/.test(iconClasses || '')
  return isError ? frappeToast.error(text) : frappeToast.success(text)
}
