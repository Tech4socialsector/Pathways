<template>
  <StaffLayout>
    <PageHeader
      title="Interviews"
      subtitle="Every scheduled interview across job openings. Schedule shortlisted candidates from the To schedule tab."
    />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <!-- A list that fails to load says so, instead of looking empty. -->
      <div v-if="loadErrors.length" class="mb-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3" role="alert">
        <FeatherIcon name="alert-octagon" class="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
        <div class="min-w-0 flex-1 text-sm text-red-800">
          <p v-for="e in loadErrors" :key="e">{{ e }}</p>
        </div>
        <Button size="sm" :loading="loading" @click="load">Retry</Button>
      </div>
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
          <span
            class="rounded-full px-1.5 text-xs font-semibold"
            :class="t.key === 'requests' && tabCount.requests ? 'bg-amber-500 text-white' : tab === t.key ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'"
          >
            {{ tabCount[t.key] }}
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

      <!-- Reschedule requests: accept a suggested time, decline, or pick another time -->
      <DataTable
        v-else-if="tab === 'requests'"
        export-name="interviews-reschedule-requests"
        :columns="requestColumns"
        :rows="requestRows"
        :loading="loading"
        :filters="requestFilters"
        empty-title="No reschedule requests waiting"
        search-placeholder="Search candidate, job or application…"
      >
        <template #cell-candidate_name="{ row }">
          <router-link :to="`/applications/${row.application}`" class="font-medium text-gray-900 hover:text-brand-700 hover:underline">{{ row.candidate_name }}</router-link>
          <div class="font-mono text-xs text-gray-500">{{ row.application_id }}</div>
        </template>
        <template #cell-reschedule_preferences="{ row }">
          <div class="flex flex-col gap-1">
            <span
              v-for="t in preferredTimes(row)"
              :key="t"
              class="w-fit whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium"
              :class="dayjs(t).isAfter(dayjs()) ? 'bg-amber-50 text-amber-900' : 'bg-gray-100 text-gray-400 line-through'"
            >
              {{ dayjs(t).format('ddd DD MMM, h:mm A') }}
            </span>
          </div>
        </template>
        <template #cell-rsvp_reason="{ value }">
          <span class="line-clamp-3 max-w-[18rem] text-gray-700" :title="value">{{ value || '—' }}</span>
        </template>
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1.5">
            <Button size="sm" variant="solid" icon-left="check" :class="BTN_BRAND" @click="openDecision(row, 'Accept')">Accept</Button>
            <Button size="sm" variant="outline" theme="red" icon-left="x" @click="openDecision(row, 'Decline')">Reject</Button>
            <Button size="sm" variant="outline" icon-left="calendar" @click="Object.assign(editDialog, { open: true, interview: row })">Reschedule</Button>
          </div>
        </template>
      </DataTable>

      <!-- Cancelled: kept for the record; nothing more can be done with them here -->
      <DataTable
        v-else-if="tab === 'cancelled'"
        export-name="interviews-cancelled"
        :columns="cancelledColumns"
        :rows="cancelledRows"
        :loading="loading"
        :filters="cancelledFilters"
        clickable
        empty-title="No cancelled interviews"
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
            v-if="row.scores?.scored"
            :to="`/panel/${row.name}`"
            class="mt-1 flex items-center gap-1 text-xs text-gray-600 hover:text-brand-700"
            @click.stop
          >
            <FeatherIcon name="clipboard" class="h-3 w-3" />Scores {{ row.scores.scored }}/{{ row.scores.panel_size }} · avg {{ row.scores.average }}/{{ row.scores.max_score }}
          </router-link>
        </template>
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1" @click.stop>
            <Dropdown :options="rowMenu(row)" placement="right">
              <Button size="sm" variant="ghost" icon="more-horizontal" :aria-label="`Actions for ${row.candidate_name}`" />
            </Dropdown>
          </div>
        </template>
      </DataTable>

      <template v-else>
      <!-- Final interview: candidates whose Round 1 is done wait here first,
           then their scheduled final interviews are listed below. -->
      <section v-if="tab === 'final'" class="mb-6">
        <div class="mb-2 flex flex-wrap items-baseline justify-between gap-2">
          <h2 class="text-sm font-semibold text-gray-900">
            Waiting for a final interview
            <span class="ml-1 rounded-full bg-brand-50 px-1.5 text-xs font-semibold text-brand-700">{{ finalWaitingRows.length }}</span>
          </h2>
          <p class="text-xs text-gray-500">Round 1 is done. Schedule the final interview with the job's Selection Committee.</p>
        </div>
        <DataTable
          export-name="interviews-final-waiting"
          :columns="finalWaitingColumns"
          :rows="finalWaitingRows"
          :loading="loading"
          empty-title="Nobody is waiting for a final interview"
          search-placeholder="Search candidate, job or application…"
        >
          <template #cell-application_id="{ row }">
            <router-link :to="`/applications/${row.name}`" class="font-mono text-xs text-gray-700 hover:text-brand-700 hover:underline">{{ row.application_id }}</router-link>
          </template>
          <template #cell-candidate_name="{ row }">
            <span class="font-medium text-gray-900">{{ row.candidate_name }}</span>
            <div v-if="row.interview_history" class="text-xs text-gray-500">{{ row.interview_history }}</div>
          </template>
          <template #cell-committee="{ row }">
            <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="row.has_committee ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'">
              {{ row.has_committee ? 'Set up' : 'Not set up' }}
            </span>
          </template>
          <template #bulk-actions="{ rows: chosen, clear }">
            <Button size="sm" variant="solid" icon-left="calendar" :class="BTN_BRAND" @click="openSchedule(chosen, clear)">Schedule final interview</Button>
          </template>
          <template #actions="{ row }">
            <Button size="sm" variant="solid" icon-left="calendar" :class="BTN_BRAND" @click="openSchedule([row])">Schedule final</Button>
          </template>
        </DataTable>
        <h2 class="mb-2 mt-6 text-sm font-semibold text-gray-900">
          Scheduled final interviews
          <span class="ml-1 rounded-full bg-gray-100 px-1.5 text-xs font-semibold text-gray-600">{{ finalRows.length }}</span>
        </h2>
      </section>
      <DataTable
        :key="tab"
        :export-name="LIST[tab].exportName"
        :columns="LIST[tab].columns"
        :rows="LIST[tab].rows.value"
        :loading="loading"
        :filters="LIST[tab].filters"
        clickable
        :empty-title="LIST[tab].empty"
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
        <template #cell-change_type="{ row }">
          <div class="text-gray-900">{{ changeLabel(row) }}<span v-if="row.change_count > 1" class="text-xs text-gray-500"> · {{ row.change_count }} times</span></div>
          <div v-if="row.change_note" class="max-w-[16rem] truncate text-xs text-gray-500" :title="row.change_note">{{ row.change_note }}</div>
        </template>
        <template #cell-rsvp_status="{ row }">
          <template v-if="['Scheduled', 'Rescheduled'].includes(row.status)">
            <span class="whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium" :class="RSVP_TONE[rsvpLabel(row.rsvp_status)]">
              {{ rsvpLabel(row.rsvp_status) }}
            </span>
            <!-- What the candidate asked for, so it can be acted on from here -->
            <div v-if="preferredTimes(row).length" class="mt-1 max-w-[15rem] text-xs text-gray-600">
              <div v-for="t in preferredTimes(row)" :key="t" class="whitespace-nowrap">{{ dayjs(t).format('DD MMM, h:mm A') }}</div>
            </div>
            <div v-if="row.rsvp_reason" class="mt-0.5 max-w-[15rem] truncate text-xs italic text-gray-500" :title="row.rsvp_reason">“{{ row.rsvp_reason }}”</div>
            <button
              v-if="rsvpLabel(row.rsvp_status) === 'Reschedule Requested' && isOpen(row)"
              type="button"
              class="mt-1 text-xs font-medium text-brand-700 hover:underline"
              @click.stop="tab = 'requests'"
            >
              Answer request
            </button>
          </template>
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
      </template>
    </div>

    <EditInterviewDialog v-model:open="editDialog.open" :interview="editDialog.interview" :assessor-limit="assessorLimit" @saved="load" />
    <RescheduleDecisionDialog v-model:open="decisionDialog.open" :interview="decisionDialog.interview" :decision="decisionDialog.decision" @decided="load" />
    <CancelInterviewDialog v-model:open="cancelDialog.open" :interview="cancelDialog.interview" :interviews="cancelDialog.interviews" @saved="onCancelled" />
    <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />
    <ScheduleInterviewDialog v-model:open="scheduleDialog.open" :candidates="scheduleDialog.candidates" :round="scheduleDialog.round" :assessor-limit="assessorLimit" @scheduled="onScheduled" />
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
import RescheduleDecisionDialog from '@/components/jobs/RescheduleDecisionDialog.vue'
import { toast } from '@/utils/notify'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { interviewService } from '@/services/interviews'
import { RSVP_TONE, preferredTimes, rsvpLabel } from '@/utils/rsvp'

