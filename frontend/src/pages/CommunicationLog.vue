<template>
  <StaffLayout>
    <PageHeader title="Communications" subtitle="Every recruitment email Pathways has sent, with what it said." />

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto bg-gray-50 p-3 sm:p-6">
      <!-- Filters: chosen here, applied with Search (filtered on the server) -->
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <FormControl label="Email" type="select" v-model="filters.event" :options="eventOptions" />
          <FormControl label="Job opening" type="select" v-model="filters.job_opening" :options="jobOptions" />
          <FormControl label="Application ID" v-model="filters.application" placeholder="e.g. PWY-APP-2026-00012" />
          <FormControl label="Status" type="select" v-model="filters.status" :options="STATUS_OPTIONS" />
          <FormControl label="Recipient" v-model="filters.recipient" placeholder="Name or email contains..." />
          <FormControl label="Sent from" type="date" v-model="filters.from_date" :max="filters.to_date || undefined" />
          <FormControl label="Sent to" type="date" v-model="filters.to_date" :min="filters.from_date || undefined" />
          <div class="flex items-end gap-2">
            <Button variant="solid" icon-left="search" class="flex-1" :class="BTN_BRAND" :loading="loading" @click="search">Search</Button>
            <Button v-if="activeCount" variant="ghost" icon-left="x" @click="clear">Clear</Button>
          </div>
        </div>
        <div class="mt-3 border-t pt-3 text-sm text-gray-600">
          <template v-if="result">
            <span class="font-semibold text-gray-900">{{ result.total }}</span> email{{ result.total === 1 ? '' : 's' }}
            <template v-if="result.total > rows.length"> · showing the latest {{ rows.length }}</template>
          </template>
        </div>
      </div>

      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</div>

      <DataTable
        export-name="communications"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :selectable="false"
        :advanced-filter="false"
        clickable
        empty-title="No emails match these filters"
        search-placeholder="Search within these results..."
        @row-click="(row) => openEmail(row.name)"
      >
        <template #cell-event_label="{ row }">
          <div class="font-medium text-gray-900">{{ row.event_label }}</div>
          <div class="text-xs text-gray-500">{{ row.email_template }}</div>
        </template>
        <template #cell-context="{ row }">
          <div v-if="row.candidate_name || row.application_id" class="text-gray-900">{{ row.candidate_name || row.application_id }}</div>
          <div v-if="row.job_title" class="text-xs text-gray-500">{{ row.job_title }}</div>
          <div v-if="!row.job_title && !row.application" class="text-xs text-gray-500">{{ row.reference_doctype }} {{ row.reference_name }}</div>
        </template>
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      </DataTable>
      <div v-if="result && result.total > rows.length" class="flex justify-center">
        <Button variant="outline" :loading="loadingMore" @click="loadMore">Load {{ Math.min(PAGE, result.total - rows.length) }} more</Button>
      </div>
    </div>

    <EmailDrawer v-model:open="drawer.open" :name="drawer.name" />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Button, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmailDrawer from '@/components/common/EmailDrawer.vue'
import { communicationService } from '@/services/communications'
import { BTN_BRAND } from '@/utils/buttonStyles'

const PAGE = 200
const STATUS_OPTIONS = [
  { label: 'Any status', value: '' },
  { label: 'Sent', value: 'Sent' },
  { label: 'Failed', value: 'Failed' },
]
const emptyFilters = () => ({ event: '', job_opening: '', application: '', status: '', recipient: '', from_date: '', to_date: '' })

const route = useRoute()
const filters = reactive({ ...emptyFilters(), job_opening: route.query.job || '', application: route.query.application || '' })
const activeCount = computed(() => Object.values(filters).filter(Boolean).length)

const options = ref({ events: [], jobs: [] })
const eventOptions = computed(() => [{ label: 'Any email', value: '' }, ...options.value.events.map((e) => ({ label: e.label, value: e.value }))])
const jobOptions = computed(() => [{ label: 'Any job', value: '' }, ...options.value.jobs.map((j) => ({ label: j.label || j.value, value: j.value }))])

const columns = [
  { key: 'sent_on', label: 'Sent', format: (row) => (row.sent_on ? dayjs(row.sent_on).format('DD MMM YYYY, h:mm A') : '') },
  { key: 'event_label', label: 'Email' },
  { key: 'recipient', label: 'To' },
  { key: 'context', label: 'About', sortable: false, format: (row) => [row.candidate_name, row.job_title].filter(Boolean).join(' · ') },
  { key: 'status', label: 'Status' },
]

const result = ref(null)
const rows = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
let applied = {}

async function search() {
  applied = JSON.parse(JSON.stringify(filters))
  loading.value = true
  error.value = ''
  try {
    result.value = await communicationService.list(applied, 0, PAGE)
    rows.value = result.value.rows
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load the emails.'
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  try {
    const more = await communicationService.list(applied, rows.value.length, PAGE)
    rows.value = [...rows.value, ...more.rows]
    result.value = { ...result.value, total: more.total }
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load more emails.'
  } finally {
    loadingMore.value = false
  }
}

function clear() {
  Object.assign(filters, emptyFilters())
  search()
}

const drawer = reactive({ open: false, name: '' })
function openEmail(name) {
  Object.assign(drawer, { open: true, name })
}

onMounted(async () => {
  search()
  try {
    options.value = await communicationService.getFilterOptions()
  } catch {
    // filters still work without the dropdown options
  }
})
</script>
