<template>
  <StaffLayout>
    <PageHeader title="Reports" subtitle="Recruitment at a glance. Filters apply to every chart and to the export.">
      <template #actions>
        <Button
          variant="solid"
          icon-left="download"
          :class="BTN_BRAND"
          :loading="exporting"
          :disabled="!!dateError || !charts.data"
          @click="exportReport"
        >
          Export Report
        </Button>
      </template>
    </PageHeader>

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto bg-gray-50 p-3 sm:p-6">
      <!-- Filters: one row above the charts -->
      <div class="flex flex-wrap items-end gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3">
        <div class="w-full sm:w-44">
          <FormControl
            label="Track"
            type="select"
            :model-value="filters.track || ALL"
            :options="[{ label: 'All tracks', value: ALL }, ...trackOptions]"
            @update:model-value="(v) => (filters.track = v === ALL ? '' : v)"
          />
        </div>
        <div class="w-full sm:w-72">
          <FormControl
            label="Job Opening"
            type="select"
            :model-value="filters.job_opening || ALL"
            :options="[{ label: 'All job openings', value: ALL }, ...jobOptions]"
            @update:model-value="(v) => (filters.job_opening = v === ALL ? '' : v)"
          />
        </div>
        <div class="w-full sm:w-40">
          <FormControl label="Applied From" type="date" v-model="filters.from_date" :max="filters.to_date || undefined" />
        </div>
        <div class="w-full sm:w-40">
          <FormControl label="Applied To" type="date" v-model="filters.to_date" :min="filters.from_date || undefined" />
        </div>
        <Button v-if="isFiltered" variant="ghost" @click="clearFilters">Clear</Button>
        <div class="ml-auto text-sm text-gray-600">
          <span v-if="dateError" class="text-red-600">{{ dateError }}</span>
          <template v-else-if="charts.data">
            <span class="font-semibold text-gray-900">{{ charts.data.total }}</span>
            application{{ charts.data.total === 1 ? '' : 's' }}
          </template>
        </div>
      </div>

      <div v-if="charts.error" class="flex items-center justify-between rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ charts.error }}
        <Button size="sm" @click="load">Try again</Button>
      </div>
      <div v-else-if="!charts.data" class="py-16 text-center text-sm text-gray-500">Loading charts...</div>
      <div v-else class="grid grid-cols-1 gap-4 transition-opacity xl:grid-cols-2" :class="charts.loading && 'opacity-60'">
        <ReportChartCard
          v-for="chart in charts.data.charts"
          :key="chart.key"
          :chart="chart"
          :class="FULL_WIDTH.has(chart.key) && 'xl:col-span-2'"
        />
      </div>

      <div class="min-w-0 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
        <h2 class="text-base font-semibold text-gray-900">Recruitment Pipeline</h2>
        <p class="mb-3 mt-0.5 text-sm text-gray-500">Each job opening's progress. Follows the Track and Job Opening filters.</p>
        <DataTable
          export-name="recruitment-pipeline"
          :columns="columns"
          :rows="pipelineRows"
          :loading="report.loading"
          row-key="job_opening"
          clickable
          empty-title="No job openings to report on"
          search-placeholder="Search job openings..."
          @row-click="(row) => $router.push(`/jobs/${row.job_opening}`)"
        />
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, createResource } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import ReportChartCard from '@/components/reports/ReportChartCard.vue'
import { reportService } from '@/services/reports'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

// Charts that need the whole row: time on a wide axis, long job titles.
const FULL_WIDTH = new Set(['timeline', 'job_opening'])

// frappe-ui's select cannot hold '' as an option value, so "All" uses a sentinel.
const ALL = '__all__'

const filters = reactive({ track: '', job_opening: '', from_date: '', to_date: '' })
const isFiltered = computed(() => Object.values(filters).some(Boolean))

function clearFilters() {
  Object.assign(filters, { track: '', job_opening: '', from_date: '', to_date: '' })
}

const dateError = computed(() =>
  filters.from_date && filters.to_date && filters.from_date > filters.to_date ? 'From date is after To date.' : '',
)

function params() {
  return Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
}

// ----- charts (latest request wins, so fast filter changes never show stale data)
const charts = reactive({ data: null, loading: false, error: '' })
let requestId = 0

async function load() {
  if (dateError.value) return
  const id = ++requestId
  charts.loading = true
  charts.error = ''
  try {
    const data = await reportService.getReportCharts(params())
    if (id === requestId) charts.data = data
  } catch (e) {
    if (id === requestId) charts.error = e?.messages?.[0] || 'Could not load the charts.'
  } finally {
    if (id === requestId) charts.loading = false
  }
}

const trackOptions = computed(() => (charts.data?.options.tracks || []).map((t) => ({ label: t, value: t })))
const jobOptions = computed(() =>
  (charts.data?.options.jobs || []).filter((j) => !filters.track || j.track === filters.track),
)

// A job from another track cannot match: drop it when the track changes.
watch(
  () => filters.track,
  () => {
    if (filters.job_opening && !jobOptions.value.some((j) => j.value === filters.job_opening)) filters.job_opening = ''
  },
)
watch(filters, load)

// ----- export
const exporting = ref(false)

async function exportReport() {
  exporting.value = true
  try {
    await reportService.exportReport(params())
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'The export failed.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    exporting.value = false
  }
}

// ----- pipeline table
const report = createResource({
  url: 'frappe.desk.query_report.run',
  params: { report_name: 'Recruitment Pipeline' },
  transform: (data) => data?.result || [],
})

const pipelineRows = computed(() =>
  (report.data || []).filter(
    (row) =>
      row.job_opening &&
      (!filters.track || row.track === filters.track) &&
      (!filters.job_opening || row.job_opening === filters.job_opening),
  ),
)

const columns = [
  { key: 'job_title', label: 'Job Opening', format: (row) => row.job_title || row.job_opening },
  { key: 'track', label: 'Track' },
  { key: 'applied', label: 'Applied', align: 'right' },
  { key: 'eligible', label: 'Eligible', align: 'right' },
  { key: 'shortlisted', label: 'Shortlisted', align: 'right' },
  { key: 'interviewed', label: 'Interviewed', align: 'right' },
  { key: 'selected', label: 'Selected', align: 'right' },
  { key: 'offered', label: 'Offered', align: 'right' },
  { key: 'joined', label: 'Joined', align: 'right' },
]

onMounted(() => {
  load()
  report.fetch()
})
</script>