const router = useRouter()
const rows = ref([])
const toSchedule = ref([])
const toScheduleCount = computed(() => toSchedule.value.reduce((n, j) => n + j.candidates.length, 0))
const TABS = [
  // In workflow order: waiting, booked, changed, called off.
  { key: 'to_schedule', label: 'To schedule' },
  { key: 'requests', label: 'Reschedule requests' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'final', label: 'Final interview' },
  { key: 'changed', label: 'Rescheduled / edited' },
  { key: 'cancelled', label: 'Cancelled' },
]
const tab = ref('scheduled')
// Most HR assessors per Round 1 interview (Pathways Settings), sent with each row.
const assessorLimit = computed(() => rows.value[0]?.hr_assessor_limit || 2)
// Scheduled tab: open and completed interviews; cancelled ones have their own tab.
const activeRows = computed(() => rows.value.filter((r) => r.status !== 'Cancelled'))
const cancelledRows = computed(() => rows.value.filter((r) => r.status === 'Cancelled'))
// Reschedule requests: open interviews whose candidate asked for another
// time, oldest request first, to answer from here.
const requestRows = computed(() =>
  activeRows.value
    .filter((r) => r.rsvp_label === 'Reschedule Requested' && isOpen(r))
    .sort((a, b) => String(a.rsvp_responded_on || '').localeCompare(String(b.rsvp_responded_on || ''))),
)
// Final interview tab, top: Round 1 done, final not yet scheduled (they are
// on To schedule too).
const finalWaitingRows = computed(() => toScheduleRows.value.filter((r) => r.next_round === 'Final'))
const finalWaitingColumns = [
  { key: 'application_id', label: 'Candidate ID' },
  { key: 'candidate_name', label: 'Candidate Name' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'track', label: 'Track' },
  { key: 'committee', label: 'Selection Committee' },
]
// Final interview: the Selection Committee round only (also on Scheduled).
const finalRows = computed(() => activeRows.value.filter((r) => r.round_type === 'Final'))
// Rescheduled / edited: open or completed interviews changed after they were
// scheduled (they stay on the Scheduled tab too).
const changedRows = computed(() =>
  activeRows.value
    .filter((r) => r.change_count > 0 || r.status === 'Rescheduled')
    // Rescheduled before changes were tracked: no change_type saved.
    .map((r) => (r.change_type ? r : { ...r, change_type: 'Rescheduled' }))
    .sort((a, b) => String(b.last_changed_on || b.modified || '').localeCompare(String(a.last_changed_on || a.modified || ''))),
)
const tabCount = computed(() => ({
  requests: requestRows.value.length,
  scheduled: activeRows.value.length,
  final: finalWaitingRows.value.length + finalRows.value.length,
  changed: changedRows.value.length,
  to_schedule: toScheduleCount.value,
  cancelled: cancelledRows.value.length,
}))

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

