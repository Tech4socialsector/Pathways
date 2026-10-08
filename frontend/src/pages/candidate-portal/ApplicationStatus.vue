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

        <!-- Progress: the same line as the staff application page -->
        <section class="isolate mb-6 rounded-xl border bg-white p-5 shadow-sm">
          <div class="mb-4 text-xs font-bold uppercase tracking-wide text-brand-700">Your progress</div>
          <ProgressStepper :steps="timelineSteps" />
        </section>

        <div class="mb-6 grid grid-cols-1 items-start gap-6 md:grid-cols-2 xl:grid-cols-3">
            <!-- Files they uploaded with the application -->
            <div class="rounded-xl border bg-white p-5 shadow-sm md:col-span-2 xl:col-span-3">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wide text-brand-700">My documents</span>
                <Button v-if="myDocuments.length" size="sm" variant="ghost" icon-left="eye" @click="openViewer(0)">View all</Button>
              </div>
              <div v-if="submissionLoading" class="text-sm text-gray-500">Loading…</div>
              <p v-else-if="!myDocuments.length" class="text-sm text-gray-500">No documents uploaded.</p>
              <ul v-else class="-mx-2 grid grid-cols-1 gap-x-4 sm:grid-cols-2 lg:grid-cols-3">
                <li v-for="(d, i) in myDocuments" :key="d.file_url + i">
                  <button
                    type="button"
                    class="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left text-sm hover:bg-brand-50"
                    @click="openViewer(i)"
                  >
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-700">
                      <FeatherIcon :name="d.kind === 'image' ? 'image' : 'file-text'" class="h-4 w-4" />
                    </span>
                    <span class="min-w-0 flex-1">
                      <span class="block truncate font-medium text-gray-900">{{ d.label }}</span>
                      <span class="block truncate text-xs text-gray-500">{{ d.group }} · {{ d.file_name }}</span>
                    </span>
                    <FeatherIcon name="eye" class="h-4 w-4 shrink-0 text-gray-400" />
                  </button>
                </li>
              </ul>
            </div>

            <div v-if="status.interviews?.length" class="rounded-xl border bg-white p-5 shadow-sm">
              <div class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Interviews</div>
              <div v-for="(iv, idx) in status.interviews" :key="iv.name || idx" class="mb-4 rounded-lg border p-3 text-sm last:mb-0">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="font-semibold text-gray-900">{{ iv.round_type === 'HR Interaction' ? 'Round 1 · HR interaction' : 'Final interview' }}</span>
                  <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="ivTone(iv)">{{ ivLabel(iv) }}</span>
                </div>
                <div class="mt-1 text-gray-700">{{ dayjs(iv.scheduled_datetime).format('dddd, DD MMM YYYY · h:mm A') }} · {{ iv.mode === 'In-Person' ? 'In person' : 'Online' }}</div>
                <div v-if="iv.location" class="mt-1 flex items-center gap-1 text-gray-700">
                  <FeatherIcon name="map-pin" class="h-3.5 w-3.5 text-gray-400" />{{ iv.location }}
                </div>
                <a v-if="iv.meeting_link && isOpen(iv)" :href="iv.meeting_link" target="_blank" rel="noopener" class="mt-1 inline-flex items-center gap-1 text-brand-700 hover:underline">
                  <FeatherIcon name="video" class="h-3.5 w-3.5" />Join {{ iv.meeting_platform || 'meeting' }}
                </a>
                <div v-if="isOpen(iv) && (iv.rsvp_status || 'Pending') === 'Pending'" class="mt-3 flex flex-wrap items-center gap-2 border-t pt-3">
                  <span class="text-gray-600">Will you attend?</span>
                  <Button size="sm" variant="solid" :class="BTN_BRAND" :loading="rsvpBusy === iv.name + 'Confirmed'" @click="rsvp(iv, 'Confirmed')">Confirm</Button>
                  <Button size="sm" variant="outline" :loading="rsvpBusy === iv.name + 'Declined'" @click="rsvp(iv, 'Declined')">Decline</Button>
                </div>
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
              <div class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Joining documents</div>
              <StatusBadge :status="status.document_status" />
            </div>
        </div>

        <!-- What they submitted, read-only, full width -->
        <section>
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-xs font-bold uppercase tracking-wide text-brand-700">My application</h2>
            <span class="flex items-center gap-1 text-xs text-gray-500"><FeatherIcon name="eye" class="h-3.5 w-3.5" />View only</span>
          </div>
          <ApplicationSubmissionPanel :app="submission" :loading="submissionLoading" :error="submissionError" />
        </section>
      </template>

      <DocumentViewer
        v-model:open="viewerOpen"
        :title="`My documents - ${status?.application_id || ''}`"
        :documents="myDocuments"
        :start-index="viewerIndex"
      />
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import BackButton from '@/components/common/BackButton.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { interviewService } from '@/services/interviews'
import dayjs from 'dayjs'
import ApplicationSubmissionPanel from '@/components/common/ApplicationSubmissionPanel.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import { applicationService } from '@/services/applications'
import { toast } from '@/utils/notify'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ProgressStepper from '@/components/common/ProgressStepper.vue'
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
const myDocuments = computed(() => submission.value?.documents || [])
const viewerOpen = ref(false)
const viewerIndex = ref(0)
function openViewer(i) {
  viewerIndex.value = i
  viewerOpen.value = true
}

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

// ----- interviews: RSVP
const rsvpBusy = ref('')
const isOpen = (iv) => ['Scheduled', 'Rescheduled'].includes(iv.status) && dayjs(iv.scheduled_datetime).isAfter(dayjs())
function ivLabel(iv) {
  if (iv.status === 'Completed') return 'Completed'
  if (iv.status === 'Cancelled') return 'Cancelled'
  if (!isOpen(iv)) return iv.status
  return { Confirmed: 'You confirmed', Declined: 'You declined' }[iv.rsvp_status] || 'Please reply'
}
function ivTone(iv) {
  if (iv.status === 'Completed') return 'bg-green-50 text-green-700'
  if (iv.status === 'Cancelled') return 'bg-gray-100 text-gray-500'
  return { Confirmed: 'bg-green-50 text-green-700', Declined: 'bg-red-50 text-red-700' }[iv.rsvp_status] || 'bg-orange-50 text-orange-700'
}
async function rsvp(iv, response) {
  rsvpBusy.value = iv.name + response
  try {
    await interviewService.respondRsvp(iv.name, response)
    iv.rsvp_status = response
    toast({ title: response === 'Confirmed' ? 'Thank you. Your attendance is confirmed.' : 'Your reply has been sent.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not send your reply.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    rsvpBusy.value = ''
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
