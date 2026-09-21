<template>
  <div class="flex h-full flex-col">
    <header class="flex items-center justify-between border-b bg-white px-6 py-3">
      <div class="text-lg font-semibold text-gray-900">NLSIU Careers</div>
      <div class="flex items-center gap-4 text-sm">
        <router-link to="/portal/jobs" class="text-gray-600 hover:text-gray-900">Openings</router-link>
        <router-link
          v-if="session.isLoggedIn"
          to="/portal/applications"
          class="text-gray-600 hover:text-gray-900"
        >
          My Applications
        </router-link>
        <button
          v-if="session.isLoggedIn"
          class="text-gray-600 hover:text-gray-900"
          @click="session.logout.submit()"
        >
          Log out
        </button>
        <a v-else :href="loginUrl" class="text-gray-600 hover:text-gray-900">Log in</a>
      </div>
    </header>
    <main class="flex-1 overflow-y-auto bg-gray-50">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const loginUrl = computed(() => `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`)
</script>