const columns = [
  { key: 'scheduled_datetime', label: 'When', format: (r) => (r.scheduled_datetime ? dayjs(r.scheduled_datetime).format('DD MMM YYYY, h:mm A [IST]') : '') },
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
  { key: 'rsvp_label', label: 'RSVP', options: Object.keys(RSVP_TONE) },
  { key: 'job_title', label: 'Job Openings' },
]
// Final interview tab: no Round column or filter (every row is Final).
const finalColumns = columns.filter((c) => c.key !== 'round_type')
const finalFilters = filters.filter((f) => f.key !== 'round_type')

const changeLabel = (r) => r.change_type || 'Rescheduled'
const changedColumns = [
  { key: 'scheduled_datetime', label: 'Now scheduled for', format: columns[0].format },
  {
    key: 'previous_datetime',
    label: 'Previously',
    format: (r) => (r.previous_datetime ? dayjs(r.previous_datetime).format('DD MMM YYYY, h:mm A [IST]') : '—'),
  },
  { key: 'candidate_name', label: 'Candidate' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'round_type', label: 'Round', format: columns[3].format },
  { key: 'change_type', label: 'Change', format: changeLabel },
  {
    key: 'last_changed_on',
    label: 'Changed on',
    format: (r) => (r.last_changed_on ? dayjs(r.last_changed_on).format('DD MMM YYYY, h:mm A [IST]') + (r.last_changed_by_name ? ` · ${r.last_changed_by_name}` : '') : '—'),
  },
  { key: 'rsvp_status', label: 'RSVP' },
  { key: 'status', label: 'Status' },
]
const changedFilters = [
  { key: 'change_type', label: 'Changes', options: ['Rescheduled', 'Details edited'] },
  { key: 'round_type', label: 'Rounds' },
  { key: 'job_title', label: 'Job Openings' },
]

