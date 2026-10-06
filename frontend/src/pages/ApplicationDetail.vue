<template>
  <StaffLayout>
    <PageHeader
      :title="candidate.full_name || status?.application_id || 'Application'"
      :breadcrumbs="[{ label: 'Applications', to: '/applications' }, { label: status?.application_id || 'Application' }]"
    >
      <template #meta>
        <div v-if="status" class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm text-gray-600">
          <span class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-xs font-medium text-gray-700">{{ status.application_id }}</span>
          <StatusBadge :status="status.status" />
          <span class="flex items-center gap-1.5">
            <FeatherIcon name="briefcase" class="h-3.5 w-3.5 text-brand-700" />{{ status.job_title }}
          </span>
          <span v-if="status.application_date" class="flex items-center gap-1.5">
            <FeatherIcon name="calendar" class="h-3.5 w-3.5 text-brand-700" />Applied {{ formatDate(status.application_date) }}
          </span>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" icon-left="eye" :class="BTN_DARK" @click="openDocuments">View Documents</Button>
        <Button
          variant="solid"
          icon-left="download"
          :class="BTN_DARK"
          :link="downloadAllUrl"
          title="All documents merged into one PDF"
        >
          Download All
        </Button>
        <Button v-if="statusOptions.can_change" variant="solid" icon-left="edit-3" :class="BTN_BRAND" @click="openStatusDialog">
          Change Status
        </Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto bg-gray-50">
      <div v-if="loading && !status" class="p-6 text-sm text-gray-500">Loading...</div>
      <div v-else-if="status" class="flex flex-col gap-6 p-4 sm:p-6">
        <!-- Candidate summary -->
        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex flex-col gap-5 xl:flex-row xl:items-center">
            <div class="flex min-w-0 flex-1 items-center gap-4">
              <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-brand-700 text-lg font-bold text-white">
                {{ initials }}
              </div>
              <div class="min-w-0">
                <div class="truncate text-lg font-bold text-gray-900">{{ candidate.full_name || '—' }}</div>
                <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
                  <a v-if="candidate.email" :href="`mailto:${candidate.email}`" class="flex items-center gap-1.5 hover:text-brand-700">
                    <FeatherIcon name="mail" class="h-3.5 w-3.5" />{{ candidate.email }}
                  </a>
                  <span v-if="candidate.mobile_number" class="flex items-center gap-1.5">
                    <FeatherIcon name="phone" class="h-3.5 w-3.5" />{{ candidate.mobile_number }}
                  </span>
                </div>
              </div>
            </div>
            <dl class="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:w-[46rem]">
              <div v-for="fact in facts" :key="fact.label" class="flex items-center gap-2.5 rounded-lg bg-brand-50/70 px-3 py-2.5">
                <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                  <FeatherIcon :name="fact.icon" class="h-4 w-4" />
                </div>
                <div class="min-w-0">
                  <dt class="truncate text-xs text-gray-600">{{ fact.label }}</dt>
                  <dd class="truncate text-sm font-bold text-gray-900">{{ fact.value }}</dd>
                </div>
              </div>
            </dl>
          </div>
          <div class="mt-5 border-t border-gray-100 pt-4">
            <div class="mb-3 flex items-center justify-between text-xs">
              <span class="font-bold uppercase tracking-wide text-brand-700">Progress</span>
              <span class="text-gray-500">{{ progressText }}</span>
            </div>
            <ProgressStepper :steps="timelineSteps" />
          </div>
        </section>

        <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
          <div class="flex min-w-0 flex-col gap-6">
            <ApplicationSubmissionPanel :app="detail" :loading="detailLoading" :error="detailError" />

            <SectionCard title="Activity" icon="clock" subtitle="Status changes and notes, newest first">
              <div v-if="!activity.length" class="text-sm text-gray-500">No activity yet.</div>
              <ol v-else class="relative ml-3 border-l border-gray-200">
                <li v-for="(event, idx) in activity" :key="idx" class="relative pb-5 pl-6 last:pb-0">
                  <span
                    class="absolute -left-[13px] top-0 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-white"
                    :class="activityStyle(event).dot"
                  >
                    <FeatherIcon :name="activityStyle(event).icon" class="h-3 w-3" />
                  </span>
                  <div class="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
                    <template v-if="event.kind === 'status'">
                      <StatusBadge :status="event.from_status" />
                      <FeatherIcon name="arrow-right" class="h-3.5 w-3.5 text-gray-400" />
                      <StatusBadge :status="event.to_status" />
                    </template>
                    <span v-else-if="event.kind === 'created'" class="font-semibold text-gray-900">Application received</span>
                    <span v-else class="text-gray-800">{{ event.text }}</span>
                  </div>
                  <div v-if="event.note" class="mt-1 text-sm text-gray-700">{{ event.note }}</div>
                  <div class="mt-0.5 text-xs text-gray-500">{{ event.by }} · {{ formatDateTime(event.at) }}</div>
                </li>
              </ol>
            </SectionCard>
          </div>

          <!-- Right rail: score, then the application at a glance -->
          <aside class="flex min-w-0 flex-col gap-6">
            <ShortlistingReviewPanel
              v-if="showReview"
              :review="review"
              :rubric="rubric"
              :show-summary="!detail"
              @scored="onScored"
            />
            <SectionCard title="At a Glance" icon="activity">
              <dl class="flex flex-col divide-y divide-gray-100 text-sm">
                <div class="py-3 first:pt-0">
                  <dt class="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    <FeatherIcon name="video" class="h-3.5 w-3.5" />Interviews
                  </dt>
                  <dd v-if="!status.interviews?.length" class="text-gray-500">None scheduled</dd>
                  <dd v-for="(iv, idx) in status.interviews" v-else :key="idx" class="flex items-center justify-between gap-2 py-1">
                    <div class="min-w-0">
                      <div class="truncate font-medium text-gray-900">{{ iv.round_type }}</div>
                      <div v-if="iv.scheduled_datetime" class="text-xs text-gray-500">{{ formatDateTime(iv.scheduled_datetime) }}</div>
                    </div>
                    <StatusBadge :status="iv.status" />
                  </dd>
                </div>
                <div class="py-3">
                  <dt class="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    <FeatherIcon name="award" class="h-3.5 w-3.5" />Offer
                  </dt>
                  <dd v-if="status.offer_status" class="flex items-center justify-between gap-2">
                    <StatusBadge :status="status.offer_status" />
                    <span v-if="status.acceptance_deadline" class="text-xs text-gray-500">Respond by {{ formatDate(status.acceptance_deadline) }}</span>
                  </dd>
                  <dd v-else class="text-gray-500">No offer yet</dd>
                </div>
                <div class="py-3 last:pb-0">
                  <dt class="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    <FeatherIcon name="folder" class="h-3.5 w-3.5" />Documents
                  </dt>
                  <dd class="flex items-center justify-between gap-2">
                    <span class="text-gray-700">{{ documentCount }} file{{ documentCount === 1 ? '' : 's' }}</span>
                    <span class="flex items-center gap-1.5 text-xs text-gray-500">
                      Verification
                      <StatusBadge v-if="status.document_status" :status="status.document_status" />
                      <span v-else class="font-medium text-gray-700">not started</span>
                    </span>
                  </dd>
                  <Button class="mt-3 w-full" :class="BTN_DARK" variant="solid" icon-left="eye" @click="openDocuments">
                    View documents
                  </Button>
                </div>
              </dl>
            </SectionCard>

            <SectionCard title="Other Applications" icon="layers" subtitle="Same candidate, other openings">
              <template v-if="otherApplications.length" #actions>
                <span class="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">{{ otherApplications.length }}</span>
              </template>
              <div v-if="!detail" class="text-sm text-gray-500">—</div>
              <div v-else-if="!otherApplications.length" class="text-sm text-gray-500">
                No other applications from this candidate.
              </div>
              <ul v-else class="-mx-2 flex flex-col">
                <li v-for="other in otherApplications" :key="other.name">
                  <RouterLink
                    :to="`/applications/${other.name}`"
                    class="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-brand-50"
                  >
                    <div class="min-w-0 flex-1">
                      <div class="truncate text-sm font-semibold text-gray-900">{{ other.job_title || other.job_opening }}</div>
                      <div class="truncate text-xs text-gray-500">
                        {{ other.application_id }}<template v-if="other.application_date"> · {{ formatDate(other.application_date) }}</template>
                      </div>
                    </div>
                    <StatusBadge :status="other.status" />
                    <FeatherIcon name="chevron-right" class="h-4 w-4 shrink-0 text-gray-400" />
                  </RouterLink>
                </li>
              </ul>
            </SectionCard>
          </aside>
        </div>
      </div>
    </div>

    <DocumentViewer
      v-model:open="showDocuments"
      :title="`Applicant Documents - ${status?.application_id || ''}`"
      :documents="documents"
      :loading="documentsLoading"
      :download-all-url="downloadAllUrl"
    />

    <Dialog v-model="showStatusDialog" :options="{ title: 'Change Application Status', size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="statusError" />
          <div class="text-sm text-gray-600">
            Current status: <StatusBadge v-if="status" :status="status.status" />
          </div>
          <FormControl label="New Status" type="select" v-model="statusForm.status" :options="statusOptions.options || []" />
          <FormControl
            label="Remarks"
            type="textarea"
            v-model="statusForm.remarks"
            placeholder="Optional. Recorded in the application's timeline."
          />
          <p class="text-xs text-gray-500">
            Offer, document and joining statuses are set from their own records and need the status override role.
          </p>
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :class="BTN_BRAND"
          :loading="savingStatus"
          :disabled="!statusForm.status || statusForm.status === status?.status"
          @click="saveStatus"
        >
          Update Status
        </Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Button, Dialog, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import { toast } from '@/utils/notify'
