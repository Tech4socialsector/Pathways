<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-end gap-2">
      <div class="w-full sm:w-64">
        <TextInput v-model="search" type="text" :placeholder="searchPlaceholder">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
        </TextInput>
      </div>
      <!-- Each filter takes several values; a row matches any of them. -->
      <MultiSelectFilter
        v-for="filter in resolvedFilters"
        :key="filter.key"
        class="w-full sm:w-44"
        hide-label
        :label="filter.label"
        :all-label="`All ${filter.label}`"
        :options="filter.options"
        :model-value="filterValues[filter.key] || []"
        @update:model-value="(v) => (filterValues[filter.key] = v)"
      />
      <Button v-if="isFiltered" variant="ghost" @click="clearFilters">Clear</Button>
      <div class="ml-auto flex items-center gap-2">
        <slot name="toolbar" />
        <!-- Column chooser: which columns this user sees, and their order -->
        <div v-if="columnsKey" ref="colRoot" class="relative">
          <Button icon-left="columns" :class="colOpen && 'bg-gray-200'" @click="colOpen = !colOpen">
            Columns<span v-if="customised" class="ml-1 h-1.5 w-1.5 rounded-full bg-brand-700" />
          </Button>
          <div v-if="colOpen" class="absolute right-0 top-9 z-30 w-72 overflow-hidden rounded-lg border bg-white shadow-xl">
            <div class="flex items-center justify-between border-b px-3 py-2">
              <span class="text-sm font-semibold text-gray-900">Show columns</span>
              <button type="button" class="text-xs font-medium text-brand-700 hover:underline disabled:opacity-40" :disabled="!customised" @click="resetColumns">
                Reset
              </button>
            </div>
            <ul class="max-h-80 overflow-y-auto py-1">
              <li v-for="(col, idx) in orderedColumns" :key="col.key" class="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-gray-50">
                <input
                  :id="`col-${columnsKey}-${col.key}`"
                  type="checkbox"
                  class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                  :checked="!hiddenSet.has(col.key)"
                  :disabled="!hiddenSet.has(col.key) && shownColumns.length === 1"
                  @change="toggleColumn(col.key, $event.target.checked)"
                />
                <label :for="`col-${columnsKey}-${col.key}`" class="min-w-0 flex-1 cursor-pointer truncate text-gray-800">{{ col.label }}</label>
                <button type="button" class="rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-30" :disabled="idx === 0" :aria-label="`Move ${col.label} up`" @click="moveColumn(idx, -1)">
                  <FeatherIcon name="chevron-up" class="h-4 w-4" />
                </button>
                <button type="button" class="rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-30" :disabled="idx === orderedColumns.length - 1" :aria-label="`Move ${col.label} down`" @click="moveColumn(idx, 1)">
                  <FeatherIcon name="chevron-down" class="h-4 w-4" />
                </button>
              </li>
            </ul>
            <p class="border-t px-3 py-2 text-xs text-gray-500">Saved for your account.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk actions for the selected rows -->
    <div
      v-if="selectable && selectedRows.length"
      class="flex flex-wrap items-center gap-2 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm"
    >
      <span class="font-semibold text-brand-800">{{ selectedRows.length }} selected</span>
      <button
        v-if="selectedRows.length < sortedRows.length"
        class="font-medium text-brand-700 underline-offset-2 hover:underline"
        @click="selectAllMatching"
      >
        Select all {{ sortedRows.length }}{{ isFiltered ? ' matching' : '' }}
      </button>
      <div class="ml-auto flex flex-wrap items-center gap-2">
        <slot name="bulk-actions" :rows="selectedRows" :clear="clearSelection" />
        <Button size="sm" icon-left="download" @click="exportSelected">{{ onExport ? 'Export' : 'Export CSV' }}</Button>
        <Button size="sm" variant="ghost" @click="clearSelection">Clear</Button>
      </div>
    </div>

    <div v-if="loading && !rows.length" class="text-sm text-gray-500">Loading...</div>
    <EmptyState v-else-if="!rows.length" :title="emptyTitle" />
    <div v-else class="overflow-x-auto rounded-lg border bg-white">
      <table class="w-full text-sm">
        <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
          <tr>
            <th v-if="selectable" class="w-10 px-4 py-2" @click.stop>
              <input
                type="checkbox"
                class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                :checked="pageAllSelected"
                :indeterminate.prop="pageSomeSelected && !pageAllSelected"
                aria-label="Select all rows on this page"
                @change="togglePage($event.target.checked)"
              />
            </th>
            <th
              v-for="col in shownColumns"
              :key="col.key"
              class="whitespace-nowrap px-4 py-2 font-medium"
              :class="[col.align === 'right' && 'text-right', col.sortable !== false && 'cursor-pointer select-none hover:text-gray-800']"
              @click="col.sortable !== false && toggleSort(col.key)"
            >
              {{ col.label }}
              <span v-if="sortKey === col.key" class="ml-0.5">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th v-if="$slots.actions" class="px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!sortedRows.length">
            <td :colspan="shownColumns.length + ($slots.actions ? 1 : 0) + (selectable ? 1 : 0)" class="px-4 py-8 text-center text-gray-500">
              No records match your search or filters.
            </td>
          </tr>
          <tr
            v-for="row in pageRows"
            :key="row[rowKey]"
            class="border-b last:border-0"
            :class="[clickable && 'cursor-pointer hover:bg-gray-50', isSelected(row) && 'bg-brand-50/60']"
            @click="clickable && emit('row-click', row)"
          >
            <td v-if="selectable" class="w-10 px-4 py-2.5" @click.stop>
              <input
                type="checkbox"
                class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                :checked="isSelected(row)"
                :aria-label="`Select ${row[rowKey]}`"
                @change="toggleRow(row, $event.target.checked)"
              />
            </td>
            <td
              v-for="(col, i) in shownColumns"
              :key="col.key"
              class="px-4 py-2.5"
              :class="[i === 0 ? 'font-medium text-gray-900' : 'text-gray-600', col.align === 'right' && 'text-right']"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ display(row, col) }}</slot>
            </td>
            <td v-if="$slots.actions" class="px-4 py-2.5 text-right" @click.stop>
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="rows.length" class="flex flex-wrap items-center justify-between gap-2 text-sm text-gray-600">
      <div>
        <template v-if="sortedRows.length">
          Showing {{ pageStart + 1 }}–{{ Math.min(pageStart + pageSize, sortedRows.length) }} of
          {{ sortedRows.length }}
        </template>
        <template v-else>0 records</template>
        <span v-if="sortedRows.length !== rows.length"> (filtered from {{ rows.length }})</span>
      </div>
      <div class="flex items-center gap-2">
        <FormControl
          type="select"
          class="w-28"
          :model-value="pageSize"
          :options="PAGE_SIZES.map((n) => ({ label: `${n} / page`, value: n }))"
          @update:model-value="(v) => (pageSize = Number(v))"
        />
        <Button icon="chevron-left" :disabled="page === 1" @click="page--" />
        <span>Page {{ page }} of {{ pageCount }}</span>
        <Button icon="chevron-right" :disabled="page >= pageCount" @click="page++" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { callMethod } from '@/services/api'
