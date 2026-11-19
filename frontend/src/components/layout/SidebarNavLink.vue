<template>
  <!-- Collapsed rail: icon centred in a square, the label as a tooltip over
       the whole row. Expanded (and the phone drawer): icon + label.
       Two explicit elements rather than <component :is="'button'">: that
       string resolves to the globally registered frappe-ui Button. -->
  <Tooltip :text="label" placement="right" :hover-delay="0.15" :disabled="isExpanded">
    <button
      v-if="as === 'button'"
      type="button"
      v-bind="$attrs"
      :aria-label="isExpanded ? undefined : label"
      :class="[base, 'text-gray-600 hover:bg-gray-100 hover:text-gray-900']"
    >
      <FeatherIcon :name="icon" class="h-[18px] w-[18px] shrink-0" />
      <span v-if="isExpanded" class="truncate">{{ label }}</span>
    </button>
    <RouterLink
      v-else
      :to="to"
      v-bind="$attrs"
      :aria-label="isExpanded ? undefined : label"
      :aria-current="isActive ? 'page' : undefined"
      :class="[base, isActive ? 'bg-brand-50 font-semibold text-brand-700' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900']"
    >
      <span v-if="isActive" class="absolute inset-y-1.5 left-0 w-[3px] rounded-r-full bg-brand-700" aria-hidden="true" />
      <FeatherIcon :name="icon" class="h-[18px] w-[18px] shrink-0" />
      <span v-if="isExpanded" class="truncate">{{ label }}</span>
    </RouterLink>
  </Tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { FeatherIcon, Tooltip } from 'frappe-ui'

// Listeners such as the toggle's @click go on the button/link, not the Tooltip.
defineOptions({ inheritAttrs: false })

const props = defineProps({
  to: { type: [String, Object], default: null },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  isExpanded: { type: Boolean, default: true },
  as: { type: String, default: 'link' },
  // Set by the sidebar for pages that sit outside their module's path
  // (route meta.sections).
  forceActive: { type: Boolean, default: false },
})

const route = useRoute()

const base = computed(() => [
  'relative flex h-10 w-full items-center rounded-lg text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand-300',
  props.isExpanded ? 'gap-3 px-3 text-left' : 'justify-center px-0',
])

const isActive = computed(() => {
  if (props.as === 'button') return false
  if (props.forceActive) return true
  if (props.to === '/') return route.path === '/'
  return route.path === props.to || route.path.startsWith(`${props.to}/`)
})
</script>
