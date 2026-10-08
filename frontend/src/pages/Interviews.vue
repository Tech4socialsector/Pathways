<template>
  <StaffLayout>
    <PageHeader
      title="Interviews"
      subtitle="Every scheduled interview across job openings. Schedule shortlisted candidates from the To schedule tab."
      :breadcrumbs="[{ label: 'Dashboard', to: '/' }, { label: 'Interviews' }]"
    />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div v-for="t in tiles" :key="t.label" class="rounded-xl border bg-white p-4 shadow-sm">
          <div class="text-2xl font-bold tabular-nums text-gray-900">{{ t.value }}</div>
          <div class="mt-0.5 text-xs text-gray-500">{{ t.label }}</div>
        </div>
      </div>
      <!-- Scheduled interviews, or shortlisted candidates still to schedule -->
      <nav class="mb-4 flex gap-1 border-b" aria-label="Interview lists">
        <button
          v-for="t in TABS"
          :key="t.key"
          type="button"
          class="relative flex items-center gap-2 px-3 pb-2.5 pt-1 text-sm"
          :class="tab === t.key ? 'font-semibold text-brand-700' : 'text-gray-600 hover:text-gray-900'"
          :aria-current="tab === t.key ? 'true' : undefined"
          @click="tab = t.key"
        >
          {{ t.label }}
          <span class="rounded-full px-1.5 text-xs font-semibold" :class="tab === t.key ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'">
            {{ t.key === 'scheduled' ? rows.length : toScheduleCount }}
          </span>
          <span v-if="tab === t.key" class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-700" />
        </button>
      </nav>

      <!-- To schedule: shortlisted candidates with no interview yet; schedule them here -->
      <DataTable
        v-if="tab === 'to_schedule'"
        export-name="interviews-to-schedule"
        :columns="toScheduleColumns"
        :extra-columns="toScheduleExtra"
        :rows="toScheduleRows"
        :loading="loading"
        :filters="toScheduleFilters"
        empty-title="Every shortlisted candidate has an interview scheduled"
        search-placeholder="Search candidate, job or application…"
      >
        <template #cell-application_id="{ row }">
          <router-link :to="`/applications/${row.name}`" class="font-mono text-xs text-gray-700 hover:text-brand-700 hover:underline">{{ row.application_id }}</router-link>
        </template>
        <template #cell-candidate_name="{ row }">
          <span class="font-medium text-gray-900">{{ row.candidate_name }}</span>
        </template>
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
          <div v-if="row.interview_history" class="mt-0.5 text-xs text-gray-500">{{ row.interview_history }}</div>
        </template>
        <template #bulk-actions="{ rows: chosen, clear }">
          <Button size="sm" variant="solid" icon-left="calendar" :class="BTN_BRAND" @click="openSchedule(chosen, clear)">Schedule interview</Button>
        </template>
        <template #actions="{ row }">
          <Button size="sm" variant="solid" icon-left="calendar" :class="BTN_BRAND" @click="openSchedule([row])">Schedule</Button>
        </template>
      </DataTable>

      <DataTable
        v-else
        export-name="interviews"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        :selectable="false"
        clickable
        empty-title="No interviews scheduled yet"
        search-placeholder="Search candidate, job or application…"
        @row-click="(r) => router.push(`/applications/${r.application}`)"
      >
        <template #cell-candidate_name="{ row }">
          <div class="font-medium text-gray-900">{{ row.candidate_name }}</div>
          <div class="font-mono text-xs text-gray-500">{{ row.application_id }}</div>
        </template>
        <template #cell-job_title="{ row }">
          <router-link :to="`/jobs/${row.job_opening}`" class="hover:text-brand-700 hover:underline" @click.stop>{{ row.job_title }}</router-link>
        </template>
        <template #cell-status="{ value }">
          <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="STATUS_TONE[value] || 'bg-gray-100 text-gray-700'">{{ value }}</span>
        </template>
        <template #cell-rsvp_status="{ row }">
          <span v-if="['Scheduled', 'Rescheduled'].includes(row.status)" class="rounded-full px-2 py-0.5 text-xs font-medium" :class="RSVP_TONE[row.rsvp_status || 'Pending']">
            {{ row.rsvp_status || 'Pending' }}
          </span>
          <span v-else class="text-gray-300">—</span>
        </template>
        <template #actions="{ row }">
          <a v-if="row.meeting_link" :href="row.meeting_link" target="_blank" rel="noopener" @click.stop>
            <Button size="sm" variant="outline" icon-left="video">Join</Button>
          </a>
        </template>
      </DataTable>
    </div>

    <ScheduleInterviewDialog v-model:open="scheduleDialog.open" :candidates="scheduleDialog.candidates" @scheduled="onScheduled" />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ScheduleInterviewDialog from '@/components/jobs/ScheduleInterviewDialog.vue'
