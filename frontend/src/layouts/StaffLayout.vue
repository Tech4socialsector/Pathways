<template>
  <div class="flex h-full flex-col">
    <TopBar />
    <div class="flex min-h-0 flex-1">
      <RoleAwareSidebar />
      <div class="flex flex-1 flex-col overflow-hidden">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import TopBar from '@/components/layout/TopBar.vue'
import RoleAwareSidebar from '@/components/layout/RoleAwareSidebar.vue'
</script>
