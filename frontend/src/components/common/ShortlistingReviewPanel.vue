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

    <SectionCard title="Eligibility" icon="filter" subtitle="Step 1: sort eligible candidates, then shortlist from that pool">
      <div v-if="review.eligibility_status !== 'Pending' && !elig.changing" class="flex flex-col gap-3 text-sm">
        <div
          class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-semibold"
          :class="review.eligibility_status === 'Eligible' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'"
        >
          <FeatherIcon :name="review.eligibility_status === 'Eligible' ? 'check-circle' : 'x-circle'" class="h-4 w-4" />
          {{ review.eligibility_status }}
        </div>
        <p v-if="review.eligibility_reason" class="text-gray-700">{{ review.eligibility_reason }}</p>
        <p class="text-xs text-gray-500">
          Checked by {{ review.eligibility_checked_by }}<template v-if="review.eligibility_checked_on"> · {{ formatDateTime(review.eligibility_checked_on) }}</template>
        </p>
        <Button v-if="review.can_mark_eligibility" variant="outline" icon-left="edit-2" @click="elig.changing = true">Change</Button>
      </div>
      <div v-else-if="review.can_mark_eligibility" class="flex flex-col gap-3">
        <p class="text-sm text-gray-600">Does the candidate meet the essential qualifications and experience in the notification?</p>
        <div class="grid grid-cols-2 gap-2">
          <Button variant="solid" icon-left="check" :class="BTN_SUCCESS" :loading="elig.saving && elig.eligible" @click="markEligible(true)">Eligible</Button>
          <Button variant="solid" icon-left="x" :class="BTN_DANGER" @click="elig.reasonOpen = true">Not eligible</Button>
        </div>
        <Button v-if="elig.changing" variant="ghost" @click="elig.changing = false">Cancel</Button>
      </div>
      <p v-else class="text-sm text-gray-500">Not checked yet.</p>
    </SectionCard>

    <Dialog v-model="elig.reasonOpen" :options="{ title: 'Not eligible', size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl
            label="Reason"
            type="textarea"
            v-model="elig.reason"
            placeholder="e.g. Master's degree below 55%; less than 15 years of experience"
          />
          <p class="text-xs text-gray-500">The application moves to Not Selected. You can change this later.</p>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :class="BTN_DANGER" :loading="elig.saving" :disabled="!elig.reason.trim()" @click="markEligible(false)">
          Mark not eligible
        </Button>
      </template>
    </Dialog>

    <SectionCard title="Shortlisting Score" icon="clipboard" :subtitle="editing ? 'Score each criterion, then shortlist or reject' : 'Saved decision'">
      <template #actions>
        <span v-if="rubric && scored" class="rounded-full bg-brand-50 px-2.5 py-0.5 text-sm font-bold text-brand-700">
          {{ totalScore }} / {{ maxScore }}
        </span>
      </template>

      <div v-if="!rubric" class="text-sm text-gray-500">
        No active shortlisting rubric configured for this track.
      </div>

      <!-- No committee yet: scoring needs one -->
      <div v-else-if="!canScore" class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-3 text-sm text-orange-800">
        <div class="font-semibold">No shortlisting committee yet</div>
        <p class="mt-0.5">Scores are recorded against this job's Shortlisting Committee (2–3 members from the office order).</p>
        <Button
          v-if="review.can_create_committee"
          class="mt-3"
          variant="solid"
          icon-left="users"
          :class="BTN_BRAND"
          @click="committeeOpen = true"
        >
          Set up committee
        </Button>
        <p v-else class="mt-1 text-xs">Ask the recruiter or an administrator to set it up.</p>
      </div>

      <!-- Step 2 only for the eligible pool -->
      <div v-else-if="review.eligibility_status !== 'Eligible'" class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-3 text-sm text-gray-700">
        <div class="flex items-center gap-2 font-semibold text-gray-900">
          <FeatherIcon name="lock" class="h-4 w-4" />
          {{ review.eligibility_status === 'Not Eligible' ? 'Not eligible: not scored' : 'Check eligibility first' }}
        </div>
        <p class="mt-0.5">Shortlisting scores are given only to candidates marked eligible above.</p>
      </div>

      <!-- Saved: read-only until "Edit score" -->
      <div v-else-if="!editing" class="flex flex-col gap-4">
        <div
          class="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-semibold"
          :class="existing?.is_shortlisted ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'"
        >
          <FeatherIcon :name="existing?.is_shortlisted ? 'check-circle' : 'x-circle'" class="h-4 w-4" />
          {{ existing?.is_shortlisted ? 'Shortlisted' : 'Rejected' }}
        </div>
        <dl v-if="scored" class="flex flex-col divide-y divide-gray-100 rounded-lg border border-gray-200 text-sm">
          <div v-for="c in form.criteria" :key="c.criterion_label" class="flex items-center justify-between gap-3 px-3 py-2.5">
            <dt class="text-gray-700">{{ c.criterion_label }}</dt>
            <dd class="font-semibold text-gray-900">{{ c.score_given }} <span class="font-normal text-gray-400">/ {{ c.max_score }}</span></dd>
          </div>
        </dl>
        <div v-if="form.remarks" class="text-sm">
          <div class="text-xs text-gray-500">Remarks</div>
          <div class="mt-0.5 whitespace-pre-line text-gray-800">{{ form.remarks }}</div>
        </div>
        <Button variant="solid" icon-left="edit-2" :class="BTN_DARK" @click="startEdit">{{ scored ? 'Edit score' : 'Change decision' }}</Button>
      </div>

      <!-- Editing -->
      <div v-else class="flex flex-col gap-4">
        <p v-if="!scored" class="text-sm text-gray-600">
          Decide from the application; note the reason in the remarks (as in the shortlisting sheet).
        </p>
        <div v-if="scored" class="flex flex-col divide-y divide-gray-100 rounded-lg border border-gray-200">
          <div v-for="(criterion, i) in form.criteria" :key="criterion.criterion_label" class="flex items-center gap-3 px-3 py-2.5">
            <div class="flex-1 text-sm">
              <div class="font-medium text-gray-900">{{ criterion.criterion_label }}</div>
              <div class="text-xs text-gray-500">Out of {{ criterion.max_score }}</div>
            </div>
            <input
              type="number"
              class="w-24 rounded-md border-gray-300 px-2 py-1.5 text-right text-sm font-semibold focus:border-brand-700 focus:ring-brand-700"
              :class="overMax(criterion) && 'border-red-500 text-red-700'"
              :min="0"
              :max="criterion.max_score"
              :aria-label="criterion.criterion_label"
              v-model.number="form.criteria[i].score_given"
            />
          </div>
        </div>

        <FormControl
          label="Remarks"
          type="textarea"
          v-model="form.remarks"
          :placeholder="scored ? 'Optional notes for the committee' : 'Reason for shortlisting or not shortlisting the candidate'"
        />

        <ErrorMessage :message="formError" />
        <div class="flex flex-wrap items-center gap-2">
          <Button
            variant="solid"
            icon-left="check"
            :class="BTN_SUCCESS"
            @click="askConfirm(1)"
          >
            {{ existing ? 'Update: Shortlist' : 'Shortlist' }}
          </Button>
          <Button
            variant="solid"
            icon-left="x"
            :class="BTN_DANGER"
            @click="askConfirm(0)"
          >
            {{ existing ? 'Update: Reject' : 'Reject' }}
          </Button>
          <Button v-if="existing" variant="ghost" @click="cancelEdit">Cancel</Button>
        </div>
      </div>
    </SectionCard>

    <Dialog v-model="confirm.open" :options="{ size: 'md' }">
      <template #body>
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div
              class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full"
              :class="confirm.shortlist ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >
              <FeatherIcon :name="confirm.shortlist ? 'check' : 'x'" class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <h3 class="text-lg font-bold text-gray-900">
                {{ confirm.shortlist ? 'Shortlist' : 'Reject' }} {{ review.candidate?.full_name || 'this candidate' }}?
              </h3>
              <p class="mt-1 text-sm text-gray-600">
                <template v-if="scored">Total score <span class="font-semibold text-gray-900">{{ totalScore }} / {{ maxScore }}</span>.</template>
                <template v-if="statusWillChange">
                  The application will move to
                  <span class="font-semibold" :class="confirm.shortlist ? 'text-green-700' : 'text-red-700'">
                    {{ confirm.shortlist ? 'Shortlisted' : 'Not Selected' }}</span>.
                </template>
                <template v-else>The score is saved; the status stays {{ review.status }}.</template>
              </p>
              <p v-if="form.remarks" class="mt-2 rounded-md bg-gray-50 px-3 py-2 text-sm text-gray-700">“{{ form.remarks }}”</p>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-2">
            <Button variant="outline" @click="confirm.open = false">Cancel</Button>
            <Button
              variant="solid"
              :icon-left="confirm.shortlist ? 'check' : 'x'"
              :class="confirm.shortlist ? BTN_SUCCESS : BTN_DANGER"
              :loading="submitting"
              @click="confirmSubmit"
            >
              Confirm {{ confirm.shortlist ? 'Shortlist' : 'Reject' }}
            </Button>
          </div>
        </div>
      </template>
    </Dialog>

    <CommitteeSetupDialog v-model:open="committeeOpen" :job-opening="review.job_opening" @created="emit('committee-created')" />
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FormControl, ErrorMessage, FeatherIcon } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StatusBadge from './StatusBadge.vue'
import SectionCard from './SectionCard.vue'
import CommitteeSetupDialog from './CommitteeSetupDialog.vue'
import dayjs from 'dayjs'
import { BTN_BRAND, BTN_DANGER, BTN_DARK, BTN_SUCCESS } from '@/utils/buttonStyles'
import { scoringService } from '@/services/scoring'