import { Button, FeatherIcon, FormControl, TextInput } from 'frappe-ui'
import EmptyState from '@/components/common/EmptyState.vue'
import MultiSelectFilter from '@/components/common/MultiSelectFilter.vue'

const props = defineProps({
  // [{ key, label, sortable?: true, align?: 'right', format?: (row) => string }]
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  rowKey: { type: String, default: 'name' },
  // [{ key, label, options? }] — options default to the distinct values in rows.
  filters: { type: Array, default: () => [] },
  emptyTitle: { type: String, default: 'No records yet' },
  searchPlaceholder: { type: String, default: 'Search...' },
  clickable: { type: Boolean, default: false },
  // Row checkboxes + bulk action bar (Export CSV always; pages add more
  // through the bulk-actions slot).
  selectable: { type: Boolean, default: true },
  // File name for Export CSV (without .csv).
  exportName: { type: String, default: 'export' },
  // @export="(rows, clear) => ..." replaces the built-in CSV of the visible
  // columns (e.g. Applications exports full records from the server).
  onExport: { type: Function, default: null },
  // Columns available from the Columns menu but hidden until a user adds them.
  extraColumns: { type: Array, default: () => [] },
  // Turns on the Columns menu; preferences are saved per user under this
  // key (defaults to exportName for lists that set one).
  settingsKey: { type: String, default: '' },
})
const emit = defineEmits(['row-click'])

