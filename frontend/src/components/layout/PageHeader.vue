<template>
  <div class="border-b bg-white px-6 pb-4 pt-3">
    <nav v-if="breadcrumbs.length > 1" class="mb-2 flex flex-wrap items-center gap-1.5 text-xs text-gray-500" aria-label="Breadcrumb">
      <RouterLink to="/" class="text-brand-700 hover:text-brand-800" aria-label="Home">
        <FeatherIcon name="home" class="h-3.5 w-3.5" />
      </RouterLink>
      <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
        <FeatherIcon name="chevron-right" class="h-3 w-3 text-gray-400" />
        <RouterLink v-if="crumb.to" :to="crumb.to" class="hover:text-gray-900 hover:underline">{{ crumb.label }}</RouterLink>
        <span v-else class="font-medium text-gray-800">{{ crumb.label }}</span>
      </template>
    </nav>
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex min-w-0 items-start gap-3">
        <BackButton v-if="showBack" :fallback="backFallback" class="mt-0.5" />
        <div class="min-w-0">
          <h1 class="text-gray-900" :class="breadcrumbs.length > 1 ? 'text-2xl font-bold' : 'text-xl font-semibold'">{{ title }}</h1>
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
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import BackButton from '@/components/common/BackButton.vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  // [{ label, to? }] — the last crumb is usually the current page (no `to`).
  breadcrumbs: { type: Array, default: () => [] },
  // Overrides the back button's fallback (used when there is no history).
  backTo: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()

// Only pages below a section get a back button (/jobs/PWY-JOB-..., not
// /jobs): list pages are reached from the sidebar.
const showBack = computed(() => route.path.split('/').filter(Boolean).length > 1)

// No history: the nearest breadcrumb link, else the list this page sits
// under (/jobs/PWY-JOB-... -> /jobs), else the dashboard.
const backFallback = computed(() => {
  if (props.backTo) return props.backTo
  const crumb = [...props.breadcrumbs].reverse().find((c) => c.to)
  if (crumb) return crumb.to
  const parts = route.path.split('/').filter(Boolean)
  if (parts.length > 1) {
    const parent = `/${parts.slice(0, -1).join('/')}`
    if (router.resolve(parent).matched.length) return parent
  }
  return '/'
})
</script>
