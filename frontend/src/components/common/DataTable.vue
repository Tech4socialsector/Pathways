<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-end gap-2">
      <div class="w-full sm:w-64">
        <TextInput v-model="search" type="text" :placeholder="searchPlaceholder">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
        </TextInput>
      </div>
      <div v-for="filter in resolvedFilters" :key="filter.key" class="w-full sm:w-44">
        <!-- frappe-ui's select cannot hold '' as an option value (it shows the
             placeholder instead), so "All" uses a sentinel. -->
        <FormControl
          type="select"
          :model-value="filterValues[filter.key] || ALL"
          :options="[{ label: `All ${filter.label}`, value: ALL }, ...filter.options]"
          @update:model-value="(v) => (filterValues[filter.key] = v === ALL ? '' : v)"
        />
      </div>
      <Button v-if="isFiltered" variant="ghost" @click="clearFilters">Clear</Button>
      <div class="ml-auto flex items-center gap-2">
        <slot name="toolbar" />
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
        <Button size="sm" icon-left="download" @click="exportCsv">Export CSV</Button>
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
              v-for="col in columns"
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
            <td :colspan="columns.length + ($slots.actions ? 1 : 0) + (selectable ? 1 : 0)" class="px-4 py-8 text-center text-gray-500">
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
              v-for="(col, i) in columns"
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
import { computed, reactive, ref, watch } from 'vue'
import { Button, FeatherIcon, FormControl, TextInput } from 'frappe-ui'
import EmptyState from '@/components/common/EmptyState.vue'

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
})
const emit = defineEmits(['row-click'])

const PAGE_SIZES = [10, 20, 50, 100]
const ALL = '__all__'

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
    return { ...f, options: options.map((o) => (typeof o === 'object' ? o : { label: String(o), value: String(o) })) }
  }),
)

const isFiltered = computed(() => !!search.value || Object.values(filterValues).some(Boolean))

function clearFilters() {
  search.value = ''
  Object.keys(filterValues).forEach((k) => (filterValues[k] = ''))
}

const filteredRows = computed(() => {
  const term = search.value.trim().toLowerCase()
  return props.rows.filter((row) => {
    for (const [key, value] of Object.entries(filterValues)) {
      if (value && String(row[key] ?? '') !== value) return false
    }
    if (!term) return true
    return props.columns.some((col) => String(display(row, col)).toLowerCase().includes(term))
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

function exportCsv() {
  const cell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`
  const lines = [
    props.columns.map((c) => cell(c.label)).join(','),
    ...selectedRows.value.map((row) => props.columns.map((c) => cell(display(row, c))).join(',')),
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
</script>
