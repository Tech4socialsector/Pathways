<template>
  <StaffLayout>
    <PageHeader title="Reports" subtitle="Recruitment at a glance. Filters apply to every chart, the shortlisting sheets and the export.">
      <template #actions>
        <Button variant="solid" icon-left="download" :class="BTN_BRAND" :disabled="!charts.data" @click="openExport">
          Export Report
        </Button>
      </template>
    </PageHeader>

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto bg-gray-50 p-3 sm:p-6">
      <!-- Filters: chosen here, applied with Search -->
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MultiSelectFilter label="Position" :options="positionOptions" v-model="filters.positions" all-label="All positions" />
          <MultiSelectFilter label="Track" :options="options.tracks || []" v-model="filters.tracks" all-label="All tracks" />
          <MultiSelectFilter label="Department" :options="options.departments || []" v-model="filters.departments" all-label="All departments" />
          <MultiSelectFilter label="Employment type" :options="options.employment_types || []" v-model="filters.employment_types" all-label="All types" />
          <MultiSelectFilter label="Job opening" :options="jobOptions" v-model="filters.job_openings" all-label="All job openings" />
          <MultiSelectFilter label="Application status" :options="options.statuses || []" v-model="filters.statuses" all-label="All statuses" />
          <MultiSelectFilter label="Eligibility" :options="options.eligibility || []" v-model="filters.eligibility" all-label="Any eligibility" />
          <div class="grid grid-cols-2 gap-2">
            <FormControl label="Applied from" type="date" v-model="filters.from_date" :max="filters.to_date || undefined" />
            <FormControl label="Applied to" type="date" v-model="filters.to_date" :min="filters.from_date || undefined" />
          </div>
        </div>
        <div class="mt-3 flex flex-wrap items-center justify-between gap-3 border-t pt-3">
          <div class="text-sm text-gray-600">
            <span v-if="dateError" class="text-red-600">{{ dateError }}</span>
            <span v-else-if="dirty" class="font-medium text-orange-700">Changes not applied yet. Click Search.</span>
            <template v-else-if="charts.data">
              <span class="font-semibold text-gray-900">{{ charts.data.total }}</span>
              application{{ charts.data.total === 1 ? '' : 's' }}<template v-if="activeCount"> · {{ activeCount }} filter{{ activeCount === 1 ? '' : 's' }} applied</template>
            </template>
          </div>
          <div class="flex gap-2">
            <Button v-if="activeCount || dirty" variant="ghost" icon-left="x" @click="clearFilters">Clear all</Button>
            <Button variant="solid" icon-left="search" :class="BTN_BRAND" :disabled="!!dateError" :loading="charts.loading" @click="applyFilters">Search</Button>
          </div>
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
              Follows the filters above.
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

    <!-- Export: what to include, and how to lay it out -->
    <Dialog v-model="exportDialog.open" :options="{ title: 'Export report', size: 'xl' }">
      <template #body-content>
        <div class="flex flex-col gap-5 text-sm">
          <section>
            <div class="mb-2 font-semibold text-gray-900">What to export</div>
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <label v-for="opt in SCOPES" :key="opt.value" class="flex cursor-pointer gap-3 rounded-lg border p-3" :class="exportDialog.scope === opt.value ? 'border-brand-700 bg-brand-50' : 'hover:bg-gray-50'">
                <input v-model="exportDialog.scope" type="radio" :value="opt.value" class="mt-0.5 text-brand-700 focus:ring-brand-700" />
                <span><span class="block font-medium text-gray-900">{{ opt.label }}</span><span class="text-xs text-gray-500">{{ opt.hint }}</span></span>
              </label>
            </div>
            <div v-if="exportDialog.scope === 'positions'" class="mt-3">
              <div class="mb-1.5 flex items-center justify-between text-xs">
                <span class="text-gray-600">Positions to export ({{ exportDialog.positions.length }} chosen)</span>
                <span class="flex gap-3">
                  <button type="button" class="font-medium text-brand-700 hover:underline" @click="exportDialog.positions = positionOptions.map((p) => p.value)">Select all</button>
                  <button type="button" class="font-medium text-gray-600 hover:underline" @click="exportDialog.positions = []">Clear</button>
                </span>
              </div>
              <div class="grid max-h-56 grid-cols-1 gap-1 overflow-y-auto rounded-lg border p-2 sm:grid-cols-2">
                <label v-for="p in positionOptions" :key="p.value" class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-gray-50">
                  <input v-model="exportDialog.positions" type="checkbox" :value="p.value" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
                  <span class="min-w-0 truncate" :title="p.label">{{ p.label }}</span>
                </label>
              </div>
              <p v-if="!exportDialog.positions.length" class="mt-1 text-xs text-orange-700">Choose at least one position.</p>
            </div>
          </section>
          <section>
            <div class="mb-2 font-semibold text-gray-900">Layout</div>
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <label v-for="opt in LAYOUTS" :key="opt.value" class="flex cursor-pointer gap-3 rounded-lg border p-3" :class="exportDialog.layout === opt.value ? 'border-brand-700 bg-brand-50' : 'hover:bg-gray-50'">
                <input v-model="exportDialog.layout" type="radio" :value="opt.value" class="mt-0.5 text-brand-700 focus:ring-brand-700" />
                <span><span class="block font-medium text-gray-900">{{ opt.label }}</span><span class="text-xs text-gray-500">{{ opt.hint }}</span></span>
              </label>
            </div>
          </section>
          <label class="flex items-center gap-2.5">
            <input v-model="exportDialog.includeCharts" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            Include the summary, the charts and the pipeline by job
          </label>
          <p class="rounded-md bg-gray-50 px-3 py-2 text-xs text-gray-600">
            Uses the filters above<template v-if="activeCount"> ({{ activeCount }} applied)</template>. Each application sheet has every field of the application form.
          </p>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="exportDialog.open = false">Cancel</Button>
          <Button
            variant="solid"
            icon-left="download"
            :class="BTN_BRAND"
            :loading="exporting"
            :disabled="exportDialog.scope === 'positions' && !exportDialog.positions.length"
            @click="exportReport"
          >
            Download Excel
          </Button>
        </div>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, Dialog, FormControl } from 'frappe-ui'
