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

    <SectionCard title="Shortlisting Score" icon="clipboard" :subtitle="editing ? 'Score each criterion, then shortlist or reject' : 'Saved decision'">
      <template #actions>
        <span v-if="rubric" class="rounded-full bg-brand-50 px-2.5 py-0.5 text-sm font-bold text-brand-700">
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
          @click="openCommitteeDialog"
        >
          Set up committee
        </Button>
        <p v-else class="mt-1 text-xs">Ask the recruiter or an administrator to set it up.</p>
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
        <dl class="flex flex-col divide-y divide-gray-100 rounded-lg border border-gray-200 text-sm">
          <div v-for="c in form.criteria" :key="c.criterion_label" class="flex items-center justify-between gap-3 px-3 py-2.5">
            <dt class="text-gray-700">{{ c.criterion_label }}</dt>
            <dd class="font-semibold text-gray-900">{{ c.score_given }} <span class="font-normal text-gray-400">/ {{ c.max_score }}</span></dd>
          </div>
        </dl>
        <div v-if="form.remarks" class="text-sm">
          <div class="text-xs text-gray-500">Remarks</div>
          <div class="mt-0.5 whitespace-pre-line text-gray-800">{{ form.remarks }}</div>
        </div>
        <Button variant="solid" icon-left="edit-2" :class="BTN_DARK" @click="startEdit">Edit score</Button>
      </div>

      <!-- Editing -->
      <div v-else class="flex flex-col gap-4">
        <div class="flex flex-col divide-y divide-gray-100 rounded-lg border border-gray-200">
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

        <FormControl label="Remarks" type="textarea" v-model="form.remarks" placeholder="Optional notes for the committee" />

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
                Total score <span class="font-semibold text-gray-900">{{ totalScore }} / {{ maxScore }}</span>.
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

    <Dialog v-model="committee.open" :options="{ title: 'Set up Shortlisting Committee', size: 'lg' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-gray-600">
            Pick {{ committee.min }}–{{ committee.max }} members who will shortlist for this job. They get the Shortlisting
            Committee Member role.
          </p>
          <div v-if="committee.loading" class="text-sm text-gray-500">Loading staff...</div>
          <div v-else class="max-h-64 overflow-y-auto rounded-lg border">
            <label
              v-for="u in committee.users"
              :key="u.name"
              class="flex cursor-pointer items-center gap-3 border-b px-3 py-2 text-sm last:border-0 hover:bg-gray-50"
            >
              <input
                v-model="committee.members"
                type="checkbox"
                :value="u.name"
                :disabled="!committee.members.includes(u.name) && committee.members.length >= committee.max"
                class="rounded border-gray-300"
              />
              <span class="flex-1">
                <span class="font-medium text-gray-900">{{ u.full_name || u.name }}</span>
                <span class="block text-xs text-gray-500">{{ u.name }}</span>
              </span>
            </label>
          </div>
          <FormControl label="Office Order Reference (optional)" v-model="committee.officeOrder" placeholder="e.g. NLSIU/OO/2026/45" />
          <ErrorMessage :message="committee.error" />
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :class="BTN_BRAND"
          :loading="committee.saving"
          :disabled="committee.members.length < committee.min"
          @click="createCommittee"
        >
          Create committee ({{ committee.members.length }} selected)
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FormControl, ErrorMessage, FeatherIcon } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StatusBadge from './StatusBadge.vue'
import SectionCard from './SectionCard.vue'
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

// ----- set up the committee in place
const committee = reactive({ open: false, loading: false, saving: false, users: [], members: [], min: 2, max: 3, officeOrder: '', error: '' })

async function openCommitteeDialog() {
  Object.assign(committee, { open: true, loading: true, members: [], officeOrder: '', error: '' })
  try {
    const options = await scoringService.getCommitteeOptions()
    Object.assign(committee, { users: options.users, min: options.min, max: options.max })
  } catch (e) {
    committee.error = e?.messages?.[0] || 'Could not load staff.'
  } finally {
    committee.loading = false
  }
}

async function createCommittee() {
  committee.saving = true
  committee.error = ''
  try {
    await scoringService.createShortlistingCommittee(props.review.job_opening, committee.members, committee.officeOrder)
    committee.open = false
    toast({ title: 'Shortlisting Committee created. You can score now.', icon: 'check', iconClasses: 'text-green-500' })
    emit('committee-created')
  } catch (e) {
    committee.error = e?.messages?.[0] || 'Could not create the committee.'
  } finally {
    committee.saving = false
  }
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
  const bad = form.criteria.find(overMax)
  if (bad) {
    formError.value = `${bad.criterion_label}: enter a score between 0 and ${bad.max_score}.`
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
      criteria: form.criteria,
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
