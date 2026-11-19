import { reactive } from 'vue'

// Installable app (PWA). The manifest and service worker are served by the
// backend at the site root (pathways/pwa/__init__.py) so the worker can
// control /pathways; index.html links the manifest and stashes Chrome's
// install event in window.__pwaInstallEvent in case it fires before this
// module loads.

const SW_URL = '/pathways-sw.js'
const SW_SCOPE = '/pathways'
// "Not now" lasts for this visit (tab session); the popup is back next time.
const DISMISS_KEY = 'pathways-install-dismissed'
// Set when this browser installs the app, so the guide isn't shown again.
const INSTALLED_KEY = 'pathways-installed'

// A runtime URL (not a Vite import): served by Frappe from pathways/public.
export const APP_ICON = '/assets/pathways/pwa/icon-192.png'

const ua = navigator.userAgent || ''
// iPadOS reports itself as a Mac; touch support tells them apart.
const isIOS = /iphone|ipad|ipod/i.test(ua) || (/macintosh/i.test(ua) && navigator.maxTouchPoints > 1)
const isAndroid = /android/i.test(ua)
const isMacSafari = !isIOS && /macintosh/i.test(ua) && /safari/i.test(ua) && !/chrome|chromium|crios|edg|opr|firefox/i.test(ua)
const isEdge = /edg\//i.test(ua)
const hasPromptEvent = 'onbeforeinstallprompt' in window

// Which manual steps to show when the browser hasn't offered its own
// install dialog (yet). null: this browser can't install web apps
// (e.g. Firefox on desktop), so no popup at all.
function detectPlatform() {
  if (isIOS) return 'ios'
  if (isAndroid) return 'android'
  if (isMacSafari) return 'mac-safari'
  if (hasPromptEvent) return isEdge ? 'edge' : 'chrome'
  return null
}

function standalone() {
  return window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true
}

// `store` is 'localStorage' or 'sessionStorage'; even reading the property
// can throw when site data is blocked, so it is looked up inside the try.
function storageGet(store, key) {
  try {
    return window[store].getItem(key)
  } catch {
    return null
  }
}

function storageSet(store, key, value) {
  try {
    if (value === null) window[store].removeItem(key)
    else window[store].setItem(key, value)
  } catch {
    // storage blocked (private mode): nothing to remember
  }
}

export const pwa = reactive({
  // Chrome / Edge / Android offered the install dialog: one-click Install.
  canInstall: false,
  // Fallback steps for the browser menu / Share sheet.
  platform: detectPlatform(),
  isStandalone: standalone(),
  installed: storageGet('localStorage', INSTALLED_KEY) === '1',
  // Install needs HTTPS (or localhost); on plain http there is nothing to offer.
  supported: window.isSecureContext,
  // The user menu's "Install app" reopens the popup.
  forceOpen: false,
})

let deferredEvent = null

function onInstallEvent(event) {
  event.preventDefault() // keep Chrome's mini-infobar from racing our popup
  deferredEvent = event
  pwa.canInstall = !pwa.isStandalone
  // The browser only offers this when the app is NOT installed: clear a
  // stale flag left by an install that was since removed.
  pwa.installed = false
  storageSet('localStorage', INSTALLED_KEY, null)
}

function markInstalled() {
  deferredEvent = null
  pwa.canInstall = false
  pwa.installed = true
  pwa.forceOpen = false
  storageSet('localStorage', INSTALLED_KEY, '1')
}

export function initPWA() {
  if (window.__pwaInstallEvent) onInstallEvent(window.__pwaInstallEvent)
  window.addEventListener('beforeinstallprompt', onInstallEvent)
  window.addEventListener('appinstalled', markInstalled)
  window.matchMedia?.('(display-mode: standalone)').addEventListener?.('change', () => {
    pwa.isStandalone = standalone()
  })

  // Chrome/Edge (Android, Windows, macOS) can tell us the app is already
  // installed (manifest related_applications); elsewhere this is a no-op.
  navigator.getInstalledRelatedApps?.()
    .then((apps) => {
      if (apps?.length) markInstalled()
    })
    .catch(() => {})

  // Production only: under `yarn dev` the page is served by Vite, not Frappe.
  if (import.meta.env.PROD && 'serviceWorker' in navigator && window.isSecureContext) {
    const register = () =>
      navigator.serviceWorker.register(SW_URL, { scope: SW_SCOPE }).catch((err) => {
        console.warn('Pathways: service worker registration failed', err)
      })
    if (document.readyState === 'complete') register()
    else window.addEventListener('load', register, { once: true })
  }
}

// Can this browser install the app at all (one-click or by following steps)?
export function installAvailable() {
  return pwa.supported && !pwa.isStandalone && !pwa.installed && (pwa.canInstall || !!pwa.platform)
}

// Opens the browser's install dialog. Returns true if the user accepted.
export async function promptInstall() {
  if (!deferredEvent) return false
  const event = deferredEvent
  deferredEvent = null // a prompt event can be used only once
  pwa.canInstall = false
  try {
    await event.prompt()
    const { outcome } = await event.userChoice
    if (outcome === 'accepted') markInstalled()
    return outcome === 'accepted'
  } catch {
    return false
  }
}

export function openInstallGuide() {
  if (pwa.canInstall) promptInstall()
  else pwa.forceOpen = true
}

export function dismissInstall() {
  pwa.forceOpen = false
  storageSet('sessionStorage', DISMISS_KEY, '1')
}

export function recentlyDismissed() {
  return storageGet('sessionStorage', DISMISS_KEY) === '1'
}
