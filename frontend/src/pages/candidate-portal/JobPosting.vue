<template>
  <CandidatePortalLayout>
    <!-- Loading -->
    <div v-if="loading" class="animate-pulse" aria-busy="true">
      <div class="border-b bg-brand-50/50">
        <div class="mx-auto max-w-6xl px-4 pb-10 pt-16 sm:px-6">
          <div class="h-6 w-48 rounded-full bg-white" />
          <div class="mt-5 h-9 w-2/3 rounded bg-white" />
          <div class="mt-5 h-4 w-1/2 rounded bg-white" />
        </div>
      </div>
      <div class="mx-auto mt-8 grid max-w-6xl gap-8 px-4 sm:px-6 lg:grid-cols-[minmax(0,1fr)_21rem]">
        <div class="h-96 rounded-2xl border bg-white" />
        <div class="h-80 rounded-2xl border bg-white" />
      </div>
    </div>

    <div v-else-if="!job" class="mx-auto max-w-3xl px-6 py-16">
      <EmptyState title="This position is not currently open for applications" description="It may have closed or been filled.">
        <template #action>
          <Button @click="router.push('/portal/jobs')">View current openings</Button>
        </template>
      </EmptyState>
    </div>

    <template v-else>
      <!-- Header -->
      <section class="border-b bg-gradient-to-b from-brand-50/70 to-white">
        <div class="mx-auto max-w-6xl px-4 pb-8 pt-5 sm:px-6 sm:pb-10">
          <button
            type="button"
            class="-ml-2 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-gray-600 transition hover:bg-white hover:text-gray-900"
            @click="goBack"
          >
            <FeatherIcon name="arrow-left" class="h-4 w-4" /> All openings
          </button>

          <div class="mt-6 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div class="min-w-0 max-w-3xl">
              <div class="flex flex-wrap items-center gap-x-3 gap-y-2">
                <span
                  class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium"
                  :class="cta.kind === 'open' ? 'bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100' : 'bg-gray-100 text-gray-600'"
                >
                  <span class="relative flex h-2 w-2">
                    <span v-if="cta.kind === 'open'" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-60" />
                    <span class="relative inline-flex h-2 w-2 rounded-full" :class="cta.kind === 'open' ? 'bg-brand-600' : 'bg-gray-400'" />
                  </span>
                  {{ statusLabel }}
                </span>
                <span v-if="eyebrow" class="text-sm font-medium uppercase tracking-wider text-gray-500">{{ eyebrow }}</span>
              </div>
              <h1 class="mt-4 font-heading text-3xl font-bold leading-tight text-gray-900 sm:text-[2.25rem]">{{ job.job_title }}</h1>
              <ul class="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-base text-gray-600">
                <li v-for="m in headerMeta" :key="m.icon" class="inline-flex items-center gap-1.5">
                  <FeatherIcon :name="m.icon" class="h-4 w-4 text-gray-400" />{{ m.text }}
                </li>
              </ul>
            </div>
            <div class="flex shrink-0 gap-2">
              <Button icon-left="link" @click="copyLink">{{ copyLabel }}</Button>
              <Button v-if="canShare" icon-left="share-2" @click="share">Share</Button>
            </div>
          </div>
        </div>
      </section>

      <!-- Body -->
      <div class="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-4 pb-10 pt-8 sm:px-6 lg:grid-cols-[minmax(0,1fr)_21rem] lg:pb-16">
        <article class="min-w-0 divide-y overflow-hidden rounded-2xl border bg-white shadow-sm">
          <!-- About -->
          <section class="p-6 sm:p-8" aria-labelledby="about-heading">
            <h2 id="about-heading" class="section-title">About the role</h2>
            <div
              v-if="hasText(job.jd_text)"
              class="prose mt-4 max-w-none text-gray-700 prose-headings:font-heading prose-headings:text-gray-900 prose-a:text-brand-700"
              v-html="job.jd_text"
            />
            <p v-else class="mt-3 text-p-base text-gray-600">
              The full job description is in the official notification<template v-if="job.jd_attachment"> and the document below</template>.
              Shortlisted candidates receive further details.
            </p>
            <a
              v-if="job.jd_attachment"
              :href="job.jd_attachment"
              target="_blank"
              rel="noopener"
              class="mt-5 inline-flex items-center gap-3 rounded-xl border px-4 py-3 transition hover:border-brand-200 hover:bg-brand-50/40"
            >
              <FeatherIcon name="file-text" class="h-5 w-5 text-brand-700" />
              <span class="text-base font-medium text-gray-900">Job description</span>
              <FeatherIcon name="download" class="h-4 w-4 text-gray-400" />
            </a>
          </section>

          <!-- Post-specific instructions -->
          <section v-if="hasText(form.instructions?.job)" class="p-6 sm:p-8" aria-labelledby="instructions-heading">
            <h2 id="instructions-heading" class="section-title">Instructions for this post</h2>
            <div class="prose mt-4 max-w-none text-gray-700 prose-a:text-brand-700" v-html="form.instructions.job" />
          </section>

          <!-- Eligibility (hidden for now)
          <section v-if="eligibility.length || questions.length" class="p-6 sm:p-8" aria-labelledby="eligibility-heading">
            <h2 id="eligibility-heading" class="section-title">Eligibility at a glance</h2>
            <p class="mt-1 text-p-sm text-gray-500">The official notification has the full criteria.</p>
            <ul v-if="eligibility.length" class="mt-4 flex flex-col gap-2.5">
              <li v-for="item in eligibility" :key="item" class="flex items-start gap-3 text-p-base text-gray-800">
                <FeatherIcon name="check" class="mt-1 h-4 w-4 shrink-0 text-brand-700" />{{ item }}
              </li>
            </ul>
            <template v-if="questions.length">
              <h3 class="mt-6 text-sm font-semibold text-gray-900">You'll be asked to confirm</h3>
              <ol class="mt-3 flex flex-col gap-2.5">
                <li v-for="(q, idx) in questions" :key="idx" class="flex gap-3 text-p-base text-gray-700">
                  <span class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-700">{{ idx + 1 }}</span>
                  <span>{{ q.question }}</span>
                </li>
              </ol>
            </template>
          </section>
          -->

          <!-- Documents -->
          <section class="p-6 sm:p-8" aria-labelledby="documents-heading">
            <h2 id="documents-heading" class="section-title">What you'll need</h2>
            <p class="mt-1 text-p-sm text-gray-500">
              Keep these ready. The form takes about {{ formMinutes }} minutes, saves your progress on this device, and can be submitted once.
            </p>
            <ul class="mt-5 grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-2">
              <li v-for="doc in documents" :key="doc.label" class="flex items-start gap-3">
                <FeatherIcon
                  :name="doc.required ? 'check-circle' : 'circle'"
                  class="mt-0.5 h-4 w-4 shrink-0"
                  :class="doc.required ? 'text-brand-700' : 'text-gray-300'"
                />
                <span class="text-p-base" :class="doc.required ? 'text-gray-800' : 'text-gray-500'">
                  {{ doc.label }}<span v-if="!doc.required" class="text-sm text-gray-400"> · if applicable</span>
                </span>
              </li>
            </ul>
            <p v-if="uploadNote" class="mt-5 flex items-start gap-2 rounded-xl bg-gray-50 px-4 py-3 text-p-sm text-gray-600">
              <FeatherIcon name="info" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />{{ uploadNote }}
            </p>
            <p v-if="extraSections.length" class="mt-3 text-p-sm text-gray-600">
              <span class="font-semibold text-gray-900">The form also asks about</span> {{ joinList(extraSections) }}.
            </p>
          </section>

          <!-- Process -->
          <section class="p-6 sm:p-8" aria-labelledby="process-heading">
            <h2 id="process-heading" class="section-title">How selection works</h2>
            <ol class="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
              <li v-for="(step, idx) in PROCESS" :key="step.title" class="flex gap-3">
                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-700 text-xs font-semibold text-white">{{ idx + 1 }}</span>
                <div class="min-w-0">
                  <h3 class="text-base font-semibold text-gray-900">{{ step.title }}</h3>
                  <p class="mt-1 text-p-sm text-gray-600">{{ step.text }}</p>
                </div>
              </li>
            </ol>
          </section>

          <!-- Official notification and corrigenda: only when there is something to show. -->
          <section v-if="hasNotice" class="p-6 sm:p-8" aria-labelledby="notice-heading">
            <h2 id="notice-heading" class="section-title">Official notification</h2>
            <div v-if="noticeHasDetails" class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-3">
              <div v-if="notification.notification_number || notification.publish_date" class="min-w-0">
                <div v-if="notification.notification_number" class="text-base font-semibold text-gray-900">{{ notification.notification_number }}</div>
                <div v-if="notification.publish_date" class="text-sm text-gray-500">Dated {{ formatDate(notification.publish_date) }}</div>
              </div>
              <div class="flex flex-wrap gap-2 sm:ml-auto">
                <a v-if="notification.notification_attachment" :href="notification.notification_attachment" target="_blank" rel="noopener" class="link-button">
                  <FeatherIcon name="file-text" class="h-4 w-4" /> Notification (PDF)
                </a>
                <a v-if="notification.notification_url" :href="notification.notification_url" target="_blank" rel="noopener noreferrer" class="link-button">
                  <FeatherIcon name="external-link" class="h-4 w-4" /> Official notice
                </a>
              </div>
            </div>
            <div v-if="corrigenda.length" class="mt-6">
              <h3 class="text-sm font-semibold text-gray-900">Corrigenda</h3>
              <ul class="mt-3 divide-y rounded-xl border">
                <li v-for="(c, idx) in corrigenda" :key="idx" class="flex flex-wrap items-start justify-between gap-3 px-4 py-3">
                  <div class="min-w-0">
                    <div class="text-sm font-medium text-gray-900">
                      <template v-if="c.changed_field === 'Closing Date'">Last date extended to {{ formatDateTime(c.new_value) }}</template>
                      <template v-else>{{ c.remarks || c.new_value }}</template>
                    </div>
                    <div class="mt-0.5 text-xs text-gray-500">Issued {{ formatDate(c.corrigendum_date) }}</div>
                  </div>
                  <a v-if="c.corrigendum_attachment" :href="c.corrigendum_attachment" target="_blank" rel="noopener" class="inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:underline">
                    <FeatherIcon name="file-text" class="h-3.5 w-3.5" /> PDF
                  </a>
                </li>
              </ul>
            </div>
          </section>
        </article>

        <!-- Apply card. On phones it comes first (closing date and details up
             front) and its button is left to the bottom bar. -->
        <aside class="order-first lg:order-none">
          <div class="overflow-hidden rounded-2xl border bg-white shadow-sm lg:sticky lg:top-24">
            <div class="p-6">
              <template v-if="deadline">
                <div class="text-sm font-medium" :class="deadline.urgent ? 'text-orange-700' : 'text-gray-500'">
                  {{ deadline.closed ? 'Applications closed' : 'Applications close' }}
                </div>
                <div class="mt-1 text-lg font-bold text-gray-900">{{ deadline.date }}</div>
                <div v-if="!deadline.closed" class="mt-3 flex items-center gap-2 text-sm" :class="deadline.urgent ? 'font-medium text-orange-700' : 'text-gray-600'">
                  <FeatherIcon name="clock" class="h-4 w-4" />{{ deadline.left }}
                </div>
              </template>
              <Button
                variant="solid"
                size="lg"
                class="mt-5 hidden w-full lg:flex"
                :class="BTN_BRAND"
                :disabled="cta.disabled"
                :icon-right="cta.kind === 'open' ? 'arrow-right' : undefined"
                @click="cta.action?.()"
              >
                {{ cta.label }}
              </Button>
              <p v-if="cta.note" class="mt-3 text-p-sm text-gray-600">{{ cta.note }}</p>
              <Button v-if="cta.secondary" variant="outline" class="mt-3 w-full" :class="BTN_BRAND_OUTLINE" @click="cta.secondary.action()">
                {{ cta.secondary.label }}
              </Button>
            </div>
            <dl class="divide-y border-t bg-gray-50/60 px-6">
              <div v-for="d in details" :key="d.label" class="flex items-baseline justify-between gap-4 py-3">
                <dt class="shrink-0 text-sm text-gray-500">{{ d.label }}</dt>
                <dd class="min-w-0 text-right text-sm font-medium text-gray-900">{{ d.value }}</dd>
              </div>
            </dl>
          </div>
        </aside>
      </div>

      <!-- Mobile: there is no side card, so keep the action in reach. Sticky
           (not fixed) so it comes to rest above the footer. -->
      <div class="sticky bottom-0 z-20 border-t bg-white/95 px-4 py-3 shadow-[0_-4px_12px_rgba(0,0,0,0.06)] backdrop-blur lg:hidden">
        <div class="mx-auto flex max-w-6xl items-center gap-3">
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-semibold text-gray-900">{{ job.job_title }}</div>
            <div class="truncate text-xs" :class="deadline?.urgent ? 'text-orange-700' : 'text-gray-500'">
              {{ cta.note && cta.kind !== 'open' ? cta.note : deadline ? deadline.left : statusLabel }}
            </div>
          </div>
          <Button variant="solid" :class="BTN_BRAND" :disabled="cta.disabled" @click="cta.action?.()">{{ cta.short || cta.label }}</Button>
        </div>
      </div>
    </template>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
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

