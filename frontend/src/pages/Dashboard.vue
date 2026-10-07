<template>
  <StaffLayout>
    <PageHeader title="Dashboard" :subtitle="`Welcome, ${session.fullName}`">
      <template v-if="session.canViewPipeline" #actions>
        <Button variant="ghost" icon-left="refresh-cw" :loading="loading" @click="load">Refresh</Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto bg-gray-50">
      <div v-if="!session.rolesLoaded" class="p-6 text-sm text-gray-500">Loading...</div>

      <!-- Staff without pipeline access: shortcuts -->
      <div v-else-if="!session.canViewPipeline" class="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="link in shortcuts"
          :key="link.to"
          :to="link.to"
          class="rounded-xl border bg-white p-4 shadow-sm hover:border-brand-200"
        >
          <div class="text-sm font-semibold text-gray-900">{{ link.label }}</div>
          <div class="mt-0.5 text-sm text-gray-500">{{ link.description }}</div>
        </router-link>
        <EmptyState v-if="!shortcuts.length" class="col-span-full" title="Nothing assigned to you yet" />
      </div>

      <div v-else class="flex flex-col gap-6 p-6">
        <!-- Filters -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-7">
            <MultiSelectFilter label="Position" all-label="All positions" :options="options.positions || []" v-model="filters.positions" />
            <MultiSelectFilter label="Track" all-label="All tracks" :options="options.tracks || []" v-model="filters.tracks" />
            <MultiSelectFilter label="Department" all-label="All departments" :options="options.departments || []" v-model="filters.departments" />
            <MultiSelectFilter label="Job opening" all-label="All job openings" :options="jobOptions" v-model="filters.job_openings" />
            <MultiSelectFilter label="Employment type" all-label="All types" :options="options.employment_types || []" v-model="filters.employment_types" />
            <MultiSelectFilter label="Application status" all-label="All statuses" :options="options.statuses || []" v-model="filters.statuses" />
            <MultiSelectFilter label="Eligibility" all-label="Any eligibility" :options="ELIGIBILITY" v-model="filters.eligibility" />
          </div>
          <div class="mt-3 flex flex-wrap items-end gap-3 border-t pt-3">
            <FormControl class="w-44" label="Applied" type="select" v-model="filters.applied" :options="APPLIED_PERIODS" />
            <template v-if="filters.applied === 'custom'">
              <FormControl class="w-40" label="Applied from" type="date" v-model="filters.applied_from" />
              <FormControl class="w-40" label="Applied to" type="date" v-model="filters.applied_to" />
            </template>
            <FormControl class="w-48" label="Ad closing date" type="select" v-model="filters.closing" :options="CLOSING_PERIODS" />
            <template v-if="filters.closing === 'custom'">
              <FormControl class="w-40" label="Closing from" type="date" v-model="filters.closing_from" />
              <FormControl class="w-40" label="Closing to" type="date" v-model="filters.closing_to" />
            </template>
            <div class="ml-auto flex items-center gap-3">
              <span v-if="dirty" class="text-xs font-medium text-orange-700">Changes not applied yet</span>
              <span v-else-if="activeCount" class="text-xs text-gray-600">{{ activeCount }} filter{{ activeCount === 1 ? '' : 's' }} applied</span>
              <Button v-if="activeCount || dirty" variant="ghost" icon-left="x" @click="clearFilters">Clear all</Button>
              <Button
                variant="solid"
                icon-left="search"
                :class="BTN_BRAND"
                :loading="loading"
                :disabled="!dirty || !complete"
                @click="applyFilters"
              >
                Search
              </Button>
            </div>
          </div>
        </div>

        <template v-if="data">
          <!-- Summary -->
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <button
              v-for="card in cards"
              :key="card.key"
              class="group flex items-start justify-between gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md"
              :title="`Show ${card.label.toLowerCase()}`"
              @click="openDrilldown(card.key, card.label)"
            >
              <div class="min-w-0">
                <div class="text-2xl font-bold text-gray-900">{{ card.value }}</div>
                <div class="mt-1 text-xs text-gray-500 group-hover:text-brand-700">{{ card.label }}</div>
              </div>
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700 group-hover:bg-brand-700 group-hover:text-white">
                <FeatherIcon :name="card.icon" class="h-4 w-4" />
              </div>
            </button>
          </div>

          <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <!-- Needs attention -->
            <SectionCard title="Needs Attention" icon="alert-circle">
              <ul class="-mx-2 flex flex-col">
                <li v-for="item in attention" :key="item.key">
                  <router-link
                    v-if="!item.drilldown"
                    :to="item.link"
                    class="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm hover:bg-brand-50"
                  >
                    <AttentionRow :item="item" />
                  </router-link>
                  <a
                    v-else
                    href="#"
                    role="button"
                    class="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm hover:bg-brand-50"
                    @click.prevent="openDrilldown(item.drilldown, item.title)"
                  >
                    <AttentionRow :item="item" />
                  </a>
                </li>
              </ul>
            </SectionCard>

            <!-- Deadlines -->
            <SectionCard title="Upcoming Deadlines" icon="calendar">
              <div v-if="!data.deadlines.length" class="text-sm text-gray-500">No upcoming deadlines.</div>
              <ul v-else class="-mx-2 flex flex-col">
                <li v-for="(d, idx) in data.deadlines" :key="idx">
                  <router-link :to="`/jobs/${d.job}`" class="flex items-center gap-3 rounded-md px-2 py-2 text-sm hover:bg-brand-50">
                    <div
                      class="flex w-12 shrink-0 flex-col items-center rounded-md py-1 text-center"
                      :class="d.days_left <= 3 ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-700'"
                    >
                      <span class="text-sm font-bold leading-none">{{ dayjs(d.date).format('D') }}</span>
                      <span class="text-[10px] uppercase">{{ dayjs(d.date).format('MMM') }}</span>
                    </div>
                    <div class="min-w-0 flex-1">
                      <div class="truncate font-medium text-gray-900">{{ d.title }}</div>
                      <div class="text-xs text-gray-500">{{ d.kind }} · {{ d.detail }}</div>
                    </div>
                    <span class="shrink-0 text-xs font-semibold" :class="d.days_left <= 3 ? 'text-orange-700' : 'text-gray-500'">
                      {{ d.days_left === 0 ? 'Today' : `${d.days_left}d` }}
                    </span>
                  </router-link>
                </li>
              </ul>
            </SectionCard>

            <!-- Upcoming interviews -->
            <SectionCard title="Upcoming Interviews" icon="video">
              <div v-if="!recruiter?.upcoming_interviews?.length" class="text-sm text-gray-500">No upcoming interviews.</div>
              <ul v-else class="-mx-2 flex flex-col">
                <li v-for="iv in recruiter.upcoming_interviews" :key="iv.name">
                  <router-link :to="`/applications/${iv.application}`" class="flex items-center justify-between gap-2 rounded-md px-2 py-2 text-sm hover:bg-brand-50">
                    <span class="text-gray-800">{{ iv.application }} · {{ iv.round_type }}</span>
                    <span class="text-xs text-gray-500">{{ dayjs(iv.scheduled_datetime).format('DD MMM, h:mm A') }}</span>
                  </router-link>
                </li>
              </ul>
            </SectionCard>
          </div>

          <!-- Jobs at a glance -->
          <SectionCard title="Job Openings at a Glance" icon="briefcase" :subtitle="`${data.jobs.length} open or recent job opening(s)`">
            <DataTable
              :columns="JOB_COLUMNS"
              :rows="data.jobs"
              :selectable="false"
              clickable
              empty-title="No job openings match the filters"
              search-placeholder="Search job openings..."
              @row-click="(j) => router.push(`/jobs/${j.name}`)"
            >
              <template #cell-job_title="{ row }">
                <div class="min-w-[12rem]">
                  <div class="font-semibold text-gray-900">{{ row.job_title }}</div>
                  <div class="text-xs font-normal text-gray-500">{{ row.position || row.name }} · {{ row.department }}</div>
                </div>
              </template>
              <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
              <template #cell-application_deadline="{ row }">
                <span v-if="row.application_deadline" class="whitespace-nowrap" :class="row.status === 'Advertised' && row.days_left <= 3 ? 'font-semibold text-orange-700' : ''">
                  {{ dayjs(row.application_deadline).format('DD MMM YYYY') }}
                  <span v-if="row.status === 'Advertised' && row.days_left >= 0" class="text-xs text-gray-500">({{ row.days_left }}d)</span>
                </span>
              </template>
              <template #cell-pending="{ value }">
                <span :class="value ? 'font-semibold text-orange-700' : 'text-gray-400'">{{ value }}</span>
              </template>
              <template #cell-shortlisted="{ row }">
                <div class="min-w-[7rem]">
                  <div class="text-xs"><b>{{ row.shortlisted }}</b> / {{ row.target }} (1:{{ row.ratio }})</div>
                  <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-gray-100">
                    <div class="h-full rounded-full bg-brand-700" :style="{ width: `${Math.min(100, (row.shortlisted / (row.target || 1)) * 100)}%` }" />
                  </div>
                </div>
              </template>
              <template #cell-has_committee="{ value }">
                <FeatherIcon :name="value ? 'check' : 'minus'" class="h-4 w-4" :class="value ? 'text-green-600' : 'text-gray-300'" />
              </template>
            </DataTable>
          </SectionCard>

          <!-- Recruitment pipeline: how far each job has got, stage by stage -->
          <SectionCard title="Recruitment Pipeline" icon="trending-up" subtitle="Each job opening's progress through the stages. Follows the Track and Job opening filters.">
            <DataTable
              export-name="recruitment-pipeline"
              :columns="PIPELINE_COLUMNS"
              :rows="pipelineRows"
              :loading="pipeline.loading"
              row-key="job_opening"
              :selectable="false"
              clickable
              empty-title="No job openings to report on"
              search-placeholder="Search job openings..."
              @row-click="(row) => router.push(`/jobs/${row.job_opening}`)"
            >
              <template #cell-job_title="{ row }">
                <span class="font-semibold text-gray-900">{{ row.job_title || row.job_opening }}</span>
              </template>
              <template v-for="k in PIPELINE_COUNTS" :key="k" #[`cell-${k}`]="{ row, value }">
                <button
                  v-if="value"
                  type="button"
                  class="rounded px-2 py-0.5 font-semibold text-brand-700 hover:bg-brand-50 hover:underline"
                  :title="`See the ${value} application(s)`"
                  @click.stop="openPipelineDrilldown(row, k)"
                >{{ value }}</button>
                <span v-else class="cursor-default px-2 text-gray-300" title="No applications at this stage" @click.stop>0</span>
              </template>
            </DataTable>
          </SectionCard>

          <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <!-- Recent applications -->
            <SectionCard title="Recent Applications" icon="inbox">
              <template #actions>
                <router-link to="/applications" class="text-xs font-semibold text-brand-700 hover:underline">View all</router-link>
              </template>
              <div v-if="!data.recent_applications.length" class="text-sm text-gray-500">No applications match the filters.</div>
              <ul v-else class="-mx-2 flex flex-col">
                <li v-for="a in data.recent_applications" :key="a.name">
                  <router-link :to="`/applications/${a.name}`" class="flex items-center gap-3 rounded-md px-2 py-2 text-sm hover:bg-brand-50">
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                      {{ initials(a.candidate_name) }}
                    </span>
                    <div class="min-w-0 flex-1">
                      <div class="truncate font-medium text-gray-900">{{ a.candidate_name }}</div>
                      <div class="truncate text-xs text-gray-500">{{ a.job_title }} · {{ dayjs(a.creation).format('DD MMM, h:mm A') }}</div>
                    </div>
                    <StatusBadge :status="a.status" />
                  </router-link>
                </li>
              </ul>
            </SectionCard>

            <!-- Recent activity -->
            <SectionCard title="Recent Activity" icon="clock">
              <div v-if="!data.activity.length" class="text-sm text-gray-500">No recent activity.</div>
              <ol v-else class="relative ml-3 border-l border-gray-200">
                <li v-for="(e, idx) in data.activity" :key="idx" class="relative pb-4 pl-5 last:pb-0">
                  <span
                    class="absolute -left-[7px] top-1.5 h-3 w-3 rounded-full ring-4 ring-white"
                    :class="e.kind === 'corrigendum' ? 'bg-orange-500' : e.text.endsWith('Not Selected') ? 'bg-red-500' : 'bg-brand-700'"
                  />
                  <router-link :to="e.link" class="block text-sm hover:text-brand-700">
                    <span class="font-medium text-gray-900">{{ e.subject }}</span>
                    <span class="block text-gray-700">{{ e.text }}</span>
                  </router-link>
                  <div class="text-xs text-gray-500">{{ e.who }} · {{ dayjs(e.at).format('DD MMM, h:mm A') }}</div>
                </li>
              </ol>
            </SectionCard>
          </div>
        </template>
      </div>
    </div>

    <DrilldownDialog
      v-model:open="drilldown.open"
      :bucket="drilldown.bucket"
      :title="drilldown.title"
      :description="drilldown.description"
      :filters="drilldown.params || { filters: apiFilters }"
    />
  </StaffLayout>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import DataTable from '@/components/common/DataTable.vue'
