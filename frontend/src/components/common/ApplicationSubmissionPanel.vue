<template>
  <div>
    <div v-if="loading && !app" class="rounded-xl border bg-white p-5 text-sm text-gray-500 shadow-sm">Loading application...</div>
    <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
    <section v-else-if="app" class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <!-- Tabs: the Application DocType's own tabs, as in Desk -->
      <!-- Scrolls sideways on narrow screens without showing a scrollbar. -->
      <nav
        class="flex overflow-x-auto border-b border-gray-200 bg-gray-50/60 px-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        role="tablist"
        aria-label="Application sections"
      >
        <button
          v-for="t in tabs"
          :key="t.key"
          role="tab"
          :aria-selected="tab === t.key"
          class="relative flex shrink-0 items-center gap-1.5 whitespace-nowrap px-3 py-3 text-sm transition-colors"
          :class="tab === t.key ? 'font-semibold text-brand-700' : 'text-gray-600 hover:text-gray-900'"
          @click="selectTab(t.key)"
        >
          {{ t.label }}
          <span
            v-if="t.count != null"
            class="rounded-full px-1.5 text-xs"
            :class="tab === t.key ? 'bg-brand-100 text-brand-700' : 'bg-gray-100 text-gray-600'"
          >{{ t.count }}</span>
          <span v-if="tab === t.key" class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-700" />
        </button>
      </nav>

      <div v-if="currentTab" class="flex flex-col divide-y divide-gray-100" role="tabpanel">
        <div v-for="(section, sIdx) in currentTab.sections" :key="sIdx" class="p-5">
          <h3 v-if="section.label" class="mb-4 text-xs font-bold uppercase tracking-wide text-brand-700">{{ section.label }}</h3>
          <div class="grid grid-cols-1 gap-x-8 gap-y-4" :class="section.columns.length > 1 && 'md:grid-cols-2'">
            <div v-for="(column, cIdx) in section.columns" :key="cIdx" class="flex min-w-0 flex-col gap-4">
              <template v-for="field in column" :key="field.fieldname">
                <!-- Child table: one card per row, every field shown -->
                <div v-if="field.fieldtype === 'Table'" class="min-w-0">
                  <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
                    {{ field.label }}
                    <span class="rounded-full bg-gray-100 px-1.5 text-xs font-normal text-gray-600">{{ rowsOf(field).length }}</span>
                  </div>
                  <div class="flex flex-col gap-3">
                    <article
                      v-for="(row, rIdx) in rowsOrPlaceholder(field)"
                      :key="row.name || rIdx"
                      class="rounded-lg border p-4"
                      :class="row.__placeholder ? 'border-dashed border-gray-300 bg-gray-50/60' : 'border-gray-200'"
                    >
                      <header class="mb-3 flex items-center gap-2.5">
                        <span
                          class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                          :class="row.__placeholder ? 'bg-gray-200 text-gray-500' : 'bg-brand-700 text-white'"
                        >{{ row.__placeholder ? '–' : rIdx + 1 }}</span>
                        <span class="min-w-0 truncate font-semibold" :class="row.__placeholder ? 'text-gray-400' : 'text-gray-900'">
                          {{ row.__placeholder ? 'Nothing provided' : rowTitle(field, row) }}
                        </span>
                      </header>
                      <dl class="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2 xl:grid-cols-3">
                        <div
                          v-for="col in field.columns"
                          :key="col.fieldname"
                          class="min-w-0"
                          :class="LONG_TEXT.includes(col.fieldtype) && 'sm:col-span-2 xl:col-span-3'"
                        >
                          <dt class="text-xs text-gray-500">{{ col.label }}</dt>
                          <dd class="mt-0.5 break-words text-sm font-medium text-gray-900">
                            <FieldValue :field="col" :value="row[col.fieldname]" />
                          </dd>
                        </div>
                      </dl>
                    </article>
                  </div>
                </div>

                <!-- Plain field -->
                <div v-else class="min-w-0">
                  <div class="text-xs text-gray-500">{{ field.label }}</div>
                  <div class="mt-0.5 min-h-[1.25rem] text-sm font-medium text-gray-900">
                    <FieldValue :field="field" :value="valueOf(field)" />
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, h, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  // pathways.api.application.get_application_detail, loaded by the page:
  // the document, candidate_details, and its form layout.
  app: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const LONG_TEXT = ['Small Text', 'Text', 'Long Text', 'Text Editor']

