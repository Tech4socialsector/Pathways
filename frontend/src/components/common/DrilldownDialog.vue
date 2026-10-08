<template>
  <Dialog :model-value="open" :options="{ size: '7xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body>
      <div class="flex h-[85vh] flex-col">
        <header class="flex shrink-0 items-start justify-between gap-3 bg-brand-700 px-6 py-4 text-white">
          <div class="min-w-0">
            <h2 class="truncate text-lg font-bold">{{ title }}</h2>
            <p class="text-sm text-white/80">
              {{ loading ? 'Loading...' : `${rows.length} application${rows.length === 1 ? '' : 's'}` }}
              <template v-if="description"> · {{ description }}</template>
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
          <button
            v-if="jobLink"
            type="button"
            class="flex items-center gap-1.5 rounded-md bg-white/15 px-3 py-1.5 text-sm font-medium text-white hover:bg-white/25"
            @click="openJob"
          >
            <FeatherIcon name="briefcase" class="h-4 w-4" />Open job opening
          </button>
          <button class="rounded-md p-1.5 text-white/80 hover:bg-white/15 hover:text-white" aria-label="Close" @click="emit('update:open', false)">
            <FeatherIcon name="x" class="h-5 w-5" />
          </button>
          </div>
        </header>

        <div class="min-h-0 flex-1 overflow-y-auto bg-gray-50 p-6">
          <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
          <DataTable
            v-else
            :columns="columns"
            :rows="rows"
            :loading="loading"
            :filters="filters"
            :selectable="false"
            empty-title="No applications here yet"
            search-placeholder="Search candidate, job or application ID..."
          >
            <template #actions="{ row }">
              <Button size="sm" variant="outline" icon-left="eye" @click="go(row)">View</Button>
            </template>
            <template #cell-candidate_name="{ row }">
              <div class="flex items-center gap-3">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                  {{ initials(row.candidate_name) }}
                </span>
                <span class="font-semibold text-gray-900">{{ row.candidate_name }}</span>
              </div>
            </template>
            <template #cell-application_id="{ row }">
              <span class="font-mono text-xs text-gray-700">{{ row.application_id }}</span>
            </template>
            <template #cell-status="{ row }">
              <StatusBadge :status="row.status" />
            </template>
            <template #cell-detail="{ row }">
              <span class="text-brand-700">{{ row.detail }}</span>
            </template>
          </DataTable>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StatusBadge from './StatusBadge.vue'
import DataTable from './DataTable.vue'
import { reportService } from '@/services/reports'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  // pathways.api.dashboard.get_drilldown bucket
  bucket: { type: String, default: '' },
  // Dashboard filters (track, department, job_opening, from_date, to_date).
  filters: { type: Object, default: () => ({}) },
  // A job's drilldown: a header button to open the job page.
  jobLink: { type: String, default: '' },
})
const emit = defineEmits(['update:open'])
const router = useRouter()

const rows = ref([])
const loading = ref(false)
const error = ref('')

watch(
  () => [props.open, props.bucket],
  async ([open, bucket]) => {
    if (!open || !bucket) return
    loading.value = true
    error.value = ''
    rows.value = []
    try {
      rows.value = (await reportService.getDrilldown(bucket, props.filters)) || []
    } catch (e) {
      error.value = e?.messages?.[0] || 'Could not load the applications.'
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const columns = computed(() => [
  { key: 'candidate_name', label: 'Candidate' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'application_id', label: 'Application ID' },
  { key: 'status', label: 'Status' },
  { key: 'application_date', label: 'Applied On', format: (row) => (row.application_date ? formatDate(row.application_date) : '') },
  // Needs Attention lists say why each application is there.
  ...(rows.value.some((r) => r.detail) ? [{ key: 'detail', label: 'Reason', sortable: false }] : []),
])

const filters = [
  { key: 'job_title', label: 'Job Openings' },
  { key: 'status', label: 'Statuses' },
]

function openJob() {
  emit('update:open', false)
  router.push(props.jobLink)
}

function go(row) {
  emit('update:open', false)
  router.push(`/applications/${row.name}`)
}

function initials(name) {
  return (name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}

function formatDate(value) {
  return dayjs(value).format('DD MMM YYYY')
}
</script>
