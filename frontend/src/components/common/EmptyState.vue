<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <div class="mb-2 text-sm font-medium text-gray-700">{{ title }}</div>
    <div v-if="description" class="text-sm text-gray-500">{{ description }}</div>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>