import DrilldownDialog from '@/components/common/DrilldownDialog.vue'
import MultiSelectFilter from '@/components/common/MultiSelectFilter.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { useSessionStore } from '@/stores/session'
import { reportService } from '@/services/reports'
import { callMethod } from '@/services/api'

const session = useSessionStore()
const router = useRouter()

const ALL = 'all'
const APPLIED_PERIODS = [
  { label: 'Any time', value: ALL },
  { label: 'Last 7 days', value: '7d' },
  { label: 'Last 30 days', value: '30d' },
  { label: 'This month', value: 'month' },
  { label: 'This year', value: 'year' },
  { label: 'Custom dates', value: 'custom' },
]
const CLOSING_PERIODS = [
  { label: 'Any closing date', value: ALL },
  { label: 'Closing in next 7 days', value: 'next7' },
  { label: 'Closing in next 30 days', value: 'next30' },
  { label: 'Already closed', value: 'passed' },
  { label: 'Custom dates', value: 'custom' },
]
const ELIGIBILITY = [
  { label: 'To check', value: 'Pending' },
  { label: 'Eligible', value: 'Eligible' },
  { label: 'Not eligible', value: 'Not Eligible' },
]
const LIST_KEYS = ['positions', 'tracks', 'departments', 'job_openings', 'employment_types', 'statuses', 'eligibility']