const PROCESS = [
  { title: 'Apply online', text: 'Fill in the form and upload your documents before the closing date. You get an application ID when you submit.' },
  { title: 'Eligibility check', text: 'Applications are checked against the criteria in the official notification.' },
  { title: 'Shortlisting', text: 'A committee reviews eligible applications and shortlists candidates for interview.' },
  { title: 'Interview', text: 'Shortlisted candidates are told the interview date, time and format.' },
  { title: 'Offer', text: 'Selected candidates receive an offer, then submit their documents for verification.' },
]

const form = computed(() => job.value?.form || {})
const viewer = computed(() => job.value?.viewer || {})
const isOpen = computed(() => form.value.is_open !== false)
const opensOn = computed(() =>
  form.value.opens_later && form.value.application_start ? dayjs(form.value.application_start).format('D MMM YYYY, h:mm A') : '',
)

// Rich-text fields can hold just "<p></p>" when emptied in the editor.
const hasText = (html) => Boolean(html && String(html).replace(/<[^>]*>|&nbsp;/g, '').trim())

const eyebrow = computed(() => (job.value?.track ? `${job.value.track} track` : ''))

const statusLabel = computed(() => {
  if (opensOn.value) return `Opens ${opensOn.value}`
  if (!isOpen.value) return 'Applications closed'
  return 'Accepting applications'
})

