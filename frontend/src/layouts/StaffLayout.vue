<template>
  <div class="flex h-full">
    <RoleAwareSidebar />
    <div class="flex flex-1 flex-col overflow-hidden">
      <slot />
    </div>
  </div>
</template>

<script setup>
import RoleAwareSidebar from '@/components/layout/RoleAwareSidebar.vue'
</script>
