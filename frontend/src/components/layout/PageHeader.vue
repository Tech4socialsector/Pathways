<template>
  <div class="flex items-center justify-between border-b px-6 py-4">
    <div>
      <h1 class="text-xl font-semibold text-gray-900">{{ title }}</h1>
      <p v-if="subtitle" class="mt-0.5 text-sm text-gray-500">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