const requestColumns = [
  { key: 'rsvp_responded_on', label: 'Requested', format: (r) => (r.rsvp_responded_on ? dayjs(r.rsvp_responded_on).format('DD MMM, h:mm A') : '') },
  { key: 'candidate_name', label: 'Candidate' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'round_type', label: 'Round', format: columns[3].format },
  { key: 'scheduled_datetime', label: 'Now scheduled', format: columns[0].format },
  { key: 'reschedule_preferences', label: 'Times suggested', sortable: false },
  { key: 'rsvp_reason', label: 'Reason', sortable: false },
]
const requestFilters = [
  { key: 'round_type', label: 'Rounds' },
  { key: 'job_title', label: 'Job Openings' },
]
const decisionDialog = reactive({ open: false, interview: null, decision: 'Accept' })
function openDecision(row, decision) {
  Object.assign(decisionDialog, { open: true, interview: row, decision })
}

const cancelledColumns = [
  { key: 'scheduled_datetime', label: 'Was scheduled for', format: (r) => (r.scheduled_datetime ? dayjs(r.scheduled_datetime).format('DD MMM YYYY, h:mm A [IST]') : '') },
  { key: 'candidate_name', label: 'Candidate' },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'round_type', label: 'Round', format: (r) => (r.round_type === 'HR Interaction' ? 'Round 1 (HR)' : r.round_type) },
  { key: 'mode', label: 'Mode', format: columns[4].format },
  { key: 'modified', label: 'Cancelled on', format: (r) => (r.modified ? dayjs(r.modified).format('DD MMM YYYY, h:mm A [IST]') : '') },
  { key: 'status', label: 'Status' },
]
const cancelledFilters = [
  { key: 'round_type', label: 'Rounds' },
  { key: 'job_title', label: 'Job Openings' },
]

// The lists of the shared table, by tab.
const LIST = {
  scheduled: { rows: activeRows, columns, filters, exportName: 'interviews', empty: 'No interviews scheduled yet' },
  final: { rows: finalRows, columns: finalColumns, filters: finalFilters, exportName: 'interviews-final', empty: 'No final interviews scheduled yet' },
  changed: { rows: changedRows, columns: changedColumns, filters: changedFilters, exportName: 'interviews-rescheduled', empty: 'No interviews have been rescheduled or edited' },
}

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

// The two lists load independently: one failing must not empty the other.
const loadErrors = ref([])
async function load() {
  loading.value = true
  const [scheduled, waiting] = await Promise.allSettled([interviewService.listInterviews(), interviewService.listToSchedule()])
  const errors = []
  // rsvp_label: Declined (older replies) reads as Withdrawn, for the RSVP filter.
  if (scheduled.status === 'fulfilled') rows.value = (scheduled.value || []).map((r) => ({ ...r, rsvp_label: rsvpLabel(r.rsvp_status) }))
  else errors.push(`Could not load scheduled interviews: ${scheduled.reason?.messages?.[0] || 'please try again.'}`)
  if (waiting.status === 'fulfilled') toSchedule.value = waiting.value || []
  else errors.push(`Could not load candidates to schedule: ${waiting.reason?.messages?.[0] || 'please try again.'}`)
  loadErrors.value = errors
  loading.value = false
}

onMounted(async () => {
  await load()
  // Candidates waiting for an answer come first; with nothing scheduled
  // yet, open on the candidates waiting for an interview.
  if (requestRows.value.length) tab.value = 'requests'
  else if (!activeRows.value.length && toSchedule.value.length) tab.value = 'to_schedule'
})
</script>
