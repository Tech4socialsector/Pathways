<template>
  <!-- Schedule Round 1 (HR) or Final interviews for candidates of one or
       more jobs (workflow steps 13-16). Slots run one after another. -->
  <Dialog :model-value="open" :options="{ title: candidates.length === 1 ? `Schedule interview: ${candidates[0].candidate_name}` : `Schedule interviews (${candidates.length} candidates)`, size: '2xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div class="flex flex-col gap-4 text-sm">
        <div class="flex rounded-lg bg-gray-100 p-1" role="group" aria-label="Round">
          <button
            v-for="r in ROUND_OPTIONS"
            :key="r.value"
            type="button"
            class="flex-1 rounded-md px-3 py-1.5 text-sm transition"
            :class="form.round === r.value ? 'bg-white font-semibold text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'"
            :aria-pressed="form.round === r.value"
            @click="form.round = r.value"
          >
            {{ r.label }}
          </button>
        </div>

        <!-- Final needs each job's Selection Committee -->
        <div v-if="form.round === 'Final' && missingCommittee.length" class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-2.5 text-orange-900">
          <div class="font-medium">Final interviews need a Selection Committee for:</div>
          <ul class="mt-1.5 flex flex-col gap-1.5">
            <li v-for="j in missingCommittee" :key="j.job_opening" class="flex flex-wrap items-center justify-between gap-2">
              <span>{{ j.job_title }}</span>
              <Button size="sm" variant="solid" icon-left="users" :class="BTN_BRAND" @click="openCommittee(j)">Set up committee</Button>
            </li>
          </ul>
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <FormControl label="Date" type="date" v-model="form.date" :min="today" />
          <FormControl label="First slot" type="time" v-model="form.time" />
          <FormControl label="Minutes per candidate" type="number" v-model="form.slot" :min="0" />
        </div>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <FormControl label="Mode" type="select" v-model="form.mode" :options="['Video Conference', 'In-Person']" />
          <div v-if="!inPerson" class="flex flex-col gap-1.5">
            <FormControl label="Platform" type="select" v-model="form.platform" :options="PLATFORMS" />
            <FormControl v-if="form.platform === 'Other'" v-model="form.otherPlatform" placeholder="Platform name, e.g. Webex" aria-label="Other platform" />
          </div>
          <FormControl label="Reply by" type="datetime-local" v-model="form.rsvp" />
        </div>
        <FormControl v-if="inPerson" label="Location" v-model="form.location" placeholder="e.g. Training Centre, Ground Floor, Room 004, NLSIU Bengaluru" />
        <template v-else>
          <label v-if="form.platform === 'Google Meet' && meet.ready" class="flex items-start gap-2.5 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2.5">
            <input v-model="form.createMeet" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            <span>
              <span class="font-medium text-gray-900">Create a Google Meet link for each interview</span>
              <span class="block text-xs text-gray-600">
                Adds the interview to Google Calendar and invites the candidate{{ form.round === 'Final' ? ' and the panel' : '' }}. The link goes into the invite email.
              </span>
            </span>
          </label>
          <p v-else-if="form.platform === 'Google Meet' && meet.checked" class="text-xs text-gray-500">
            To create Meet links automatically, set up Google Meet in Settings → Google Meet. For now, paste the link.
          </p>
          <FormControl v-if="!(form.platform === 'Google Meet' && meet.ready && form.createMeet)" label="Meeting link" v-model="form.link" :placeholder="LINK_HINT[form.platform] || 'https://…'" />
        </template>

        <div v-if="slots.length" class="rounded-lg border bg-gray-50 px-3 py-2">
          <div class="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">{{ slots.length === 1 ? 'Slot' : `Slots (${slots.length})` }}</div>
          <ul class="flex max-h-48 flex-col gap-0.5 overflow-y-auto">
            <li v-for="s in slots" :key="s.name" class="flex justify-between gap-3">
              <span class="min-w-0 truncate">{{ s.candidate }} <span class="text-gray-400">· {{ s.job }}</span></span>
              <span class="shrink-0 tabular-nums text-gray-600">{{ s.time }}</span>
            </li>
          </ul>
        </div>

        <label class="flex items-center gap-2.5">
          <input v-model="form.send" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
          Email the {{ form.round === 'Final' ? 'interview call letter' : 'Round 1 invite' }} to
          {{ candidates.length === 1 ? candidates[0].candidate_name : `each of the ${candidates.length} candidates` }}
        </label>
        <EmailRecipients
          v-if="form.send && open"
          v-model="form.cc"
          :round-type="form.round"
          :job-openings="jobs.map((j) => j.job_opening)"
          :candidate-names="candidates.map((c) => c.candidate_name)"
        />
        <p v-if="blocker" class="flex items-center gap-1.5 text-orange-700">
          <FeatherIcon name="info" class="h-4 w-4 shrink-0" />{{ blocker }}
        </p>
        <p v-if="form.error" class="whitespace-pre-line rounded-md bg-red-50 px-3 py-2 text-red-700">{{ form.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="emit('update:open', false)">Cancel</Button>
        <Button
          variant="solid"
          :class="BTN_BRAND"
          :loading="form.saving"
          :disabled="!!blocker"
          @click="schedule"
        >
          {{ candidates.length === 1 ? 'Schedule' : `Schedule ${candidates.length}` }}
        </Button>
      </div>
    </template>
  </Dialog>

  <SelectionCommitteeDialog
    v-model:open="committeeDialog.open"
    :job-opening="committeeDialog.job"
    :job-title="committeeDialog.title"
    @saved="onCommitteeSaved"
  />
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import EmailRecipients from '@/components/jobs/EmailRecipients.vue'
import SelectionCommitteeDialog from '@/components/jobs/SelectionCommitteeDialog.vue'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  // [{ name, candidate_name, job_opening, job_title, has_committee, committee_date?, committee_time? }]
  candidates: { type: Array, default: () => [] },
  round: { type: String, default: 'HR Interaction' },
})
const emit = defineEmits(['update:open', 'scheduled'])

