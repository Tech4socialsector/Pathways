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

      <!-- Shortlisting sheets (workflow folder "4. Shortlisting") for every job -->
      <div class="min-w-0 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-gray-900">Shortlisting Sheets</h2>
            <p class="mt-0.5 text-sm text-gray-500">
              Each job's sheet in its track's layout: Admin, Research, or Faculty (Eligibility Check and Consolidated scores).
              Follows the Track and Job Opening filters.
            </p>
          </div>
          <Button
            variant="solid"
            icon-left="download"
            :class="BTN_BRAND"
            :loading="exportingSheets"
            :disabled="!sheets.rows.length"
            @click="downloadAllSheets"
          >
            Download all (Excel)
          </Button>
        </div>
        <div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <div v-for="t in sheetTotals" :key="t.label" class="rounded-lg px-3 py-2" :class="t.tone">
            <div class="text-xs">{{ t.label }}</div>
            <div class="text-lg font-bold">{{ t.value }}</div>
          </div>
        </div>
        <DataTable
          export-name="shortlisting-overview"
          :columns="sheetColumns"
          :rows="sheets.rows"
          :loading="sheets.loading"
          row-key="job_opening"
          :selectable="false"
          empty-title="No job openings with applications"
          search-placeholder="Search job openings..."
        >
          <template #cell-job_title="{ row }">
            <router-link :to="`/jobs/${row.job_opening}`" class="font-medium text-gray-900 hover:text-brand-700 hover:underline">{{ row.job_title }}</router-link>
            <div class="text-xs text-gray-500">{{ row.job_code }} · {{ row.department }}</div>
          </template>
          <template #cell-shortlisted="{ row }">
            <span :class="row.shortlisted > row.target ? 'font-semibold text-orange-700' : ''">{{ row.shortlisted }} / {{ row.target }}</span>
          </template>
          <template #cell-committee="{ value }">
            <span v-if="value" class="text-xs">{{ value }}</span>
            <span v-else class="text-xs text-orange-700">Not set up</span>
          </template>
          <template #actions="{ row }">
            <div class="flex justify-end gap-2">
              <Button size="sm" variant="ghost" icon-left="eye" @click="openSheet(row)">View</Button>
              <a :href="scoringService.shortlistingReportUrl(row.job_opening)">
                <Button size="sm" variant="outline" icon-left="download">Excel</Button>
              </a>
            </div>
          </template>
        </DataTable>
      </div>
    </div>

    <ShortlistingSheetDialog
      v-model:open="sheetDialog.open"
      :job-opening="sheetDialog.job"
      :job-title="sheetDialog.title"
      :track="sheetDialog.track"
    />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import ReportChartCard from '@/components/reports/ReportChartCard.vue'
import ShortlistingSheetDialog from '@/components/common/ShortlistingSheetDialog.vue'
import { scoringService } from '@/services/scoring'
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

onMounted(load)


// ----- shortlisting sheets
const sheets = reactive({ rows: [], loading: false })
const sheetColumns = [
  { key: 'job_title', label: 'Job Opening' },
  { key: 'track', label: 'Track' },
  { key: 'applications', label: 'Applied', align: 'right' },
  { key: 'pending', label: 'To check', align: 'right' },
  { key: 'eligible', label: 'Eligible', align: 'right' },
  { key: 'not_eligible', label: 'Not eligible', align: 'right' },
  { key: 'scored', label: 'Decided', align: 'right' },
  { key: 'shortlisted', label: 'Shortlisted / Target' },
  { key: 'committee', label: 'Committee' },
]
const sheetTotals = computed(() => {
  const sum = (k) => sheets.rows.reduce((n, r) => n + (r[k] || 0), 0)
  return [
    { label: 'Jobs', value: sheets.rows.length, tone: 'bg-gray-50 text-gray-900' },
    { label: 'Applications', value: sum('applications'), tone: 'bg-gray-50 text-gray-900' },
    { label: 'To check', value: sum('pending'), tone: 'bg-orange-50 text-orange-900' },
    { label: 'Eligible', value: sum('eligible'), tone: 'bg-green-50 text-green-900' },
    { label: 'Not eligible', value: sum('not_eligible'), tone: 'bg-red-50 text-red-900' },
    { label: 'Shortlisted', value: sum('shortlisted'), tone: 'bg-brand-50 text-brand-900' },
  ]
})

async function loadSheets() {
  sheets.loading = true
  try {
    const p = params()
    sheets.rows = await reportService.listShortlistingSheets({ track: p.track, job_opening: p.job_opening })
  } catch {
    sheets.rows = []
  } finally {
    sheets.loading = false
  }
}

const sheetDialog = reactive({ open: false, job: '', title: '', track: '' })
function openSheet(row) {
  Object.assign(sheetDialog, { open: true, job: row.job_opening, title: row.job_title, track: row.track })
}

const exportingSheets = ref(false)
async function downloadAllSheets() {
  exportingSheets.value = true
  try {
    const p = params()
    await reportService.downloadAllShortlistingSheets({ track: p.track, job_opening: p.job_opening })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the sheets.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    exportingSheets.value = false
  }
}

watch(() => [filters.track, filters.job_opening], loadSheets)
onMounted(loadSheets)
</script>