// What the main button does for this viewer.
const cta = computed(() => {
  if (viewer.value.already_applied) {
    return {
      kind: 'applied',
      label: 'View my applications',
      short: 'My applications',
      note: `You've applied for this position (${viewer.value.already_applied}). An application can be submitted only once.`,
      action: () => router.push('/portal/applications'),
    }
  }
  if (viewer.value.is_staff) {
    return {
      kind: 'staff',
      label: 'Apply Now',
      disabled: true,
      note: "You're signed in with a staff account. Candidates apply with their personal email.",
      secondary: { label: 'Open in Pathways', action: () => router.push(`/jobs/${job.value.name}`) },
    }
  }
  if (opensOn.value) return { kind: 'later', label: `Opens ${opensOn.value}`, short: 'Opens soon', disabled: true }
  if (!isOpen.value) return { kind: 'closed', label: 'Applications closed', short: 'Closed', disabled: true }
  return { kind: 'open', label: 'Apply now', action: apply }
})

const payLabel = computed(() => {
  const pay = String(job.value?.pay_level || '').trim()
  if (!pay) return ''
  return /^\d/.test(pay) ? `Level ${pay}` : pay
})

const vacancyText = computed(() => {
  const n = Number(job.value?.vacancies) || 0
  return n ? `${n} ${n === 1 ? 'post' : 'posts'}` : ''
})

