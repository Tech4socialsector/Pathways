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
        </div>

        <!-- Staff opening a candidate's page (e.g. from an email link) -->
        <div v-if="!session.isCandidate" class="mb-6 flex items-start gap-3 rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-900">
          <FeatherIcon name="alert-circle" class="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p class="font-medium">You are signed in as staff ({{ session.user }}), not as this candidate.</p>
            <p class="mt-0.5">Only the candidate can reply to the interview or see their submitted application here. To test as the candidate, use a private window and sign in with their Candidate ID, or use the buttons in the invite email.
              <router-link :to="`/applications/${id}`" class="font-medium text-brand-700 hover:underline">Open this application in Pathways</router-link>.
            </p>
          </div>
        </div>

        <!-- Upcoming interviews: first thing on the page, with the reply -->
        <InterviewReplyCard
          v-for="iv in upcomingInterviews"
          :key="'up-' + iv.name"
          :ref="(el) => (replyCards[iv.name] = el)"
          :interview="iv"
          :highlighted="highlighted === iv.name"
          :can-reply="session.isCandidate"
          @replied="(r) => Object.assign(iv, r)"
        />

        <div class="mb-6 grid grid-cols-1 items-start gap-6 md:grid-cols-2 xl:grid-cols-3">
            <!-- Files they uploaded with the application -->
            <div v-if="session.isCandidate" class="rounded-xl border bg-white p-5 shadow-sm md:col-span-2 xl:col-span-3">
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

            <div v-if="pastInterviews.length" class="rounded-xl border bg-white p-5 shadow-sm">
              <div class="mb-3 text-xs font-bold uppercase tracking-wide text-brand-700">Past interviews</div>
              <div v-for="(iv, idx) in pastInterviews" :key="iv.name || idx" class="mb-4 rounded-lg border p-3 text-sm last:mb-0">
                <div class="font-semibold text-gray-900">{{ iv.round_type === 'HR Interaction' ? 'Round 1 · HR interaction' : 'Final interview' }}</div>
                <div class="mt-1 text-gray-700">{{ dayjs(iv.scheduled_datetime).format('dddd, DD MMM YYYY · h:mm A [IST]') }} · {{ iv.mode === 'In-Person' ? 'In person' : 'Online' }}</div>
                <div v-if="iv.location" class="mt-1 flex items-center gap-1 text-gray-700">
                  <FeatherIcon name="map-pin" class="h-3.5 w-3.5 text-gray-400" />{{ iv.location }}
                </div>
                <a v-if="iv.meeting_link && isOpen(iv)" :href="iv.meeting_link" target="_blank" rel="noopener" class="mt-1 inline-flex items-center gap-1 text-brand-700 hover:underline">
                  <FeatherIcon name="video" class="h-3.5 w-3.5" />Join {{ iv.meeting_platform || 'meeting' }}
                </a>
              </div>
            </div>

            <CandidateOfferCard :application="id" @changed="fetchStatus(id)" />

        </div>

        <!-- Joining documents: checklist, upload and verification status -->
        <OnboardingDocumentsPanel v-if="status.document_status" :application="id" :can-edit="session.isCandidate" />

        <!-- What they submitted, read-only, full width -->
        <section v-if="session.isCandidate">
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
import { useSessionStore } from '@/stores/session'
import BackButton from '@/components/common/BackButton.vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import ApplicationSubmissionPanel from '@/components/common/ApplicationSubmissionPanel.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import { applicationService } from '@/services/applications'
import { toast } from '@/utils/notify'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import OnboardingDocumentsPanel from '@/components/candidate/OnboardingDocumentsPanel.vue'
import { useApplicationStatus } from '@/composables/useApplications'
import CandidateOfferCard from '@/components/offers/CandidateOfferCard.vue'
import InterviewReplyCard from '@/components/candidate/InterviewReplyCard.vue'

const session = useSessionStore()
const props = defineProps({ id: { type: String, required: true } })

const { status, loading, error, fetchStatus } = useApplicationStatus()

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

// ----- interviews: upcoming ones at the top, past ones in the card below
const upcomingInterviews = computed(() => (status.value?.interviews || []).filter((iv) => isOpen(iv)))
const pastInterviews = computed(() => (status.value?.interviews || []).filter((iv) => !isOpen(iv)))

const isOpen = (iv) => ['Scheduled', 'Rescheduled'].includes(iv.status) && dayjs(iv.scheduled_datetime).isAfter(dayjs())

// Ask before replying. The invite email links here with ?interview=…,
// so the candidate signs in and answers on the portal, not in the email.
const route = useRoute()
const router = useRouter()
const highlighted = ref('')
const replyCards = {}
watch(
  () => status.value?.interviews,
  async (list) => {
    const wanted = route.query.interview
    const answer = route.query.rsvp
    if (!list || !wanted) return
    const iv = upcomingInterviews.value.find((x) => x.name === wanted)
    // Done with the query either way, so a refresh does not ask again.
    router.replace({ query: {} })
    if (!iv) {
      toast({ title: 'This interview is no longer open for a reply. See the details below.', icon: 'info', iconClasses: 'text-blue-500' })
      return
    }
    highlighted.value = iv.name
    await nextTick()
    document.getElementById('interview-' + iv.name)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    // "Click here to respond": the card is highlighted and they choose.
    // Older emails had separate accept / decline links: ask that one.
    if (answer && (iv.rsvp_status || 'Pending') === 'Pending' && session.isCandidate) {
      const response = { Declined: 'Withdrawn', Withdrawn: 'Withdrawn', 'Reschedule Requested': 'Reschedule Requested' }[answer] || 'Confirmed'
      replyCards[iv.name]?.openReply(response)
    }
  },
)

function formatDay(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

onMounted(() => {
  fetchStatus(props.id)
  if (session.isCandidate) fetchSubmission(props.id)
})
watch(() => props.id, (id) => {
  fetchStatus(id)
  if (session.isCandidate) fetchSubmission(id)
})
</script>
