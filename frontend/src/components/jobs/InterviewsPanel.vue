<template>
  <!-- Workflow steps 13-16: shortlisted candidates, their Round 1 (HR
       interaction) and Final interviews, invites and RSVPs. -->
  <SectionCard title="Interviews" icon="calendar" :subtitle="subtitle">
    <div v-if="!data" class="text-sm text-gray-500">Loading…</div>
    <div v-else-if="!data.candidates.length" class="rounded-lg border border-dashed px-4 py-6 text-center text-sm text-gray-500">
      No shortlisted candidates yet. Candidates appear here once they are shortlisted.
    </div>
    <template v-else>
      <!-- Actions for the ticked candidates -->
      <div v-if="data.can_manage" class="mb-3 flex flex-wrap items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm">
        <span class="text-gray-600">{{ selected.length ? `${selected.length} selected` : 'Tick candidates to schedule them' }}</span>
        <div class="ml-auto flex flex-wrap gap-2">
          <Button size="sm" variant="outline" icon-left="phone" :disabled="!selected.length" @click="openSchedule('HR Interaction')">Schedule Round 1 (HR)</Button>
          <Button
            size="sm"
            variant="solid"
            icon-left="calendar"
            :class="BTN_BRAND"
            :disabled="!selected.length || !data.committee"
            :title="!data.committee ? 'Set up the Selection Committee first' : ''"
            @click="openSchedule('Final')"
          >
            Schedule Final
          </Button>
        </div>
      </div>
      <p v-if="data.can_manage && !data.committee" class="mb-3 text-xs text-orange-700">Set up the Selection Committee (right) before scheduling final interviews.</p>

      <div class="overflow-x-auto rounded-lg border">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th v-if="data.can_manage" class="w-10 px-3 py-2">
                <input
                  type="checkbox"
                  class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                  :checked="selected.length === data.candidates.length"
                  :indeterminate.prop="selected.length > 0 && selected.length < data.candidates.length"
                  aria-label="Select all candidates"
                  @change="selected = $event.target.checked ? data.candidates.map((c) => c.name) : []"
                />
              </th>
              <th class="px-3 py-2 font-medium">Candidate</th>
              <th class="px-3 py-2 font-medium">Round 1 (HR)</th>
              <th class="px-3 py-2 font-medium">Final</th>
              <th class="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="c in data.candidates" :key="c.name" class="align-top">
              <td v-if="data.can_manage" class="px-3 py-3">
                <input v-model="selected" type="checkbox" :value="c.name" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" :aria-label="`Select ${c.candidate_name}`" />
              </td>
              <td class="px-3 py-3">
                <router-link :to="`/applications/${c.name}`" class="font-medium text-gray-900 hover:text-brand-700 hover:underline">{{ c.candidate_name }}</router-link>
                <div class="font-mono text-xs text-gray-500">{{ c.application_id }}</div>
              </td>
              <td v-for="round in ROUNDS" :key="round" class="px-3 py-3">
                <template v-if="c.rounds[round]">
                  <div class="whitespace-nowrap text-gray-900">{{ dayjs(c.rounds[round].scheduled_datetime).format('DD MMM, h:mm A') }}</div>
                  <div class="mt-1 flex flex-wrap items-center gap-1">
                    <span class="rounded-full px-2 py-0.5 text-[11px] font-medium" :class="STATUS_TONE[c.rounds[round].status] || 'bg-gray-100 text-gray-700'">
                      {{ c.rounds[round].status }}
                    </span>
                    <span
                      v-if="['Scheduled', 'Rescheduled'].includes(c.rounds[round].status)"
                      class="rounded-full px-2 py-0.5 text-[11px] font-medium"
                      :class="RSVP_TONE[c.rounds[round].rsvp_status || 'Pending']"
                    >
                      RSVP: {{ c.rounds[round].rsvp_status || 'Pending' }}
                    </span>
                    <Dropdown v-if="data.can_manage" :options="roundMenu(c.rounds[round])" placement="left">
                      <button type="button" class="rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700" :aria-label="`${round} actions`">
                        <FeatherIcon name="more-horizontal" class="h-4 w-4" />
                      </button>
                    </Dropdown>
                  </div>
                  <div v-if="c.rounds[round].location" class="mt-1 flex items-center gap-1 text-xs text-gray-600">
                    <FeatherIcon name="map-pin" class="h-3 w-3" />{{ c.rounds[round].location }}
                  </div>
                  <a v-if="c.rounds[round].meeting_link" :href="c.rounds[round].meeting_link" target="_blank" rel="noopener" class="mt-1 block text-xs text-brand-700 hover:underline">{{ c.rounds[round].meeting_platform || 'Meeting' }} link</a>
                </template>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-3 py-3"><StatusBadge :status="c.status" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <ScheduleInterviewDialog v-model:open="scheduleOpen" :candidates="scheduleCandidates" :round="scheduleRound" @scheduled="onScheduled" />
  </SectionCard>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dropdown, FeatherIcon } from 'frappe-ui'
