import { reactive } from 'vue'
import { callMethod } from '@/services/api'

// Appearance from Pathways Settings (pathways.api.settings.get_appearance),
// applied as CSS variables: tailwind's brand-* colours and font families
// read them (tailwind.config.js, index.css), so the whole app follows.

export const DEFAULT_APPEARANCE = {
  app_name: 'Pathways',
  app_logo: '',
  brand_color: '#920C24',
  body_font: 'Merriweather',
  heading_font: 'Merriweather',
}

// Google Fonts offered in Settings, with the weights each one has (asking
// Google for a weight a family lacks fails the whole request).
export const FONTS = {
  Merriweather: { weights: '300;400;700;900', fallback: 'Georgia, serif' },
  Inter: { weights: '400;500;600;700', fallback: 'system-ui, sans-serif' },
  Roboto: { weights: '400;500;700', fallback: 'system-ui, sans-serif' },
  'Open Sans': { weights: '400;500;600;700', fallback: 'system-ui, sans-serif' },
  Lato: { weights: '400;700;900', fallback: 'system-ui, sans-serif' },
  Poppins: { weights: '400;500;600;700', fallback: 'system-ui, sans-serif' },
  'Noto Sans': { weights: '400;500;600;700', fallback: 'system-ui, sans-serif' },
  Lora: { weights: '400;500;600;700', fallback: 'Georgia, serif' },
  'Source Serif 4': { weights: '400;600;700', fallback: 'Georgia, serif' },
  'Playfair Display': { weights: '400;600;700', fallback: 'Georgia, serif' },
  'System Default': { weights: '', fallback: 'system-ui, -apple-system, "Segoe UI", sans-serif' },
}

export const COLOR_PRESETS = [
  { name: 'Maroon', value: '#920C24' },
  { name: 'Navy', value: '#1E3A8A' },
  { name: 'Teal', value: '#0F766E' },
  { name: 'Forest', value: '#166534' },
  { name: 'Purple', value: '#6B21A8' },
  { name: 'Charcoal', value: '#374151' },
]

// The live appearance, for components that show the name / logo.
export const appearance = reactive({ ...DEFAULT_APPEARANCE })

// ----- colour

function parseHex(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex || '').trim())
  if (!m) return null
  const n = parseInt(m[1], 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function mix(rgb, target, amount) {
  return rgb.map((c, i) => Math.round(c + (target[i] - c) * amount))
}

// The chosen colour is shade 700; lighter shades blend toward white,
// darker ones toward black (same steps the original maroon scale used).
const SHADES = { 50: 0.95, 100: 0.9, 200: 0.75, 300: 0.55, 400: 0.35, 500: 0.18, 600: 0.08, 700: 0, 800: -0.18, 900: -0.36 }

export function brandScale(hex) {
  const base = parseHex(hex) || parseHex(DEFAULT_APPEARANCE.brand_color)
  return Object.fromEntries(
    Object.entries(SHADES).map(([shade, amount]) => [
      shade,
      amount >= 0 ? mix(base, [255, 255, 255], amount) : mix(base, [0, 0, 0], -amount),
    ]),
  )
}

function luminance([r, g, b]) {
  const lin = (c) => {
    c /= 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

// Contrast of white text on the brand colour (buttons, top bar).
export function whiteTextContrast(hex) {
  const rgb = parseHex(hex)
  if (!rgb) return 0
  return 1.05 / (luminance(rgb) + 0.05)
}

export function isValidHex(hex) {
  return !!parseHex(hex)
}

// ----- fonts

const loadedFonts = new Set(['Merriweather']) // index.html preloads the default

function loadFont(name) {
  const font = FONTS[name]
  if (!font?.weights || loadedFonts.has(name)) return
  loadedFonts.add(name)
  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(name).replace(/%20/g, '+')}:wght@${font.weights}&display=swap`
  document.head.appendChild(link)
}

function fontStack(name) {
  const font = FONTS[name] || FONTS[DEFAULT_APPEARANCE.body_font]
  return name === 'System Default' || !FONTS[name] ? font.fallback : `'${name}', ${font.fallback}`
}

// ----- apply

export function applyAppearance(values = {}) {
  const next = { ...DEFAULT_APPEARANCE }
  for (const [key, value] of Object.entries(values || {})) if (value) next[key] = value
  Object.assign(appearance, next)

  const root = document.documentElement.style
  for (const [shade, rgb] of Object.entries(brandScale(next.brand_color))) {
    root.setProperty(`--brand-${shade}`, rgb.join(' '))
  }
  loadFont(next.body_font)
  loadFont(next.heading_font)
  root.setProperty('--font-body', fontStack(next.body_font))
  root.setProperty('--font-heading', fontStack(next.heading_font))
  document.title = next.app_name
}

export async function loadAppearance() {
  try {
    applyAppearance(await callMethod('pathways.api.settings.get_appearance'))
  } catch {
    applyAppearance()
  }
}