const props = defineProps({
  review: { type: Object, required: true },
  rubric: { type: Object, default: null },
  // Also show candidate, CV/SOP and qualifications (when the page can't).
  showSummary: { type: Boolean, default: true },
})

const emit = defineEmits(['scored', 'committee-created'])

const canScore = computed(() => !!props.review.shortlisting_committee)

function overMax(c) {
  const score = Number(c.score_given)
  return Number.isNaN(score) || score < 0 || score > Number(c.max_score)
}

// A rubric with no criteria (e.g. Admin) is a decision with remarks, no score.
const scored = computed(() => (props.rubric?.criteria || []).length > 0 && props.rubric?.scoring_mode !== 'Pass/Fail Only')

const totalScore = computed(() => form.criteria.reduce((sum, c) => sum + (Number(c.score_given) || 0), 0))
const maxScore = computed(() => form.criteria.reduce((sum, c) => sum + (Number(c.max_score) || 0), 0))

const submitting = ref(false)
const formError = ref('')
const existing = computed(() => props.review.existing_shortlisting_score)
// Saved scores open read-only; "Edit score" switches to the inputs.
const editing = ref(!existing.value)

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

watch(
  () => [props.review, props.rubric],
  () => {
    resetForm()
    editing.value = !existing.value
  },
  { immediate: true },
)

