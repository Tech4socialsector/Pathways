<template>
  <div class="flex flex-col gap-6">
    <div v-if="loading && !app" class="text-sm text-gray-500">Loading application...</div>
    <div v-else-if="error" class="text-sm text-red-600">{{ error }}</div>
    <template v-else-if="app">
      <section class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Personal Details</div>
        <dl class="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          <Field label="Name" :value="c.full_name" />
          <Field label="Email" :value="c.email" />
          <Field label="Mobile" :value="c.mobile_number" />
          <Field label="Date of Birth" :value="c.date_of_birth ? `${formatDate(c.date_of_birth)} (age ${age(c.date_of_birth)})` : ''" />
          <Field label="Gender" :value="c.gender" />
          <Field label="Heard via" :value="app.source" />
          <Field class="sm:col-span-2" label="Address" :value="c.address" />
        </dl>
      </section>

      <section class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Academic Qualifications</div>
        <div v-if="!app.qualifications?.length" class="text-sm text-gray-500">None provided.</div>
        <div v-for="q in app.qualifications" :key="q.name" class="mb-3 rounded border p-3 text-sm last:mb-0">
          <div class="font-medium text-gray-900">{{ q.degree_name }} <span class="font-normal text-gray-500">· {{ q.degree_level }}</span></div>
          <div class="text-gray-600">
            {{ q.other_institution || q.institution }} · {{ q.year_of_graduation }} · {{ q.percentage_or_cgpa }}% ·
            {{ q.division_grade }} · {{ q.specialization }}
          </div>
          <div class="mt-1 flex gap-3">
            <FileLink :url="q.transcript_attachment" label="Transcript" />
            <FileLink :url="q.certificate_attachment" label="Certificate" />
          </div>
        </div>
      </section>

      <section class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Professional Experience</div>
        <dl class="mb-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          <Field label="Overall (years)" :value="app.overall_experience_years" />
          <Field label="Relevant (years)" :value="app.relevant_experience_years" />
          <Field label="Notice period" :value="app.notice_period" />
        </dl>
        <div v-for="(e, idx) in app.employment_history" :key="e.name" class="mb-3 rounded border p-3 text-sm last:mb-0">
          <div class="font-medium text-gray-900">#{{ idx + 1 }} {{ e.designation }}, {{ e.employer_name }}</div>
          <div class="text-gray-600">
            {{ formatDate(e.from_date) }} – {{ e.is_current ? 'Present' : formatDate(e.to_date) }}
          </div>
          <div v-if="e.key_responsibilities" class="mt-1 whitespace-pre-line text-gray-700">{{ e.key_responsibilities }}</div>
        </div>
      </section>

      <section v-if="app.screening_answers?.length" class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Screening Questions</div>
        <div v-for="a in app.screening_answers" :key="a.name" class="mb-3 text-sm last:mb-0">
          <div class="text-gray-600">{{ a.question }}</div>
          <div class="font-medium text-gray-900">{{ a.answer || '—' }}</div>
          <div v-if="a.details" class="mt-0.5 whitespace-pre-line text-gray-700">{{ a.details }}</div>
        </div>
      </section>

      <section class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">References</div>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div v-for="r in app.references" :key="r.name" class="rounded border p-3 text-sm">
            <div class="font-medium text-gray-900">{{ r.referee_name }}</div>
            <div class="text-gray-600">{{ r.current_designation_org }} · {{ r.relationship }}</div>
            <div class="text-gray-600">{{ r.email }} · {{ r.mobile }}</div>
          </div>
        </div>
      </section>

      <section class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Documents & Compensation</div>
        <div class="mb-3 flex flex-wrap gap-x-4 gap-y-1">
          <FileLink :url="app.resume_attachment" label="Resume / CV" />
          <FileLink :url="app.sop_attachment" label="Statement of Purpose" />
          <FileLink v-for="d in app.documents" :key="d.name" :url="d.attachment" :label="d.document_type" />
          <FileLink :url="app.additional_attachment" label="Additional Documents" />
        </div>
        <dl class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          <Field v-if="'current_salary' in app" label="Current salary / month" :value="money(app.current_salary)" />
          <Field v-if="'expected_salary' in app" label="Expected salary" :value="money(app.expected_salary)" />
          <Field label="Earliest joining" :value="formatDate(app.earliest_doj)" />
          <Field
            label="Declaration"
            :value="app.declaration_accepted ? `Accepted ${formatDate(app.declaration_accepted_on)}` : 'Not recorded'"
          />
        </dl>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, h, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { applicationService } from '@/services/applications'

const props = defineProps({ applicationName: { type: String, required: true } })

const app = ref(null)
const loading = ref(false)
const error = ref('')
const c = computed(() => app.value?.candidate_details || {})

async function load(name) {
  loading.value = true
  error.value = ''
  try {
    app.value = await applicationService.getApplicationDetail(name)
  } catch (e) {
    app.value = null
    error.value = e?.messages?.[0] || 'Could not load the application.'
  } finally {
    loading.value = false
  }
}

watch(() => props.applicationName, load, { immediate: true })

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

function age(dob) {
  return dayjs().diff(dayjs(dob), 'year')
}

function money(value) {
  return value == null ? '' : `₹ ${Number(value).toLocaleString('en-IN')}`
}

const Field = (p) =>
  h('div', { class: p.class }, [
    h('dt', { class: 'text-gray-500' }, p.label),
    h('dd', { class: 'font-medium text-gray-900 whitespace-pre-line' }, p.value === 0 ? '0' : p.value || '—'),
  ])
Field.props = ['label', 'value', 'class']

const FileLink = (p) =>
  p.url
    ? h('a', { href: p.url, target: '_blank', rel: 'noopener', class: 'text-sm text-blue-600 hover:underline' }, p.label)
    : null
FileLink.props = ['url', 'label']
</script>