const headerMeta = computed(() =>
  [
    { icon: 'home', text: job.value?.department },
    { icon: 'briefcase', text: job.value?.employment_type },
    { icon: 'users', text: vacancyText.value },
    { icon: 'map-pin', text: 'Bengaluru' },
  ].filter((m) => m.text),
)

const details = computed(() =>
  [
    { label: 'Track', value: job.value?.track },
    { label: 'Designation', value: job.value?.designation },
    { label: 'Department', value: job.value?.department },
    { label: 'Employment', value: job.value?.employment_type },
    { label: 'Vacancies', value: vacancyText.value },
    { label: 'Pay (VII CPC)', value: payLabel.value },
    { label: 'Tenure', value: job.value?.tenure_description },
  ].filter((d) => d.value),
)

const deadline = computed(() => {
  const value = job.value?.application_deadline
  if (!value) return null
  const close = dayjs(value)
  const closed = close.isBefore(dayjs())
  const days = close.startOf('day').diff(dayjs().startOf('day'), 'day')
  const left = closed
    ? 'Closed'
    : days === 0
      ? `Closes today at ${close.format('h:mm A')}`
      : `${days} day${days === 1 ? '' : 's'} left`
  return { date: close.format('D MMMM YYYY, h:mm A'), left, closed, urgent: !closed && days <= 3 }
})