const ROUND_OPTIONS = [
  { value: 'HR Interaction', label: 'Round 1 (HR interaction)' },
  { value: 'Final', label: 'Final interview' },
]
const today = dayjs().format('YYYY-MM-DD')
const form = reactive({ round: 'HR Interaction', date: '', time: '10:00', slot: 20, mode: 'Video Conference', platform: 'Microsoft Teams', otherPlatform: '', link: '', createMeet: true, location: '', rsvp: '', send: true, cc: [], saving: false, error: '' })
const inPerson = computed(() => form.mode === 'In-Person')
// Google Meet through the Google Calendar integration (Settings > Google Meet).
const meet = reactive({ ready: false, checked: false })
watch(
  () => props.open,
  async (open) => {
    if (!open || meet.checked) return
    try {
      Object.assign(meet, { ready: !!(await interviewService.getMeetStatus())?.ready, checked: true })
    } catch {
      meet.checked = true
    }
  },
)
const autoMeet = computed(() => !inPerson.value && form.platform === 'Google Meet' && meet.ready && form.createMeet)

const PLATFORMS = ['Microsoft Teams', 'Zoom', 'Google Meet', 'Other']
const LINK_HINT = {
  'Microsoft Teams': 'https://teams.microsoft.com/l/meetup-join/…',
  Zoom: 'https://zoom.us/j/…',
  'Google Meet': 'https://meet.google.com/…',
}
// Pasting a link picks its platform.
const HOSTS = [
  ['meet.google.com', 'Google Meet'],
  ['zoom.us', 'Zoom'],
  ['teams.microsoft.com', 'Microsoft Teams'],
  ['teams.live.com', 'Microsoft Teams'],
]
watch(
  () => form.link,
  (link) => {
    const hit = HOSTS.find(([host]) => (link || '').toLowerCase().includes(host))
    if (hit) form.platform = hit[1]
  },
)
const platformName = computed(() => (form.platform === 'Other' ? form.otherPlatform.trim() : form.platform))
// Why Schedule is not available yet, in plain words.
const blocker = computed(() => {
  if (!props.candidates.length) return 'Choose at least one candidate.'
  if (!form.date) return 'Choose the interview date.'
  if (!form.time) return 'Choose the time of the first slot.'
  if (dayjs(`${form.date} ${form.time}`).isBefore(dayjs())) return 'The first slot is in the past. Choose a later date or time.'
  if (inPerson.value && !form.location.trim()) return 'Enter the location of the in-person interview.'
  if (!inPerson.value && form.platform === 'Other' && !form.otherPlatform.trim()) return 'Enter the name of the meeting platform.'
  if (form.round === 'Final' && missingCommittee.value.length) return 'Set up the Selection Committee for the job(s) above first.'
  return ''
})
// Committees set up from this dialog.
const committeeAdded = ref(new Set())

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const first = props.candidates.find((c) => c.committee_date)
    Object.assign(form, {
      round: props.round,
      error: '',
      send: true,
      cc: [],
      slot: props.round === 'Final' ? 30 : 20,
      // Default to tomorrow, so the form is never left without a date.
      date: props.round === 'Final' && first?.committee_date ? first.committee_date : form.date || dayjs().add(1, 'day').format('YYYY-MM-DD'),
      time: props.round === 'Final' && first?.committee_time ? first.committee_time.slice(0, 5) : form.time,
    })
    committeeAdded.value = new Set()
  },
)
watch(() => form.round, (r) => (form.slot = r === 'Final' ? 30 : 20))

