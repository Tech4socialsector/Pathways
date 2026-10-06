<template>
  <div>
    <!-- Wide screens: every step in one row -->
    <ol class="hidden md:flex">
      <li v-for="(step, idx) in steps" :key="step.key" class="relative flex flex-1 flex-col items-center text-center">
        <span
          v-if="idx > 0"
          class="absolute right-1/2 top-3 h-0.5 w-full -translate-y-1/2"
          :class="step.state === 'pending' || step.state === 'skipped' ? 'bg-gray-200' : 'bg-brand-700'"
        />
        <span
          class="relative z-10 flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold"
          :class="dotClass(step)"
        >
          <FeatherIcon v-if="step.state === 'completed'" name="check" class="h-3.5 w-3.5" />
          <FeatherIcon v-else-if="step.state === 'rejected'" name="x" class="h-3.5 w-3.5" />
          <template v-else>{{ idx + 1 }}</template>
        </span>
        <span class="mt-1.5 px-1 text-[11px] leading-tight" :class="labelClass(step)">{{ step.label }}</span>
      </li>
    </ol>

    <!-- Narrow screens: just where the application is -->
    <div class="flex items-center gap-3 md:hidden">
      <span class="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold" :class="dotClass(current)">
        {{ currentIndex + 1 }}
      </span>
      <div class="text-sm">
        <div class="font-semibold text-gray-900">{{ current?.label }}</div>
        <div class="text-xs text-gray-500">Step {{ currentIndex + 1 }} of {{ steps.length }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

// steps: [{ key, label, state: 'completed' | 'current' | 'pending' | 'rejected' | 'skipped' }]
const props = defineProps({
  steps: { type: Array, required: true },
})

const currentIndex = computed(() => {
  const idx = props.steps.findIndex((s) => s.state === 'current' || s.state === 'rejected')
  return idx === -1 ? Math.max(props.steps.findLastIndex((s) => s.state === 'completed'), 0) : idx
})
const current = computed(() => props.steps[currentIndex.value])

function dotClass(step) {
  if (step?.state === 'completed') return 'bg-brand-700 text-white'
  if (step?.state === 'current') return 'bg-white text-brand-700 ring-2 ring-brand-700'
  if (step?.state === 'rejected') return 'bg-red-600 text-white'
  return 'bg-gray-100 text-gray-400'
}

function labelClass(step) {
  if (step.state === 'current') return 'font-bold text-brand-700'
  if (step.state === 'completed') return 'text-gray-700'
  if (step.state === 'rejected') return 'font-bold text-red-600'
  return 'text-gray-400'
}
</script>
