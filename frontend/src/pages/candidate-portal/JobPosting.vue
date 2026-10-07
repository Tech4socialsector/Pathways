<template>
  <CandidatePortalLayout>
    <div v-if="loading" class="mx-auto max-w-6xl px-6 py-16 text-sm text-gray-500">Loading...</div>
    <div v-else-if="!job" class="mx-auto max-w-3xl px-6 py-16">
      <EmptyState title="This position is not currently open for applications" description="It may have closed or been filled.">
        <template #action>
          <Button @click="$router.push('/portal/jobs')">View current openings</Button>
        </template>
      </EmptyState>
    </div>

    <template v-else>
      <!-- Hero -->
      <section class="bg-gradient-to-br from-brand-900 via-brand-800 to-brand-600 text-white">
        <div class="mx-auto max-w-6xl px-6 pb-10 pt-6">
          <button
            class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-white/80 hover:bg-white/10 hover:text-white"
            @click="goBack"
          >
            <FeatherIcon name="arrow-left" class="h-4 w-4" /> All openings
          </button>

          <div class="mt-6 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white/70">
                <span>{{ job.track }} Track</span>
                <span v-if="job.designation">· {{ job.designation }}</span>
              </div>
              <h1 class="mt-2 text-3xl font-bold leading-tight sm:text-4xl">{{ job.job_title }}</h1>
              <p class="mt-2 text-white/80">National Law School of India University, Bengaluru</p>
              <div class="mt-5 flex flex-wrap gap-2 text-sm">
                <span v-for="chip in chips" :key="chip.text" class="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 ring-1 ring-inset ring-white/20">
                  <FeatherIcon :name="chip.icon" class="h-3.5 w-3.5" />{{ chip.text }}
                </span>
              </div>
            </div>
            <div class="shrink-0">
              <button
                class="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-base font-bold text-brand-800 shadow-lg transition hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="!isOpen"
                @click="apply"
              >
                {{ isOpen ? 'Apply Now' : closedLabel }}
                <FeatherIcon v-if="isOpen" name="arrow-right" class="h-5 w-5" />
              </button>
              <p v-if="deadline" class="mt-2 text-center text-xs text-white/80">{{ deadline.short }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Body -->
      <div class="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 py-10 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div class="flex min-w-0 flex-col gap-8">
          <section class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 class="mb-4 flex items-center gap-2 text-xl font-bold text-gray-900">
              <span class="h-6 w-1 rounded-full bg-brand-700" />About the role
            </h2>
            <div v-if="job.jd_text" class="prose max-w-none text-gray-700 prose-headings:text-gray-900 prose-a:text-brand-700" v-html="job.jd_text" />
            <p v-else class="text-gray-500">A detailed description will be shared with shortlisted candidates.</p>
            <a
              v-if="job.jd_attachment"
              :href="job.jd_attachment"
              target="_blank"
              rel="noopener"
              class="mt-6 inline-flex items-center gap-2 rounded-lg border border-brand-200 px-4 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              <FeatherIcon name="download" class="h-4 w-4" /> Download the full job description
            </a>
          </section>

          <!-- Official notification and corrigenda -->
          <section v-if="notification || corrigenda.length" class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 class="mb-4 flex items-center gap-2 text-xl font-bold text-gray-900">
              <span class="h-6 w-1 rounded-full bg-brand-700" />Official notification
            </h2>
            <div v-if="notification" class="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
              <span v-if="notification.notification_number" class="font-semibold text-gray-900">{{ notification.notification_number }}</span>
              <span v-if="notification.publish_date" class="text-gray-600">Dated {{ formatDate(notification.publish_date) }}</span>
              <a
                v-if="notification.notification_attachment"
                :href="notification.notification_attachment"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-1.5 font-semibold text-brand-700 hover:underline"
              >
                <FeatherIcon name="file-text" class="h-4 w-4" /> Notification (PDF)
              </a>
              <a
                v-if="notification.notification_url"
                :href="notification.notification_url"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-1.5 font-semibold text-brand-700 hover:underline"
              >
                <FeatherIcon name="external-link" class="h-4 w-4" /> View on nls.ac.in
              </a>
            </div>
            <div v-if="corrigenda.length" class="mt-5">
              <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Corrigenda</h3>
              <ul class="flex flex-col gap-2 text-sm">
                <li v-for="(c, idx) in corrigenda" :key="idx" class="flex flex-wrap items-start justify-between gap-2 rounded-lg bg-brand-50 px-3 py-2.5">
                  <div>
                    <div class="font-semibold text-gray-900">
                      <template v-if="c.changed_field === 'Closing Date'">Last date extended to {{ formatDateTime(c.new_value) }}</template>
                      <template v-else>{{ c.remarks || c.new_value }}</template>
                    </div>
                    <div class="text-xs text-gray-600">Issued {{ formatDate(c.corrigendum_date) }}</div>
                  </div>
                  <a v-if="c.corrigendum_attachment" :href="c.corrigendum_attachment" target="_blank" rel="noopener" class="text-xs font-semibold text-brand-700 hover:underline">
                    Corrigendum (PDF)
                  </a>
                </li>
              </ul>
            </div>
          </section>

          <section class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 class="mb-1 flex items-center gap-2 text-xl font-bold text-gray-900">
              <span class="h-6 w-1 rounded-full bg-brand-700" />Before you apply
            </h2>
            <p class="mb-6 text-sm text-gray-600">
              Keep these ready. The form takes about {{ formMinutes }} minutes and can be submitted only once.
            </p>

            <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <h3 class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Documents to upload</h3>
                <ul class="flex flex-col gap-2 text-sm">
                  <li v-for="doc in documents" :key="doc.label" class="flex items-start gap-2.5">
                    <FeatherIcon
                      :name="doc.required ? 'check-circle' : 'circle'"
                      class="mt-0.5 h-4 w-4 shrink-0"
                      :class="doc.required ? 'text-brand-700' : 'text-gray-400'"
                    />
                    <span :class="doc.required ? 'text-gray-800' : 'text-gray-500'">
                      {{ doc.label }}<span v-if="!doc.required" class="text-xs"> (if applicable)</span>
                    </span>
                  </li>
                </ul>
              </div>
              <div v-if="questions.length">
                <h3 class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Eligibility questions</h3>
                <ol class="flex flex-col gap-2.5 text-sm text-gray-700">
                  <li v-for="(q, idx) in questions" :key="idx" class="flex gap-2.5">
                    <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-50 text-[11px] font-bold text-brand-700">
                      {{ idx + 1 }}
                    </span>
                    <span>{{ q.question }}</span>
                  </li>
                </ol>
              </div>
            </div>

            <div v-if="extraSections.length" class="mt-6 rounded-lg bg-gray-50 p-4 text-sm text-gray-700">
              <span class="font-semibold text-gray-900">You'll also be asked about:</span> {{ extraSections.join(', ') }}.
            </div>
          </section>
        </div>

        <!-- Summary -->
        <aside class="lg:sticky lg:top-20 lg:self-start">
          <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <div v-if="deadline" class="border-b px-5 py-4" :class="deadline.urgent ? 'bg-orange-50' : 'bg-brand-50'">
              <div class="text-xs font-semibold uppercase tracking-wide" :class="deadline.urgent ? 'text-orange-700' : 'text-brand-700'">
                Applications close
              </div>
              <div class="mt-0.5 text-lg font-bold text-gray-900">{{ deadline.date }}</div>
              <div class="text-sm" :class="deadline.urgent ? 'text-orange-700' : 'text-gray-600'">{{ deadline.left }}</div>
            </div>
            <dl class="flex flex-col divide-y divide-gray-100 px-5 text-sm">
              <div v-for="item in details" :key="item.label" class="flex gap-3 py-3">
                <FeatherIcon :name="item.icon" class="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />
                <div class="min-w-0">
                  <dt class="text-xs text-gray-500">{{ item.label }}</dt>
                  <dd class="font-medium text-gray-900">{{ item.value }}</dd>
                </div>
              </div>
            </dl>
            <div class="flex flex-col gap-2 border-t p-5">
              <Button variant="solid" size="lg" :class="BTN_BRAND" :disabled="!isOpen" @click="apply">
                {{ isOpen ? 'Apply Now' : closedLabel }}
              </Button>
              <Button variant="outline" icon-left="link" :class="BTN_BRAND_OUTLINE" @click="copyLink">
                {{ copied ? 'Link copied' : 'Copy link to this job' }}
              </Button>
            </div>
          </div>
        </aside>
      </div>
    </template>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'
import { BTN_BRAND, BTN_BRAND_OUTLINE } from '@/utils/buttonStyles'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

// Public: the endpoint only returns Advertised jobs, otherwise job stays null.
const { job, loading, fetchJob } = useJobOpeningDetail()

const form = computed(() => job.value?.form || {})
const isOpen = computed(() => form.value.is_open !== false)
const opensOn = computed(() =>
  form.value.opens_later && form.value.application_start ? dayjs(form.value.application_start).format('D MMM YYYY, h:mm A') : '',
)
const closedLabel = computed(() => (opensOn.value ? `Opens ${opensOn.value}` : 'Applications closed'))

const chips = computed(() =>
  [
    { icon: 'home', text: job.value?.department },
    { icon: 'briefcase', text: job.value?.employment_type },
    { icon: 'users', text: job.value?.vacancies ? `${job.value.vacancies} vacanc${job.value.vacancies == 1 ? 'y' : 'ies'}` : '' },
  ].filter((c) => c.text),
)

const details = computed(() =>
  [
    { icon: 'home', label: 'Department', value: job.value?.department },
    { icon: 'award', label: 'Designation', value: job.value?.designation },
    { icon: 'git-branch', label: 'Recruitment Track', value: job.value?.track },
    { icon: 'briefcase', label: 'Employment Type', value: job.value?.employment_type },
    { icon: 'users', label: 'Vacancies', value: job.value?.vacancies },
    { icon: 'credit-card', label: 'Pay', value: job.value?.pay_level },
    { icon: 'clock', label: 'Tenure', value: job.value?.tenure_description },
  ].filter((d) => d.value),
)

const deadline = computed(() => {
  const value = job.value?.application_deadline
  if (!value) return null
  const close = dayjs(value)
  const days = close.startOf('day').diff(dayjs().startOf('day'), 'day')
  const left = days < 0 ? 'Closed' : days === 0 ? `Closes today at ${close.format('h:mm A')}` : `${days} day${days === 1 ? '' : 's'} left`
  return {
    date: close.format('D MMMM YYYY, h:mm A'),
    left,
    short: days < 0 ? 'Closed' : `${left} · closes ${close.format('D MMM')}`,
    urgent: days >= 0 && days <= 3,
  }
})

// Everything the form will ask the candidate to upload.
const documents = computed(() => {
  const list = [
    { label: 'Resume / CV', required: true },
    { label: 'Statement of Purpose', required: true },
    { label: 'Degree certificates and transcripts', required: true },
  ]
  for (const d of form.value.required_documents || []) list.push({ label: d.label, required: !!d.mandatory })
  return list
})

const questions = computed(() => form.value.screening_questions || [])

const notification = computed(() => job.value?.notice?.notification)
const corrigenda = computed(() => job.value?.notice?.corrigenda || [])

function formatDate(value) {
  return value ? dayjs(value).format('D MMM YYYY') : ''
}
function formatDateTime(value) {
  return value ? dayjs(value).format('D MMM YYYY, h:mm A') : ''
}

const extraSections = computed(() => {
  const s = form.value.sections || {}
  return [
    s.specialization && 'your area of specialization',
    s.phd && 'your PhD',
    s.net && 'NET / SLET / SET',
    s.experience_months && 'teaching and research experience (in months)',
    s.admin_responsibilities && 'administrative responsibilities',
    s.publications && `your publications (up to ${s.max_publications})`,
  ].filter(Boolean)
})

const formMinutes = computed(() => (extraSections.value.length ? 90 : 30))

function apply() {
  if (isOpen.value) router.push(`/portal/jobs/${job.value.name}/apply`)
}

function goBack() {
  if (window.history.state?.back) router.back()
  else router.push('/portal/jobs')
}

const copied = ref(false)
async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    // clipboard unavailable — the address bar has the link
  }
}

onMounted(() => fetchJob(props.id))
</script>
