<template>
  <!-- Signed-out landing for /pathways (router/index.js). It replaces the
       instant jump to /login: the browser can only install the app from a
       page inside /pathways, so new users get the Install button here,
       always visible (no popup to dismiss). Deep links still go straight to
       the login page. -->
  <div class="flex min-h-full flex-col items-center justify-center bg-gray-50 px-4 py-10">
    <div class="w-full max-w-sm rounded-2xl border bg-white p-8 text-center shadow-sm">
      <img
        v-if="appearance.app_logo"
        :src="appearance.app_logo"
        alt=""
        class="mx-auto h-16 w-16 rounded-2xl object-contain"
      />
      <img v-else :src="APP_ICON" alt="" class="mx-auto h-16 w-16 rounded-2xl" />
      <h1 class="mt-5 font-heading text-2xl font-bold text-gray-900">{{ appearance.app_name }}</h1>
      <p class="mt-1.5 text-sm text-gray-500">Recruitment and onboarding at NLSIU</p>

      <Button variant="solid" size="lg" class="mt-7 w-full" :class="BTN_BRAND" @click="signIn">
        <template #prefix><FeatherIcon name="log-in" class="h-4 w-4" /></template>
        Sign in
      </Button>

      <!-- Install: the browser's own dialog when it offers one, otherwise
           the steps for this browser, right here in the card. -->
      <template v-if="installAvailable()">
        <Button variant="outline" size="lg" class="mt-3 w-full" :class="BTN_BRAND_OUTLINE" @click="install">
          <template #prefix><FeatherIcon name="download" class="h-4 w-4" /></template>
          Install app
        </Button>
        <p v-if="!showSteps" class="mt-2 text-xs text-gray-500">
          Open {{ appearance.app_name }} from your {{ onPhone ? 'home screen' : 'desktop or taskbar' }} in its own window.
        </p>
        <InstallSteps v-else class="mt-3" />
      </template>
      <p v-else-if="pwa.installed && !pwa.isStandalone" class="mt-3 flex items-center justify-center gap-1.5 text-xs text-green-700">
        <FeatherIcon name="check-circle" class="h-3.5 w-3.5" />
        Installed — open {{ appearance.app_name }} from your apps.
      </p>

      <div class="mt-6 border-t pt-4">
        <RouterLink to="/portal/jobs" class="text-sm font-medium text-brand-700 hover:underline">Browse open positions</RouterLink>
      </div>
    </div>
    <p class="mt-6 text-xs text-gray-400">National Law School of India University, Bengaluru</p>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import { BTN_BRAND, BTN_BRAND_OUTLINE } from '@/utils/buttonStyles'
import { appearance } from '@/utils/theme'
import { APP_ICON, installAvailable, promptInstall, pwa } from '@/utils/pwa'
import InstallSteps from '@/components/common/InstallSteps.vue'

const showSteps = ref(false)
const onPhone = computed(() => pwa.platform === 'ios' || pwa.platform === 'android')

async function install() {
  if (pwa.canInstall) {
    showSteps.value = false
    // Cancelled: the browser fires its offer again on a later visit.
    await promptInstall()
    return
  }
  // No dialog from the browser (iOS, Safari, private window...): show how.
  showSteps.value = !showSteps.value
}

function signIn() {
  window.location.href = '/login?redirect-to=/pathways'
}
</script>