function emptyFilters() {
  return {
    ...Object.fromEntries(LIST_KEYS.map((k) => [k, []])),
    applied: ALL,
    applied_from: '',
    applied_to: '',
    closing: ALL,
    closing_from: '',
    closing_to: '',
  }
}

// ----- filters (remembered on this device)
const STORE_KEY = 'pathways-dashboard-filters-v2'
function savedFilters() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY) || '{}')
  } catch {
    return {}
  }
}
// `filters` is what is being edited; `applied` is what the page shows.
// Nothing reloads until Search.
const applied = reactive({ ...emptyFilters(), ...savedFilters() })
const filters = reactive(JSON.parse(JSON.stringify(applied)))
const activeCount = computed(
  () => LIST_KEYS.filter((k) => applied[k].length).length + (applied.applied !== ALL) + (applied.closing !== ALL),
)
const dirty = computed(() => JSON.stringify(filters) !== JSON.stringify(applied))
const complete = computed(() => {
  const incomplete = (p, a, b) => p === 'custom' && !(a && b)
  return !incomplete(filters.applied, filters.applied_from, filters.applied_to) && !incomplete(filters.closing, filters.closing_from, filters.closing_to)
})

function applyFilters() {
  Object.assign(applied, JSON.parse(JSON.stringify(filters)))
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(applied))
  } catch {
    // storage unavailable
  }
  load()
}

