<template>
  <div class="flex flex-col gap-6">
    <div v-if="loading && !app" class="text-sm text-gray-500">Loading application...</div>
    <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
    <template v-else-if="app">
      <Card icon="user" title="Personal Details">
        <dl class="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
          <Field label="Name" :value="c.full_name" />
          <Field label="Email" :value="c.email" />
          <Field label="Mobile" :value="c.mobile_number" />
          <Field label="Date of Birth" :value="c.date_of_birth ? `${formatDate(c.date_of_birth)} (age ${age(c.date_of_birth)})` : ''" />
          <Field label="Gender" :value="c.gender" />
          <Field label="Heard via" :value="app.source" />
          <Field class="sm:col-span-2" label="Address" :value="c.address" />
        </dl>
      </Card>

      <Card icon="book-open" title="Academic Qualifications">
        <div v-if="!app.qualifications?.length" class="text-sm text-gray-500">None provided.</div>
        <div class="flex flex-col gap-3">
          <div v-for="q in app.qualifications" :key="q.name" class="rounded-lg border border-gray-200 p-4 text-sm">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-bold text-gray-900">{{ q.degree_name }}</span>
              <span class="rounded bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">{{ levelLabel(q.degree_level) }}</span>
            </div>
            <div class="mt-1 text-gray-600">{{ q.other_institution || q.institution }}</div>
            <dl class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Field label="Year" :value="q.year_of_graduation" />
              <Field label="Percentage" :value="q.percentage_or_cgpa ? `${q.percentage_or_cgpa}%` : ''" />
              <Field label="Division / Grade" :value="q.division_grade" />
              <Field label="Specialization" :value="q.specialization" />
            </dl>
            <div class="mt-3 flex flex-wrap gap-2">
              <FileChip :url="q.transcript_attachment" label="Transcript" />
              <FileChip :url="q.certificate_attachment" label="Degree Certificate" />
            </div>
          </div>
        </div>
      </Card>

      <Card icon="briefcase" title="Professional Experience">
        <dl class="mb-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <Field label="Overall (years)" :value="app.overall_experience_years" />
          <Field label="Relevant (years)" :value="app.relevant_experience_years" />
          <Field label="Notice period" :value="app.notice_period" />
        </dl>
        <ol v-if="app.employment_history?.length" class="relative ml-2 border-l border-gray-200 text-sm">
          <li v-for="e in app.employment_history" :key="e.name" class="mb-4 ml-5 last:mb-0">
            <span class="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full bg-brand-700" />
            <div class="font-bold text-gray-900">{{ e.designation }}</div>
            <div class="text-gray-700">{{ e.employer_name }}</div>
            <div class="text-xs text-gray-500">{{ formatDate(e.from_date) }} – {{ e.is_current ? 'Present' : formatDate(e.to_date) }}</div>
            <div v-if="e.key_responsibilities" class="mt-1 whitespace-pre-line text-gray-700">{{ e.key_responsibilities }}</div>
          </li>
        </ol>
        <div v-else class="text-sm text-gray-500">No employment history.</div>
      </Card>

      <Card v-if="app.screening_answers?.length" icon="help-circle" title="Screening Questions">
        <div class="flex flex-col divide-y">
          <div v-for="a in app.screening_answers" :key="a.name" class="py-3 text-sm first:pt-0 last:pb-0">
            <div class="text-gray-600">{{ a.question }}</div>
            <div class="mt-0.5 font-bold text-gray-900">{{ a.answer || '—' }}</div>
            <div v-if="a.details" class="mt-1 whitespace-pre-line text-gray-700">{{ a.details }}</div>
          </div>
        </div>
      </Card>

      <Card icon="users" title="References">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div v-for="r in app.references" :key="r.name" class="rounded-lg border border-gray-200 p-4 text-sm">
            <div class="font-bold text-gray-900">{{ r.referee_name }}</div>
            <div class="text-gray-600">{{ r.current_designation_org }}</div>
            <div class="mt-1 text-xs text-gray-500">{{ r.relationship }}</div>
            <div class="mt-2 flex flex-col gap-1 text-gray-700">
              <span class="flex items-center gap-1.5"><FeatherIcon name="mail" class="h-3.5 w-3.5 text-gray-400" />{{ r.email }}</span>
              <span class="flex items-center gap-1.5"><FeatherIcon name="phone" class="h-3.5 w-3.5 text-gray-400" />{{ r.mobile }}</span>
            </div>
          </div>
        </div>
      </Card>

      <Card icon="paperclip" title="Documents & Compensation">
        <template #action>
          <button class="flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline" @click="emit('view-documents')">
            <FeatherIcon name="eye" class="h-4 w-4" /> View documents
          </button>
        </template>
        <div class="mb-4 flex flex-wrap gap-2">
          <FileChip :url="app.resume_attachment" label="Resume / CV" />
          <FileChip :url="app.sop_attachment" label="Statement of Purpose" />
          <FileChip v-for="d in app.documents" :key="d.name" :url="d.attachment" :label="d.document_type" />
          <FileChip :url="app.additional_attachment" label="Additional Documents" />
        </div>
        <dl class="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Field v-if="'current_salary' in app" label="Current salary / month" :value="money(app.current_salary)" />
          <Field v-if="'expected_salary' in app" label="Expected salary / month" :value="money(app.expected_salary)" />
          <Field label="Earliest joining" :value="formatDate(app.earliest_doj)" />
          <Field
            label="Declaration"
            :value="app.declaration_accepted ? `Accepted ${formatDate(app.declaration_accepted_on)}` : 'Not recorded'"
          />
        </dl>
      </Card>
    </template>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import dayjs from 'dayjs'
import { FeatherIcon } from 'frappe-ui'
import SectionCard from './SectionCard.vue'

const props = defineProps({
  // pathways.api.application.get_application_detail, loaded by the page.
  app: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['view-documents'])

const c = computed(() => props.app?.candidate_details || {})

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

function age(dob) {
  return dayjs().diff(dayjs(dob), 'year')
}

function money(value) {
  return value == null ? '' : `₹ ${Number(value).toLocaleString('en-IN')}`
}

function levelLabel(level) {
  return level === 'Undergraduate' ? 'Graduate' : level === 'Postgraduate' ? 'Post Graduate' : level
}

// Same card as the rest of the staff pages.
const Card = (p, { slots }) => h(SectionCard, { title: p.title, icon: p.icon }, { default: slots.default, actions: slots.action })
Card.props = ['icon', 'title']

const Field = (p) =>
  h('div', { class: p.class }, [
    h('dt', { class: 'text-xs text-gray-500' }, p.label),
    h('dd', { class: 'mt-0.5 font-medium text-gray-900 whitespace-pre-line break-words' }, p.value === 0 ? '0' : p.value || '—'),
  ])
Field.props = ['label', 'value', 'class']

const FileChip = (p) =>
  p.url
    ? h(
        'a',
        {
          href: p.url,
          target: '_blank',
          rel: 'noopener',
          class:
            'inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-medium text-gray-700 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700',
        },
        [h(FeatherIcon, { name: 'file-text', class: 'h-3.5 w-3.5' }), p.label],
      )
    : null
FileChip.props = ['url', 'label']
</script>
