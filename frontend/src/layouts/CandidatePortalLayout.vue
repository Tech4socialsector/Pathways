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
        <nav class="flex items-center gap-1 text-sm">
          <router-link
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="relative rounded-md px-3 py-2 font-medium transition-colors"
            :class="isActive(link.to) ? 'text-brand-700' : 'text-gray-600 hover:text-gray-900'"
          >
            {{ link.label }}
            <span v-if="isActive(link.to)" class="absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full bg-brand-700" />
          </router-link>
          <button
            v-if="session.isLoggedIn"
            class="rounded-md px-3 py-2 font-medium text-gray-600 hover:text-gray-900"
            @click="session.logout.submit()"
          >
            Log out
          </button>
          <a
            v-else
            :href="loginUrl"
            class="ml-1 rounded-md border border-brand-200 px-3 py-1.5 font-semibold text-brand-700 hover:bg-brand-50"
          >
            Log in
          </a>
        </nav>
      </div>
    </header>
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { appearance } from '@/utils/theme'

const session = useSessionStore()
const route = useRoute()
const loginUrl = computed(() => `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`)
const year = new Date().getFullYear()

const links = computed(() => [
  { to: '/portal/jobs', label: 'Openings' },
  ...(session.isLoggedIn ? [{ to: '/portal/applications', label: 'My Applications' }] : []),
])

function isActive(to) {
  return route.path === to || route.path.startsWith(`${to}/`)
}
</script>
