<template>
  <div class="border-b bg-white px-6 py-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex min-w-0 items-start gap-3">
        <BackButton v-if="showBack" :fallback="backFallback" class="mt-0.5" />
        <div class="min-w-0">
          <h1 class="text-2xl font-semibold text-gray-900">{{ title }}</h1>
          <p v-if="subtitle" class="mt-0.5 text-sm text-gray-500">{{ subtitle }}</p>
          <slot name="meta" />
        </div>
      </div>
      <div class="flex items-center gap-2">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BackButton from '@/components/common/BackButton.vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  // Overrides the back button's fallback (used when there is no history).
  backTo: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()

// Only pages below a section get a back button (/jobs/PWY-JOB-..., not
// /jobs): list pages are reached from the sidebar.
const showBack = computed(() => route.path.split('/').filter(Boolean).length > 1)

// No history: backTo, else the list this page sits under
// (/jobs/PWY-JOB-... -> /jobs), else the dashboard.
const backFallback = computed(() => {
  if (props.backTo) return props.backTo
  const parts = route.path.split('/').filter(Boolean)
  if (parts.length > 1) {
    const parent = `/${parts.slice(0, -1).join('/')}`
    if (router.resolve(parent).matched.length) return parent
  }
  return '/'
})
</script>
