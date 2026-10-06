<template>
  <div class="flex flex-col gap-4">
    <div class="rounded-lg border bg-white p-4">
      <div class="mb-3 text-sm font-semibold text-gray-900">Candidate</div>
      <dl class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt class="text-gray-500">Name</dt>
          <dd class="font-medium text-gray-900">{{ review.candidate.full_name }}</dd>
        </div>
        <div>
          <dt class="text-gray-500">Email</dt>
          <dd class="font-medium text-gray-900">{{ review.candidate.email }}</dd>
        </div>
        <div v-if="review.expected_salary">
          <dt class="text-gray-500">Expected Salary</dt>
          <dd class="font-medium text-gray-900">{{ review.expected_salary }}</dd>
        </div>
        <div v-if="review.earliest_doj">
          <dt class="text-gray-500">Earliest DOJ</dt>
          <dd class="font-medium text-gray-900">{{ review.earliest_doj }}</dd>
        </div>
      </dl>
    </div>

    <div class="rounded-lg border bg-white p-4">
      <div class="mb-3 text-sm font-semibold text-gray-900">CV & SOP</div>
      <div class="flex flex-col gap-2 text-sm">
        <a
          v-if="review.resume_attachment"
          :href="review.resume_attachment"
          target="_blank"
          rel="noopener"
          class="flex items-center gap-2 text-blue-600 hover:underline"
        >
          <FeatherIcon name="file-text" class="h-4 w-4" />
          Resume / CV
        </a>
        <a
          v-if="review.sop_attachment"
          :href="review.sop_attachment"
          target="_blank"
          rel="noopener"
          class="flex items-center gap-2 text-blue-600 hover:underline"
        >
          <FeatherIcon name="file-text" class="h-4 w-4" />
          Statement of Purpose
        </a>
        <div v-if="!review.resume_attachment && !review.sop_attachment" class="text-gray-500">
          No documents uploaded.
        </div>
      </div>
    </div>

    <div v-if="review.qualifications?.length" class="rounded-lg border bg-white p-4">
      <div class="mb-3 text-sm font-semibold text-gray-900">Qualifications</div>
      <ul class="flex flex-col gap-2 text-sm">
        <li v-for="(q, i) in review.qualifications" :key="i" class="border-b pb-2 last:border-0 last:pb-0">
          <div class="font-medium text-gray-900">{{ q.degree_name }} ({{ q.degree_level }})</div>
          <div class="text-gray-600">
            {{ q.institution }} &middot; {{ q.year_of_graduation }} &middot; {{ q.percentage_or_cgpa }}
          </div>
        </li>
      </ul>
    </div>

    <div class="rounded-lg border bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <div class="text-sm font-semibold text-gray-900">Shortlisting Score</div>
        <StatusBadge v-if="alreadyScored" status="Scored" />
      </div>

      <div v-if="!rubric" class="text-sm text-gray-500">
        No active shortlisting rubric configured for this track.
      </div>
      <div v-else class="flex flex-col gap-3">
        <div v-for="(criterion, i) in form.criteria" :key="criterion.criterion_label" class="flex items-center gap-3">
          <div class="flex-1 text-sm text-gray-700">
            {{ criterion.criterion_label }}
            <span class="text-gray-400">(max {{ criterion.max_score }})</span>
          </div>
          <input
            type="number"
            class="w-24 rounded border px-2 py-1 text-sm"
            :min="0"
            :max="criterion.max_score"
            v-model.number="form.criteria[i].score_given"
          />
        </div>

        <FormControl label="Remarks" type="textarea" v-model="form.remarks" />

        <div class="flex items-center gap-3">
          <Button
            variant="solid"
            theme="green"
            :loading="submitting && form.is_shortlisted === 1"
            @click="submit(1)"
          >
            Shortlist
          </Button>
          <Button variant="outline" theme="red" :loading="submitting && form.is_shortlisted === 0" @click="submit(0)">
            Reject
          </Button>
        </div>
        <ErrorMessage :message="formError" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { Button, FormControl, ErrorMessage, FeatherIcon, toast } from 'frappe-ui'
import StatusBadge from './StatusBadge.vue'
import { scoringService } from '@/services/scoring'

const props = defineProps({
  review: { type: Object, required: true },
  rubric: { type: Object, default: null },
})

const emit = defineEmits(['scored'])

const submitting = ref(false)
const formError = ref('')
const alreadyScored = ref(!!props.review.existing_shortlisting_score)

const form = reactive({
  is_shortlisted: null,
  remarks: '',
  criteria: [],
})

function resetForm() {
  const existing = props.review.existing_shortlisting_score
  form.remarks = existing?.remarks || ''
  form.criteria = (props.rubric?.criteria || []).map((c) => {
    const existingRow = existing?.criteria?.find((r) => r.criterion_label === c.criterion_label)
    return {
      criterion_label: c.criterion_label,
      max_score: c.max_score,
      score_given: existingRow?.score_given ?? 0,
    }
  })
}

watch(() => [props.review, props.rubric], resetForm, { immediate: true })

async function submit(isShortlisted) {
  formError.value = ''
  form.is_shortlisted = isShortlisted
  submitting.value = true
  try {
    await scoringService.submitShortlistingScore({
      application: props.review.name,
      shortlisting_committee: props.review.shortlisting_committee,
      is_shortlisted: isShortlisted,
      remarks: form.remarks,
      criteria: form.criteria,
    })
    alreadyScored.value = true
    toast({ title: 'Score submitted.', icon: 'check', iconClasses: 'text-green-500' })
    emit('scored')
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not submit the score.'
  } finally {
    submitting.value = false
  }
}
</script>
