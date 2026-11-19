/* Pathways service worker. Served at /pathways-sw.js (pathways/pwa/__init__.py)
 * and registered with scope "/pathways" (frontend/src/utils/pwa.js).
 *
 * What it does, deliberately little:
 *  - Pages (/pathways, /pathways/...): always from the network, so users get
 *    the latest build and a fresh session/CSRF token. When the network is
 *    down, a small "You're offline" page instead of the browser's error.
 *  - Built files (/assets/pathways/frontend/assets/*, hashed names, never
 *    change) and the app icons: cache-first, so the app opens fast and a tab
 *    left open across a deploy can still load its old page chunks.
 *  - Everything else (API calls, /files, /private, other sites): untouched.
 *    No user data is ever cached, so nothing leaks between users on logout.
 *
 * Bump VERSION when this file's caching rules change; old caches are dropped.
 */
const VERSION = 'v1'
const ASSET_CACHE = `pathways-assets-${VERSION}`
const MAX_ASSETS = 250
const APP_PATH = '/pathways'
const CACHEABLE = ['/assets/pathways/frontend/assets/', '/assets/pathways/pwa/']

self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys()
      await Promise.all(keys.filter((k) => k.startsWith('pathways-') && k !== ASSET_CACHE).map((k) => caches.delete(k)))
      if (self.registration.navigationPreload) {
        await self.registration.navigationPreload.enable().catch(() => {})
      }
      await self.clients.claim()
    })(),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  if (request.mode === 'navigate') {
    if (url.pathname === APP_PATH || url.pathname.startsWith(`${APP_PATH}/`)) {
      event.respondWith(networkPage(event))
    }
    return
  }

  if (CACHEABLE.some((prefix) => url.pathname.startsWith(prefix))) {
    event.respondWith(cacheFirst(request))
  }
})

async function networkPage(event) {
  try {
    const preloaded = await event.preloadResponse
    return preloaded || (await fetch(event.request))
  } catch {
    return new Response(OFFLINE_HTML, {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
    })
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(ASSET_CACHE)
  const hit = await cache.match(request)
  if (hit) return hit
  const response = await fetch(request)
  if (response.ok && response.type === 'basic') {
    cache
      .put(request, response.clone())
      .then(() => trim(cache))
      .catch(() => {})
  }
  return response
}

// Keys come back oldest first; drop the oldest past the limit.
async function trim(cache) {
  const keys = await cache.keys()
  for (const key of keys.slice(0, Math.max(0, keys.length - MAX_ASSETS))) await cache.delete(key)
}

const OFFLINE_HTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#920C24">
<title>Offline · Pathways</title>
<style>
  html,body{height:100%;margin:0}
  body{display:flex;align-items:center;justify-content:center;background:#f9fafb;color:#111827;
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:24px;box-sizing:border-box}
  .card{max-width:360px;text-align:center}
  svg{width:56px;height:56px;margin-bottom:20px}
  h1{font-size:20px;margin:0 0 8px}
  p{font-size:14px;line-height:1.6;color:#4b5563;margin:0 0 24px}
  button{background:#920C24;color:#fff;border:0;border-radius:8px;padding:10px 20px;font-size:14px;font-weight:600;cursor:pointer}
  button:hover{background:#780a1e}
</style></head>
<body><div class="card">
  <svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#920C24"/><path d="M18 46V18h13a10 10 0 0 1 0 20h-7v8h-6zm6-14h6a4 4 0 0 0 0-8h-6v8z" fill="#fff"/></svg>
  <h1>You're offline</h1>
  <p>Pathways needs an internet connection. Check your connection and try again &mdash; this page reloads on its own when you're back online.</p>
  <button type="button" onclick="location.reload()">Try again</button>
</div>
<script>addEventListener('online', function () { location.reload() })</script>
</body></html>`
