<template>
  <ol class="flex flex-col gap-0">
    <li v-for="(step, idx) in steps" :key="step.key" class="relative flex gap-3 pb-5 last:pb-0">
      <div class="flex flex-col items-center">
        <span
          class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
          :class="dotClass(step)"
        >
          <FeatherIcon v-if="step.state === 'completed'" name="check" class="h-3.5 w-3.5" />
          <FeatherIcon v-else-if="step.state === 'rejected'" name="x" class="h-3.5 w-3.5" />
          <span v-else-if="step.state === 'current'" class="h-2 w-2 rounded-full bg-white" />
          <template v-else>{{ idx + 1 }}</template>
        </span>
        <span v-if="idx < steps.length - 1" class="mt-1 w-px flex-1" :class="lineClass(step)" />
      </div>
      <div class="pb-1">
        <div class="text-sm font-medium" :class="labelClass(step)">{{ step.label }}</div>
        <div v-if="step.detail" class="text-xs text-gray-500">{{ step.detail }}</div>
      </div>
    </li>
  </ol>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

// steps: [{ key, label, detail?, state: 'completed' | 'current' | 'pending' | 'rejected' | 'skipped' }]
defineProps({
  steps: { type: Array, required: true },
})

function dotClass(step) {
  if (step.state === 'completed') return 'bg-green-500 text-white'
  if (step.state === 'current') return 'bg-indigo-500 text-white ring-4 ring-indigo-100'
  if (step.state === 'rejected') return 'bg-red-500 text-white'
  if (step.state === 'skipped') return 'bg-gray-200 text-gray-400'
  return 'bg-gray-200 text-gray-500'
}

function lineClass(step) {
  return step.state === 'completed' ? 'bg-green-300' : 'bg-gray-200'
}

function labelClass(step) {
  if (step.state === 'pending' || step.state === 'skipped') return 'text-gray-400'
  if (step.state === 'rejected') return 'text-red-600'
  return 'text-gray-900'
}
</script>
