<template>
  <StaffLayout>
    <PageHeader :title="status?.application_id || 'Application'" :subtitle="status?.job_title">
      <template #actions>
        <StatusBadge v-if="status" :status="status.status" />
        <Button icon-left="eye" @click="openDocuments">View Documents</Button>
        <Button icon-left="download" :link="downloadAllUrl" title="All documents merged into one PDF">Download All</Button>
        <Button v-if="statusOptions.can_change" variant="solid" icon-left="edit-3" @click="openStatusDialog">Change Status</Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto bg-gray-50 p-4 sm:p-6">
      <div v-if="loading && !status" class="text-sm text-gray-500">Loading...</div>
      <div v-else-if="status" class="mx-auto flex max-w-7xl flex-col gap-6">
        <!-- Candidate summary -->
        <section class="rounded-xl border bg-white p-5 shadow-sm">
          <div class="flex flex-col gap-5 lg:flex-row lg:items-center">
            <div class="flex min-w-0 flex-1 items-center gap-4">
              <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-lg font-bold text-indigo-700">
                {{ initials }}
              </div>
              <div class="min-w-0">
                <div class="truncate text-lg font-bold text-gray-900">{{ candidate.full_name || '—' }}</div>
                <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
                  <span v-if="candidate.email" class="flex items-center gap-1.5"><FeatherIcon name="mail" class="h-3.5 w-3.5" />{{ candidate.email }}</span>
                  <span v-if="candidate.mobile_number" class="flex items-center gap-1.5"><FeatherIcon name="phone" class="h-3.5 w-3.5" />{{ candidate.mobile_number }}</span>
                  <span v-if="status.application_date" class="flex items-center gap-1.5">
                    <FeatherIcon name="calendar" class="h-3.5 w-3.5" />Applied {{ formatDate(status.application_date) }}
                  </span>
                </div>
              </div>
            </div>
            <dl class="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:w-[34rem]">
              <div v-for="fact in facts" :key="fact.label" class="rounded-lg bg-gray-50 px-3 py-2">
                <dt class="text-xs text-gray-500">{{ fact.label }}</dt>
                <dd class="mt-0.5 truncate text-sm font-bold text-gray-900">{{ fact.value }}</dd>
              </div>
            </dl>
          </div>
        </section>

        <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div class="flex min-w-0 flex-col gap-6 lg:col-span-2">
            <ShortlistingReviewPanel
              v-if="canReview && review"
              :review="review"
              :rubric="rubric"
              @scored="fetchStatus(props.id)"
            />
            <ApplicationSubmissionPanel :app="detail" :loading="detailLoading" :error="detailError" @view-documents="openDocuments" />
          </div>

          <!-- Side panel -->
          <aside class="flex flex-col gap-4 lg:sticky lg:top-0 lg:self-start">
            <section class="rounded-xl border bg-white p-4 shadow-sm">
              <div class="mb-4 flex items-center justify-between">
                <div class="text-sm font-bold text-gray-900">Application Progress</div>
                <span class="text-xs text-gray-500">{{ progressText }}</span>
              </div>
              <RecruitmentTimeline :steps="timelineSteps" />
            </section>

            <section class="rounded-xl border bg-white p-4 shadow-sm">
              <div class="mb-2 flex items-center gap-2 text-sm font-bold text-gray-900">
                <FeatherIcon name="video" class="h-4 w-4 text-gray-400" />Interviews
              </div>
              <div v-if="!status.interviews?.length" class="text-sm text-gray-500">No interviews scheduled.</div>
              <ul v-else class="flex flex-col gap-2 text-sm">
                <li v-for="(iv, idx) in status.interviews" :key="idx" class="flex items-center justify-between gap-2">
                  <div>
                    <div class="text-gray-800">{{ iv.round_type }}</div>
                    <div v-if="iv.scheduled_datetime" class="text-xs text-gray-500">{{ formatDateTime(iv.scheduled_datetime) }}</div>
                  </div>
                  <StatusBadge :status="iv.status" />
                </li>
              </ul>
            </section>

            <section class="rounded-xl border bg-white p-4 shadow-sm">
              <div class="mb-2 flex items-center gap-2 text-sm font-bold text-gray-900">
                <FeatherIcon name="award" class="h-4 w-4 text-gray-400" />Offer
              </div>
              <div v-if="status.offer_status" class="text-sm">
                <StatusBadge :status="status.offer_status" />
                <div v-if="status.acceptance_deadline" class="mt-1 text-xs text-gray-500">
                  Respond by {{ formatDate(status.acceptance_deadline) }}
                </div>
              </div>
              <div v-else class="text-sm text-gray-500">No offer yet.</div>
            </section>

            <section class="rounded-xl border bg-white p-4 shadow-sm">
              <div class="mb-2 flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-bold text-gray-900">
                  <FeatherIcon name="folder" class="h-4 w-4 text-gray-400" />Documents
                </div>
                <button class="text-xs font-medium text-indigo-600 hover:underline" @click="openDocuments">View all</button>
              </div>
              <div class="text-sm text-gray-600">{{ documentCount }} file{{ documentCount === 1 ? '' : 's' }} uploaded</div>
              <div class="mt-2 text-xs text-gray-500">
                Verification:
                <StatusBadge v-if="status.document_status" :status="status.document_status" />
                <span v-else>not started</span>
              </div>
            </section>
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
import { Button, Dialog, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import { toast } from '@/utils/notify'
import { applicationService } from '@/services/applications'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
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
    { label: 'Experience', value: d.overall_experience_years != null ? `${d.overall_experience_years} yrs` : '—' },
    { label: 'Relevant', value: d.relevant_experience_years != null ? `${d.relevant_experience_years} yrs` : '—' },
  ]
  if ('expected_salary' in d) list.push({ label: 'Expected / month', value: money(d.expected_salary) })
  list.push({ label: 'Can join', value: d.earliest_doj ? formatDate(d.earliest_doj) : '—' })
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