function clearFilters() {
  Object.assign(filters, emptyFilters())
  applyFilters()
}

function range(preset, from, to) {
  const today = dayjs()
  const r = {
    '7d': [today.subtract(6, 'day'), today],
    '30d': [today.subtract(29, 'day'), today],
    month: [today.startOf('month'), today],
    year: [today.startOf('year'), today],
    next7: [today, today.add(7, 'day')],
    next30: [today, today.add(30, 'day')],
    passed: [today.subtract(10, 'year'), today.subtract(1, 'day')],
    custom: from && to ? [dayjs(from), dayjs(to)] : null,
  }[preset]
  return r ? r.map((d) => d.format('YYYY-MM-DD')) : null
}

const apiFilters = computed(() => {
  const out = {}
  for (const k of LIST_KEYS) if (applied[k].length) out[k] = applied[k]
  const appliedRange = range(applied.applied, applied.applied_from, applied.applied_to)
  if (appliedRange) [out.from_date, out.to_date] = appliedRange
  const closing = range(applied.closing, applied.closing_from, applied.closing_to)
  if (closing) [out.deadline_from, out.deadline_to] = closing
  return out
})

// Job openings narrowed to the other job filters.
const jobOptions = computed(() =>
  (options.value.jobs || [])
    .filter(
      (j) =>
        (!filters.tracks.length || filters.tracks.includes(j.track)) &&
        (!filters.departments.length || filters.departments.includes(j.department)) &&
        (!filters.positions.length || filters.positions.includes(j.position)) &&
        (!filters.employment_types.length || filters.employment_types.includes(j.employment_type)),
    )
    .map((j) => ({ label: j.job_title, value: j.name })),
)