import { applicationService } from '@/services/applications'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import { BTN_BRAND, BTN_DARK } from '@/utils/buttonStyles'
import ProgressStepper from '@/components/common/ProgressStepper.vue'
import ShortlistingReviewPanel from '@/components/common/ShortlistingReviewPanel.vue'
import ApplicationSubmissionPanel from '@/components/common/ApplicationSubmissionPanel.vue'
import { useApplicationStatus } from '@/composables/useApplications'
import { useApplicationReview } from '@/composables/useScoring'
import { useSessionStore } from '@/stores/session'

const props = defineProps({ id: { type: String, required: true } })

const session = useSessionStore()
const { status, loading, fetchStatus } = useApplicationStatus()
const { review, rubric, fetchReview } = useApplicationReview()

// Committee membership is a behavioural role; staff who can see the whole
// pipeline may review too. Scoring itself is permission-checked server-side.
const canReview = computed(
  () => session.hasRole('Pathways Shortlisting Committee Member') || session.canViewPipeline,
)

const PIPELINE = [
  { key: 'Submitted', label: 'Application Received' },
  { key: 'Under Review', label: 'Under Review' },
  { key: 'Shortlisted', label: 'Shortlisted' },
  { key: 'Interview Scheduled', label: 'Interview Scheduled' },
  { key: 'Interview Completed', label: 'Interview Completed' },
  { key: 'Selected', label: 'Selected' },
  { key: 'Offer Extended', label: 'Offer Extended' },
  { key: 'Offer Accepted', label: 'Offer Accepted' },
  { key: 'Documents Verified', label: 'Documents Verified' },
  { key: 'Joined', label: 'Joined' },
]

