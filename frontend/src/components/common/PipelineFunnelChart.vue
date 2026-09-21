<template>
  <div class="viz-root">
    <div v-if="!maxValue" class="text-sm text-gray-500">No applications yet.</div>
    <div v-else class="flex flex-col gap-2">
      <div v-for="(stage, i) in stages" :key="stage.label" class="flex items-center gap-3">
        <div class="w-32 shrink-0 text-xs text-gray-600">{{ stage.label }}</div>
        <div class="relative flex-1">
          <div
            class="funnel-bar flex h-6 items-center justify-end rounded-r pr-2 text-xs font-medium text-white transition-[filter] duration-150"
            :style="{
              width: barWidth(stage.value) + '%',
              backgroundColor: `var(--funnel-step-${i})`,
            }"
            :tabindex="0"
            role="img"
            :aria-label="`${stage.label}: ${stage.value}${dropOffLabel(i) ? ', ' + dropOffLabel(i) : ''}`"
            @mouseenter="hovered = i"
            @mouseleave="hovered = null"
            @focus="hovered = i"
            @blur="hovered = null"
          >
            {{ stage.value }}
          </div>
          <div
            v-if="hovered === i && dropOffLabel(i)"
            class="pointer-events-none absolute left-0 top-full z-10 mt-1 whitespace-nowrap rounded bg-gray-900 px-2 py-1 text-xs text-white shadow-sm"
          >
            {{ dropOffLabel(i) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  stages: {
    // [{ label: 'Applied', value: 12 }, ...] — ordered, most-to-least
    type: Array,
    required: true,
  },
})

const hovered = ref(null)

const maxValue = computed(() => Math.max(0, ...props.stages.map((s) => s.value || 0)))

function barWidth(value) {
  if (!maxValue.value) return 0
  // Floor so a non-zero stage is never visually indistinguishable from zero.
  return Math.max((value / maxValue.value) * 100, value > 0 ? 4 : 0)
}

function dropOffLabel(index) {
  if (index === 0) return ''
  const prev = props.stages[index - 1].value
  const current = props.stages[index].value
  if (!prev) return ''
  const pct = Math.round((current / prev) * 100)
  return `${pct}% of ${props.stages[index - 1].label}`
}
</script>

<style scoped>
.viz-root {
  color-scheme: light;
  --funnel-step-0: #86b6ef;
  --funnel-step-1: #5598e7;
  --funnel-step-2: #2a78d6;
  --funnel-step-3: #1c5cab;
  --funnel-step-4: #104281;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) .viz-root {
    color-scheme: dark;
    --funnel-step-0: #184f95;
    --funnel-step-1: #256abf;
    --funnel-step-2: #3987e5;
    --funnel-step-3: #6da7ec;
    --funnel-step-4: #9ec5f4;
  }
}

:root[data-theme='dark'] .viz-root {
  color-scheme: dark;
  --funnel-step-0: #184f95;
  --funnel-step-1: #256abf;
  --funnel-step-2: #3987e5;
  --funnel-step-3: #6da7ec;
  --funnel-step-4: #9ec5f4;
}

.funnel-bar:hover,
.funnel-bar:focus-visible {
  filter: brightness(1.08);
  outline: none;
}
</style>