// ----- data
const data = ref(null)
const recruiter = ref(null)
const loading = ref(false)
const options = computed(() => data.value?.options || {})

let requestId = 0
async function load() {
  const id = ++requestId
  loading.value = true
  try {
    const [dashboard, summary] = await Promise.all([
      reportService.getDashboard({ filters: apiFilters.value }),
      recruiter.value ? Promise.resolve(recruiter.value) : reportService.getRecruiterSummary(),
    ])
    if (id !== requestId) return
    data.value = dashboard
    recruiter.value = summary
  } finally {
    if (id === requestId) loading.value = false
  }
}

// Chosen job openings that no longer match the other filters drop out.
watch(jobOptions, (jobs) => {
  const allowed = new Set(jobs.map((j) => j.value))
  const kept = filters.job_openings.filter((j) => allowed.has(j))
  if (kept.length !== filters.job_openings.length) filters.job_openings = kept
})

const cards = computed(() => {
  const s = data.value?.summary || {}
  return [
    { key: 'total_applications', icon: 'inbox', label: 'Total Applications', value: s.total_applications },
    { key: 'screening_pending', icon: 'clock', label: 'Screening Pending', value: s.screening_pending },
    { key: 'shortlisted', icon: 'check-circle', label: 'Shortlisted', value: s.shortlisted },
    { key: 'interviews_scheduled', icon: 'video', label: 'Interviews Scheduled', value: s.interviews_scheduled },
    { key: 'selected', icon: 'star', label: 'Selected', value: s.selected },
    { key: 'offers_released', icon: 'send', label: 'Offers Released', value: s.offers_released },
    { key: 'offers_accepted', icon: 'thumbs-up', label: 'Offers Accepted', value: s.offers_accepted },
    { key: 'documents_pending', icon: 'file', label: 'Documents Pending', value: s.documents_pending },
    { key: 'joined', icon: 'user-check', label: 'Joined', value: s.joined },
    { key: 'rejected', icon: 'x-circle', label: 'Not Selected', value: s.rejected },
  ]
})

const attention = computed(() => {
  const r = recruiter.value || {}
  return [
    ...(data.value?.attention || []),
    { key: 'feedback_pending', count: r.feedback_pending_count || 0, label: 'interview(s) awaiting feedback', drilldown: 'feedback_pending', title: 'Interviews Awaiting Feedback' },
    { key: 'document_checklists', count: r.documents_pending || 0, label: 'document checklist(s) pending', drilldown: 'document_checklists', title: 'Document Checklists Pending' },
    { key: 'offers_awaiting', count: r.offers_pending || 0, label: 'offer(s) awaiting candidate response', drilldown: 'offers_awaiting', title: 'Offers Awaiting Response' },
  ].sort((a, b) => (b.count > 0) - (a.count > 0))
})