import ScheduleInterviewDialog from '@/components/jobs/ScheduleInterviewDialog.vue'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  jobOpening: { type: String, required: true },
  jobTitle: { type: String, default: '' },
  // pathways.api.interviews.get_job_interviews, loaded by the parent
  data: { type: Object, default: null },
})
const emit = defineEmits(['changed'])

const ROUNDS = ['HR Interaction', 'Final']
const STATUS_TONE = {
  Scheduled: 'bg-blue-50 text-blue-700',
  Rescheduled: 'bg-blue-50 text-blue-700',
  Completed: 'bg-green-50 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}
const RSVP_TONE = {
  Pending: 'bg-orange-50 text-orange-700',
  Confirmed: 'bg-green-50 text-green-700',
  Declined: 'bg-red-50 text-red-700',
}

const selected = ref([])
watch(
  () => props.data,
  (d) => {
    const names = new Set((d?.candidates || []).map((c) => c.name))
    selected.value = selected.value.filter((n) => names.has(n))
  },
)

const subtitle = computed(() => {
  const list = props.data?.candidates || []
  if (!list.length) return ''
  const scheduled = list.filter((c) => Object.values(c.rounds).some((r) => r && ['Scheduled', 'Rescheduled'].includes(r.status))).length
  return `${list.length} shortlisted · ${scheduled} with an interview scheduled`
})

// ----- schedule dialog (shared with the Interviews page)
const scheduleOpen = ref(false)
const scheduleRound = ref('Final')
const scheduleCandidates = computed(() => {
  const c = props.data?.committee
  return (props.data?.candidates || [])
    .filter((x) => selected.value.includes(x.name))
    .map((x) => ({
      name: x.name,
      candidate_name: x.candidate_name,
      job_opening: props.jobOpening,
      job_title: props.jobTitle,
      has_committee: !!c,
      committee_date: c?.scheduled_date,
      committee_time: c?.scheduled_time,
    }))
})
function openSchedule(round) {
  scheduleRound.value = round
  scheduleOpen.value = true
}
function onScheduled() {
  selected.value = []
  emit('changed')
}

// ----- per-interview actions
function roundMenu(iv) {
  const open = ['Scheduled', 'Rescheduled'].includes(iv.status)
  const items = []
  if (open) {
    items.push({ label: 'Resend invite', icon: 'send', onClick: () => act(() => interviewService.resendInvite(iv.name), 'Invite queued.') })
    items.push({ label: 'Mark completed', icon: 'check', onClick: () => act(() => interviewService.setStatus(iv.name, 'Completed'), 'Marked completed.') })
    items.push({ label: 'Cancel interview', icon: 'x', onClick: () => act(() => interviewService.setStatus(iv.name, 'Cancelled'), 'Interview cancelled.') })
  }
  return [{ group: 'Interview', hideLabel: true, items: items.length ? items : [{ label: `No actions (${iv.status})`, disabled: true }] }]
}

async function act(fn, message) {
  try {
    await fn()
    toast({ title: message, icon: 'check', iconClasses: 'text-green-500' })
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'That did not work.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}
</script>