const timelineSteps = computed(() => {
  if (!status.value) return []
  const currentStatus = status.value.status
  if (currentStatus === 'Not Selected' || currentStatus === 'Withdrawn') {
    return [
      ...PIPELINE.slice(0, 2).map((s) => ({ ...s, state: 'completed' })),
      { key: currentStatus, label: currentStatus, state: 'rejected' },
    ]
  }
  const currentIdx = PIPELINE.findIndex((s) => s.key === currentStatus)
  return PIPELINE.map((step, idx) => ({
    ...step,
    state: idx < currentIdx ? 'completed' : idx === currentIdx ? 'current' : 'pending',
  }))
})

// ----- manual status change (staff with write access)
const statusOptions = ref({ can_change: false })
const showStatusDialog = ref(false)
const statusForm = reactive({ status: '', remarks: '' })
const statusError = ref('')
const savingStatus = ref(false)

async function loadStatusOptions(id) {
  try {
    statusOptions.value = await applicationService.getStatusOptions(id)
  } catch {
    statusOptions.value = { can_change: false }
  }
}

// A shortlisting decision moves the status, which several parts show.
function onScored() {
  fetchStatus(props.id)
  loadDetail(props.id)
  loadStatusOptions(props.id)
}

function openStatusDialog() {
  Object.assign(statusForm, { status: status.value?.status || '', remarks: '' })
  statusError.value = ''
  showStatusDialog.value = true
}