const JOB_COLUMNS = [
  { key: 'job_title', label: 'Job Opening' },
  { key: 'track', label: 'Track' },
  { key: 'status', label: 'Status' },
  { key: 'application_deadline', label: 'Closes' },
  { key: 'applications', label: 'Applied', align: 'right' },
  { key: 'pending', label: 'To check', align: 'right' },
  { key: 'eligible', label: 'Eligible', align: 'right' },
  { key: 'shortlisted', label: 'Shortlisted / target' },
  { key: 'has_committee', label: 'Committee', sortable: false },
]

// One dialog for every drill-down.
const drilldown = reactive({ open: false, bucket: '', title: '', description: '', params: null })
function openDrilldown(bucket, title, description = '') {
  Object.assign(drilldown, { open: true, bucket, title, description, params: null })
}

function initials(name) {
  return (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('')
}

const SHORTCUTS = [
  { key: 'approvals', to: '/approvals', label: 'My Approvals', description: 'Green Sheets waiting for your decision.' },
  { key: 'applications', to: '/applications', label: 'Applications', description: 'Applications assigned to your committee.' },
  { key: 'interviews', to: '/interviews', label: 'Interviews', description: 'Interviews you are part of.' },
  { key: 'jobs', to: '/jobs', label: 'Job Openings', description: 'Positions and their approval status.' },
  { key: 'offers', to: '/offers', label: 'Offers', description: 'Offer and appointment orders.' },
]
const shortcuts = computed(() => SHORTCUTS.filter((s) => session.hasMenu(s.key)))

onMounted(async () => {
  await session.fetchRoles()
  if (session.canViewPipeline) load()
})

// Count badge + label + chevron for a Needs Attention item.
const AttentionRow = (p) => [
  h(
    'span',
    {
      class: [
        'flex h-7 min-w-7 items-center justify-center rounded-full px-2 text-xs font-bold',
        p.item.count ? 'bg-brand-700 text-white' : 'bg-gray-100 text-gray-500',
      ],
    },
    String(p.item.count),
  ),
  h('span', { class: ['flex-1', p.item.count ? 'text-gray-900' : 'text-gray-500'] }, p.item.label),
  h(FeatherIcon, { name: 'chevron-right', class: 'h-4 w-4 text-gray-400' }),
]
AttentionRow.props = ['item']

// ----- recruitment pipeline (the Recruitment Pipeline report)
const PIPELINE_COUNTS = ['applied', 'eligible', 'shortlisted', 'interviewed', 'selected', 'offered', 'joined']
const PIPELINE_COLUMNS = [
  { key: 'job_title', label: 'Job Opening', format: (row) => row.job_title || row.job_opening },
  { key: 'track', label: 'Track' },
  { key: 'status', label: 'Status' },
  ...PIPELINE_COUNTS.map((k) => ({ key: k, label: k[0].toUpperCase() + k.slice(1), align: 'right' })),
]
const pipeline = reactive({ rows: [], loading: false })
async function loadPipeline() {
  pipeline.loading = true
  try {
    const res = await callMethod('frappe.desk.query_report.run', { report_name: 'Recruitment Pipeline' })
    pipeline.rows = (res?.result || []).filter((r) => r && r.job_opening)
  } catch {
    pipeline.rows = []
  } finally {
    pipeline.loading = false
  }
}
const pipelineRows = computed(() =>
  pipeline.rows.filter(
    (r) =>
      (!applied.tracks.length || applied.tracks.includes(r.track)) &&
      (!applied.job_openings.length || applied.job_openings.includes(r.job_opening)),
  ),
)
onMounted(loadPipeline)

const STAGE_LABELS = {
  applied: 'Applied',
  eligible: 'Eligible',
  shortlisted: 'Shortlisted',
  interviewed: 'Interviewed',
  selected: 'Selected',
  offered: 'Offered',
  joined: 'Joined',
}
function openPipelineDrilldown(row, stage) {
  Object.assign(drilldown, {
    open: true,
    bucket: `pipeline:${stage}`,
    title: `${STAGE_LABELS[stage]} · ${row.job_title || row.job_opening}`,
    description: `Applications counted as "${STAGE_LABELS[stage]}" for this job opening.`,
    params: { job_opening: row.job_opening },
  })
}
</script>