// The Details tab starts with the candidate's own fields (they live on the
// Candidate record, not the Application).
const tabs = computed(() => {
  const app = props.app
  if (!app?.layout) return []
  return app.layout.map((t, idx) => {
    const sections = [...t.sections]
    if (idx === 0 && app.candidate_fields?.length) {
      sections.unshift({
        label: 'Candidate',
        columns: splitInTwo(app.candidate_fields.map((f) => ({ ...f, source: 'candidate' }))),
      })
    }
    const fields = sections.flatMap((s) => s.columns.flat())
    const only = fields.length === 1 && fields[0].fieldtype === 'Table' ? fields[0] : null
    return { ...t, sections, count: only ? (app[only.fieldname] || []).length : null }
  })
})

function splitInTwo(fields) {
  const half = Math.ceil(fields.length / 2)
  return [fields.slice(0, half), fields.slice(half)].filter((c) => c.length)
}

function valueOf(field) {
  return field.source === 'candidate' ? props.app.candidate_details?.[field.fieldname] : props.app[field.fieldname]
}

function rowsOf(field) {
  return props.app[field.fieldname] || []
}

// An empty table still shows its fields, blank, in one placeholder card.
function rowsOrPlaceholder(field) {
  const rows = rowsOf(field)
  return rows.length ? rows : [{ __placeholder: true }]
}

// Card heading: the row's first filled text value (degree, designation, referee...).
function rowTitle(field, row) {
  const col = field.columns.find((c) => !['Attach', 'Attach Image', 'Check'].includes(c.fieldtype) && row[c.fieldname])
  return col ? String(row[col.fieldname]) : `Row ${row.idx || ''}`
}

// The open tab lives in the URL hash (as in Desk), so reloads and shared
// links keep it.
const route = useRoute()
const router = useRouter()
const tab = ref('details')
const currentTab = computed(() => tabs.value.find((t) => t.key === tab.value) || tabs.value[0])

watch(
  [() => route.hash, tabs],
  ([hash]) => {
    const key = (hash || '').replace('#', '')
    tab.value = tabs.value.some((t) => t.key === key) ? key : tabs.value[0]?.key || 'details'
  },
  { immediate: true },
)

function selectTab(key) {
  tab.value = key
  router.replace({ hash: key === tabs.value[0]?.key ? '' : `#${key}` })
}

// ----- one value, formatted by field type; empty shows a dash
function isEmpty(value) {
  return value === null || value === undefined || value === ''
}

function fileName(url) {
  return decodeURIComponent(String(url).split('/').pop())
}

const FieldValue = (p) => {
  const { field, value } = p
  if (field.fieldtype === 'Check') {
    return h('span', { class: value ? 'text-green-700' : 'text-gray-500' }, value ? 'Yes' : 'No')
  }
  if (isEmpty(value)) return h('span', { class: 'font-normal text-gray-300' }, '—')

  switch (field.fieldtype) {
    case 'Attach':
    case 'Attach Image':
      return h(
        'a',
        {
          href: value,
          target: '_blank',
          rel: 'noopener',
          title: fileName(value),
          class:
            'inline-flex max-w-full items-center gap-1.5 rounded-md border border-gray-200 bg-white px-2 py-0.5 text-xs font-medium text-gray-700 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700',
        },
        [h(FeatherIcon, { name: 'file-text', class: 'h-3.5 w-3.5 shrink-0' }), h('span', { class: 'truncate' }, fileName(value))],
      )
    case 'Date':
      return dayjs(value).format('DD MMM YYYY')
    case 'Datetime':
      return dayjs(value).format('DD MMM YYYY, h:mm A')
    case 'Currency':
      return `₹ ${Number(value).toLocaleString('en-IN')}`
    default:
      if (LONG_TEXT.includes(field.fieldtype)) return h('span', { class: 'whitespace-pre-line font-normal' }, String(value))
      return String(value)
  }
}
FieldValue.props = ['field', 'value']
</script>
