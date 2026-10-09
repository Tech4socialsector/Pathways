<template>
  <!-- Cancel one or more scheduled interviews, with a reason and an
       optional email to each candidate. -->
  <Dialog :model-value="open" :options="{ title: list.length > 1 ? `Cancel ${list.length} interviews` : 'Cancel interview', size: 'md' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div v-if="list.length > 1" class="flex flex-col gap-4 text-sm">
        <div class="text-gray-700">
          Cancel these {{ list.length }} interviews?
          <ul class="mt-2 max-h-40 overflow-y-auto rounded-lg border bg-gray-50 px-3 py-2 text-xs">
            <li v-for="iv in list" :key="iv.name" class="flex justify-between gap-3 py-0.5">
              <span class="truncate">{{ iv.candidate_name }}</span>
              <span class="shrink-0 text-gray-500">{{ dayjs(iv.scheduled_datetime).format('DD MMM, h:mm A') }}</span>
            </li>
          </ul>
        </div>
        <FormControl label="Reason (optional)" type="textarea" v-model="form.reason" :rows="2" placeholder="e.g. The panel is not available on this date." />
        <label class="flex items-center gap-2.5">
          <input v-model="form.notify" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
          Email each candidate that the interview is cancelled
        </label>
        <EmailRecipients v-if="form.notify && open" v-model="form.cc" cancelled :job-openings="jobOpenings" :candidate-names="list.map((iv) => iv.candidate_name)" />
        <p v-if="form.error" class="whitespace-pre-line rounded-md bg-red-50 px-3 py-2 text-red-700">{{ form.error }}</p>
      </div>
      <div v-else-if="interview" class="flex flex-col gap-4 text-sm">
        <p class="text-gray-700">
          Cancel the {{ interview.round_type === 'Final' ? 'final interview' : 'Round 1 (HR) interview' }} of
          <b>{{ interview.candidate_name }}</b> on {{ dayjs(interview.scheduled_datetime).format('ddd, DD MMM YYYY, h:mm A') }}?
          <span v-if="interview.calendar_event" class="block text-xs text-gray-500">The Google Calendar event is cancelled too.</span>
        </p>
        <FormControl label="Reason (optional)" type="textarea" v-model="form.reason" :rows="2" placeholder="e.g. The panel is not available on this date." />
        <label class="flex items-center gap-2.5">
          <input v-model="form.notify" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
          Email {{ interview.candidate_name }} that the interview is cancelled
        </label>
        <EmailRecipients v-if="form.notify && open" v-model="form.cc" cancelled :job-openings="jobOpenings" :candidate-names="[interview.candidate_name]" />
        <p class="text-xs text-gray-500">To move it to another time instead, use Reschedule.</p>
        <p v-if="form.error" class="rounded-md bg-red-50 px-3 py-2 text-red-700">{{ form.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="emit('update:open', false)">{{ list.length > 1 ? 'Keep them' : 'Keep interview' }}</Button>
        <Button variant="solid" theme="red" :loading="form.saving" @click="cancel">{{ list.length > 1 ? `Cancel ${list.length} interviews` : 'Cancel interview' }}</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { Button, Dialog, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import EmailRecipients from '@/components/jobs/EmailRecipients.vue'
import { interviewService } from '@/services/interviews'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  interview: { type: Object, default: null },
  // Several at once (bulk); takes over from `interview`.
  interviews: { type: Array, default: () => [] },
})
const list = computed(() => (props.interviews.length ? props.interviews : props.interview ? [props.interview] : []))
const emit = defineEmits(['update:open', 'saved'])

const jobOpenings = computed(() => [...new Set(list.value.map((iv) => iv.job_opening).filter(Boolean))])
const form = reactive({ reason: '', notify: true, cc: [], saving: false, error: '' })
watch(
  () => props.open,
  (open) => open && Object.assign(form, { reason: '', notify: true, cc: [], error: '' }),
)

async function cancel() {
  form.saving = true
  form.error = ''
  const failed = []
  let done = 0
  try {
    for (const iv of list.value) {
      try {
        await interviewService.setStatus(iv.name, 'Cancelled', { reason: form.reason.trim(), notify: form.notify ? 1 : 0, cc: form.notify ? form.cc : [] })
        done++
      } catch (e) {
        failed.push(`${iv.candidate_name}: ${e?.messages?.[0] || 'could not cancel'}`)
      }
    }
    if (done) {
      toast({ title: done > 1 ? `${done} interviews cancelled.` : 'Interview cancelled.', icon: 'check', iconClasses: 'text-green-500' })
      emit('saved')
    }
    if (failed.length) form.error = failed.join('\n')
    else emit('update:open', false)
  } finally {
    form.saving = false
  }
}
</script>
