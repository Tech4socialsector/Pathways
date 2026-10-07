<template>
  <!-- A filter that allows several values: a button showing what is chosen,
       opening a searchable checkbox list. -->
  <div ref="root" class="relative">
    <span class="mb-1.5 block text-xs text-gray-600">{{ label }}</span>
    <button
      type="button"
      class="flex h-8 w-full items-center gap-2 rounded border px-2.5 text-left text-sm transition"
      :class="modelValue.length ? 'border-brand-200 bg-brand-50 text-brand-800' : 'border-transparent bg-gray-100 text-gray-800 hover:bg-gray-200'"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="min-w-0 flex-1 truncate">{{ summary }}</span>
      <span v-if="modelValue.length > 1" class="rounded-full bg-brand-700 px-1.5 text-[11px] font-semibold text-white">{{ modelValue.length }}</span>
      <FeatherIcon name="chevron-down" class="h-4 w-4 shrink-0 text-gray-500" />
    </button>

    <div
      v-if="open"
      class="absolute left-0 top-full z-30 mt-1 w-72 overflow-hidden rounded-lg border bg-white shadow-xl"
      @keydown.esc="open = false"
    >
      <div v-if="normalized.length > 6" class="border-b p-2">
        <input
          ref="searchInput"
          v-model="query"
          type="search"
          :placeholder="`Search ${label.toLowerCase()}...`"
          class="w-full rounded border-gray-200 py-1.5 text-sm focus:border-brand-700 focus:ring-brand-700"
        />
      </div>
      <ul class="max-h-64 overflow-y-auto py-1">
        <li v-for="opt in visible" :key="opt.value">
          <label class="flex cursor-pointer items-center gap-2.5 px-3 py-1.5 text-sm hover:bg-gray-50">
            <input
              type="checkbox"
              class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
              :checked="modelValue.includes(opt.value)"
              @change="toggle(opt.value)"
            />
            <span class="min-w-0 flex-1 truncate" :title="opt.label">{{ opt.label }}</span>
          </label>
        </li>
        <li v-if="!visible.length" class="px-3 py-2 text-sm text-gray-500">No matches.</li>
      </ul>
      <div class="flex items-center justify-between border-t px-3 py-2 text-xs">
        <button type="button" class="font-medium text-brand-700 hover:underline" @click="selectAll">Select all{{ query ? ' shown' : '' }}</button>
        <button type="button" class="font-medium text-gray-600 hover:underline" :disabled="!modelValue.length" @click="emit('update:modelValue', [])">Clear</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  label: { type: String, required: true },
  // ['A', 'B'] or [{ label, value }]
  options: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  allLabel: { type: String, default: 'All' },
})
const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const searchInput = ref(null)
const open = ref(false)
const query = ref('')

const normalized = computed(() => props.options.map((o) => (typeof o === 'object' ? o : { label: o, value: o })))
const visible = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? normalized.value.filter((o) => o.label.toLowerCase().includes(q)) : normalized.value
})
const summary = computed(() => {
  if (!props.modelValue.length) return props.allLabel
  if (props.modelValue.length === 1) return normalized.value.find((o) => o.value === props.modelValue[0])?.label || props.modelValue[0]
  return `${props.modelValue.length} selected`
})

function toggle(value) {
  const next = props.modelValue.includes(value) ? props.modelValue.filter((v) => v !== value) : [...props.modelValue, value]
  emit('update:modelValue', next)
}

function selectAll() {
  emit('update:modelValue', [...new Set([...props.modelValue, ...visible.value.map((o) => o.value)])])
}

watch(open, async (isOpen) => {
  if (!isOpen) return (query.value = '')
  await nextTick()
  searchInput.value?.focus()
})

function onOutside(e) {
  if (open.value && root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', onOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutside))
</script>