const PAGE_SIZES = [10, 20, 50, 100]

const search = ref('')
const filterValues = reactive({})
const sortKey = ref('')
const sortDir = ref('asc')
const page = ref(1)
const pageSize = ref(20)

function display(row, col) {
  const value = col.format ? col.format(row) : row[col.key]
  return value ?? ''
}

const resolvedFilters = computed(() =>
  props.filters.map((f) => {
    const options = f.options || [...new Set(props.rows.map((r) => r[f.key]).filter((v) => v !== null && v !== undefined && v !== ''))].sort()
    // Values are compared as strings against String(row[key]).
    return { ...f, options: options.map((o) => (typeof o === 'object' ? { ...o, value: String(o.value) } : { label: String(o), value: String(o) })) }
  }),
)

const isFiltered = computed(() => !!search.value || Object.values(filterValues).some((v) => v.length))

function clearFilters() {
  search.value = ''
  Object.keys(filterValues).forEach((k) => (filterValues[k] = []))
}

const filteredRows = computed(() => {
  const term = search.value.trim().toLowerCase()
  return props.rows.filter((row) => {
    for (const [key, values] of Object.entries(filterValues)) {
      if (values.length && !values.includes(String(row[key] ?? ''))) return false
    }
    if (!term) return true
    return allColumns.value.some((col) => String(display(row, col)).toLowerCase().includes(term))
  })
})

function toggleSort(key) {
  if (sortKey.value !== key) {
    sortKey.value = key
    sortDir.value = 'asc'
  } else if (sortDir.value === 'asc') {
    sortDir.value = 'desc'
  } else {
    sortKey.value = ''
  }
}

