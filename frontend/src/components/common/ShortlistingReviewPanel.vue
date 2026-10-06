<template>
  <div class="flex flex-col gap-4">
    <!-- Shown only when the full submission isn't available to this
         reviewer; otherwise the page already shows all of this. -->
    <template v-if="showSummary">
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

    </template>

    <SectionCard title="Shortlisting Score" icon="clipboard" subtitle="Score each criterion, then shortlist or reject">
      <template #actions>
        <StatusBadge v-if="alreadyScored" status="Scored" />
        <span v-if="rubric" class="rounded-full bg-brand-50 px-2.5 py-0.5 text-sm font-bold text-brand-700">
          {{ totalScore }} / {{ maxScore }}
        </span>
      </template>

      <div v-if="!rubric" class="text-sm text-gray-500">
        No active shortlisting rubric configured for this track.
      </div>
      <div v-else class="flex flex-col gap-4">
        <div v-if="!review.shortlisting_committee" class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-2.5 text-sm text-orange-800">
          <div class="font-semibold">No shortlisting committee yet</div>
          <p class="mt-0.5">
            Scores are recorded against this job's Shortlisting Committee. Set one up, with its members, to start scoring.
          </p>
          <a
            v-if="session.can('Shortlisting Committee', 'create')"
            :href="`/desk/shortlisting-committee/new?job_opening=${encodeURIComponent(review.job_opening)}`"
            target="_blank"
            rel="noopener"
            class="mt-2 inline-flex items-center gap-1 font-semibold text-brand-700 hover:underline"
          >
            Set up committee <FeatherIcon name="external-link" class="h-3.5 w-3.5" />
          </a>
          <p v-else class="mt-1 text-xs">Ask the recruiter or an administrator to set it up.</p>
        </div>
        <div class="flex flex-col divide-y divide-gray-100 rounded-lg border border-gray-200">
          <div v-for="(criterion, i) in form.criteria" :key="criterion.criterion_label" class="flex items-center gap-3 px-3 py-2.5">
            <div class="flex-1 text-sm">
              <div class="font-medium text-gray-900">{{ criterion.criterion_label }}</div>
              <div class="text-xs text-gray-500">Out of {{ criterion.max_score }}</div>
            </div>
            <input
              type="number"
              class="w-24 rounded-md border-gray-300 px-2 py-1.5 text-right text-sm font-semibold focus:border-brand-700 focus:ring-brand-700"
              :min="0"
              :max="criterion.max_score"
              :aria-label="criterion.criterion_label"
              :disabled="!canScore"
              :class="overMax(criterion) && 'border-red-500 text-red-700'"
              v-model.number="form.criteria[i].score_given"
            />
          </div>
        </div>

        <FormControl label="Remarks" type="textarea" v-model="form.remarks" placeholder="Optional notes for the committee" />

        <ErrorMessage :message="formError" />
        <div class="flex flex-wrap items-center gap-3">
          <Button
            variant="solid"
            icon-left="check"
            :class="BTN_SUCCESS"
            :disabled="!canScore"
            :loading="submitting && form.is_shortlisted === 1"
            @click="submit(1)"
          >
            Shortlist
          </Button>
          <Button
            variant="solid"
            icon-left="x"
            :class="BTN_DANGER"
            :disabled="!canScore"
            :loading="submitting && form.is_shortlisted === 0"
            @click="submit(0)"
          >
            Reject
          </Button>
        </div>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, FormControl, ErrorMessage, FeatherIcon } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StatusBadge from './StatusBadge.vue'
import SectionCard from './SectionCard.vue'
import { BTN_DANGER, BTN_SUCCESS } from '@/utils/buttonStyles'
import { scoringService } from '@/services/scoring'
import { useSessionStore } from '@/stores/session'

const props = defineProps({
  review: { type: Object, required: true },
  rubric: { type: Object, default: null },
  // Also show candidate, CV/SOP and qualifications (when the page can't).
  showSummary: { type: Boolean, default: true },
})

const emit = defineEmits(['scored'])

const session = useSessionStore()
const canScore = computed(() => !!props.review.shortlisting_committee)

function overMax(c) {
  const score = Number(c.score_given)
  return Number.isNaN(score) || score < 0 || score > Number(c.max_score)
}

const totalScore = computed(() => form.criteria.reduce((sum, c) => sum + (Number(c.score_given) || 0), 0))
const maxScore = computed(() => form.criteria.reduce((sum, c) => sum + (Number(c.max_score) || 0), 0))

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
  const bad = form.criteria.find(overMax)
  if (bad) {
    formError.value = `${bad.criterion_label}: enter a score between 0 and ${bad.max_score}.`
    return
  }
  form.is_shortlisted = isShortlisted
  submitting.value = true
  try {
    const result = await scoringService.submitShortlistingScore({
      application: props.review.name,
      shortlisting_committee: props.review.shortlisting_committee,
      is_shortlisted: isShortlisted,
      remarks: form.remarks,
      criteria: form.criteria,
    })
    alreadyScored.value = true
    toast({
      title: result?.status ? `Score saved. Application is now ${result.status}.` : 'Score saved.',
      icon: 'check',
      iconClasses: 'text-green-500',
    })
    emit('scored')
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not submit the score.'
  } finally {
    submitting.value = false
  }
}
</script>
