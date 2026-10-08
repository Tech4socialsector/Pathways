<template>
  <div class="flex items-center gap-1">
    <div class="min-w-0 flex-1">
      <Autocomplete
        :placeholder="placeholder"
        :options="options"
        :model-value="modelValue || ''"
        :loading="loading"
        :disabled="disabled"
        @update:query="onQuery"
        @update:model-value="(opt) => emit('update:modelValue', opt?.value ?? null)"
      />
    </div>
    <Button
      v-if="modelValue && !disabled"
      variant="ghost"
      icon="x"
      :aria-label="`Clear ${label}`"
      :title="`Clear ${label}`"
      @click="emit('update:modelValue', null)"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Autocomplete, Button } from 'frappe-ui'
import { searchLink as search } from '@/utils/masterForm'

const props = defineProps({
  doctype: { type: String, required: true },
  modelValue: { type: String, default: null },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const placeholder = computed(() => `Select ${props.label || props.doctype}`)

const results = ref([])
const loading = ref(false)
let request = 0
let timer = null

async function load(txt) {
  const mine = ++request
  loading.value = true
  try {
    const rows = (await search(props.doctype, txt)) || []
    if (mine === request) results.value = rows
  } catch {
    if (mine === request) results.value = []
  } finally {
    if (mine === request) loading.value = false
  }
}

function onQuery(txt) {
  clearTimeout(timer)
  timer = setTimeout(() => load((txt || '').trim()), 250)
}

onMounted(() => load(''))
onBeforeUnmount(() => clearTimeout(timer))

// The dropdown filters on label and value only, so the server's description
// (e.g. a user's full name) goes into the label to stay searchable. The
// current value is always listed, so it shows even if it isn't in the results.
const options = computed(() => {
  const opts = results.value.map((r) => {
    const main = r.label && r.label !== r.value ? `${r.label} (${r.value})` : r.value
    return { value: r.value, label: r.description ? `${main} · ${r.description}` : main }
  })
  if (props.modelValue && !opts.some((o) => o.value === props.modelValue)) {
    opts.unshift({ value: props.modelValue, label: props.modelValue })
  }
  return opts
})
</script>