async function saveStatus() {
  savingStatus.value = true
  statusError.value = ''
  try {
    await applicationService.setStatus(props.id, statusForm.status, statusForm.remarks)
    showStatusDialog.value = false
    toast({ title: `Status changed to ${statusForm.status}.`, icon: 'check', iconClasses: 'text-green-500' })
    await Promise.all([fetchStatus(props.id), loadStatusOptions(props.id)])
  } catch (e) {
    statusError.value = e?.messages?.[0] || 'Could not change the status.'
  } finally {
    savingStatus.value = false
  }
}

// ----- full submission (summary card + details panel)
const detail = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const candidate = computed(() => detail.value?.candidate_details || {})
const otherApplications = computed(() => detail.value?.other_applications || [])
const activity = computed(() => detail.value?.activity || [])
const showReview = computed(() => canReview.value && !!review.value)

function activityStyle(event) {
  if (event.kind === 'created') return { icon: 'inbox', dot: 'bg-gray-200 text-gray-600' }
  if (event.kind === 'note') return { icon: 'message-square', dot: 'bg-gray-200 text-gray-600' }
  if (event.to_status === 'Not Selected' || event.to_status === 'Withdrawn') return { icon: 'x', dot: 'bg-red-600 text-white' }
  return { icon: 'arrow-up-right', dot: 'bg-brand-700 text-white' }
}

async function loadDetail(id) {
  detailLoading.value = true
  detailError.value = ''
  try {
    detail.value = await applicationService.getApplicationDetail(id)
  } catch (e) {
    detail.value = null
    detailError.value = e?.messages?.[0] || 'Could not load the application.'
  } finally {
    detailLoading.value = false
  }
}

const initials = computed(() =>
  (candidate.value.full_name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join(''),
)

const facts = computed(() => {
  const d = detail.value || {}
  const list = [
    { label: 'Experience', icon: 'briefcase', value: d.overall_experience_years != null ? `${d.overall_experience_years} yrs` : '—' },
    { label: 'Relevant', icon: 'target', value: d.relevant_experience_years != null ? `${d.relevant_experience_years} yrs` : '—' },
  ]
  if ('expected_salary' in d) list.push({ label: 'Expected pay / month', icon: 'credit-card', value: money(d.expected_salary) })
  list.push({ label: 'Can join', icon: 'calendar', value: d.earliest_doj ? formatDate(d.earliest_doj) : '—' })
  return list
})

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}
function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A') : ''
}
function money(value) {
  return value == null ? '—' : `₹ ${Number(value).toLocaleString('en-IN')}`
}

const progressText = computed(() => {
  const done = timelineSteps.value.filter((s) => s.state === 'completed').length
  return `${done + 1} of ${timelineSteps.value.length}`
})

// ----- documents viewer
const showDocuments = ref(false)
const documents = ref([])
const documentsLoading = ref(false)
const downloadAllUrl = computed(() => applicationService.downloadAllDocumentsUrl(props.id))
const documentCount = computed(() => documents.value.length)

async function loadDocuments(id) {
  documentsLoading.value = true
  try {
    documents.value = (await applicationService.getApplicationDocuments(id)).documents
  } catch {
    documents.value = []
  } finally {
    documentsLoading.value = false
  }
}

function openDocuments() {
  showDocuments.value = true
}

function loadReviewIfAllowed(id) {
  if (canReview.value) fetchReview(id)
}

onMounted(() => {
  fetchStatus(props.id)
  loadReviewIfAllowed(props.id)
  loadStatusOptions(props.id)
  loadDetail(props.id)
  loadDocuments(props.id)
})
watch(
  () => props.id,
  (id) => {
    fetchStatus(id)
    loadReviewIfAllowed(id)
    loadStatusOptions(id)
    loadDetail(id)
    loadDocuments(id)
  },
)
</script>
