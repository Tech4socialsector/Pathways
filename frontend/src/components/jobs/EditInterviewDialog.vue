<template>
  <!-- Reschedule or edit one scheduled interview: time, mode, platform,
       link or venue. The candidate can be sent an updated invite. -->
  <Dialog :model-value="open" :options="{ title: `Reschedule / edit: ${interview?.candidate_name || ''}`, size: 'xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div v-if="interview" class="flex flex-col gap-4 text-sm">
        <div class="rounded-lg bg-gray-50 px-3 py-2 text-gray-700">
          {{ interview.round_type === 'Final' ? 'Final interview' : 'Round 1 (HR interaction)' }}<template v-if="interview.job_title"> · {{ interview.job_title }}</template>
          <div class="text-xs text-gray-500">Currently {{ dayjs(interview.scheduled_datetime).format('ddd, DD MMM YYYY, h:mm A') }}</div>
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <FormControl label="Date" type="date" v-model="form.date" :min="today" />
          <FormControl label="Time" type="time" v-model="form.time" />
          <FormControl label="Minutes" type="number" v-model="form.minutes" :min="5" />
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
          <p v-if="interview.calendar_event && form.platform === 'Google Meet'" class="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-xs text-gray-700">
            This interview has a Google Calendar event. Its time is updated and the Meet link stays the same.
          </p>
          <label v-else-if="form.platform === 'Google Meet' && meet.ready" class="flex items-start gap-2.5 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2.5">
            <input v-model="form.createMeet" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            <span class="font-medium text-gray-900">Create a Google Meet link</span>
          </label>
          <FormControl v-if="!usesMeetEvent" label="Meeting link" v-model="form.link" placeholder="https://…" />
        </template>

        <FormControl label="Note to the candidate (optional)" type="textarea" v-model="form.note" :rows="2" placeholder="e.g. The interview has been moved because of a panel member's availability." />
        <label class="flex items-center gap-2.5">
          <input v-model="form.send" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
          Email the updated invite to {{ interview.candidate_name }}
        </label>
        <EmailRecipients
          v-if="form.send && open"
          v-model="form.cc"
          :round-type="interview.round_type"
          :job-openings="interview.job_opening ? [interview.job_opening] : []"
          :candidate-names="[interview.candidate_name]"
        />
        <p v-if="timeChanged" class="flex items-center gap-1.5 text-xs text-gray-600">
          <FeatherIcon name="info" class="h-3.5 w-3.5 shrink-0" />The interview will be marked Rescheduled and the candidate asked to confirm again.
        </p>
        <p v-if="blocker" class="flex items-center gap-1.5 text-orange-700"><FeatherIcon name="info" class="h-4 w-4 shrink-0" />{{ blocker }}</p>
        <p v-if="form.error" class="rounded-md bg-red-50 px-3 py-2 text-red-700">{{ form.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="emit('update:open', false)">Close</Button>
        <Button variant="solid" :class="BTN_BRAND" :loading="form.saving" :disabled="!!blocker" @click="save">
          {{ timeChanged ? 'Reschedule' : 'Save changes' }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import EmailRecipients from '@/components/jobs/EmailRecipients.vue'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  // { name, candidate_name, job_title, round_type, scheduled_datetime, mode, meeting_platform, meeting_link, location, calendar_event }
  interview: { type: Object, default: null },
})
const emit = defineEmits(['update:open', 'saved'])

const PLATFORMS = ['Microsoft Teams', 'Zoom', 'Google Meet', 'Other']
const today = dayjs().format('YYYY-MM-DD')
const form = reactive({ date: '', time: '', minutes: 30, mode: 'Video Conference', platform: 'Microsoft Teams', otherPlatform: '', link: '', location: '', createMeet: false, rsvp: '', note: '', send: true, cc: [], saving: false, error: '' })
const meet = reactive({ ready: false, checked: false })
const inPerson = computed(() => form.mode === 'In-Person')
const usesMeetEvent = computed(() => form.platform === 'Google Meet' && (!!props.interview?.calendar_event || (meet.ready && form.createMeet)))

watch(
  () => props.open,
  async (open) => {
    const iv = props.interview
    if (!open || !iv) return
    const at = dayjs(iv.scheduled_datetime)
    const known = PLATFORMS.includes(iv.meeting_platform)
    Object.assign(form, {
      date: at.format('YYYY-MM-DD'),
      time: at.format('HH:mm'),
      minutes: iv.round_type === 'Final' ? 30 : 20,
      mode: iv.mode || 'Video Conference',
      platform: iv.meeting_platform ? (known ? iv.meeting_platform : 'Other') : 'Microsoft Teams',
      otherPlatform: known ? '' : iv.meeting_platform || '',
      link: iv.meeting_link || '',
      location: iv.location || '',
      createMeet: false,
      rsvp: '',
      note: '',
      send: true,
      cc: [],
      error: '',
    })
    if (!meet.checked) {
      try {
        meet.ready = !!(await interviewService.getMeetStatus())?.ready
      } catch {
        /* Meet stays off */
      }
      meet.checked = true
    }
  },
)

const start = computed(() => (form.date && form.time ? dayjs(`${form.date} ${form.time}`) : null))
const timeChanged = computed(() => !!start.value && !!props.interview && !start.value.isSame(dayjs(props.interview.scheduled_datetime), 'minute'))
const platformName = computed(() => (form.platform === 'Other' ? form.otherPlatform.trim() : form.platform))
const blocker = computed(() => {
  if (!start.value) return 'Choose the date and time.'
  if (timeChanged.value && start.value.isBefore(dayjs())) return 'The new time is in the past.'
  if (inPerson.value && !form.location.trim()) return 'Enter the location of the in-person interview.'
  if (!inPerson.value && form.platform === 'Other' && !form.otherPlatform.trim()) return 'Enter the name of the meeting platform.'
  return ''
})

async function save() {
  form.saving = true
  form.error = ''
  try {
    await interviewService.updateInterview({
      interview: props.interview.name,
      start: start.value.format('YYYY-MM-DD HH:mm:ss'),
      minutes: Number(form.minutes) || 30,
      mode: form.mode,
      meeting_platform: inPerson.value ? '' : platformName.value,
      meeting_link: inPerson.value || usesMeetEvent.value ? '' : form.link.trim(),
      location: inPerson.value ? form.location.trim() : '',
      create_meet: !inPerson.value && form.platform === 'Google Meet' && meet.ready && form.createMeet ? 1 : 0,
      rsvp_deadline: form.rsvp ? dayjs(form.rsvp).format('YYYY-MM-DD HH:mm:ss') : null,
      send_invite: form.send ? 1 : 0,
      cc: JSON.stringify(form.send ? form.cc : []),
      note: form.note.trim(),
    })
    toast({ title: timeChanged.value ? 'Interview rescheduled.' : 'Interview updated.', icon: 'check', iconClasses: 'text-green-500' })
    emit('update:open', false)
    emit('saved')
  } catch (e) {
    form.error = e?.messages?.[0] || 'Could not update the interview.'
  } finally {
    form.saving = false
  }
}
</script>
