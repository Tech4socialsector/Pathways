<template>
  <!-- Candidate portal: one upcoming interview and the candidate's reply —
       Confirm, Request reschedule (reason + preferred times) or Withdraw. -->
  <section
    :id="'interview-' + interview.name"
    class="mb-6 scroll-mt-20 overflow-hidden rounded-xl border-2 bg-white shadow-sm transition"
    :class="[STATE[state].border, highlighted ? 'ring-4 ring-brand-200' : '']"
  >
    <div class="flex flex-wrap items-center justify-between gap-2 px-5 py-3" :class="STATE[state].header">
      <span class="flex items-center gap-2 text-sm font-semibold">
        <FeatherIcon :name="STATE[state].icon" class="h-4 w-4" />{{ STATE[state].title }}
      </span>
      <span class="text-xs opacity-80">{{ roundLabel }}</span>
    </div>

    <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
      <!-- When and where -->
      <div class="flex items-start gap-4">
        <div class="flex w-16 shrink-0 flex-col items-center rounded-lg border bg-brand-50 py-2 text-brand-800">
          <span class="text-[11px] font-semibold uppercase">{{ at.format('MMM') }}</span>
          <span class="text-2xl font-bold leading-none">{{ at.format('D') }}</span>
          <span class="text-[11px]">{{ at.format('ddd') }}</span>
        </div>
        <div class="min-w-0 text-sm">
          <div class="text-lg font-semibold text-gray-900" :class="state === 'Withdrawn' && 'text-gray-500 line-through'">{{ at.format('dddd, DD MMMM YYYY') }}</div>
          <div class="mt-0.5 text-gray-700">{{ at.format('h:mm A [IST]') }} · {{ interview.mode === 'In-Person' ? 'In person' : 'Online' }}</div>
          <div v-if="interview.location" class="mt-1 flex items-center gap-1.5 text-gray-700">
            <FeatherIcon name="map-pin" class="h-4 w-4 text-gray-400" />{{ interview.location }}
          </div>
          <a
            v-if="interview.meeting_link && state !== 'Withdrawn'"
            :href="interview.meeting_link"
            target="_blank"
            rel="noopener"
            class="mt-2 inline-flex items-center gap-1.5 rounded-md border border-brand-200 px-3 py-1.5 font-medium text-brand-700 hover:bg-brand-50"
          >
            <FeatherIcon name="video" class="h-4 w-4" />Join {{ interview.meeting_platform || 'meeting' }}
          </a>
        </div>
      </div>

      <!-- The reply -->
      <div class="flex flex-col gap-2 md:w-72">
        <template v-if="state === 'Pending'">
          <span class="text-sm font-medium text-gray-700">Will you attend this interview?</span>
          <template v-if="canReply">
            <Button size="md" variant="solid" icon-left="check" :class="BTN_BRAND" @click="openReply('Confirmed')">Confirm attendance</Button>
            <Button size="md" variant="outline" icon-left="calendar" @click="openReply('Reschedule Requested')">Request reschedule</Button>
            <button type="button" class="mt-0.5 text-sm font-medium text-red-700 hover:underline" @click="openReply('Withdrawn')">Withdraw from interview</button>
          </template>
        </template>

        <template v-else-if="state === 'Confirmed'">
          <p class="flex items-center gap-2 text-sm font-medium text-green-700">
            <FeatherIcon name="check-circle" class="h-5 w-5" />You confirmed. See you then.
          </p>
          <p v-if="interview.rsvp_responded_on" class="text-xs text-gray-500">Replied {{ fmt(interview.rsvp_responded_on) }}</p>
          <div v-if="canReply" class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
            <button type="button" class="font-medium text-brand-700 hover:underline" @click="openReply('Reschedule Requested')">Need another time?</button>
            <button type="button" class="font-medium text-red-700 hover:underline" @click="openReply('Withdrawn')">Withdraw</button>
          </div>
        </template>

        <template v-else-if="state === 'Reschedule Requested'">
          <p class="text-sm text-gray-700">
            You asked for another time<template v-if="interview.rsvp_responded_on"> on {{ fmt(interview.rsvp_responded_on) }}</template>.
            The recruitment team will email you the new time; until then this slot stays booked.
          </p>
          <div v-if="preferences.length" class="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            <div class="font-semibold">Times you suggested</div>
            <ul class="mt-1 list-inside list-disc">
              <li v-for="p in preferences" :key="p">{{ p }}</li>
            </ul>
          </div>
          <button v-if="canReply" type="button" class="self-start text-sm font-medium text-red-700 hover:underline" @click="openReply('Withdrawn')">Withdraw instead</button>
        </template>

        <template v-else>
          <p class="text-sm text-gray-700">You withdrew from this interview<template v-if="interview.rsvp_responded_on"> on {{ fmt(interview.rsvp_responded_on) }}</template>.</p>
          <p class="text-xs text-gray-500">If this was a mistake, please write to the recruitment team.</p>
        </template>
      </div>
    </div>
  </section>

  <!-- Confirm / Reschedule / Withdraw -->
  <Dialog v-model="reply.open" :options="{ size: reply.response === 'Reschedule Requested' ? 'lg' : 'md' }">
    <template #body>
      <div class="px-6 pb-6 pt-6">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full" :class="DIALOG[reply.response].tone">
            <FeatherIcon :name="DIALOG[reply.response].icon" class="h-5 w-5" />
          </span>
          <div class="min-w-0">
            <h2 class="font-heading text-lg font-bold text-gray-900">{{ DIALOG[reply.response].title }}</h2>
            <p class="mt-0.5 text-sm text-gray-600">{{ roundLabel }} · {{ at.format('ddd, DD MMM YYYY [at] h:mm A [IST]') }}</p>
          </div>
        </div>

        <div class="mt-5 flex flex-col gap-4 text-sm">
          <p v-if="reply.response === 'Confirmed'" class="text-gray-700">
            The recruitment team will be told that you will attend.
            <template v-if="interview.mode !== 'In-Person'">Please join a few minutes early using the link on this page.</template>
          </p>

          <template v-else-if="reply.response === 'Reschedule Requested'">
            <p class="text-gray-700">
              Tell us why, and give up to {{ MAX_SLOTS }} times in the next {{ WINDOW_DAYS }} days that suit you. The recruitment team
              will try to match one and email you the new time. Your current slot stays booked until then.
            </p>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-700" for="reschedule-reason">Reason <span class="text-red-600">*</span></label>
              <textarea
                id="reschedule-reason"
                v-model="reply.reason"
                rows="3"
                :maxlength="MAX_REASON"
                class="block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
                placeholder="e.g. I have a university examination at that time."
              />
              <div class="mt-1 flex justify-between text-xs" :class="reasonTooShort ? 'text-red-600' : 'text-gray-500'">
                <span>{{ reasonTooShort ? `At least ${MIN_REASON} characters.` : '' }}</span>
                <span>{{ reply.reason.length }}/{{ MAX_REASON }}</span>
              </div>
            </div>
            <div>
              <div class="mb-1 text-xs font-medium text-gray-700">Times that suit you (IST) <span class="text-red-600">*</span></div>
              <div v-for="(slot, i) in reply.slots" :key="i" class="mb-2 flex items-center gap-2">
                <span class="w-5 shrink-0 text-right text-xs tabular-nums text-gray-500">{{ i + 1 }}.</span>
                <input
                  v-model="reply.slots[i]"
                  type="datetime-local"
                  :min="minSlot"
                  :max="maxSlot"
                  class="block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
                  :class="slotErrors[i] && 'border-red-500 ring-1 ring-red-500'"
                  :aria-label="`Preferred time ${i + 1}`"
                />
                <Button v-if="reply.slots.length > 1" variant="ghost" icon="x" :aria-label="`Remove time ${i + 1}`" @click="reply.slots.splice(i, 1)" />
              </div>
              <p v-for="(e, i) in slotErrors" v-show="e" :key="'e' + i" class="-mt-1 mb-1 pl-7 text-xs text-red-600">{{ e }}</p>
              <Button v-if="reply.slots.length < MAX_SLOTS" size="sm" variant="ghost" icon-left="plus" @click="reply.slots.push('')">Add another time</Button>
            </div>
          </template>

          <template v-else>
            <p class="rounded-lg bg-red-50 px-3 py-2.5 text-red-800">
              You will not be interviewed at this time, and this cannot be undone from the portal. If you only need a different time,
              use <b>Request reschedule</b> instead.
            </p>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-700" for="withdraw-reason">Reason (optional)</label>
              <textarea
                id="withdraw-reason"
                v-model="reply.reason"
                rows="3"
                :maxlength="MAX_REASON"
                class="block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
                placeholder="e.g. I have accepted another offer."
              />
            </div>
          </template>

          <p v-if="reply.error" class="flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2 text-red-700" role="alert">
            <FeatherIcon name="alert-circle" class="mt-0.5 h-4 w-4 shrink-0" />{{ reply.error }}
          </p>
        </div>

        <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button size="md" :disabled="reply.sending" @click="reply.open = false">Cancel</Button>
          <Button
            size="md"
            variant="solid"
            :theme="reply.response === 'Withdrawn' ? 'red' : 'gray'"
            :class="reply.response === 'Withdrawn' ? '' : BTN_BRAND"
            :loading="reply.sending"
            :disabled="!canSend"
            @click="send"
          >
            {{ DIALOG[reply.response].action }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  interview: { type: Object, required: true },
  highlighted: { type: Boolean, default: false },
  // Staff opening a candidate's page see the card but cannot reply.
  canReply: { type: Boolean, default: true },
})
const emit = defineEmits(['replied'])

