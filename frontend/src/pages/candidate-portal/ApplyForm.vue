<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <div v-if="jobLoading && !job" class="text-sm text-gray-500">Loading...</div>
      <EmptyState
        v-else-if="!job"
        title="This position is not open"
        description="It may have closed or the link may be wrong."
      >
        <template #action><Button @click="$router.push('/portal/jobs')">See current openings</Button></template>
      </EmptyState>

      <template v-else>
        <header class="overflow-hidden rounded-xl border bg-white shadow-sm">
          <div class="border-b bg-gradient-to-r from-indigo-50 to-white px-5 py-5 sm:px-6">
            <div class="text-xs font-bold uppercase tracking-wider text-indigo-600">Application Form</div>
            <h1 class="mt-1 text-2xl font-bold text-gray-900">{{ job.job_title }}</h1>
            <div class="mt-3 flex flex-wrap gap-2 text-xs text-gray-700">
              <span v-for="chip in jobChips" :key="chip.text" class="inline-flex items-center gap-1.5 rounded-full border bg-white px-2.5 py-1">
                <FeatherIcon :name="chip.icon" class="h-3.5 w-3.5 text-gray-400" />{{ chip.text }}
              </span>
            </div>
            <p
              v-if="form.application_deadline"
              class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium"
              :class="form.is_open ? 'text-amber-700' : 'text-red-600'"
            >
              <FeatherIcon name="clock" class="h-4 w-4" />
              Applications close {{ formatDateTime(form.application_deadline) }} (IST)
            </p>
          </div>
          <details v-if="job.jd_text || job.jd_attachment" class="group px-5 py-3 sm:px-6">
            <summary class="flex cursor-pointer list-none items-center justify-between text-sm font-bold text-gray-900">
              Job Description
              <FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-500 transition group-open:rotate-180" />
            </summary>
            <div v-if="job.jd_text" class="prose prose-sm mt-3 max-w-none" v-html="job.jd_text" />
            <a
              v-if="job.jd_attachment"
              :href="job.jd_attachment"
              target="_blank"
              class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:underline"
            >
              <FeatherIcon name="download" class="h-4 w-4" /> Download the full notification
            </a>
          </details>
        </header>

        <!-- Gates -->
        <div v-if="!form.is_open" class="mt-6 rounded-lg border bg-white p-6 text-center text-sm text-gray-700">
          Applications for this position are closed.
        </div>

        <div v-else-if="submitted" class="mt-6 overflow-hidden rounded-xl border bg-white shadow-sm">
          <div class="flex flex-col items-center bg-green-50 px-6 pb-8 pt-10 text-center">
            <div class="flex h-16 w-16 items-center justify-center rounded-full bg-green-500 shadow-[0_0_0_8px_rgb(34_197_94_/_0.15)]">
              <FeatherIcon name="check" class="h-9 w-9 text-white" :stroke-width="3" />
            </div>
            <h2 class="mt-5 text-xl font-semibold text-gray-900">Application submitted successfully</h2>
            <p class="mt-1 text-sm text-gray-600">Thank you for applying to National Law School of India University.</p>

            <div class="mt-6 flex items-center gap-2 rounded-lg border border-green-200 bg-white px-4 py-2.5">
              <div class="text-left">
                <div class="text-xs uppercase tracking-wide text-gray-500">Application ID</div>
                <div class="font-mono text-lg font-semibold text-gray-900">{{ applicationId }}</div>
              </div>
              <Button variant="ghost" :icon="copied ? 'check' : 'copy'" :aria-label="copied ? 'Copied' : 'Copy application ID'" @click="copyApplicationId" />
            </div>
          </div>

          <div class="grid gap-6 px-6 py-6 sm:grid-cols-2">
            <dl class="flex flex-col gap-3 text-sm">
              <div class="flex gap-3">
                <FeatherIcon name="briefcase" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div>
                  <dt class="text-gray-500">Position</dt>
                  <dd class="font-medium text-gray-900">{{ job.job_title }}</dd>
                  <dd class="text-gray-600">{{ job.department }}</dd>
                </div>
              </div>
              <div class="flex gap-3">
                <FeatherIcon name="calendar" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div>
                  <dt class="text-gray-500">Submitted on</dt>
                  <dd class="font-medium text-gray-900">{{ submittedAt }}</dd>
                </div>
              </div>
              <div class="flex gap-3">
                <FeatherIcon name="mail" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div>
                  <dt class="text-gray-500">Confirmation sent to</dt>
                  <dd class="break-all font-medium text-gray-900">{{ submittedEmail }}</dd>
                </div>
              </div>
            </dl>

            <div>
              <div class="mb-3 text-sm font-semibold text-gray-900">What happens next</div>
              <ol class="flex flex-col gap-3 text-sm">
                <li v-for="(step, i) in NEXT_STEPS" :key="step.title" class="flex gap-3">
                  <span
                    class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
                    :class="i === 0 ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-600'"
                  >
                    <FeatherIcon v-if="i === 0" name="check" class="h-3.5 w-3.5" />
                    <template v-else>{{ i + 1 }}</template>
                  </span>
                  <div>
                    <div class="font-medium text-gray-900">{{ step.title }}</div>
                    <div class="text-gray-500">{{ step.text }}</div>
                  </div>
                </li>
              </ol>
            </div>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-3 border-t bg-gray-50 px-6 py-4">
            <p class="text-xs text-gray-500">Please keep your application ID for any communication with us.</p>
            <div class="flex gap-2">
              <Button @click="$router.push('/portal/jobs')">View other openings</Button>
              <Button v-if="viewer.logged_in" variant="solid" @click="$router.push('/portal/applications')">
                Track my applications
              </Button>
            </div>
          </div>
        </div>

        <div v-else-if="viewer.is_staff" class="mt-6 rounded-lg border bg-white p-6 text-sm text-gray-700">
          You are logged in with a staff account ({{ viewer.email }}). To apply, log out and register with your personal
          email address.
        </div>

        <div v-else-if="viewer.already_applied" class="mt-6 rounded-lg border bg-white p-6 text-center text-sm text-gray-700">
          You have already applied for this position (application
          <span class="font-mono">{{ viewer.already_applied }}</span>). An application can be submitted only once.
          <div class="mt-4"><Button @click="$router.push('/portal/applications')">Track my applications</Button></div>
        </div>

        <!-- The form -->
        <form v-else class="mt-6 flex flex-col gap-6 [counter-reset:section]" novalidate @submit.prevent="handleSubmit">
          <p class="text-sm text-gray-600">
            Fields marked <span class="text-red-500">*</span> are required. Your progress is saved on this device until you
            submit.
          </p>

          <Section title="Personal Details">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="candidate.email" :error="errors['candidate.email']">
                <FormControl v-if="viewer.logged_in" label="Email" :model-value="viewer.email" disabled />
                <FormControl v-else label="Email" type="email" v-model="data.candidate.email" placeholder="you@example.com" required />
              </FormField>
              <FormField name="candidate.full_name" :error="errors['candidate.full_name']">
                <FormControl label="Name" v-model="data.candidate.full_name" required />
              </FormField>
              <FormField name="candidate.mobile_number" :error="errors['candidate.mobile_number']">
                <FormControl
                  label="Mobile Number"
                  type="tel"
                  v-model="data.candidate.mobile_number"
                  placeholder="10-digit number, or +country code"
                  required
                />
              </FormField>
              <FormField name="candidate.date_of_birth" :error="errors['candidate.date_of_birth']">
                <div class="grid grid-cols-[1fr_auto] items-end gap-3">
                  <FormControl label="Date of Birth" type="date" v-model="data.candidate.date_of_birth" :max="today" required />
                  <div class="pb-2 text-sm text-gray-600">{{ age !== null ? `Age ${age}` : '' }}</div>
                </div>
              </FormField>
              <FormField name="candidate.gender" :error="errors['candidate.gender']">
                <FormControl
                  label="Gender"
                  type="select"
                  v-model="data.candidate.gender"
                  :options="['', 'Female', 'Male', 'Prefer not to say', 'Other']"
                  required
                />
              </FormField>
            </div>
            <FormField class="mt-4" name="candidate.address" :error="errors['candidate.address']">
              <FormControl label="Address for Correspondence" type="textarea" v-model="data.candidate.address" required />
            </FormField>
          </Section>

          <Section
            v-for="q in data.application.qualifications"
            :key="q.degree_level"
            :title="q.degree_level === 'Undergraduate' ? 'Graduate Degree' : 'Post Graduate Degree'"
            :badge="q.degree_level === 'Postgraduate' && !form.require_postgraduate ? 'optional' : ''"
          >
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField :name="`qual.${q.degree_level}.degree_name`" :error="errors[`qual.${q.degree_level}.degree_name`]">
                <FormControl label="Name of the Degree" v-model="q.degree_name" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.other_institution`" :error="errors[`qual.${q.degree_level}.other_institution`]">
                <FormControl label="College / University" v-model="q.other_institution" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.year_of_graduation`" :error="errors[`qual.${q.degree_level}.year_of_graduation`]">
                <FormControl
                  label="Year of Graduation"
                  inputmode="numeric"
                  maxlength="4"
                  placeholder="YYYY"
                  v-model="q.year_of_graduation"
                  :required="isRequiredDegree(q)"
                />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.percentage_or_cgpa`" :error="errors[`qual.${q.degree_level}.percentage_or_cgpa`]">
                <FormControl
                  label="Percentage"
                  inputmode="decimal"
                  v-model="q.percentage_or_cgpa"
                  :required="isRequiredDegree(q)"
                  description="Exact percentage. If you have a CGPA, convert it using your university's table."
                />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.division_grade`" :error="errors[`qual.${q.degree_level}.division_grade`]">
                <FormControl label="Division / Grade" v-model="q.division_grade" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.specialization`" :error="errors[`qual.${q.degree_level}.specialization`]">
                <FormControl label="Specialization" v-model="q.specialization" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.transcript_attachment`" :error="errors[`qual.${q.degree_level}.transcript_attachment`]">
                <UploadField
                  v-model="q.transcript_attachment"
                  label="Transcript (with percentage clearly mentioned)"
                  :required="isRequiredDegree(q)"
                  :rule="form.upload_rule"
                />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.certificate_attachment`" :error="errors[`qual.${q.degree_level}.certificate_attachment`]">
                <UploadField v-model="q.certificate_attachment" label="Degree Certificate" :required="isRequiredDegree(q)" :rule="form.upload_rule" />
              </FormField>
            </div>
          </Section>

          <Section title="Professional Experience" subtitle="In reverse chronological order — most recent first.">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="application.overall_experience_years" :error="errors['application.overall_experience_years']">
                <FormControl label="Overall work experience (years)" inputmode="decimal" v-model="data.application.overall_experience_years" required />
              </FormField>
              <FormField name="application.relevant_experience_years" :error="errors['application.relevant_experience_years']">
                <FormControl label="Relevant work experience (years)" inputmode="decimal" v-model="data.application.relevant_experience_years" required />
              </FormField>
            </div>
            <div v-for="(e, idx) in data.application.employment_history" :key="idx" class="mt-4 rounded border p-3">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-gray-900">Organisation #{{ idx + 1 }}</span>
                <Button v-if="idx > 0" size="sm" variant="ghost" @click="data.application.employment_history.splice(idx, 1)">Remove</Button>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormField :name="`emp.${idx}.designation`" :error="errors[`emp.${idx}.designation`]">
                  <FormControl label="Designation" v-model="e.designation" :required="idx === 0" />
                </FormField>
                <FormField :name="`emp.${idx}.employer_name`" :error="errors[`emp.${idx}.employer_name`]">
                  <FormControl label="Name of the employer" v-model="e.employer_name" :required="idx === 0" />
                </FormField>
                <FormField :name="`emp.${idx}.from_date`" :error="errors[`emp.${idx}.from_date`]">
                  <FormControl label="From Date" type="date" v-model="e.from_date" :max="today" :required="idx === 0" />
                </FormField>
                <FormField :name="`emp.${idx}.to_date`" :error="errors[`emp.${idx}.to_date`]">
                  <FormControl v-if="!e.is_current" label="To Date" type="date" v-model="e.to_date" :max="today" :required="idx === 0" />
                  <label class="mt-2 flex items-center gap-2 text-sm text-gray-700">
                    <input v-model="e.is_current" type="checkbox" class="rounded border-gray-300" /> I currently work here
                  </label>
                </FormField>
                <FormField class="sm:col-span-2" :name="`emp.${idx}.key_responsibilities`" :error="errors[`emp.${idx}.key_responsibilities`]">
                  <FormControl label="Key Responsibilities" type="textarea" v-model="e.key_responsibilities" :required="idx === 0" />
                </FormField>
              </div>
            </div>
            <Button class="mt-3" size="sm" variant="ghost" @click="addEmployment">+ Add another organisation</Button>
            <FormField class="mt-4 sm:w-1/2" name="application.notice_period" :error="errors['application.notice_period']">
              <FormControl label="Current Notice Period" v-model="data.application.notice_period" placeholder="e.g. 60 days" />
            </FormField>
          </Section>

          <Section v-if="form.screening_questions.length" title="Eligibility">
            <div class="flex flex-col gap-5">
              <!-- answers[] is filled right after the job loads; guard the render in between. -->
              <FormField
                v-for="q in form.screening_questions.filter((x) => answers[x.idx])"
                :key="q.idx"
                :name="`screening.${q.idx}`"
                :error="errors[`screening.${q.idx}`]"
              >
                <div class="mb-1.5 text-sm text-gray-800">
                  {{ q.question }}<span v-if="q.mandatory" class="text-red-500">*</span>
                </div>
                <div v-if="q.answer_type === 'Yes/No' || q.answer_type === 'Single Choice'" class="flex flex-wrap gap-x-5 gap-y-1.5">
                  <label
                    v-for="opt in q.answer_type === 'Yes/No' ? ['Yes', 'No'] : q.options"
                    :key="opt"
                    class="flex items-center gap-2 text-sm text-gray-700"
                  >
                    <input v-model="answers[q.idx].answer" type="radio" :name="`q${q.idx}`" :value="opt" /> {{ opt }}
                  </label>
                </div>
                <FormControl v-else-if="q.answer_type === 'Long Text'" type="textarea" v-model="answers[q.idx].answer" />
                <FormControl v-else :inputmode="q.answer_type === 'Number' ? 'decimal' : 'text'" v-model="answers[q.idx].answer" />
                <FormField
                  v-if="q.ask_details_if_yes && answers[q.idx].answer === 'Yes'"
                  class="mt-2"
                  :name="`screening.${q.idx}.details`"
                  :error="errors[`screening.${q.idx}.details`]"
                >
                  <FormControl type="textarea" :label="q.details_label" v-model="answers[q.idx].details" required />
                </FormField>
              </FormField>
            </div>
          </Section>

          <Section
            title="References"
            subtitle="Your former or current manager / reporting supervisor. References from colleagues, peers or friends will not be considered."
          >
            <div v-for="(r, idx) in data.application.references" :key="idx" class="mb-4 last:mb-0">
              <div class="mb-2 text-sm font-medium text-gray-900">Referee #{{ idx + 1 }}</div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormField :name="`ref.${idx}.referee_name`" :error="errors[`ref.${idx}.referee_name`]">
                  <FormControl label="Name" v-model="r.referee_name" required />
                </FormField>
                <FormField :name="`ref.${idx}.current_designation_org`" :error="errors[`ref.${idx}.current_designation_org`]">
                  <FormControl label="Current Designation and Organization" v-model="r.current_designation_org" required />
                </FormField>
                <FormField :name="`ref.${idx}.relationship`" :error="errors[`ref.${idx}.relationship`]">
                  <FormControl label="Nature of Relationship" v-model="r.relationship" required placeholder="e.g. Reporting manager" />
                </FormField>
                <FormField :name="`ref.${idx}.email`" :error="errors[`ref.${idx}.email`]">
                  <FormControl label="Email Address" type="email" v-model="r.email" required />
                </FormField>
                <FormField :name="`ref.${idx}.mobile`" :error="errors[`ref.${idx}.mobile`]">
                  <FormControl label="Mobile Number" type="tel" v-model="r.mobile" placeholder="10-digit number, or +country code" required />
                </FormField>
              </div>
            </div>
          </Section>

          <Section title="Supporting Documents">
            <div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <FormField name="application.resume_attachment" :error="errors['application.resume_attachment']">
                <UploadField v-model="data.application.resume_attachment" label="Resume / CV" required :rule="form.upload_rule" />
              </FormField>
              <FormField name="application.sop_attachment" :error="errors['application.sop_attachment']">
                <UploadField
                  v-model="data.application.sop_attachment"
                  label="Statement of Purpose"
                  required
                  :rule="form.upload_rule"
                  hint="Why you are interested in this role and how your qualifications, experience, skills and aspirations make you suitable (max 500 words)."
                />
              </FormField>
              <FormField
                v-for="d in form.required_documents"
                :key="d.document_type"
                :name="`doc.${d.document_type}`"
                :error="errors[`doc.${d.document_type}`]"
              >
                <UploadField v-model="documents[d.document_type]" :label="d.label" :required="!!d.mandatory" :rule="d" />
              </FormField>
              <FormField name="application.additional_attachment" :error="errors['application.additional_attachment']">
                <UploadField v-model="data.application.additional_attachment" label="Additional Documents" :rule="form.upload_rule" />
              </FormField>
            </div>
          </Section>

          <Section title="Other Details">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="application.current_salary" :error="errors['application.current_salary']">
                <FormControl label="Current Salary (per month, ₹)" inputmode="decimal" v-model="data.application.current_salary" required />
              </FormField>
              <FormField name="application.expected_salary" :error="errors['application.expected_salary']">
                <FormControl label="Expected Salary (per month, ₹)" inputmode="decimal" v-model="data.application.expected_salary" required />
              </FormField>
              <FormField name="application.earliest_doj" :error="errors['application.earliest_doj']">
                <FormControl label="Earliest Date of Joining" type="date" v-model="data.application.earliest_doj" :min="today" required />
              </FormField>
              <FormField name="application.source" :error="errors['application.source']">
                <FormControl
                  label="How did you hear about this position?"
                  type="select"
                  v-model="data.application.source"
                  :options="['', ...form.sources]"
                  required
                />
              </FormField>
            </div>
          </Section>

          <Section title="Declaration">
            <p class="mb-3 whitespace-pre-line text-sm text-gray-700">{{ form.declaration }}</p>
            <FormField name="declaration" :error="errors.declaration">
              <label class="flex items-center gap-2 text-sm font-medium text-gray-900">
                <input v-model="data.declaration_accepted" type="checkbox" class="rounded border-gray-300" /> Yes, I agree.
              </label>
            </FormField>
          </Section>

          <div v-if="errorCount || submitError" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <template v-if="errorCount">
              Please correct the {{ errorCount === 1 ? 'highlighted field' : `${errorCount} highlighted fields` }} above.
              <button type="button" class="ml-1 font-medium underline" @click="scrollToFirstError">Go to first</button>
            </template>
            <!-- Errors that belong to no single field, e.g. applications closed. -->
            <div v-else>{{ submitError }}</div>
          </div>

          <div class="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-3 border-t bg-white/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-xl sm:border sm:px-5 sm:shadow-lg">
            <span class="text-xs text-gray-500">
              <template v-if="errorCount">{{ errorCount }} field{{ errorCount === 1 ? '' : 's' }} to fix</template>
              <template v-else>Please review your details. An application can be submitted only once.</template>
            </span>
            <Button variant="solid" size="lg" :loading="submitting" type="submit" icon-right="send">Submit Application</Button>
          </div>
        </form>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, h, nextTick, onMounted, provide, reactive, ref, watch } from 'vue'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UploadField from '@/components/candidate/UploadField.vue'
import FormField from '@/components/candidate/FormField.vue'
import { validateApplication } from '@/utils/applicationValidation'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'
import { useApplicationForm } from '@/composables/useApplications'

const props = defineProps({ id: { type: String, required: true } })

const { job, loading: jobLoading, fetchJob } = useJobOpeningDetail()
const { submitting, submit } = useApplicationForm()

const form = computed(
  () =>
    job.value?.form || {
      is_open: false,
      screening_questions: [],
      required_documents: [],
      sources: [],
      upload_rule: { formats: [], max_size_mb: 5 },
    },
)
const viewer = computed(() => job.value?.viewer || {})

const jobChips = computed(() =>
  [
    { icon: 'home', text: job.value?.department },
    { icon: 'briefcase', text: job.value?.employment_type },
    { icon: 'users', text: job.value?.vacancies ? `${job.value.vacancies} vacanc${job.value.vacancies == 1 ? 'y' : 'ies'}` : '' },
    { icon: 'award', text: job.value?.designation },
  ].filter((c) => c.text),
)

// Guests apply without an account: their uploads go to the application's
// own endpoint, and each returns a token sent back with the submission.
const uploadTokens = reactive(new Map())
provide('guestUpload', {
  enabled: computed(() => !viewer.value.logged_in),
  endpoint: computed(
    () => `/api/method/pathways.api.application.upload_application_file?job_opening=${encodeURIComponent(props.id)}`,
  ),
  tokens: uploadTokens,
})

// ----- form state
function emptyData() {
  return {
    candidate: { full_name: '', email: '', mobile_number: '', date_of_birth: '', gender: '', address: '' },
    application: {
      qualifications: [
        { degree_level: 'Undergraduate' },
        { degree_level: 'Postgraduate' },
      ],
      overall_experience_years: '',
      relevant_experience_years: '',
      notice_period: '',
      employment_history: [{ is_current: false }],
      references: [{}, {}],
      resume_attachment: '',
      sop_attachment: '',
      additional_attachment: '',
      current_salary: '',
      expected_salary: '',
      earliest_doj: '',
      source: '',
    },
    declaration_accepted: false,
  }
}

const data = reactive(emptyData())
const answers = reactive({})
const documents = reactive({})

function isRequiredDegree(q) {
  return q.degree_level === 'Undergraduate' || !!form.value.require_postgraduate
}

const age = computed(() => {
  const dob = data.candidate.date_of_birth
  if (!dob || !dayjs(dob).isValid()) return null
  const years = dayjs().diff(dayjs(dob), 'year')
  return years >= 0 && years < 120 ? years : null
})

function addEmployment() {
  data.application.employment_history.push({ is_current: false })
}

// ----- draft kept on this device only (convenience; never trusted)
const draftKey = computed(() => `pathways-apply-${props.id}-${viewer.value.email || 'guest'}`)

function saveDraft() {
  if (submitted.value) return
  try {
    localStorage.setItem(
      draftKey.value,
      JSON.stringify({ data, answers, documents, uploadTokens: Object.fromEntries(uploadTokens) }),
    )
  } catch {
    // storage unavailable — drafts are a convenience only
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(draftKey.value)
  } catch {
    // ignore
  }
}

function restore() {
  Object.assign(data, emptyData())
  for (const key of Object.keys(answers)) delete answers[key]
  for (const key of Object.keys(documents)) delete documents[key]
  for (const q of form.value.screening_questions) answers[q.idx] = { idx: q.idx, answer: '', details: '' }

  // Prefill from the candidate's profile (earlier application), then any draft.
  const profile = viewer.value.profile
  if (profile) {
    for (const key of Object.keys(data.candidate)) data.candidate[key] = profile[key] || ''
  }
  try {
    const saved = JSON.parse(localStorage.getItem(draftKey.value) || 'null')
    if (saved?.data) {
      Object.assign(data.candidate, saved.data.candidate || {})
      Object.assign(data.application, saved.data.application || {})
      data.declaration_accepted = false
      for (const [idx, a] of Object.entries(saved.answers || {})) if (answers[idx]) Object.assign(answers[idx], a)
      Object.assign(documents, saved.documents || {})
      for (const [url, token] of Object.entries(saved.uploadTokens || {})) uploadTokens.set(url, token)
    }
  } catch {
    // corrupt or unavailable draft — start clean
  }
}

let draftTimer = null
watch([() => data, answers, documents], () => {
  clearTimeout(draftTimer)
  draftTimer = setTimeout(saveDraft, 600)
}, { deep: true })

// ----- submit
const submitted = ref(false)
const applicationId = ref('')
const submittedEmail = ref('')
const submittedAt = ref('')
const copied = ref(false)

const NEXT_STEPS = [
  { title: 'Application received', text: 'We have your application and documents.' },
  { title: 'Screening', text: 'The recruitment team reviews eligibility and documents.' },
  { title: 'Shortlisting', text: 'Shortlisted candidates are contacted by email for the next round.' },
  { title: 'Interview & decision', text: 'Interview details and the final outcome are sent to your email.' },
]

async function copyApplicationId() {
  try {
    await navigator.clipboard.writeText(applicationId.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    // clipboard unavailable — the ID is shown on screen
  }
}
const submitError = ref('')

// Field errors: { fieldKey: message }, shown under each field. Checked in
// the browser first (utils/applicationValidation.js); the server re-checks
// and returns the same keys. After the first attempt they update live.
const errors = reactive({})
const attempted = ref(false)
const errorCount = computed(() => Object.keys(errors).length)
const today = dayjs().format('YYYY-MM-DD')

function setErrors(next) {
  for (const key of Object.keys(errors)) delete errors[key]
  Object.assign(errors, next)
}

function runChecks() {
  return validateApplication({ data, answers, documents, form: form.value, viewer: viewer.value })
}

watch([() => data, answers, documents], () => {
  if (attempted.value && !submitting.value) setErrors(runChecks())
}, { deep: true })

async function scrollToFirstError() {
  await nextTick()
  const first = [...document.querySelectorAll('[data-field]')].find((el) => errors[el.dataset.field])
  first?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  first?.querySelector('input, select, textarea, button')?.focus({ preventScroll: true })
}

async function handleSubmit() {
  submitError.value = ''
  attempted.value = true
  setErrors(runChecks())
  if (errorCount.value) return scrollToFirstError()

  const payload = {
    candidate: { ...data.candidate },
    application: {
      ...data.application,
      screening_answers: Object.values(answers),
      documents: Object.entries(documents)
        .filter(([, url]) => url)
        .map(([document_type, attachment]) => ({ document_type, attachment })),
    },
    declaration_accepted: data.declaration_accepted ? 1 : 0,
    upload_tokens: Object.fromEntries(uploadTokens),
  }
  try {
    const result = await submit(props.id, payload)
    applicationId.value = result.application_id
    submittedEmail.value = result.email
    submittedAt.value = dayjs().format('DD MMMM YYYY, h:mm A')
    submitted.value = true
    clearDraft()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    setErrors(e?.fieldErrors || {})
    if (errorCount.value) return scrollToFirstError()
    submitError.value = e?.messages?.[0] || 'Something went wrong. Please try again.'
  }
}

function formatDateTime(value) {
  return dayjs(value).format('DD MMMM YYYY, h:mm A')
}

async function load(id) {
  submitted.value = false
  submitError.value = ''
  attempted.value = false
  setErrors({})
  await fetchJob(id)
  if (job.value) restore()
}

onMounted(() => load(props.id))
watch(() => props.id, load)

const Section = (p, { slots }) =>
  h('section', { class: 'rounded-xl border bg-white p-5 shadow-sm sm:p-6 [counter-increment:section]' }, [
    h('div', { class: 'mb-5 flex items-start gap-3 border-b pb-4' }, [
      // Numbered automatically (CSS counter), so optional sections never leave gaps.
      h('span', {
        class:
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white before:content-[counter(section)]",
      }),
      h('div', [
        h('div', { class: 'flex items-center gap-2' }, [
          h('h2', { class: 'text-base font-bold text-gray-900' }, p.title),
          p.badge ? h('span', { class: 'rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600' }, p.badge) : null,
        ]),
        p.subtitle ? h('p', { class: 'mt-0.5 text-sm text-gray-500' }, p.subtitle) : null,
      ]),
    ]),
    slots.default?.(),
  ])
Section.props = ['title', 'subtitle', 'badge']
</script>
