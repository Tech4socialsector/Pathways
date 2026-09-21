<template>
  <StaffLayout>
    <PageHeader title="Dashboard" :subtitle="`Welcome, ${session.user}`" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <template v-else>
        <div class="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <div v-for="card in adminCards" :key="card.label" class="rounded-lg border bg-white p-4">
            <div class="text-2xl font-semibold text-gray-900">{{ card.value }}</div>
            <div class="mt-1 text-xs text-gray-500">{{ card.label }}</div>
          </div>
        </div>

        <div v-if="adminDashboard.funnel.value.length" class="mb-8 rounded-lg border bg-white p-4">
          <div class="mb-4 text-sm font-semibold text-gray-900">Recruitment Pipeline</div>
          <PipelineFunnelChart :stages="adminDashboard.funnel.value" />
        </div>

        <div v-if="recruiterSummary.summary" class="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Upcoming Interviews</div>
            <EmptyState
              v-if="!recruiterSummary.summary.upcoming_interviews?.length"
              title="No upcoming interviews"
            />
            <ul v-else class="flex flex-col gap-2">
              <li
                v-for="iv in recruiterSummary.summary.upcoming_interviews"
                :key="iv.name"
                class="flex items-center justify-between text-sm"
              >
                <span class="text-gray-700">{{ iv.application }} &middot; {{ iv.round_type }}</span>
                <span class="text-gray-500">{{ formatDate(iv.scheduled_datetime) }}</span>
              </li>
            </ul>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Needs Attention</div>
            <ul class="flex flex-col gap-2 text-sm text-gray-700">
              <li>{{ recruiterSummary.summary.feedback_pending_count }} interview(s) awaiting feedback</li>
              <li>{{ recruiterSummary.summary.documents_pending }} document checklist(s) pending</li>
              <li>{{ recruiterSummary.summary.offers_pending }} offer(s) awaiting candidate response</li>
            </ul>
          </div>
        </div>
      </template>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PipelineFunnelChart from '@/components/common/PipelineFunnelChart.vue'
import { useSessionStore } from '@/stores/session'
import { useAdminDashboard, useRecruiterDashboard } from '@/composables/useRecruitmentDashboard'

const session = useSessionStore()
const adminDashboard = useAdminDashboard()
const recruiterSummary = useRecruiterDashboard()

const loading = computed(() => adminDashboard.loading.value || recruiterSummary.loading.value)

const adminCards = computed(() => {
  const s = adminDashboard.summary.value
  if (!s) return []
  return [
    { label: 'Total Applications', value: s.total_applications },
    { label: 'Screening Pending', value: s.screening_pending },
    { label: 'Shortlisted', value: s.shortlisted },
    { label: 'Interviews Scheduled', value: s.interviews_scheduled },
    { label: 'Selected', value: s.selected },
    { label: 'Offers Released', value: s.offers_released },
    { label: 'Offers Accepted', value: s.offers_accepted },
    { label: 'Documents Pending', value: s.documents_pending },
    { label: 'Joined', value: s.joined },
    { label: 'Not Selected', value: s.rejected },
  ]
})

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

onMounted(() => {
  adminDashboard.fetchSummary()
  recruiterSummary.fetchSummary()
})
</script>