// Same limits as the server (pathways.api.interviews.respond_rsvp).
const MAX_SLOTS = 3
const WINDOW_DAYS = 60
const MIN_REASON = 10
const MAX_REASON = 1000

const STATE = {
  Pending: { title: 'Action needed: please reply to your interview', icon: 'bell', header: 'bg-brand-700 text-white', border: 'border-brand-700' },
  Confirmed: { title: 'Interview confirmed', icon: 'check-circle', header: 'bg-green-700 text-white', border: 'border-green-300' },
  'Reschedule Requested': { title: 'Reschedule requested', icon: 'clock', header: 'bg-amber-500 text-white', border: 'border-amber-300' },
  Withdrawn: { title: 'You withdrew from this interview', icon: 'slash', header: 'bg-gray-500 text-white', border: 'border-gray-200' },
}
const DIALOG = {
  Confirmed: { title: 'Confirm your attendance?', action: 'Yes, I will attend', icon: 'check', tone: 'bg-green-50 text-green-700' },
  'Reschedule Requested': { title: 'Request a different time', action: 'Send request', icon: 'calendar', tone: 'bg-amber-50 text-amber-700' },
  Withdrawn: { title: 'Withdraw from this interview?', action: 'Withdraw', icon: 'alert-triangle', tone: 'bg-red-50 text-red-700' },
}

