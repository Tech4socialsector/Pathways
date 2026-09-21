<template>
  <component
    :is="as === 'button' ? 'button' : RouterLink"
    v-bind="linkProps"
    class="flex h-8 items-center gap-2 rounded px-2 text-sm text-gray-700 transition-colors hover:bg-gray-100"
    :class="isActive ? 'bg-gray-200 font-medium text-gray-900' : ''"
  >
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

const isActive = computed(() => props.as !== 'button' && route.path === props.to)
</script>
