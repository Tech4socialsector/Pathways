<template>
  <!-- A <label> focuses its input when the caption is clicked; use as="div"
       for a group of checkboxes or a rich-text editor. -->
  <component :is="as" class="block" :class="error && 'field-invalid'">
    <span class="mb-1.5 block text-sm font-medium text-gray-700">{{ label }}</span>
    <slot />
    <p v-if="error" class="mt-1 text-sm text-red-600" role="alert">{{ error }}</p>
    <p v-else-if="warning" class="mt-1 flex items-start gap-1.5 text-p-sm text-amber-700">
      <FeatherIcon name="alert-triangle" class="mt-0.5 h-3.5 w-3.5 shrink-0" />{{ warning }}
    </p>
    <p v-else-if="hint" class="mt-1 text-p-sm text-gray-500">{{ hint }}</p>
  </component>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  label: { type: String, required: true },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  warning: { type: String, default: '' },
  as: { type: String, default: 'label' },
})
</script>
