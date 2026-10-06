<template>
  <button
    type="button"
    class="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-gray-200 bg-white px-2.5 text-sm text-gray-700 transition-colors hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"
    aria-label="Go back"
    @click="goBack"
  >
    <FeatherIcon name="arrow-left" class="h-4 w-4" />
    <span v-if="label">{{ label }}</span>
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  // Where to go when there is no in-app page to return to (the page was
  // opened from a link, a bookmark or a new tab).
  fallback: { type: String, default: '/' },
  label: { type: String, default: 'Back' },
})

const router = useRouter()

function goBack() {
  // vue-router records the previous in-app route in history.state.back.
  if (window.history.state?.back) router.back()
  else router.push(props.fallback)
}
</script>
