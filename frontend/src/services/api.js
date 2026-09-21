import { call } from 'frappe-ui'

/**
 * Thin wrapper around frappe-ui's `call` for one-off method calls.
 * Every service module in this directory routes through here rather
 * than calling `frappe-ui` directly from composables/components.
 */
export function callMethod(method, params = {}) {
  return call(method, params)
}
