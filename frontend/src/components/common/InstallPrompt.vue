<template>
  <!-- "Install Pathways" popup (src/utils/pwa.js), shown as soon as the app
       opens on every page once signed in, until the app is installed
       (signed out, the welcome page has its own Install button). Install always shows: it opens the
       browser's own install dialog when the browser offers one, otherwise
       it expands the steps for this browser (a web page cannot start an
       install by itself, e.g. in Incognito or on iOS). "Not now" hides it
       for this visit; the user menu's "Install app" brings it back.
       A card bottom-right on desktop, a bottom sheet on phones. Above page
       content and the phone menu (z-45), below dialogs (z-50). -->
  <Transition
    enter-from-class="translate-y-4 opacity-0"
    enter-active-class="transition duration-300 ease-out"
    leave-to-class="translate-y-4 opacity-0"
    leave-active-class="transition duration-200 ease-in"
  >
    <div
      v-if="visible"
      role="dialog"
      aria-labelledby="pwa-install-title"
      class="fixed inset-x-3 z-[48] rounded-xl border bg-white p-4 shadow-2xl sm:inset-x-auto sm:right-5 sm:w-[24rem]"
      style="bottom: calc(0.75rem + env(safe-area-inset-bottom))"
    >
      <div class="flex items-start gap-3">
        <img :src="APP_ICON" alt="" class="h-11 w-11 shrink-0 rounded-[10px]" />
        <div class="min-w-0 flex-1">
          <h2 id="pwa-install-title" class="font-heading text-base font-bold text-gray-900">Install {{ appearance.app_name }}</h2>
          <p class="mt-0.5 text-sm leading-relaxed text-gray-600">
            Open it from your {{ onPhone ? 'home screen' : 'desktop or taskbar' }} in its own window.
          </p>
        </div>
        <button
          type="button"
          class="-mr-1 -mt-1 shrink-0 rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          aria-label="Close"
          @click="notNow"
        >
          <FeatherIcon name="x" class="h-4 w-4" />
        </button>
      </div>

      <!-- No install dialog from the browser (yet): how to do it by hand. -->
      <InstallSteps v-if="!pwa.canInstall && showSteps" class="mt-3" />

      <div class="mt-4 flex justify-end gap-2">
        <Button variant="ghost" @click="notNow">Not now</Button>
        <Button v-if="pwa.canInstall || !showSteps" variant="solid" :class="BTN_BRAND" @click="install">
          <template #prefix><FeatherIcon name="download" class="h-4 w-4" /></template>
          Install
        </Button>
        <Button v-else variant="solid" :class="BTN_BRAND" @click="notNow">Got it</Button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { appearance } from '@/utils/theme'
import { useSessionStore } from '@/stores/session'
import InstallSteps from './InstallSteps.vue'
import { APP_ICON, dismissInstall, installAvailable, promptInstall, pwa, recentlyDismissed } from '@/utils/pwa'

const session = useSessionStore()
const route = useRoute()

// A short beat so the page paints first and Chrome's install event (which
// usually arrives within it) can turn the steps into a one-click Install.
const ready = ref(false)
const closed = ref(recentlyDismissed())
// The manual steps, shown when Install is pressed without a browser dialog.
const showSteps = ref(false)
let timer = null
onMounted(() => (timer = setTimeout(() => (ready.value = true), 700)))
onBeforeUnmount(() => clearTimeout(timer))

// The menu's "Install app" reopens it after "Not now".
watch(
  () => pwa.forceOpen,
  (open) => {
    if (open) {
      closed.value = false
      ready.value = true
      showSteps.value = true // asked for it from the menu: go straight to how
    }
  },
)

// Signed-in users, on every page. Signed-out visitors get the Install
// button on the welcome page itself (Welcome.vue), and nothing while
// browsing or applying for jobs.
const visible = computed(
  () => ready.value && !closed.value && installAvailable() && route.name !== 'Welcome' && (session.isLoggedIn || pwa.forceOpen),
)

const onPhone = computed(() => pwa.platform === 'ios' || pwa.platform === 'android')

function notNow() {
  closed.value = true
  dismissInstall()
}

async function install() {
  // No dialog from the browser: explain how instead.
  if (!pwa.canInstall) {
    showSteps.value = true
    return
  }
  closed.value = true
  const accepted = await promptInstall()
  // Cancelled in the browser's dialog: treat it as "not now".
  if (!accepted) dismissInstall()
}
</script>
