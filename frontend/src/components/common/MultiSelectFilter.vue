<template>
  <!-- A filter that allows several values: a button showing what is chosen,
       opening a searchable checkbox list. The list renders in a portal so it
       is never clipped by a dialog or a scrolling container. -->
  <div>
    <span v-if="!hideLabel" class="mb-1.5 block text-xs text-gray-600">{{ label }}</span>
    <Popover v-model:show="open" class="w-full" placement="bottom-start" :offset="4" match-target-width>
      <template #target="{ togglePopover }">
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded border px-2.5 text-left text-sm transition"
          :class="[
            hideLabel ? 'h-7' : 'h-8',
            modelValue.length ? 'border-brand-200 bg-brand-50 text-brand-800' : 'border-transparent bg-gray-100 text-gray-800 hover:bg-gray-200',
          ]"
          :aria-expanded="open"
          aria-haspopup="listbox"
          :title="modelValue.length > 1 ? selectedLabels.join(', ') : undefined"
          @click="togglePopover()"
        >
          <span class="min-w-0 flex-1 truncate">{{ summary }}</span>
          <span v-if="modelValue.length > 1" class="rounded-full bg-brand-700 px-1.5 text-[11px] font-semibold text-white">{{ modelValue.length }}</span>
          <FeatherIcon name="chevron-down" class="h-4 w-4 shrink-0 text-gray-500" />
        </button>
      </template>

      <template #body>
        <div class="w-max min-w-full max-w-[min(32rem,calc(100vw-2rem))] overflow-hidden rounded-lg border bg-white shadow-xl">
          <div v-if="allOptions.length > 6" class="border-b p-2">
            <input
              ref="searchInput"
              v-model="query"
              type="search"
              :placeholder="`Search ${label.toLowerCase()}...`"
              class="w-full rounded border-gray-200 py-1.5 text-sm focus:border-brand-700 focus:ring-brand-700"
            />
          </div>
          <ul class="max-h-64 overflow-y-auto py-1" role="listbox" aria-multiselectable="true">
            <li v-for="opt in visible" :key="String(opt.value)">
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
          <div class="flex items-center justify-between gap-4 border-t px-3 py-2 text-xs">
            <button type="button" class="font-medium text-brand-700 hover:underline" :disabled="!visible.length" @click="selectAll">
              Select all{{ query ? ' shown' : '' }}
            </button>
            <button
              type="button"
              class="font-medium text-gray-600 hover:underline disabled:opacity-50"
              :disabled="!modelValue.length"
              @click="emit('update:modelValue', [])"
            >
              Clear
            </button>
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { FeatherIcon, Popover } from 'frappe-ui'

const props = defineProps({
  label: { type: String, required: true },
  // ['A', 'B'] or [{ label, value }]
  options: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  allLabel: { type: String, default: 'All' },
  // Inline in a toolbar: no caption above, and the height of the other inputs.
  hideLabel: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const searchInput = ref(null)
const open = ref(false)
const query = ref('')

const normalized = computed(() => props.options.map((o) => (typeof o === 'object' ? o : { label: String(o), value: o })))
// A chosen value can drop out of the options (e.g. the last row with that
// status changed). Keep listing it so it can still be unticked.
const allOptions = computed(() => {
  const known = new Set(normalized.value.map((o) => o.value))
  const orphans = props.modelValue.filter((v) => !known.has(v)).map((v) => ({ label: String(v), value: v }))
  return [...orphans, ...normalized.value]
})
const visible = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? allOptions.value.filter((o) => String(o.label).toLowerCase().includes(q)) : allOptions.value
})
const selectedLabels = computed(() =>
  props.modelValue.map((v) => allOptions.value.find((o) => o.value === v)?.label ?? String(v)),
)
const summary = computed(() => {
  if (!props.modelValue.length) return props.allLabel
  if (props.modelValue.length === 1) return selectedLabels.value[0]
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
</script>
