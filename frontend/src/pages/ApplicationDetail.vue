<template>
  <StaffLayout>
    <PageHeader :title="status?.application_id || 'Application'" :subtitle="status?.job_title">
      <template #actions>
        <StatusBadge v-if="status" :status="status.status" />
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <div v-else-if="status" class="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div class="flex flex-col gap-6 md:col-span-2">
          <div class="rounded-lg border bg-white p-4">
            <div class="mb-4 text-sm font-semibold text-gray-900">Recruitment Timeline</div>
            <RecruitmentTimeline :steps="timelineSteps" />
          </div>

          <ShortlistingReviewPanel
            v-if="canReview && review"
            :review="review"
            :rubric="rubric"
            @scored="fetchStatus(props.id)"
          />

          <ApplicationSubmissionPanel :application-name="props.id" />
        </div>

        <div class="flex flex-col gap-4">
          <div class="rounded-lg border bg-white p-4">
            <div class="mb-2 text-sm font-semibold text-gray-900">Interviews</div>
            <EmptyState v-if="!status.interviews?.length" title="No interviews scheduled" />
            <ul v-else class="flex flex-col gap-2 text-sm">
              <li v-for="(iv, idx) in status.interviews" :key="idx" class="flex items-center justify-between">
                <span class="text-gray-700">{{ iv.round_type }}</span>
                <StatusBadge :status="iv.status" />
              </li>
            </ul>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-2 text-sm font-semibold text-gray-900">Offer</div>
            <div v-if="status.offer_status" class="text-sm">
              <StatusBadge :status="status.offer_status" />
              <div v-if="status.acceptance_deadline" class="mt-1 text-xs text-gray-500">
                Deadline: {{ status.acceptance_deadline }}
              </div>
            </div>
            <div v-else class="text-sm text-gray-500">No offer yet</div>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-2 text-sm font-semibold text-gray-900">Documents</div>
            <StatusBadge v-if="status.document_status" :status="status.document_status" />
            <div v-else class="text-sm text-gray-500">Not started</div>
          </div>
        </div>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
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

function loadReviewIfAllowed(id) {
  if (canReview.value) fetchReview(id)
}

onMounted(() => {
  fetchStatus(props.id)
  loadReviewIfAllowed(props.id)
})
watch(
  () => props.id,
  (id) => {
    fetchStatus(id)
    loadReviewIfAllowed(id)
  },
)
</script>
