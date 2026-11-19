<template>
  <FrappeUIProvider>
    <router-view />
    <InstallPrompt />
  </FrappeUIProvider>
</template>

<script setup>
import { onMounted } from 'vue'
import { FrappeUIProvider } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import InstallPrompt from '@/components/common/InstallPrompt.vue'

const session = useSessionStore()

onMounted(() => {
  if (session.isLoggedIn) {
    session.fetchRoles()
  }
})
</script>