function startEdit() {
  formError.value = ''
  editing.value = true
}

function cancelEdit() {
  resetForm()
  formError.value = ''
  editing.value = false
}

const committeeOpen = ref(false)

// ----- eligibility (step 1)
const elig = reactive({ changing: false, saving: false, eligible: false, reasonOpen: false, reason: '' })

async function markEligible(eligible) {
  elig.saving = true
  elig.eligible = eligible
  try {
    const result = await scoringService.setEligibility(props.review.name, eligible, eligible ? '' : elig.reason)
    toast({
      title: `Marked ${eligible ? 'eligible' : 'not eligible'}. Application is ${result.status}.`,
      icon: 'check',
      iconClasses: 'text-green-500',
    })
    Object.assign(elig, { changing: false, reasonOpen: false, reason: '' })
    emit('scored')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save eligibility.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    elig.saving = false
  }
}

function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A') : ''
}

// ----- confirm before a decision is saved
const confirm = reactive({ open: false, shortlist: true })
// Mirrors api.scoring.SHORTLISTING_STAGE: past it, a decision keeps the status.
const SHORTLISTING_STAGE = ['Submitted', 'Under Review', 'Shortlisted', 'Not Selected']
const statusWillChange = computed(() => {
  const target = confirm.shortlist ? 'Shortlisted' : 'Not Selected'
  return SHORTLISTING_STAGE.includes(props.review.status) && props.review.status !== target
})

function askConfirm(isShortlisted) {
  formError.value = ''
  const bad = scored.value && form.criteria.find(overMax)
  if (bad) {
    formError.value = `${bad.criterion_label}: enter a score between 0 and ${bad.max_score}.`
    return
  }
  if (!scored.value && !form.remarks.trim()) {
    formError.value = 'Add a remark: the reason for shortlisting or not shortlisting.'
    return
  }
  Object.assign(confirm, { open: true, shortlist: !!isShortlisted })
}

// Close either way: a failure shows its message in the card, under the scores.
async function confirmSubmit() {
  await submit(confirm.shortlist ? 1 : 0)
  confirm.open = false
}

async function submit(isShortlisted) {
  formError.value = 
  form.is_shortlisted = isShortlisted
  submitting.value = true
  try {
    const result = await scoringService.submitShortlistingScore({
      application: props.review.name,
      shortlisting_committee: props.review.shortlisting_committee,
      is_shortlisted: isShortlisted,
      remarks: form.remarks,
      criteria: scored.value ? form.criteria : [],
    })
    editing.value = false
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