const jobs = computed(() => {
  const map = new Map()
  for (const c of props.candidates) {
    if (!map.has(c.job_opening)) map.set(c.job_opening, { job_opening: c.job_opening, job_title: c.job_title, has_committee: c.has_committee, names: [] })
    map.get(c.job_opening).names.push(c.name)
  }
  return [...map.values()]
})
const missingCommittee = computed(() => jobs.value.filter((j) => !j.has_committee && !committeeAdded.value.has(j.job_opening)))

// One timeline across all the chosen candidates, in the order given.
const slots = computed(() => {
  if (!form.date || !form.time) return []
  const start = dayjs(`${form.date} ${form.time}`)
  return props.candidates.map((c, i) => ({
    name: c.name,
    candidate: c.candidate_name,
    job: c.job_title,
    time: start.add(Number(form.slot || 0) * i, 'minute').format('DD MMM, h:mm A'),
  }))
})

const committeeDialog = reactive({ open: false, job: '', title: '' })
function openCommittee(j) {
  Object.assign(committeeDialog, { open: true, job: j.job_opening, title: j.job_title })
}
function onCommitteeSaved() {
  committeeAdded.value = new Set([...committeeAdded.value, committeeDialog.job])
}

async function schedule() {
  form.saving = true
  form.error = ''
  const start = dayjs(`${form.date} ${form.time}`)
  const step = Number(form.slot || 0)
  let index = 0
  let done = 0
  const problems = []
  for (const j of jobs.value) {
    const order = props.candidates.filter((c) => c.job_opening === j.job_opening).map((c) => c.name)
    const firstIndex = props.candidates.findIndex((c) => c.job_opening === j.job_opening)
    try {
      const r = await interviewService.scheduleInterviews({
        job_opening: j.job_opening,
        applications: order,
        round_type: form.round,
        start: start.add(step * firstIndex, 'minute').format('YYYY-MM-DD HH:mm:ss'),
        slot_minutes: step,
        mode: form.mode,
        meeting_link: inPerson.value || autoMeet.value ? '' : form.link,
        create_meet: autoMeet.value ? 1 : 0,
        location: inPerson.value ? form.location : '',
        meeting_platform: inPerson.value ? '' : platformName.value,
        rsvp_deadline: form.rsvp ? form.rsvp.replace('T', ' ') + ':00' : null,
        send_invite: form.send ? 1 : 0,
        cc: JSON.stringify(form.send ? form.cc : []),
      })
      done += r.scheduled
    } catch (e) {
      problems.push(`${j.job_title}: ${e?.messages?.[0] || 'could not be scheduled'}`)
    }
    index += order.length
  }
  form.saving = false
  if (done) {
    toast({ title: `${done} interview${done === 1 ? '' : 's'} scheduled${form.send ? ', invites queued' : ''}.`, icon: 'check', iconClasses: 'text-green-500' })
    emit('scheduled')
  }
  if (problems.length) {
    form.error = problems.join('\n')
  } else {
    emit('update:open', false)
  }
}
</script>