import { useRouter } from 'vue-router'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { Button } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { interviewService } from '@/services/interviews'

const router = useRouter()
const rows = ref([])
const toSchedule = ref([])
const toScheduleCount = computed(() => toSchedule.value.reduce((n, j) => n + j.candidates.length, 0))
const TABS = [
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'to_schedule', label: 'To schedule' },
]
const tab = ref('scheduled')

// To schedule: one row per candidate (the API groups them by job).
const toScheduleRows = computed(() =>
  toSchedule.value.flatMap((j) =>
    j.candidates.map((c) => ({
      ...c,
      job_opening: j.job_opening,
      job_title: j.job_title,
      position: j.position,
      track: j.track,
      committee: j.has_committee ? 'Set up' : 'Not set up',
      has_committee: j.has_committee,
      committee_date: j.committee_date,
      committee_time: j.committee_time,
    })),
  ),
)
const toScheduleColumns = [
  { key: 'application_id', label: 'Candidate ID' },
  { key: 'candidate_name', label: 'Candidate Name' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'track', label: 'Track' },
  { key: 'status', label: 'Current Status' },
]
// Available from the Columns menu.
const toScheduleExtra = [
  { key: 'position', label: 'Job Code' },
  { key: 'committee', label: 'Selection Committee' },
  { key: 'eligibility_status', label: 'Eligibility' },
]
const toScheduleFilters = [
  { key: 'job_title', label: 'Job Openings' },
  { key: 'track', label: 'Tracks' },
  { key: 'committee', label: 'Committee' },
]

// ----- schedule from this page
const scheduleDialog = reactive({ open: false, candidates: [], clear: null })
function openSchedule(chosen, clear = null) {
  Object.assign(scheduleDialog, { open: true, candidates: chosen, clear })
}
async function onScheduled() {
  scheduleDialog.clear?.()
  await load()
}
const loading = ref(false)

const STATUS_TONE = {
  Scheduled: 'bg-blue-50 text-blue-700',
  Rescheduled: 'bg-blue-50 text-blue-700',
  Completed: 'bg-green-50 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}
const RSVP_TONE = { Pending: 'bg-orange-50 text-orange-700', Confirmed: 'bg-green-50 text-green-700', Declined: 'bg-red-50 text-red-700' }

const columns = [
  { key: 'scheduled_datetime', label: 'When', format: (r) => (r.scheduled_datetime ? dayjs(r.scheduled_datetime).format('DD MMM YYYY, h:mm A') : '') },
  { key: 'candidate_name', label: 'Candidate' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'round_type', label: 'Round', format: (r) => (r.round_type === 'HR Interaction' ? 'Round 1 (HR)' : r.round_type) },
  { key: 'mode', label: 'Mode', format: (r) => (r.mode === 'In-Person' ? `In person${r.location ? ' · ' + r.location : ''}` : `Online${r.meeting_platform ? ' · ' + r.meeting_platform : ''}`) },
  { key: 'rsvp_status', label: 'RSVP' },
  { key: 'status', label: 'Status' },
]
const filters = [
  { key: 'status', label: 'Statuses' },
  { key: 'round_type', label: 'Rounds' },
  { key: 'job_title', label: 'Job Openings' },
]

const tiles = computed(() => {
  const now = dayjs()
  const open = rows.value.filter((r) => ['Scheduled', 'Rescheduled'].includes(r.status))
  return [
    { label: 'Upcoming', value: open.filter((r) => dayjs(r.scheduled_datetime).isAfter(now)).length },
    { label: 'Today', value: open.filter((r) => dayjs(r.scheduled_datetime).isSame(now, 'day')).length },
    { label: 'Awaiting RSVP', value: open.filter((r) => (r.rsvp_status || 'Pending') === 'Pending').length },
    { label: 'Shortlisted, not scheduled', value: toScheduleCount.value },
  ]
})

async function load() {
  loading.value = true
  try {
    ;[rows.value, toSchedule.value] = await Promise.all([interviewService.listInterviews(), interviewService.listToSchedule()])
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await load()
  // Nothing scheduled yet: open on the candidates waiting for one.
  if (!rows.value.length && toSchedule.value.length) tab.value = 'to_schedule'
})
</script>
