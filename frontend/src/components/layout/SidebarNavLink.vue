<template>
  <component
    :is="as === 'button' ? 'button' : RouterLink"
    v-bind="linkProps"
    :aria-label="isExpanded ? undefined : label"
    class="relative flex h-9 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors"
    :class="isActive ? 'bg-brand-50 font-semibold text-brand-700' : 'text-gray-700 hover:bg-gray-100'"
  >
    <span v-if="isActive" class="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-brand-700" />
    <Tooltip :text="label" placement="right" :disabled="isExpanded">
      <span class="flex h-4 w-4 shrink-0 items-center justify-center">
        <FeatherIcon :name="icon" class="h-4 w-4" />
      </span>
    </Tooltip>
    <span v-if="isExpanded" class="truncate">{{ label }}</span>
  </component>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { FeatherIcon, Tooltip } from 'frappe-ui'

const props = defineProps({
  to: { type: [String, Object], default: null },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  isExpanded: { type: Boolean, default: true },
  as: { type: String, default: 'link' },
})

const route = useRoute()

const linkProps = computed(() => (props.as === 'button' ? {} : { to: props.to }))

const isActive = computed(() => {
  if (props.as === 'button') return false
  if (props.to === '/') return route.path === '/'
  return route.path === props.to || route.path.startsWith(`${props.to}/`)
})
</script>
