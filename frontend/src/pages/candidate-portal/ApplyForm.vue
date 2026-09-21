<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-2xl px-6 py-10">
      <div v-if="jobLoading" class="text-sm text-gray-500">Loading...</div>
      <template v-else-if="job">
        <h1 class="mb-1 text-2xl font-semibold text-gray-900">Apply: {{ job.job_title }}</h1>
        <p class="mb-6 text-sm text-gray-500">{{ job.department }} &middot; {{ job.employment_type }}</p>

        <Alert v-if="submitError" theme="red" class="mb-4">{{ submitError }}</Alert>

        <div v-if="submitted" class="rounded-lg border bg-white p-6 text-center">
          <div class="mb-2 text-lg font-semibold text-gray-900">Application Submitted</div>
          <p class="text-sm text-gray-600">
            Your application ID is <span class="font-mono font-medium">{{ applicationId }}</span>.
            You can track your status from "My Applications" once you're logged in with this email.
          </p>
        </div>

        <form v-else class="flex flex-col gap-6" @submit.prevent="handleSubmit">
          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Personal Details</div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Full Name" v-model="candidate.full_name" required />
              <FormControl label="Email" type="email" v-model="candidate.email" required @blur="checkDup" />
              <FormControl label="Mobile Number" v-model="candidate.mobile_number" required />
              <FormControl label="Date of Birth" type="date" v-model="candidate.date_of_birth" />
              <FormControl
                label="Gender"
                type="select"
                v-model="candidate.gender"
                :options="['', 'Female', 'Male', 'Prefer not to say', 'Other']"
              />
            </div>
            <FormControl
              class="mt-4"
              label="Address for Correspondence"
              type="textarea"
              v-model="candidate.address"
            />
            <Alert v-if="duplicateWarning" theme="orange" class="mt-3">
              An application from this email already exists for this position.
            </Alert>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 flex items-center justify-between">
              <div class="text-sm font-semibold text-gray-900">Academic Qualifications</div>
              <Button variant="ghost" size="sm" @click="addQualification">+ Add</Button>
            </div>
            <div
              v-for="(q, idx) in application.qualifications"
              :key="idx"
              class="mb-3 grid grid-cols-1 gap-3 rounded border p-3 sm:grid-cols-2"
            >
              <FormControl
                label="Degree Level"
                type="select"
                v-model="q.degree_level"
                :options="['', 'Undergraduate', 'Postgraduate', 'Doctoral']"
              />
              <FormControl label="Degree Name" v-model="q.degree_name" />
              <FormControl label="College / University" v-model="q.other_institution" />
              <FormControl label="Year of Graduation" type="number" v-model="q.year_of_graduation" />
              <FormControl label="Percentage / CGPA" v-model="q.percentage_or_cgpa" />
              <FormControl label="Specialization" v-model="q.specialization" />
            </div>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 flex items-center justify-between">
              <div class="text-sm font-semibold text-gray-900">Professional Experience</div>
              <Button variant="ghost" size="sm" @click="addEmployment">+ Add</Button>
            </div>
            <div
              v-for="(e, idx) in application.employment_history"
              :key="idx"
              class="mb-3 grid grid-cols-1 gap-3 rounded border p-3 sm:grid-cols-2"
            >
              <FormControl label="Designation" v-model="e.designation" />
              <FormControl label="Employer" v-model="e.employer_name" />
              <FormControl label="From Date" type="date" v-model="e.from_date" />
              <FormControl label="To Date" type="date" v-model="e.to_date" />
              <FormControl
                class="sm:col-span-2"
                label="Key Responsibilities"
                type="textarea"
                v-model="e.key_responsibilities"
              />
            </div>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">References</div>
            <div
              v-for="(r, idx) in application.references"
              :key="idx"
              class="mb-3 grid grid-cols-1 gap-3 rounded border p-3 sm:grid-cols-2"
            >
              <FormControl label="Name" v-model="r.referee_name" />
              <FormControl label="Designation & Organization" v-model="r.current_designation_org" />
              <FormControl label="Relationship" v-model="r.relationship" />
              <FormControl label="Email" type="email" v-model="r.email" />
              <FormControl label="Mobile" v-model="r.mobile" />
            </div>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Additional Details</div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Current Salary (per month)" type="number" v-model="application.current_salary" />
              <FormControl label="Expected Salary (per month)" type="number" v-model="application.expected_salary" />
              <FormControl label="Earliest Date of Joining" type="date" v-model="application.earliest_doj" />
            </div>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <label class="flex items-start gap-2 text-sm text-gray-700">
              <input type="checkbox" v-model="declarationAccepted" class="mt-0.5" />
              <span>
                I hereby declare that the information provided is true and accurate to the best of my
                knowledge, and I understand that any false information may lead to cancellation of my
                candidature or termination of appointment.
              </span>
            </label>
          </div>

          <Button variant="solid" size="lg" :loading="submitting" type="submit" :disabled="!declarationAccepted">
            Submit Application
          </Button>
        </form>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { Alert, Button, FormControl } from 'frappe-ui'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'
import { useApplicationForm } from '@/composables/useApplications'

const props = defineProps({ id: { type: String, required: true } })

const { job, loading: jobLoading, fetchJob } = useJobOpeningDetail()
const { submitting, checkDuplicate, submit } = useApplicationForm()

const candidate = reactive({
  full_name: '',
  email: '',
  mobile_number: '',
  date_of_birth: '',
  gender: '',
  address: '',
})

const application = reactive({
  job_opening: props.id,
  current_salary: null,
  expected_salary: null,
  earliest_doj: '',
  qualifications: [{}],
  employment_history: [{}],
  references: [{}, {}],
})

const declarationAccepted = ref(false)
const duplicateWarning = ref(false)
const submitted = ref(false)
const applicationId = ref('')
const submitError = ref('')

function addQualification() {
  application.qualifications.push({})
}
function addEmployment() {
  application.employment_history.push({})
}

async function checkDup() {
  if (!candidate.email) return
  const result = await checkDuplicate(candidate.email, candidate.mobile_number, props.id)
  duplicateWarning.value = !!result?.duplicate
}

async function handleSubmit() {
  submitError.value = ''
  if (duplicateWarning.value) {
    submitError.value = 'You have already applied for this position with this email address.'
    return
  }
  try {
    const result = await submit(candidate, application)
    applicationId.value = result.application_id
    submitted.value = true
  } catch (e) {
    submitError.value = e?.messages?.[0] || 'Something went wrong. Please try again.'
  }
}

onMounted(() => fetchJob(props.id))
watch(() => props.id, (id) => {
  application.job_opening = id
  fetchJob(id)
})
</script>