const eligibility = computed(() => (form.value.require_postgraduate ? ['A postgraduate degree is required.'] : []))
const questions = computed(() => form.value.screening_questions || [])

// Everything the form asks the candidate to upload.
const documents = computed(() => {
  const list = [
    { label: 'Resume / CV', required: true },
    { label: 'Statement of Purpose', required: true },
    { label: 'Degree certificates and transcripts', required: true },
  ]
  for (const d of form.value.required_documents || []) list.push({ label: d.label, required: Boolean(d.mandatory) })
  return list
})

const uploadNote = computed(() => {
  const rule = form.value.upload_rule
  if (!rule) return ''
  const formats = (rule.formats || []).map((f) => String(f).toUpperCase()).join(', ')
  const parts = [formats && `Accepted formats: ${formats}`, rule.max_size_mb && `up to ${rule.max_size_mb} MB per file`].filter(Boolean)
  return parts.length ? `${parts.join(', ')}, unless the form says otherwise for a document.` : ''
})

const extraSections = computed(() => {
  const s = form.value.sections || {}
  return [
    s.specialization && 'your area of specialisation',
    s.phd && 'your PhD',
    s.net && 'NET / SLET / SET',
    s.experience_months && 'teaching and research experience (in months)',
    s.admin_responsibilities && 'administrative responsibilities',
    s.publications && `your publications (up to ${s.max_publications})`,
  ].filter(Boolean)
})
const joinList = (items) => (items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`)

const formMinutes = computed(() => (extraSections.value.length ? 90 : 30))

const notification = computed(() => job.value?.notice?.notification || null)
const corrigenda = computed(() => job.value?.notice?.corrigenda || [])
// A notification record can exist with every field still blank.
const noticeHasDetails = computed(() => {
  const n = notification.value
  return Boolean(n && (n.notification_number || n.publish_date || n.notification_url || n.notification_attachment))
})
const hasNotice = computed(() => noticeHasDetails.value || corrigenda.value.length > 0)

function formatDate(value) {
  return value ? dayjs(value).format('D MMM YYYY') : ''
}
function formatDateTime(value) {
  return value ? dayjs(value).format('D MMM YYYY, h:mm A') : ''
}

function apply() {
  if (isOpen.value) router.push(`/portal/jobs/${job.value.name}/apply`)
}

function goBack() {
  if (window.history.state?.back) router.back()
  else router.push('/portal/jobs')
}

// Copy and share. The Clipboard API needs HTTPS (or localhost), so fall back
// to a hidden textarea on plain-HTTP deployments.
const copyState = ref('')
let copyTimer = null
const copyLabel = computed(() => (copyState.value === 'copied' ? 'Link copied' : copyState.value === 'failed' ? 'Copy from address bar' : 'Copy link'))
async function copyLink() {
  const url = window.location.href
  let ok = false
  try {
    await navigator.clipboard.writeText(url)
    ok = true
  } catch {
    const area = document.createElement('textarea')
    area.value = url
    area.setAttribute('readonly', '')
    area.style.position = 'fixed'
    area.style.opacity = '0'
    document.body.appendChild(area)
    area.select()
    try {
      ok = document.execCommand('copy')
    } catch {
      ok = false
    }
    area.remove()
  }
  copyState.value = ok ? 'copied' : 'failed'
  clearTimeout(copyTimer)
  copyTimer = setTimeout(() => (copyState.value = ''), 2500)
}

const canShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function'
async function share() {
  try {
    await navigator.share({ title: job.value.job_title, text: `${job.value.job_title} at NLSIU`, url: window.location.href })
  } catch {
    // dismissed by the user
  }
}

onMounted(() => fetchJob(props.id))
onBeforeUnmount(() => clearTimeout(copyTimer))
</script>

<style scoped>
.section-title {
  @apply font-heading text-xl font-bold text-gray-900;
}
.link-button {
  @apply inline-flex items-center gap-1.5 rounded-lg border border-brand-200 px-3 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50;
}
</style>
