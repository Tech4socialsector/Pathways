<template>
  <div class="viz-root">
    <div v-if="!maxValue" class="text-sm text-gray-500">No applications yet.</div>
    <div v-else class="flex flex-col gap-2">
      <div
        v-for="(stage, i) in stages"
        :key="stage.label"
        class="group flex cursor-pointer items-center gap-3 rounded-md px-1 py-0.5 hover:bg-gray-50"
        @click="emit('select', stage)"
      >
        <div class="w-32 shrink-0 text-xs text-gray-600 group-hover:font-semibold group-hover:text-gray-900">{{ stage.label }}</div>
        <div class="relative flex-1">
          <div
            class="funnel-bar flex h-6 items-center justify-end rounded-r pr-2 text-xs font-medium text-white transition-[filter] duration-150"
            :style="{
              width: barWidth(stage.value) + '%',
              backgroundColor: `var(--funnel-step-${i})`,
            }"
            :tabindex="0"
            role="button"
            :aria-label="`${stage.label}: ${stage.value}${dropOffLabel(i) ? ', ' + dropOffLabel(i) : ''}. Show applications.`"
            @keydown.enter="emit('select', stage)"
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

const emit = defineEmits(['select'])

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
  --funnel-step-0: #dc5a6f;
  --funnel-step-1: #c42a44;
  --funnel-step-2: #a9142f;
  --funnel-step-3: #920c24;
  --funnel-step-4: #5e0818;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) .viz-root {
    color-scheme: dark;
    --funnel-step-0: #780a1e;
    --funnel-step-1: #a9142f;
    --funnel-step-2: #c42a44;
    --funnel-step-3: #dc5a6f;
    --funnel-step-4: #ec94a2;
  }
}

:root[data-theme='dark'] .viz-root {
  color-scheme: dark;
  --funnel-step-0: #780a1e;
  --funnel-step-1: #a9142f;
  --funnel-step-2: #c42a44;
  --funnel-step-3: #dc5a6f;
  --funnel-step-4: #ec94a2;
}

.funnel-bar:hover,
.funnel-bar:focus-visible {
  filter: brightness(1.08);
  outline: none;
}
</style>
