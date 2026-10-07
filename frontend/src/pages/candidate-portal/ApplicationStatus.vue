<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div v-if="loading" class="flex flex-col gap-4">
        <div class="h-24 animate-pulse rounded-xl border bg-white" />
        <div class="h-64 animate-pulse rounded-xl border bg-white" />
      </div>
      <div v-else-if="error" class="mx-auto max-w-md rounded-xl border bg-white p-8 text-center shadow-sm">
        <FeatherIcon name="alert-circle" class="mx-auto h-8 w-8 text-red-500" />
        <h1 class="mt-3 font-heading text-lg font-bold text-gray-900">We couldn't open this application</h1>
        <p class="mt-1 text-sm text-gray-500">{{ error?.messages?.[0] || 'It may not belong to your account.' }}</p>
        <Button class="mt-4" variant="outline" @click="$router.push('/portal/applications')">Back to my applications</Button>
      </div>
      <template v-else-if="status">
        <BackButton fallback="/portal/applications" label="My applications" class="mb-4" />
        <div class="mb-6 flex flex-wrap items-start justify-between gap-3 rounded-xl border bg-white p-5 shadow-sm">
          <div class="min-w-0">
            <h1 class="font-heading text-2xl font-bold text-gray-900">{{ status.job_title }}</h1>
            <p class="mt-1 text-sm text-gray-500">
              {{ status.department }} · <span class="font-mono">{{ status.application_id }}</span> · Applied {{ formatDay(status.application_date) }}
            </p>
          </div>
          <StatusBadge :status="status.status" />
          <div class="flex w-full items-start gap-3 rounded-lg px-4 py-3 text-sm" :class="headline.tone">
            <FeatherIcon :name="headline.icon" class="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div class="font-semibold">{{ headline.title }}</div>
              <div class="mt-0.5 opacity-90">{{ headline.text }}</div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div class="flex flex-col gap-6">
            <div class="rounded-xl border bg-white p-5 shadow-sm">
              <div class="mb-4 text-xs font-bold uppercase tracking-wide text-brand-700">Your progress</div>
              <RecruitmentTimeline :steps="timelineSteps" />
            </div>

            <div v-if="status.interviews?.length" class="rounded-xl border bg-white p-5 shadow-sm">
              <div class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Interviews</div>
              <div v-for="(iv, idx) in status.interviews" :key="idx" class="mb-3 text-sm last:mb-0">
                <div class="font-medium text-gray-900">{{ iv.round_type }}</div>
                <div class="text-gray-600">{{ formatDate(iv.scheduled_datetime) }} · {{ iv.mode }}</div>
                <a v-if="iv.meeting_link" :href="iv.meeting_link" target="_blank" rel="noopener" class="text-brand-700 hover:underline">
                  Join meeting
                </a>
              </div>
            </div>

            <div v-if="offer.offer.value" class="rounded-xl border bg-white p-5 shadow-sm">
              <div class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Offer</div>
              <StatusBadge :status="offer.offer.value.status" />
              <p v-if="offer.offer.value.acceptance_deadline" class="mt-1 text-xs text-gray-500">
                Please respond by {{ offer.offer.value.acceptance_deadline }}
              </p>
              <div v-if="offer.offer.value.status === 'Sent'" class="mt-4 flex flex-col gap-3">
                <FormControl label="Confirmed Date of Joining" type="date" v-model="confirmedDoj" />
                <div class="flex gap-2">
                  <Button variant="solid" theme="green" @click="respondAccept">Accept Offer</Button>
                  <Button variant="outline" theme="red" @click="respondDecline">Decline</Button>
                </div>
              </div>
            </div>

            <div v-if="status.document_status" class="rounded-xl border bg-white p-5 shadow-sm">
              <div class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Documents</div>
              <StatusBadge :status="status.document_status" />
            </div>
          </div>

          <!-- What they submitted, read-only -->
          <div class="lg:col-span-2">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-xs font-bold uppercase tracking-wide text-brand-700">My application</h2>
              <span class="flex items-center gap-1 text-xs text-gray-500"><FeatherIcon name="eye" class="h-3.5 w-3.5" />View only</span>
            </div>
            <ApplicationSubmissionPanel :app="submission" :loading="submissionLoading" :error="submissionError" />
          </div>
        </div>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import BackButton from '@/components/common/BackButton.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import ApplicationSubmissionPanel from '@/components/common/ApplicationSubmissionPanel.vue'
import { applicationService } from '@/services/applications'
import { toast } from '@/utils/notify'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
import { useApplicationStatus } from '@/composables/useApplications'
import { useMyOffer } from '@/composables/useOffers'

const props = defineProps({ id: { type: String, required: true } })

const { status, loading, error, fetchStatus } = useApplicationStatus()
const offer = useMyOffer()
const confirmedDoj = ref('')

