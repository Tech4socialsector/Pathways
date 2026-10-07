import { call } from 'frappe-ui'

/**
 * Thin wrapper around frappe-ui's `call` for one-off method calls.
 * Every service module in this directory routes through here rather
 * than calling `frappe-ui` directly from composables/components.
 */
export function callMethod(method, params = {}) {
  return call(method, params)
}

/**
 * POST to a whitelisted method that answers with a file
 * (frappe.local.response.type = "download") and save it. On an error the
 * thrown Error carries the server's messages in `messages`.
 */
export async function downloadMethod(method, params = {}, fallbackName = 'download') {
  const headers = { 'Content-Type': 'application/json; charset=utf-8' }
  if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') headers['X-Frappe-CSRF-Token'] = window.csrf_token
  const res = await fetch(`/api/method/${method}`, { method: 'POST', headers, body: JSON.stringify(params) })
  if (!res.ok) {
    const error = new Error(`${method} failed`)
    error.messages = serverMessages(await res.json().catch(() => ({})))
    throw error
  }
  saveBlob(await res.blob(), fileNameFrom(res.headers.get('Content-Disposition')) || fallbackName)
}

/** Save a Blob (or a data: URL) under a file name. */
export function saveBlob(blobOrUrl, fileName) {
  const isBlob = typeof blobOrUrl !== 'string'
  const link = document.createElement('a')
  link.href = isBlob ? URL.createObjectURL(blobOrUrl) : blobOrUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  // Revoke later: some browsers start the download after click() returns.
  if (isBlob) setTimeout(() => URL.revokeObjectURL(link.href), 10000)
}

function fileNameFrom(disposition) {
  if (!disposition) return ''
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(disposition)
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1])
    } catch {
      // fall through to the plain name
    }
  }
  return /filename="?([^";]+)"?/i.exec(disposition)?.[1] || ''
}

export function serverMessages(body) {
  const messages = []
  try {
    for (const m of JSON.parse(body._server_messages || '[]')) messages.push(JSON.parse(m).message)
  } catch {
    // malformed — fall through to the generic message
  }
  if (body.exc_type === 'RateLimitExceededError' || body.exc_type === 'TooManyRequestsError') {
    return ['Too many attempts from your network. Please wait a few minutes and try again.']
  }
  return messages.length ? messages : ['Something went wrong. Please try again.']
}
