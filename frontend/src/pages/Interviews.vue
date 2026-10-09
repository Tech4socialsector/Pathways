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
        empty-title="Nobody is waiting for an interview to be scheduled"
        search-placeholder="Search candidate, job or application…"
      >
        <template #cell-application_id="{ row }">
          <router-link :to="`/applications/${row.name}`" class="font-mono text-xs text-gray-700 hover:text-brand-700 hover:underline">{{ row.application_id }}</router-link>
        </template>
        <template #cell-candidate_name="{ row }">
          <span class="font-medium text-gray-900">{{ row.candidate_name }}</span>
        </template>
        <template #cell-next_round_label="{ row }">
          <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="row.next_round === 'Final' ? 'bg-brand-50 text-brand-700' : 'bg-blue-50 text-blue-700'">{{ row.next_round_label }}</span>
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
        <template #cell-status="{ row, value }">
          <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="STATUS_TONE[value] || 'bg-gray-100 text-gray-700'">{{ value }}</span>
          <router-link
                    v-if="row.scores?.panel_size"
                    :to="`/panel/${row.name}`"
                    class="mt-1 flex items-center gap-1 text-xs text-gray-600 hover:text-brand-700"
                    @click.stop
                  >
                    <FeatherIcon name="clipboard" class="h-3 w-3" />Scores {{ row.scores.scored }}/{{ row.scores.panel_size }}<template v-if="row.scores.scored"> · avg {{ row.scores.average }}/{{ row.scores.max_score }}</template>
                  </router-link>
        </template>
        <template #cell-rsvp_status="{ row }">
          <span v-if="['Scheduled', 'Rescheduled'].includes(row.status)" class="rounded-full px-2 py-0.5 text-xs font-medium" :class="RSVP_TONE[row.rsvp_status || 'Pending']">
            {{ row.rsvp_status || 'Pending' }}
          </span>
          <span v-else class="text-gray-300">—</span>
        </template>
        <template #bulk-actions="{ rows: chosen, clear }">
          <span v-if="openOnly(chosen).length < chosen.length" class="text-xs text-gray-500">{{ openOnly(chosen).length }} still open</span>
          <Button size="sm" variant="outline" icon-left="send" :disabled="!openOnly(chosen).length" @click="bulkResend(chosen, clear)">Resend invite</Button>
          <Button size="sm" variant="outline" icon-left="check" :disabled="!openOnly(chosen).length" @click="bulkComplete(chosen, clear)">Mark completed</Button>
          <Button size="sm" variant="outline" theme="red" icon-left="x" :disabled="!openOnly(chosen).length" @click="bulkCancel(chosen, clear)">Cancel</Button>
        </template>
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1" @click.stop>
            <a v-if="row.meeting_link && isOpen(row)" :href="row.meeting_link" target="_blank" rel="noopener">
              <Button size="sm" variant="outline" icon-left="video">Join</Button>
            </a>
            <Dropdown :options="rowMenu(row)" placement="right">
              <Button size="sm" variant="ghost" icon="more-horizontal" :aria-label="`Actions for ${row.candidate_name}`" />
            </Dropdown>
          </div>
        </template>
      </DataTable>
    </div>

    <EditInterviewDialog v-model:open="editDialog.open" :interview="editDialog.interview" @saved="load" />
    <CancelInterviewDialog v-model:open="cancelDialog.open" :interview="cancelDialog.interview" :interviews="cancelDialog.interviews" @saved="onCancelled" />
    <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />
    <ScheduleInterviewDialog v-model:open="scheduleDialog.open" :candidates="scheduleDialog.candidates" :round="scheduleDialog.round" @scheduled="onScheduled" />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ScheduleInterviewDialog from '@/components/jobs/ScheduleInterviewDialog.vue'
import { useRouter } from 'vue-router'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { Button, Dropdown, FeatherIcon } from 'frappe-ui'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import CancelInterviewDialog from '@/components/jobs/CancelInterviewDialog.vue'
import EditInterviewDialog from '@/components/jobs/EditInterviewDialog.vue'
import { toast } from '@/utils/notify'
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
      next_round_label: c.next_round === 'Final' ? 'Final interview' : 'Round 1 (HR)',
    })),
  ),
)
const toScheduleColumns = [
  { key: 'application_id', label: 'Candidate ID' },
  { key: 'candidate_name', label: 'Candidate Name' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'track', label: 'Track' },
  { key: 'next_round_label', label: 'Next Round' },
  { key: 'status', label: 'Current Status' },
]
// Available from the Columns menu.
const toScheduleExtra = [
  { key: 'position', label: 'Job Code' },
  { key: 'committee', label: 'Selection Committee' },
  { key: 'eligibility_status', label: 'Eligibility' },
]
const toScheduleFilters = [
  { key: 'next_round_label', label: 'Next Rounds' },
  { key: 'job_title', label: 'Job Openings' },
  { key: 'track', label: 'Tracks' },
  { key: 'committee', label: 'Committee' },
]

