<template>
  <!-- Interviews > Reschedule requests: accept one of the candidate's
       preferred times, or decline and keep the current time. -->
  <Dialog :model-value="open" :options="{ size: 'lg' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body>
      <div v-if="interview" class="px-6 pb-6 pt-6 text-sm">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full" :class="accept ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
            <FeatherIcon :name="accept ? 'check' : 'x'" class="h-5 w-5" />
          </span>
          <div class="min-w-0">
            <h2 class="font-heading text-lg font-bold text-gray-900">{{ accept ? 'Accept the reschedule request' : 'Reject the reschedule request' }}</h2>
            <p class="mt-0.5 text-gray-600">
              {{ interview.candidate_name }} · {{ interview.round_type === 'Final' ? 'Final interview' : 'Round 1 (HR)' }}<template v-if="interview.job_title"> · {{ interview.job_title }}</template>
            </p>
          </div>
        </div>

        <div class="mt-4 rounded-lg bg-gray-50 px-3 py-2.5 text-gray-700">
          <div><span class="text-gray-500">Now scheduled:</span> {{ fmt(interview.scheduled_datetime) }}</div>
          <div v-if="interview.rsvp_reason" class="mt-1"><span class="text-gray-500">Candidate's reason:</span> “{{ interview.rsvp_reason }}”</div>
        </div>

        <!-- Accept: one of the suggested times -->
        <fieldset v-if="accept" class="mt-4">
          <legend class="mb-2 text-xs font-medium text-gray-700">Move the interview to <span class="text-red-600">*</span></legend>
          <div class="flex flex-col gap-2">
            <label
              v-for="t in times"
              :key="t.value"
              class="flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition"
              :class="[form.time === t.value ? 'border-brand-700 bg-brand-50' : 'border-gray-200 hover:border-gray-300', t.past && 'cursor-not-allowed opacity-50']"
            >
              <input v-model="form.time" type="radio" :value="t.value" :disabled="t.past" class="text-brand-700 focus:ring-brand-700" />
              <span class="font-medium text-gray-900">{{ t.label }}</span>
              <span v-if="t.past" class="ml-auto text-xs text-gray-500">Already passed</span>
            </label>
          </div>
          <p v-if="!times.some((t) => !t.past)" class="mt-2 text-xs text-orange-700">
            Every suggested time has passed. Close this and use Reschedule to choose another time.
          </p>
        </fieldset>

        <div class="mt-4">
          <label class="mb-1 block text-xs font-medium text-gray-700" for="decision-note">
            {{ accept ? 'Note to the candidate (optional)' : 'Reason, shown to the candidate' }}<span v-if="!accept" class="text-red-600"> *</span>
          </label>
          <textarea
            id="decision-note"
            v-model="form.note"
            rows="3"
            maxlength="1000"
            class="block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
            :class="noteError && 'border-red-500 ring-1 ring-red-500'"
            :placeholder="accept ? 'e.g. The panel is available at this time. See you then.' : 'e.g. The panel is available only on this date. We are unable to move the interview.'"
          />
          <p v-if="noteError" class="mt-1 text-xs text-red-600">{{ noteError }}</p>
          <p v-else-if="!accept" class="mt-1 text-xs text-gray-500">The interview keeps its time. The candidate is asked to confirm or withdraw, and cannot ask again for this slot.</p>
        </div>

        <label class="mt-4 flex items-center gap-2.5">
          <input v-model="form.send" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
          {{ accept ? `Email the updated invite to ${interview.candidate_name}` : `Email ${interview.candidate_name} that the request is rejected` }}
        </label>

        <p v-if="form.error" class="mt-4 flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2 text-red-700" role="alert">
          <FeatherIcon name="alert-circle" class="mt-0.5 h-4 w-4 shrink-0" />{{ form.error }}
        </p>

        <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button size="md" :disabled="form.saving" @click="emit('update:open', false)">Cancel</Button>
          <Button
            size="md"
            variant="solid"
            :theme="accept ? 'gray' : 'red'"
            :class="accept ? BTN_BRAND : ''"
            :loading="form.saving"
            @click="submit"
          >
            {{ accept ? 'Accept and reschedule' : 'Reject request' }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { preferredTimes } from '@/utils/rsvp'

const props = defineProps({
  open: { type: Boolean, default: false },
  interview: { type: Object, default: null },
  // Accept | Decline
  decision: { type: String, default: 'Accept' },
})
const emit = defineEmits(['update:open', 'decided'])

// Same limit as the server (decide_reschedule_request).
const MIN_NOTE = 10
const accept = computed(() => props.decision === 'Accept')
const fmt = (v) => dayjs(v).format('ddd, DD MMM YYYY, h:mm A [IST]')
const times = computed(() =>
  preferredTimes(props.interview).map((t) => ({ value: t, label: fmt(t), past: !dayjs(t).isAfter(dayjs()) })),
)

const form = reactive({ time: '', note: '', send: true, saving: false, error: '', attempted: false })
watch(
  () => props.open,
  (open) => {
    if (!open) return
    // The first time still to come is chosen to start with.
    Object.assign(form, { time: times.value.find((t) => !t.past)?.value || '', note: '', send: true, saving: false, error: '', attempted: false })
  },
)
const noteError = computed(() => {
  if (accept.value || !form.attempted) return ''
  const n = form.note.trim().length
  return n >= MIN_NOTE ? '' : n ? `At least ${MIN_NOTE} characters (${MIN_NOTE - n} more).` : 'Tell the candidate why the request cannot be met.'
})

async function submit() {
  form.attempted = true
  form.error = ''
  if (accept.value && !form.time) {
    form.error = 'Choose one of the times the candidate suggested.'
    return
  }
  if (noteError.value) return
  form.saving = true
  try {
    await interviewService.decideRescheduleRequest(props.interview.name, props.decision, {
      preferredTime: accept.value ? `${form.time}:00` : null,
      note: form.note.trim(),
      sendInvite: form.send,
    })
    toast({
      title: accept.value ? `Moved to ${fmt(form.time)}${form.send ? '. Updated invite queued.' : '.'}` : `Request rejected${form.send ? '; the candidate is emailed.' : '.'}`,
      icon: 'check',
      iconClasses: 'text-green-500',
    })
    emit('update:open', false)
    emit('decided')
  } catch (e) {
    form.error = e?.messages?.[0] || 'Could not save the decision. Please try again.'
  } finally {
    form.saving = false
  }
}
</script>
