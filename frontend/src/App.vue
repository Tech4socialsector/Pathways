<template>
  <FrappeUIProvider>
    <router-view />
  </FrappeUIProvider>
</template>

<script setup>
import { onMounted } from 'vue'
import { FrappeUIProvider } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()

onMounted(() => {
  if (session.isLoggedIn) {
    session.fetchRoles()
  }
})
</script>