const sortedRows = computed(() => {
  if (!sortKey.value) return filteredRows.value
  const key = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  // Sort on raw values so dates and numbers order correctly, not their display text.
  return [...filteredRows.value].sort((a, b) => {
    const x = a[key]
    const y = b[key]
    if (x == null || x === '') return 1
    if (y == null || y === '') return -1
    if (typeof x === 'number' && typeof y === 'number') return (x - y) * dir
    return String(x).localeCompare(String(y), undefined, { numeric: true }) * dir
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)))
const pageStart = computed(() => (page.value - 1) * pageSize.value)
const pageRows = computed(() => sortedRows.value.slice(pageStart.value, pageStart.value + pageSize.value))

watch([search, filterValues, pageSize], () => (page.value = 1))

// ----- selection (by rowKey, so it survives sorting, filtering and paging)
const selected = ref(new Set())
const selectedRows = computed(() => props.rows.filter((r) => selected.value.has(r[props.rowKey])))
const pageAllSelected = computed(() => pageRows.value.length > 0 && pageRows.value.every((r) => selected.value.has(r[props.rowKey])))
const pageSomeSelected = computed(() => pageRows.value.some((r) => selected.value.has(r[props.rowKey])))

function isSelected(row) {
  return selected.value.has(row[props.rowKey])
}

function toggleRow(row, on) {
  const next = new Set(selected.value)
  on ? next.add(row[props.rowKey]) : next.delete(row[props.rowKey])
  selected.value = next
}

function togglePage(on) {
  const next = new Set(selected.value)
  for (const row of pageRows.value) on ? next.add(row[props.rowKey]) : next.delete(row[props.rowKey])
  selected.value = next
}

function selectAllMatching() {
  selected.value = new Set(sortedRows.value.map((r) => r[props.rowKey]))
}

function clearSelection() {
  selected.value = new Set()
}

// Rows reloaded (e.g. after a bulk action): drop selections that no longer exist.
watch(
  () => props.rows,
  (rows) => {
    const keys = new Set(rows.map((r) => r[props.rowKey]))
    const kept = [...selected.value].filter((k) => keys.has(k))
    if (kept.length !== selected.value.size) selected.value = new Set(kept)
  },
)

function exportSelected() {
  if (props.onExport) props.onExport(selectedRows.value, clearSelection)
  else exportCsv()
}

function exportCsv() {
  const cell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`
  const lines = [
    shownColumns.value.map((c) => cell(c.label)).join(','),
    ...selectedRows.value.map((row) => shownColumns.value.map((c) => cell(display(row, c))).join(',')),
  ]
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${props.exportName}-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}
watch(pageCount, (n) => {
  if (page.value > n) page.value = n
})

// ----- columns chooser (per user)
const columnsKey = computed(() => props.settingsKey || (props.exportName !== 'export' ? props.exportName : ''))
const allColumns = computed(() => [...props.columns, ...props.extraColumns.filter((e) => !props.columns.some((c) => c.key === e.key))])
const prefs = ref(null) // { order: [...keys], hidden: [...keys] }
const colOpen = ref(false)
const colRoot = ref(null)

const defaultHidden = computed(() => props.extraColumns.map((c) => c.key))
const hiddenSet = computed(() => new Set(prefs.value ? prefs.value.hidden : defaultHidden.value))
const orderedColumns = computed(() => {
  const order = prefs.value?.order || []
  const byKey = Object.fromEntries(allColumns.value.map((c) => [c.key, c]))
  const known = order.filter((k) => byKey[k]).map((k) => byKey[k])
  return [...known, ...allColumns.value.filter((c) => !order.includes(c.key))]
})
const shownColumns = computed(() => {
  if (!columnsKey.value) return props.columns
  const shown = orderedColumns.value.filter((c) => !hiddenSet.value.has(c.key))
  return shown.length ? shown : props.columns
})
const customised = computed(() => !!prefs.value)

let saveTimer = null
function savePrefs() {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    callMethod('pathways.api.preferences.save_list_columns', { list_key: columnsKey.value, settings: prefs.value }).catch(() => {})
  }, 400)
}
function currentPrefs() {
  return { order: orderedColumns.value.map((c) => c.key), hidden: [...hiddenSet.value] }
}
function toggleColumn(key, show) {
  const p = currentPrefs()
  p.hidden = show ? p.hidden.filter((k) => k !== key) : [...p.hidden, key]
  prefs.value = p
  savePrefs()
}
function moveColumn(idx, step) {
  const p = currentPrefs()
  const [moved] = p.order.splice(idx, 1)
  p.order.splice(idx + step, 0, moved)
  prefs.value = p
  savePrefs()
}
function resetColumns() {
  prefs.value = null
  savePrefs()
}

async function loadPrefs() {
  if (!columnsKey.value) return
  try {
    const saved = await callMethod('pathways.api.preferences.get_list_columns', { list_key: columnsKey.value })
    if (saved && Array.isArray(saved.order)) prefs.value = { order: saved.order, hidden: saved.hidden || [] }
  } catch {
    /* defaults */
  }
}
function onOutsideColumns(e) {
  if (colOpen.value && colRoot.value && !colRoot.value.contains(e.target)) colOpen.value = false
}
onMounted(() => {
  loadPrefs()
  document.addEventListener('mousedown', onOutsideColumns)
})
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutsideColumns))
</script>
