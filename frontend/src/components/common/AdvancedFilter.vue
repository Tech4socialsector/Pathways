<template>
  <!-- Desk-style filter builder: field · condition · value rows, applied together. -->
  <div ref="root" class="relative">
    <div class="flex items-center">
      <Button
        icon-left="filter"
        :class="[applied.length && '!rounded-r-none !bg-brand-50 !text-brand-800', open && 'bg-gray-200']"
        @click="toggle"
      >
        Filter<span v-if="applied.length" class="ml-1 rounded-full bg-brand-700 px-1.5 text-[11px] font-semibold text-white">{{ applied.length }}</span>
      </Button>
      <Button
        v-if="applied.length"
        icon="x"
        class="!rounded-l-none !border-l !border-brand-100 !bg-brand-50 !text-brand-800"
        aria-label="Clear filters"
        title="Clear filters"
        @click="clearAll"
      />
    </div>

    <div
      v-if="open"
      class="absolute right-0 top-9 z-40 w-[min(42rem,calc(100vw-2rem))] rounded-xl border bg-white p-3 shadow-xl"
      @keydown.esc="open = false"
    >
      <p v-if="!draft.length" class="px-1 pb-2 text-sm text-gray-500">No filters yet. Add one to narrow the list.</p>
      <div v-for="(c, i) in draft" :key="c.id" class="mb-2 grid grid-cols-[minmax(0,1fr)_minmax(0,0.8fr)_minmax(0,1fr)_auto] items-center gap-2">
        <select v-model="c.key" class="h-8 min-w-0 rounded border-gray-200 bg-gray-100 text-sm focus:border-brand-700 focus:ring-brand-700" :aria-label="`Filter ${i + 1} field`" @change="onFieldChange(c)">
          <option v-for="col in columns" :key="col.key" :value="col.key">{{ col.label }}</option>
        </select>
        <select v-model="c.op" class="h-8 min-w-0 rounded border-gray-200 bg-gray-100 text-sm focus:border-brand-700 focus:ring-brand-700" :aria-label="`Filter ${i + 1} condition`">
          <option v-for="op in opsFor(c.key)" :key="op.value" :value="op.value">{{ op.label }}</option>
        </select>
        <div class="flex min-w-0 gap-1">
          <template v-if="!NO_VALUE.has(c.op)">
            <select
              v-if="typeOf(c.key) === 'text' && (c.op === 'eq' || c.op === 'neq') && choices(c.key).length"
              v-model="c.value"
              class="h-8 min-w-0 flex-1 rounded border-gray-200 bg-gray-100 text-sm focus:border-brand-700 focus:ring-brand-700"
              :aria-label="`Filter ${i + 1} value`"
            >
              <option value="">Choose…</option>
              <option v-for="v in choices(c.key)" :key="v" :value="v">{{ v }}</option>
            </select>
            <input
              v-else
              v-model="c.value"
              :type="inputType(c.key)"
              class="h-8 min-w-0 flex-1 rounded border-gray-200 bg-gray-100 px-2 text-sm focus:border-brand-700 focus:ring-brand-700"
              :placeholder="typeOf(c.key) === 'text' ? 'Value' : ''"
              :aria-label="`Filter ${i + 1} value`"
              @keydown.enter="apply"
            />
            <input
              v-if="c.op === 'between'"
              v-model="c.value2"
              :type="inputType(c.key)"
              class="h-8 min-w-0 flex-1 rounded border-gray-200 bg-gray-100 px-2 text-sm focus:border-brand-700 focus:ring-brand-700"
              :aria-label="`Filter ${i + 1} second value`"
            />
          </template>
        </div>
        <button type="button" class="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700" :aria-label="`Remove filter ${i + 1}`" @click="draft.splice(i, 1)">
          <FeatherIcon name="x" class="h-4 w-4" />
        </button>
      </div>
      <div class="mt-1 flex flex-wrap items-center justify-between gap-2 border-t pt-3">
        <button type="button" class="flex items-center gap-1 text-sm font-medium text-gray-700 hover:text-brand-700" @click="addRow">
          <FeatherIcon name="plus" class="h-4 w-4" />Add a filter
        </button>
        <div class="flex gap-2">
          <Button @click="clearAll">Clear Filters</Button>
          <Button variant="solid" :class="BTN_BRAND" @click="apply">Apply Filters</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { conditionOps, NO_VALUE, valueType } from '@/utils/advancedFilter'

const props = defineProps({
  // [{ key, label, format?, type? }] — every column the list can show.
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  // Applied conditions: [{ key, op, value, value2 }]
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const open = ref(false)
const draft = ref([])
const applied = ref(props.modelValue)
watch(
  () => props.modelValue,
  (v) => (applied.value = v),
)

let seq = 0
const copy = (list) => list.map((c) => ({ ...c, id: ++seq }))

function toggle() {
  if (!open.value) {
    draft.value = copy(applied.value)
    if (!draft.value.length) addRow()
  }
  open.value = !open.value
}

function typeOf(key) {
  return valueType(props.columns.find((c) => c.key === key), props.rows)
}
function opsFor(key) {
  return conditionOps(typeOf(key))
}
function inputType(key) {
  return { number: 'number', date: 'date' }[typeOf(key)] || 'text'
}
// Up to 40 distinct values: offer them as a list for equals / not equals.
function choices(key) {
  const col = props.columns.find((c) => c.key === key)
  const values = new Set()
  for (const row of props.rows) {
    const v = col?.format ? col.format(row) : row[key]
    if (v !== null && v !== undefined && v !== '') values.add(String(v))
    if (values.size > 40) return []
  }
  return [...values].sort((a, b) => a.localeCompare(b))
}

function addRow() {
  const key = props.columns[0]?.key
  draft.value.push({ id: ++seq, key, op: opsFor(key)[0].value, value: '', value2: '' })
}
function onFieldChange(c) {
  const ops = opsFor(c.key)
  if (!ops.some((o) => o.value === c.op)) c.op = ops[0].value
  c.value = ''
  c.value2 = ''
}

function apply() {
  // Drop rows that still need a value.
  const ready = draft.value
    .filter((c) => c.key && (NO_VALUE.has(c.op) || String(c.value).trim() !== ''))
    .map(({ key, op, value, value2 }) => ({ key, op, value, value2 }))
  emit('update:modelValue', ready)
  open.value = false
}
function clearAll() {
  draft.value = []
  emit('update:modelValue', [])
  open.value = false
}

function onOutside(e) {
  if (open.value && root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', onOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutside))
</script>
