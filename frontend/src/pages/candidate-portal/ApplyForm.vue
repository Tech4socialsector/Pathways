<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <div v-if="jobLoading && !job" class="text-sm text-gray-500">Loading...</div>
      <EmptyState
        v-else-if="!job"
        title="This position is not open"
        description="It may have closed or the link may be wrong."
      >
        <template #action><Button @click="$router.push('/portal/jobs')">See current openings</Button></template>
      </EmptyState>

      <template v-else>
        <h1 class="mb-1 text-2xl font-semibold text-gray-900">{{ job.job_title }}</h1>
        <p class="text-sm text-gray-500">
          {{ job.department }} &middot; {{ job.employment_type }} &middot; {{ job.vacancies }} vacancy(ies)
        </p>
        <p v-if="form.application_deadline" class="mt-1 text-sm" :class="form.is_open ? 'text-gray-700' : 'text-red-600'">
          Applications close {{ formatDateTime(form.application_deadline) }} (IST)
        </p>
        <div v-if="job.jd_text" class="prose prose-sm mt-4 max-w-none rounded-lg border bg-white p-4" v-html="job.jd_text" />
        <a v-if="job.jd_attachment" :href="job.jd_attachment" target="_blank" class="mt-2 inline-block text-sm text-blue-600 hover:underline">
          Download the full notification
        </a>

        <!-- Gates -->
        <div v-if="!form.is_open" class="mt-6 rounded-lg border bg-white p-6 text-center text-sm text-gray-700">
          Applications for this position are closed.
        </div>

        <div v-else-if="submitted" class="mt-6 rounded-lg border bg-white p-6 text-center">
          <div class="mb-2 text-lg font-semibold text-gray-900">Application Submitted</div>
          <p class="text-sm text-gray-600">
            Your application ID is <span class="font-mono font-medium">{{ applicationId }}</span>. A confirmation has been
            sent to {{ viewer.email }}.
          </p>
          <Button class="mt-4" @click="$router.push('/portal/applications')">Track my applications</Button>
        </div>

        <div v-else-if="!viewer.logged_in" class="mt-6 grid gap-4 sm:grid-cols-2">
          <div class="rounded-lg border bg-white p-5">
            <div class="mb-1 font-semibold text-gray-900">Already registered?</div>
            <p class="mb-4 text-sm text-gray-600">Log in to fill in your application.</p>
            <Button variant="solid" @click="goToLogin">Log in to apply</Button>
          </div>
          <div class="rounded-lg border bg-white p-5">
            <div class="mb-1 font-semibold text-gray-900">New here?</div>
            <p class="mb-3 text-sm text-gray-600">Create an account with your email. We'll send a link to set a password.</p>
            <div v-if="registerMessage" class="rounded bg-green-50 px-3 py-2 text-sm text-green-800">{{ registerMessage }}</div>
            <form v-else class="flex flex-col gap-3" @submit.prevent="register">
              <ErrorMessage :message="registerError" />
              <FormControl v-model="registration.full_name" label="Full name" required />
              <FormControl v-model="registration.email" label="Email" type="email" required />
              <Button type="submit" :loading="registering">Create account</Button>
            </form>
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
        <form v-else class="mt-6 flex flex-col gap-6" novalidate @submit.prevent="handleSubmit">
          <p class="text-sm text-gray-600">
            Fields marked <span class="text-red-500">*</span> are required. Your progress is saved on this device until you
            submit.
          </p>

          <Section title="Personal Details">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Email" :model-value="viewer.email" disabled />
              <FormControl label="Name" v-model="data.candidate.full_name" required />
              <FormControl label="Mobile Number" type="tel" v-model="data.candidate.mobile_number" required />
              <div class="grid grid-cols-[1fr_auto] items-end gap-3">
                <FormControl label="Date of Birth" type="date" v-model="data.candidate.date_of_birth" required />
                <div class="pb-2 text-sm text-gray-600">{{ age !== null ? `Age ${age}` : '' }}</div>
              </div>
              <FormControl
                label="Gender"
                type="select"
                v-model="data.candidate.gender"
                :options="['', 'Female', 'Male', 'Prefer not to say', 'Other']"
                required
              />
            </div>
            <FormControl class="mt-4" label="Address for Correspondence" type="textarea" v-model="data.candidate.address" required />
          </Section>

          <Section
            v-for="q in data.application.qualifications"
            :key="q.degree_level"
            :title="q.degree_level === 'Undergraduate' ? 'Graduate Degree' : 'Post Graduate Degree'"
            :badge="q.degree_level === 'Postgraduate' && !form.require_postgraduate ? 'optional' : ''"
          >
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Name of the Degree" v-model="q.degree_name" :required="isRequiredDegree(q)" />
              <FormControl label="College / University" v-model="q.other_institution" :required="isRequiredDegree(q)" />
              <FormControl label="Year of Graduation" type="number" v-model="q.year_of_graduation" :required="isRequiredDegree(q)" />
              <FormControl
                label="Percentage"
                v-model="q.percentage_or_cgpa"
                :required="isRequiredDegree(q)"
                description="Exact percentage. If you have a CGPA, convert it using your university's table."
              />
              <FormControl label="Division / Grade" v-model="q.division_grade" :required="isRequiredDegree(q)" />
              <FormControl label="Specialization" v-model="q.specialization" :required="isRequiredDegree(q)" />
              <UploadField
                v-model="q.transcript_attachment"
                label="Transcript (with percentage clearly mentioned)"
                :required="isRequiredDegree(q)"
                :rule="form.upload_rule"
              />
              <UploadField v-model="q.certificate_attachment" label="Degree Certificate" :required="isRequiredDegree(q)" :rule="form.upload_rule" />
            </div>
          </Section>

          <Section title="Professional Experience" subtitle="In reverse chronological order — most recent first.">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Overall work experience (years)" type="number" v-model="data.application.overall_experience_years" required />
              <FormControl label="Relevant work experience (years)" type="number" v-model="data.application.relevant_experience_years" required />
            </div>
            <div v-for="(e, idx) in data.application.employment_history" :key="idx" class="mt-4 rounded border p-3">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-gray-900">Organisation #{{ idx + 1 }}</span>
                <Button v-if="idx > 0" size="sm" variant="ghost" @click="data.application.employment_history.splice(idx, 1)">Remove</Button>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormControl label="Designation" v-model="e.designation" :required="idx === 0" />
                <FormControl label="Name of the employer" v-model="e.employer_name" :required="idx === 0" />
                <FormControl label="From Date" type="date" v-model="e.from_date" :required="idx === 0" />
                <div>
                  <FormControl v-if="!e.is_current" label="To Date" type="date" v-model="e.to_date" :required="idx === 0" />
                  <label class="mt-2 flex items-center gap-2 text-sm text-gray-700">
                    <input v-model="e.is_current" type="checkbox" class="rounded border-gray-300" /> I currently work here
                  </label>
                </div>
                <FormControl class="sm:col-span-2" label="Key Responsibilities" type="textarea" v-model="e.key_responsibilities" :required="idx === 0" />
              </div>
            </div>
            <Button class="mt-3" size="sm" variant="ghost" @click="addEmployment">+ Add another organisation</Button>
            <FormControl class="mt-4 sm:w-1/2" label="Current Notice Period" v-model="data.application.notice_period" placeholder="e.g. 60 days" />
          </Section>

          <Section v-if="form.screening_questions.length" title="Eligibility">
            <div class="flex flex-col gap-5">
              <!-- answers[] is filled right after the job loads; guard the render in between. -->
              <div v-for="q in form.screening_questions.filter((x) => answers[x.idx])" :key="q.idx">
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
                <FormControl v-else :type="q.answer_type === 'Number' ? 'number' : 'text'" v-model="answers[q.idx].answer" />
                <FormControl
                  v-if="q.ask_details_if_yes && answers[q.idx].answer === 'Yes'"
                  class="mt-2"
                  type="textarea"
                  :label="q.details_label"
                  v-model="answers[q.idx].details"
                  required
                />
              </div>
            </div>
          </Section>

          <Section
            title="References"
            subtitle="Your former or current manager / reporting supervisor. References from colleagues, peers or friends will not be considered."
          >
            <div v-for="(r, idx) in data.application.references" :key="idx" class="mb-4 last:mb-0">
              <div class="mb-2 text-sm font-medium text-gray-900">Referee #{{ idx + 1 }}</div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormControl label="Name" v-model="r.referee_name" required />
                <FormControl label="Current Designation and Organization" v-model="r.current_designation_org" required />
                <FormControl label="Nature of Relationship" v-model="r.relationship" required placeholder="e.g. Reporting manager" />
                <FormControl label="Email Address" type="email" v-model="r.email" required />
                <FormControl label="Mobile Number" type="tel" v-model="r.mobile" required />
              </div>
            </div>
          </Section>

          <Section title="Supporting Documents">
            <div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <UploadField v-model="data.application.resume_attachment" label="Resume / CV" required :rule="form.upload_rule" />
              <UploadField
                v-model="data.application.sop_attachment"
                label="Statement of Purpose"
                required
                :rule="form.upload_rule"
                hint="Why you are interested in this role and how your qualifications, experience, skills and aspirations make you suitable (max 500 words)."
              />
              <UploadField
                v-for="d in form.required_documents"
                :key="d.document_type"
                v-model="documents[d.document_type]"
                :label="d.label"
                :required="!!d.mandatory"
                :rule="d"
              />
              <UploadField v-model="data.application.additional_attachment" label="Additional Documents" :rule="form.upload_rule" />
            </div>
          </Section>

          <Section title="Other Details">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Current Salary (per month, ₹)" type="number" v-model="data.application.current_salary" required />
              <FormControl label="Expected Salary (per month, ₹)" type="number" v-model="data.application.expected_salary" required />
              <FormControl label="Earliest Date of Joining" type="date" v-model="data.application.earliest_doj" required />
              <FormControl
                label="How did you hear about this position?"
                type="select"
                v-model="data.application.source"
                :options="['', ...form.sources]"
                required
              />
            </div>
          </Section>

          <Section title="Declaration">
            <p class="mb-3 whitespace-pre-line text-sm text-gray-700">{{ form.declaration }}</p>
            <label class="flex items-center gap-2 text-sm font-medium text-gray-900">
              <input v-model="data.declaration_accepted" type="checkbox" class="rounded border-gray-300" /> Yes, I agree.
            </label>
          </Section>

          <div v-if="submitError" ref="errorBox" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <!-- Server-built list; every item is HTML-escaped server-side. -->
            <div class="mb-1 font-medium">Please correct the following</div>
            <div class="[&_ul]:list-disc [&_ul]:pl-5" v-html="submitError" />
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <Button variant="solid" size="lg" :loading="submitting" type="submit" :disabled="!data.declaration_accepted">
              Submit Application
            </Button>
            <span class="text-xs text-gray-500">An application can be submitted only once.</span>
          </div>
        </form>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, h, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { Button, ErrorMessage, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UploadField from '@/components/candidate/UploadField.vue'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'
import { useApplicationForm } from '@/composables/useApplications'
import { applicationService } from '@/services/applications'

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

// ----- form state
function emptyData() {
  return {
    candidate: { full_name: '', mobile_number: '', date_of_birth: '', gender: '', address: '' },
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
const draftKey = computed(() => `pathways-apply-${props.id}-${viewer.value.email || ''}`)

function saveDraft() {
  if (!viewer.value.email || submitted.value) return
  try {
    localStorage.setItem(draftKey.value, JSON.stringify({ data, answers, documents }))
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
const submitError = ref('')
const errorBox = ref(null)

async function handleSubmit() {
  submitError.value = ''
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
  }
  try {
    const result = await submit(props.id, payload)
    applicationId.value = result.application_id
    submitted.value = true
    clearDraft()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    submitError.value = e?.messages?.[0] || 'Something went wrong. Please try again.'
    await nextTick()
    errorBox.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// ----- login / registration
function goToLogin() {
  window.location.href = `/login?redirect-to=${encodeURIComponent(`/pathways/portal/jobs/${props.id}/apply`)}`
}

const registration = reactive({ full_name: '', email: '' })
const registering = ref(false)
const registerError = ref('')
const registerMessage = ref('')

async function register() {
  registerError.value = ''
  registering.value = true
  try {
    registerMessage.value = await applicationService.registerCandidate(
      registration.email,
      registration.full_name,
      `/pathways/portal/jobs/${props.id}/apply`,
    )
  } catch (e) {
    registerError.value = e?.messages?.[0] || 'Could not create your account. Please try again later.'
  } finally {
    registering.value = false
  }
}

function formatDateTime(value) {
  return dayjs(value).format('DD MMMM YYYY, h:mm A')
}

async function load(id) {
  submitted.value = false
  submitError.value = ''
  await fetchJob(id)
  if (job.value) restore()
}

onMounted(() => load(props.id))
watch(() => props.id, load)

const Section = (p, { slots }) =>
  h('section', { class: 'rounded-lg border bg-white p-4 sm:p-5' }, [
    h('div', { class: 'mb-4' }, [
      h('div', { class: 'flex items-center gap-2' }, [
        h('h2', { class: 'text-base font-semibold text-gray-900' }, p.title),
        p.badge ? h('span', { class: 'rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600' }, p.badge) : null,
      ]),
      p.subtitle ? h('p', { class: 'mt-0.5 text-sm text-gray-500' }, p.subtitle) : null,
    ]),
    slots.default?.(),
  ])
Section.props = ['title', 'subtitle', 'badge']
</script>
