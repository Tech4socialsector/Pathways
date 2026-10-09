<template>
  <!-- The page itself scrolls (no inner scroll area), so the browser has one
       scrollbar and scrollIntoView / window.scrollTo behave. -->
  <div class="flex min-h-full flex-col bg-gray-50">
    <header class="sticky top-0 z-20 border-t-4 border-brand-700 bg-white/95 shadow-sm backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
        <router-link to="/portal/jobs" class="flex min-w-0 items-center gap-3">
          <img v-if="appearance.app_logo" :src="appearance.app_logo" alt="" class="h-9 w-9 shrink-0 rounded-md object-contain" />
          <span v-else class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-brand-700 font-heading text-lg font-bold text-white">
            N
          </span>
          <span class="min-w-0">
            <span class="block truncate font-heading text-lg font-bold leading-tight text-gray-900">NLSIU Careers</span>
            <span class="hidden truncate text-xs text-gray-500 sm:block">National Law School of India University</span>
          </span>
        </router-link>
        <!-- Desktop navigation -->
        <nav class="hidden items-center gap-1 text-sm md:flex">
          <router-link
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="relative whitespace-nowrap rounded-md px-3 py-2 font-medium transition-colors"
            :class="isActive(link.to) ? 'text-brand-700' : 'text-gray-600 hover:text-gray-900'"
          >
            {{ link.label }}
            <span v-if="isActive(link.to)" class="absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full bg-brand-700" />
          </router-link>
          <button
            v-if="session.isLoggedIn"
            class="whitespace-nowrap rounded-md px-3 py-2 font-medium text-gray-600 hover:text-gray-900"
            @click="confirmLogout = true"
          >
            Log out
          </button>
          <a
            v-else
            :href="loginUrl"
            class="ml-1 whitespace-nowrap rounded-md border border-brand-200 px-3 py-1.5 font-semibold text-brand-700 hover:bg-brand-50"
          >
            Log in
          </a>
        </nav>

        <!-- Phones: Log in stays visible; everything else is in a menu. -->
        <div class="flex shrink-0 items-center gap-2 md:hidden">
          <a
            v-if="!session.isLoggedIn"
            :href="loginUrl"
            class="whitespace-nowrap rounded-md border border-brand-200 px-3 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
          >
            Log in
          </a>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md text-gray-700 hover:bg-gray-100"
            :aria-expanded="menuOpen"
            aria-controls="portal-menu"
            :aria-label="menuOpen ? 'Close menu' : 'Open menu'"
            @click="menuOpen = !menuOpen"
          >
            <FeatherIcon :name="menuOpen ? 'x' : 'menu'" class="h-5 w-5" />
          </button>
        </div>
      </div>

      <nav v-if="menuOpen" id="portal-menu" class="border-t bg-white px-4 py-2 md:hidden">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="flex items-center justify-between rounded-md px-3 py-2.5 text-base font-medium"
          :class="isActive(link.to) ? 'bg-brand-50 text-brand-700' : 'text-gray-700 hover:bg-gray-50'"
        >
          {{ link.label }}
          <FeatherIcon name="chevron-right" class="h-4 w-4 opacity-50" />
        </router-link>
        <button
          v-if="session.isLoggedIn"
          type="button"
          class="flex w-full items-center rounded-md px-3 py-2.5 text-left text-base font-medium text-gray-700 hover:bg-gray-50"
          @click="(menuOpen = false), (confirmLogout = true)"
        >
          Log out
        </button>
      </nav>
    </header>
    <Dialog v-model="confirmLogout" :options="{ title: 'Log out?', size: 'sm' }">
      <template #body-content>
        <p class="text-sm text-gray-600">You'll need your username and password to log in again.</p>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="confirmLogout = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="session.logout.loading" @click="session.logout.submit()">Log out</Button>
        </div>
      </template>
    </Dialog>

    <main class="flex-1">
      <slot />
    </main>
    <footer class="border-t bg-white">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-5 text-xs text-gray-500">
        <span>© {{ year }} National Law School of India University, Bengaluru</span>
        <a href="https://www.nls.ac.in" target="_blank" rel="noopener" class="hover:text-brand-700">www.nls.ac.in</a>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { appearance } from '@/utils/theme'

const session = useSessionStore()
const confirmLogout = ref(false)
const route = useRoute()
const loginUrl = computed(() => `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`)
const year = new Date().getFullYear()

// Phone menu; closes on navigation.
const menuOpen = ref(false)
watch(() => route.fullPath, () => (menuOpen.value = false))

// Signed-in candidates see their own pages first; Openings comes last.
const links = computed(() => [
  ...(session.isLoggedIn ? [{ to: '/portal/applications', label: 'My Applications' }] : []),
  ...(session.isCandidate ? [{ to: '/portal/profile', label: 'Profile' }] : []),
  { to: '/portal/jobs', label: 'Openings' },
])

function isActive(to) {
  if (to === '/portal/profile' && route.path === '/portal/change-password') return true
  return route.path === to || route.path.startsWith(`${to}/`)
}
</script>
