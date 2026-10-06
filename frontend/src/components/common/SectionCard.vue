<template>
  <section class="rounded-xl border border-gray-200 bg-white shadow-sm">
    <header v-if="title" class="relative flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 px-5 py-3.5">
      <div class="flex min-w-0 items-center gap-2.5">
        <div v-if="icon" class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700">
          <FeatherIcon :name="icon" class="h-[18px] w-[18px]" />
        </div>
        <div class="min-w-0">
          <h2 class="text-lg font-bold leading-tight text-brand-700">{{ title }}</h2>
          <p v-if="subtitle" class="text-xs text-gray-500">{{ subtitle }}</p>
        </div>
      </div>
      <!-- Accent under the title, over the divider. -->
      <span class="absolute -bottom-px left-5 h-0.5 w-10 rounded-full bg-brand-700" aria-hidden="true" />
      <div class="flex shrink-0 items-center gap-2">
        <slot name="actions" />
      </div>
    </header>
    <div class="px-5 py-4">
      <slot />
    </div>
  </section>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: '' },
})
</script>