import MultiSelectFilter from '@/components/common/MultiSelectFilter.vue'
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
const FULL_WIDTH = new Set(['timeline', 'position'])

const LIST_KEYS = ['positions', 'tracks', 'departments', 'employment_types', 'job_openings', 'statuses', 'eligibility']
const emptyFilters = () => ({ ...Object.fromEntries(LIST_KEYS.map((k) => [k, []])), from_date: '', to_date: '' })

// `filters` is being edited; `applied` is what the page shows.
const filters = reactive(emptyFilters())
const applied = reactive(emptyFilters())
const dirty = computed(() => JSON.stringify(filters) !== JSON.stringify(applied))
const activeCount = computed(() => LIST_KEYS.filter((k) => applied[k].length).length + (applied.from_date || applied.to_date ? 1 : 0))

const dateError = computed(() =>
  filters.from_date && filters.to_date && filters.from_date > filters.to_date ? 'From date is after To date.' : '',
)

function applyFilters() {
  if (dateError.value) return
  Object.assign(applied, JSON.parse(JSON.stringify(filters)))
  load()
  loadSheets()
}
function clearFilters() {
  Object.assign(filters, emptyFilters())
  applyFilters()
}
const apiFilters = () => JSON.parse(JSON.stringify(applied))

// ----- charts (latest request wins)
const charts = reactive({ data: null, loading: false, error: '' })
let requestId = 0

async function load() {
  const id = ++requestId
  charts.loading = true
  charts.error = ''
  try {
    const data = await reportService.getReportCharts({ filters: apiFilters() })
    if (id === requestId) charts.data = data
  } catch (e) {
    if (id === requestId) charts.error = e?.messages?.[0] || 'Could not load the charts.'
  } finally {
    if (id === requestId) charts.loading = false
  }
}

const options = computed(() => charts.data?.options || {})
const positionOptions = computed(() => options.value.positions || [])
// Job openings narrowed to the other chosen filters.
const jobOptions = computed(() =>
  (options.value.jobs || [])
    .filter(
      (j) =>
        (!filters.positions.length || filters.positions.includes(j.position)) &&
        (!filters.tracks.length || filters.tracks.includes(j.track)) &&
        (!filters.departments.length || filters.departments.includes(j.department)) &&
        (!filters.employment_types.length || filters.employment_types.includes(j.employment_type)),
    )
    .map((j) => ({ value: j.value, label: j.label })),
)

// ----- export
const SCOPES = [
  { value: 'all', label: 'All data', hint: 'Everything that matches the filters.' },
  { value: 'positions', label: 'Specific positions', hint: 'Only the positions you choose.' },
]
const LAYOUTS = [
  { value: 'single', label: 'One sheet', hint: 'All applications together on one sheet.' },
  { value: 'position_wise', label: 'A sheet per position', hint: 'Each position on its own sheet in the same Excel file.' },
]
const exportDialog = reactive({ open: false, scope: 'all', positions: [], layout: 'single', includeCharts: true })
const exporting = ref(false)

function openExport() {
  Object.assign(exportDialog, { open: true, positions: [...applied.positions], scope: applied.positions.length ? 'positions' : 'all' })
}

async function exportReport() {
  exporting.value = true
  try {
    await reportService.exportReport({
      filters: apiFilters(),
      scope: exportDialog.scope,
      positions: exportDialog.positions,
      layout: exportDialog.layout,
      include_charts: exportDialog.includeCharts ? 1 : 0,
    })
    exportDialog.open = false
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'The export failed.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    exporting.value = false
  }
}

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
    sheets.rows = await reportService.listShortlistingSheets({ job_openings: filteredJobNames() })
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
    await reportService.downloadAllShortlistingSheets({ job_openings: filteredJobNames() })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the sheets.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    exportingSheets.value = false
  }
}

// Jobs matching the applied job-level filters (null = all jobs).
function filteredJobNames() {
  const jobs = options.value.jobs
  const jobLevel = ['positions', 'tracks', 'departments', 'employment_types', 'job_openings'].some((k) => applied[k].length)
  if (!jobLevel || !jobs) return null
  return jobs
    .filter(
      (j) =>
        (!applied.positions.length || applied.positions.includes(j.position)) &&
        (!applied.tracks.length || applied.tracks.includes(j.track)) &&
        (!applied.departments.length || applied.departments.includes(j.department)) &&
        (!applied.employment_types.length || applied.employment_types.includes(j.employment_type)) &&
        (!applied.job_openings.length || applied.job_openings.includes(j.value)),
    )
    .map((j) => j.value)
}

onMounted(async () => {
  await load()
  loadSheets()
})
</script>
