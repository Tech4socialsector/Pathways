<template>
  <!-- A list of email addresses (v-model): type or paste, Enter / comma adds. -->
  <div>
    <div class="mb-1 text-xs text-gray-600">{{ label }}</div>
    <div class="flex flex-wrap items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2 py-1.5 focus-within:border-gray-500">
      <span v-for="e in modelValue" :key="e" class="flex items-center gap-1 rounded-full bg-blue-50 py-0.5 pl-2 pr-1 text-xs text-blue-800">
        {{ e }}
        <button type="button" class="rounded-full p-0.5 hover:bg-blue-100" :aria-label="`Remove ${e}`" @click="remove(e)">
          <FeatherIcon name="x" class="h-3 w-3" />
        </button>
      </span>
      <input
        v-model="draft"
        type="email"
        class="min-w-[12rem] flex-1 border-0 p-0.5 text-sm focus:ring-0"
        :placeholder="modelValue.length ? '' : placeholder"
        :aria-label="label"
        @keydown.enter.prevent="addDraft"
        @keydown="(e) => [',', ';'].includes(e.key) && (e.preventDefault(), addDraft())"
        @blur="addDraft"
      />
    </div>
    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: 'Email addresses' },
  placeholder: { type: String, default: 'Add email, press Enter' },
  // Addresses already on the email elsewhere (e.g. CC when this is BCC).
  exclude: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const draft = ref('')
const error = ref('')
const EMAIL = /^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$/

function remove(email) {
  emit('update:modelValue', props.modelValue.filter((e) => e !== email))
}

// Also called by the parent before it sends, so a typed but not yet added address counts.
function addDraft() {
  const parts = draft.value.split(/[\s,;]+/).filter(Boolean)
  const bad = parts.filter((p) => !EMAIL.test(p))
  const seen = new Set([...props.modelValue, ...props.exclude].map((e) => e.toLowerCase()))
  // One emit for all of them: the prop only updates after the parent re-renders.
  const fresh = parts.filter((p) => EMAIL.test(p) && !seen.has(p.toLowerCase()) && seen.add(p.toLowerCase()))
  const all = fresh.length ? [...props.modelValue, ...fresh] : props.modelValue
  if (fresh.length) emit('update:modelValue', all)
  draft.value = bad.join(', ')
  error.value = bad.length ? `Not a valid email: ${bad.join(', ')}` : ''
  return { emails: all, valid: !bad.length }
}

defineExpose({ addDraft })
</script>
