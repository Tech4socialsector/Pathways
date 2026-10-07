<template>
  <!-- Shown after a bulk action that skipped some records, with each reason. -->
  <Dialog :model-value="!!result" :options="{ title, size: 'xl' }" @update:model-value="(v) => !v && emit('close')">
    <template #body-content>
      <div v-if="result" class="flex flex-col gap-3 text-sm">
        <p class="text-gray-700">
          <span class="font-semibold text-green-700">{{ result.done.length }} done</span>,
          <span class="font-semibold text-red-700">{{ result.failed.length }} skipped</span>.
        </p>
        <ul class="max-h-72 divide-y overflow-y-auto rounded-lg border">
          <li v-for="f in result.failed" :key="f.name" class="px-3 py-2">
            <div class="font-medium text-gray-900">{{ labelFor ? labelFor(f.name) : f.name }}</div>
            <div class="text-xs text-red-700">{{ f.error }}</div>
          </li>
        </ul>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'

defineProps({
  // { done: [names], failed: [{ name, error }] } or null
  result: { type: Object, default: null },
  title: { type: String, default: 'Some records were skipped' },
  // name -> display label (e.g. the application ID or job title)
  labelFor: { type: Function, default: null },
})
const emit = defineEmits(['close'])
</script>
