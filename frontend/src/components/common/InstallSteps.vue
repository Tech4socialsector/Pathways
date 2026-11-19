<template>
  <!-- How to install by hand in this browser (src/utils/pwa.js platform),
       for when the browser hasn't offered its own install dialog: iOS,
       Safari, private windows, or an older shortcut already installed.
       Shared by the install popup and the welcome page. -->
  <div>
    <ol class="space-y-2 rounded-lg bg-gray-50 p-3 text-left text-sm text-gray-700">
      <li v-for="(step, i) in steps" :key="i" class="flex gap-2.5">
        <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-700 text-[11px] font-bold text-white">{{ i + 1 }}</span>
        <span class="min-w-0">
          <template v-for="(part, j) in step" :key="j">
            <span
              v-if="part.icon"
              class="mx-0.5 inline-flex translate-y-0.5 items-center rounded border bg-white p-0.5 text-gray-700"
              :aria-label="part.label"
            ><FeatherIcon :name="part.icon" class="h-3.5 w-3.5" /></span>
            <strong v-else-if="part.b" class="font-semibold text-gray-900">{{ part.b }}</strong>
            <template v-else>{{ part }}</template>
          </template>
        </span>
      </li>
    </ol>
    <p v-if="privateNote" class="mt-2 flex gap-1.5 text-left text-xs leading-relaxed text-gray-500">
      <FeatherIcon name="info" class="mt-0.5 h-3.5 w-3.5 shrink-0" />
      <span>
        Don't see the option? Browsers can't install from a private or Incognito window — use a normal window.
        If an older {{ appearance.app_name }} shortcut is already installed, the browser shows <strong class="font-semibold">Open in app</strong> instead:
        open it, then ⋮ → <strong class="font-semibold">Uninstall</strong>, and reload this page.
      </span>
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { appearance } from '@/utils/theme'
import { pwa } from '@/utils/pwa'

// Chromium browsers (and Android) offer the dialog except in private windows
// or when an app already covers this page.
const privateNote = computed(() => ['chrome', 'edge', 'android'].includes(pwa.platform))

// Each step: plain text, { b } for bold, { icon, label } for a browser icon.
const steps = computed(() => {
  switch (pwa.platform) {
    case 'ios':
      return [
        ['Tap the ', { icon: 'share', label: 'Share' }, ' ', { b: 'Share' }, ' button in the browser bar.'],
        ['Scroll down and tap ', { b: 'Add to Home Screen' }, '.'],
        ['Tap ', { b: 'Add' }, '.'],
      ]
    case 'android':
      return [
        ['Tap the browser menu ', { icon: 'more-vertical', label: 'Menu' }, ' at the top right.'],
        ['Tap ', { b: 'Install app' }, ' (or ', { b: 'Add to Home screen' }, ').'],
        ['Tap ', { b: 'Install' }, '.'],
      ]
    case 'mac-safari':
      return [
        ['In the menu bar, choose ', { b: 'File' }, ' → ', { b: 'Add to Dock' }, '.'],
        ['Click ', { b: 'Add' }, '.'],
      ]
    case 'edge':
      return [
        ['Click the install icon ', { icon: 'plus-square', label: 'Install' }, ' in the address bar,'],
        ['or open the menu ', { icon: 'more-horizontal', label: 'Menu' }, ' → ', { b: 'Apps' }, ' → ', { b: `Install ${appearance.app_name}` }, '.'],
      ]
    default: // Chrome and other Chromium browsers on desktop
      return [
        ['Click the install icon ', { icon: 'download', label: 'Install' }, ' at the right end of the address bar,'],
        ['or open the menu ', { icon: 'more-vertical', label: 'Menu' }, ' → ', { b: 'Cast, save and share' }, ' → ', { b: 'Install page as app' }, '.'],
        ['Click ', { b: 'Install' }, '.'],
      ]
  }
})
</script>