// ----- schedule from this page
const scheduleDialog = reactive({ open: false, candidates: [], clear: null, round: 'HR Interaction' })
// The dialog opens on the candidates' next round: Final once Round 1 is completed.
function openSchedule(chosen, clear = null) {
  const round = chosen.length && chosen.every((c) => c.next_round === 'Final') ? 'Final' : 'HR Interaction'
  Object.assign(scheduleDialog, { open: true, candidates: chosen, clear, round })
}
async function onScheduled() {
  scheduleDialog.clear?.()
  await load()
}
const loading = ref(false)

// ----- per-interview actions: reschedule / edit, resend, complete, cancel
const editDialog = reactive({ open: false, interview: null })
const cancelDialog = reactive({ open: false, interview: null, interviews: [], clear: null })
const confirmBox = reactive({ open: false, title: '', message: '', label: '', run: null })
const askConfirm = (o) => Object.assign(confirmBox, { open: true, ...o })
const isOpen = (row) => ['Scheduled', 'Rescheduled'].includes(row.status)
const openOnly = (list) => list.filter(isOpen)
const roundName = (row) => (row.round_type === 'Final' ? 'final' : 'Round 1 (HR)')
function rowMenu(row) {
  const items = []
  if (isOpen(row)) {
    items.push({ label: 'Reschedule / edit', icon: 'edit-2', onClick: () => Object.assign(editDialog, { open: true, interview: row }) })
    items.push({ label: 'Resend invite', icon: 'send', onClick: () => askConfirm({ title: 'Resend invite?', message: `Email the ${roundName(row)} invite to ${row.candidate_name} again?`, label: 'Resend', run: () => act(() => interviewService.resendInvite(row.name), 'Invite queued.') }) })
    items.push({ label: 'Mark completed', icon: 'check', onClick: () => askConfirm({ title: 'Mark interview completed?', message: `Mark the ${roundName(row)} interview of ${row.candidate_name} as completed? It can no longer be rescheduled.`, label: 'Mark completed', run: () => act(() => interviewService.setStatus(row.name, 'Completed'), 'Marked completed.') }) })
    items.push({ label: 'Cancel interview', icon: 'x', onClick: () => Object.assign(cancelDialog, { open: true, interview: row, interviews: [], clear: null }) })
  }
  items.push({ label: 'Open application', icon: 'external-link', onClick: () => router.push(`/applications/${row.application}`) })
  return [{ group: 'Interview', hideLabel: true, items }]
}
// ----- bulk actions (only interviews still open)
async function runEach(list, fn, done, clear) {
  const failed = []
  for (const row of list) {
    try {
      await fn(row)
    } catch (e) {
      failed.push(`${row.candidate_name}: ${e?.messages?.[0] || 'failed'}`)
    }
  }
  const ok = list.length - failed.length
  if (ok) toast({ title: done(ok), icon: 'check', iconClasses: 'text-green-500' })
  if (failed.length) toast({ title: failed.join(' · '), icon: 'alert-triangle', iconClasses: 'text-red-500' })
  clear?.()
  await load()
}
function bulkResend(chosen, clear) {
  const list = openOnly(chosen)
  askConfirm({
    title: `Resend ${list.length} invite${list.length === 1 ? '' : 's'}?`,
    message: `Email the interview invite again to ${list.length} candidate${list.length === 1 ? '' : 's'}.`,
    label: 'Resend',
    run: () => runEach(list, (r) => interviewService.resendInvite(r.name), (n) => `${n} invite${n === 1 ? '' : 's'} queued.`, clear),
  })
}
function bulkComplete(chosen, clear) {
  const list = openOnly(chosen)
  askConfirm({
    title: `Mark ${list.length} interview${list.length === 1 ? '' : 's'} completed?`,
    message: 'They can no longer be rescheduled. Completed final interviews move the application to Interview Completed.',
    label: 'Mark completed',
    run: () => runEach(list, (r) => interviewService.setStatus(r.name, 'Completed'), (n) => `${n} marked completed.`, clear),
  })
}
function bulkCancel(chosen, clear) {
  Object.assign(cancelDialog, { open: true, interview: null, interviews: openOnly(chosen), clear })
}
function onCancelled() {
  cancelDialog.clear?.()
  load()
}
async function act(fn, message) {
  try {
    await fn()
    toast({ title: message, icon: 'check', iconClasses: 'text-green-500' })
    await load()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'That did not work.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

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
    { label: 'Waiting to be scheduled', value: toScheduleCount.value },
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
