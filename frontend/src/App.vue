<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()

onMounted(() => {
  if (session.isLoggedIn) {
    session.fetchRoles()
  }
})
</script>