// Older replies say Declined; it now reads as Withdrawn.
const state = computed(() => {
  const s = props.interview.rsvp_status || 'Pending'
  return s === 'Declined' ? 'Withdrawn' : STATE[s] ? s : 'Pending'
})
const at = computed(() => dayjs(props.interview.scheduled_datetime))
const roundLabel = computed(() => (props.interview.round_type === 'HR Interaction' ? 'Round 1 · HR interaction' : 'Final interview'))
const preferences = computed(() =>
  (props.interview.reschedule_preferences || '').split('\n').filter(Boolean).map((p) => dayjs(p).format('ddd, DD MMM YYYY, h:mm A [IST]')),
)
const fmt = (v) => dayjs(v).format('DD MMM YYYY, h:mm A')

const reply = reactive({ open: false, response: 'Confirmed', reason: '', slots: [''], sending: false, error: '' })
function openReply(response) {
  Object.assign(reply, { open: true, response, reason: '', slots: [''], sending: false, error: '' })
}
defineExpose({ openReply })

const minSlot = computed(() => dayjs().add(1, 'hour').startOf('hour').format('YYYY-MM-DDTHH:mm'))
const maxSlot = computed(() => dayjs().add(WINDOW_DAYS, 'day').format('YYYY-MM-DDTHH:mm'))
const reasonTooShort = computed(() => reply.reason.trim().length > 0 && reply.reason.trim().length < MIN_REASON)
// One message per filled slot that the server would refuse.
const slotErrors = computed(() => {
  const now = dayjs()
  const seen = new Set()
  return reply.slots.map((s) => {
    if (!s) return ''
    const t = dayjs(s)
    if (!t.isValid()) return 'Not a valid date and time.'
    if (!t.isAfter(now)) return 'This time is in the past.'
    if (t.isAfter(now.add(WINDOW_DAYS, 'day'))) return `Choose a time within the next ${WINDOW_DAYS} days.`
    if (t.isSame(at.value, 'minute')) return 'This is the time already scheduled.'
    const key = t.format('YYYY-MM-DD HH:mm')
    if (seen.has(key)) return 'You gave this time twice.'
    seen.add(key)
    return ''
  })
})
const canSend = computed(() => {
  if (reply.response !== 'Reschedule Requested') return true
  return reply.reason.trim().length >= MIN_REASON && reply.slots.some(Boolean) && !slotErrors.value.some(Boolean)
})

async function send() {
  if (!canSend.value) return
  reply.sending = true
  reply.error = ''
  try {
    const result = await interviewService.respondRsvp(props.interview.name, reply.response, {
      reason: reply.reason.trim(),
      preferredSlots: reply.response === 'Reschedule Requested' ? reply.slots.filter(Boolean).map((s) => dayjs(s).format('YYYY-MM-DD HH:mm:00')) : [],
    })
    emit('replied', result)
    reply.open = false
    toast({
      title: {
        Confirmed: 'Thank you. Your attendance is confirmed.',
        'Reschedule Requested': 'Request sent. The recruitment team will email you a new time.',
        Withdrawn: 'You have withdrawn from this interview.',
      }[reply.response],
      icon: 'check',
      iconClasses: 'text-green-500',
    })
  } catch (e) {
    reply.error = e?.messages?.[0] || 'Could not send your reply. Please try again.'
  } finally {
    reply.sending = false
  }
}
</script>