// The same six stages as the My Applications list.
const STAGES = [
  { key: 'received', label: 'Application received', detail: 'We have your application and documents.' },
  { key: 'screening', label: 'Screening', detail: 'Eligibility and documents are checked.' },
  { key: 'shortlisted', label: 'Shortlisted', detail: 'The committee shortlists candidates for interview.' },
  { key: 'interview', label: 'Interview', detail: 'Interview details are emailed and shown here.' },
  { key: 'decision', label: 'Decision & offer', detail: 'The selection outcome and any offer.' },
  { key: 'joining', label: 'Joining', detail: 'Documents and onboarding.' },
]
const STAGE_OF = {
  Submitted: 0,
  'Under Review': 1,
  Shortlisted: 2,
  'Interview Scheduled': 3,
  'Interview Completed': 3,
  Selected: 4,
  'Offer Extended': 4,
  'Offer Declined': 4,
  'Offer Accepted': 5,
  'Documents Pending': 5,
  'Documents Verified': 5,
  Joined: 5,
}

const timelineSteps = computed(() => {
  if (!status.value) return []
  const current = status.value.status
  if (current === 'Not Selected' || current === 'Withdrawn') {
    return [
      { ...STAGES[0], state: 'completed' },
      { ...STAGES[1], state: 'completed' },
      {
        key: current,
        label: current === 'Withdrawn' ? 'Withdrawn' : 'Not progressed',
        detail: current === 'Withdrawn' ? 'You withdrew this application.' : 'Your application was not taken forward.',
        state: 'rejected',
      },
    ]
  }
  const idx = STAGE_OF[current] ?? 1
  const done = current === 'Joined'
  return STAGES.map((step, i) => ({
    ...step,
    state: i < idx || (done && i === idx) ? 'completed' : i === idx ? 'current' : 'pending',
  }))
})

const HEADLINES = {
  Submitted: ['inbox', 'Application received', 'Your application is in the queue for screening.'],
  'Under Review': ['search', 'Under review', 'The recruitment team is reviewing eligibility and documents. We will email you when there is an update.'],
  Shortlisted: ['star', 'You have been shortlisted', 'Interview details will be emailed to you and shown on this page.'],
  'Interview Scheduled': ['calendar', 'Interview scheduled', 'See the interview details below.'],
  'Interview Completed': ['check-circle', 'Interview completed', 'The selection committee is finalising its decision.'],
  Selected: ['award', 'Selected', 'Your offer is being prepared.'],
  'Offer Extended': ['mail', 'Offer extended', 'Please review and respond to your offer below.'],
  'Offer Accepted': ['thumbs-up', 'Offer accepted', 'We will be in touch about joining documents.'],
  'Offer Declined': ['x-circle', 'Offer declined', 'You declined the offer.'],
  'Documents Pending': ['file-text', 'Documents pending', 'Please submit the joining documents requested by email.'],
  'Documents Verified': ['check-square', 'Documents verified', 'You are all set for joining.'],
  Joined: ['smile', 'Welcome to NLSIU', 'You have joined.'],
  'Not Selected': ['info', 'Not taken forward', 'Thank you for your interest. Unfortunately your application was not taken forward this time.'],
  Withdrawn: ['slash', 'Withdrawn', 'You withdrew this application.'],
}
const headline = computed(() => {
  const st = status.value?.status
  const [icon, title, text] = HEADLINES[st] || ['info', st, '']
  const tone = st === 'Not Selected' || st === 'Withdrawn' || st === 'Offer Declined'
    ? 'bg-gray-50 text-gray-700'
    : ['Shortlisted', 'Selected', 'Offer Extended', 'Offer Accepted', 'Joined'].includes(st)
      ? 'bg-green-50 text-green-800'
      : 'bg-brand-50 text-brand-900'
  return { icon, title, text, tone }
})

const submission = ref(null)
const submissionLoading = ref(false)
const submissionError = ref('')

async function fetchSubmission(id) {
  submissionLoading.value = true
  submissionError.value = ''
  try {
    submission.value = await applicationService.getMyApplicationDetail(id)
  } catch (e) {
    submission.value = null
    submissionError.value = e?.messages?.[0] || 'Could not load your application.'
  } finally {
    submissionLoading.value = false
  }
}

function formatDay(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function respondAccept() {
  if (!confirmedDoj.value) {
    toast({ title: 'Please select your confirmed date of joining before accepting.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    return
  }
  try {
    await offer.respond(offer.offer.value.name, 'Accepted', confirmedDoj.value)
    toast({ title: 'Offer accepted. Congratulations!', icon: 'check', iconClasses: 'text-green-500' })
    await offer.fetchOffer(props.id)
    await fetchStatus(props.id)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not accept the offer.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

async function respondDecline() {
  try {
    await offer.respond(offer.offer.value.name, 'Declined')
    toast({ title: 'Offer declined.', icon: 'info', iconClasses: 'text-gray-500' })
    await offer.fetchOffer(props.id)
    await fetchStatus(props.id)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not decline the offer.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

onMounted(() => {
  fetchStatus(props.id)
  offer.fetchOffer(props.id)
  fetchSubmission(props.id)
})
watch(() => props.id, (id) => {
  fetchStatus(id)
  offer.fetchOffer(id)
  fetchSubmission(id)
})
</script>
