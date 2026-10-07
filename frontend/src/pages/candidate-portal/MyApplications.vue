<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 class="font-heading text-2xl font-bold text-gray-900">My Applications</h1>
          <p class="mt-1 text-sm text-gray-500">Track where each application is. Updates also come to your email.</p>
        </div>
        <Button variant="outline" icon-left="search" @click="$router.push('/portal/jobs')">Browse openings</Button>
      </div>

      <div v-if="loading" class="flex flex-col gap-3">
        <div v-for="i in 2" :key="i" class="h-28 animate-pulse rounded-xl border bg-white" />
      </div>
      <EmptyState
        v-else-if="!applications.length"
        title="No applications yet"
        description="Browse open positions to get started."
      >
        <template #action>
          <Button variant="solid" :class="BTN_BRAND" @click="$router.push('/portal/jobs')">View openings</Button>
        </template>
      </EmptyState>
      <div v-else class="flex flex-col gap-3">
        <router-link
          v-for="app in applications"
          :key="app.name"
          :to="`/portal/applications/${app.name}`"
          class="group rounded-xl border bg-white p-5 shadow-sm transition hover:border-brand-200 hover:shadow-md"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="font-heading text-lg font-bold text-gray-900 group-hover:text-brand-700">{{ app.job_title || app.job_opening }}</div>
              <div class="mt-0.5 text-sm text-gray-500">
                {{ [app.department, app.track].filter(Boolean).join(' · ') }}
              </div>
            </div>
            <StatusBadge :status="app.status" />
          </div>

          <div class="mt-4 flex items-center gap-1" :aria-label="`Stage: ${stageLabel(app.status)}`">
            <span
              v-for="(s, i) in STAGES"
              :key="s"
              class="h-1.5 flex-1 rounded-full"
              :class="barClass(app.status, i)"
            />
          </div>
          <div class="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
            <span><span class="font-mono">{{ app.application_id }}</span> · Applied {{ formatDate(app.application_date) }}</span>
            <span class="font-medium" :class="app.status === 'Not Selected' ? 'text-red-700' : 'text-brand-700'">{{ stageLabel(app.status) }}</span>
          </div>
        </router-link>
      </div>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import { Button } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useMyApplications } from '@/composables/useApplications'
import { BTN_BRAND } from '@/utils/buttonStyles'

const { applications, loading, fetchApplications } = useMyApplications()

// Candidate-facing stages; each application status maps to one.
const STAGES = ['Received', 'Screening', 'Shortlisted', 'Interview', 'Decision', 'Joining']
const STAGE_OF = {
  Submitted: 0,
  'Under Review': 1,
  Shortlisted: 2,
  'Interview Scheduled': 3,
  'Interview Completed': 3,
  Selected: 4,
  'Offer Extended': 4,
  'Offer Accepted': 5,
  'Offer Declined': 4,
  'Documents Pending': 5,
  'Documents Verified': 5,
  Joined: 5,
}

function stageIndex(status) {
  return STAGE_OF[status] ?? 1
}
function stageLabel(status) {
  if (status === 'Not Selected') return 'Not progressed'
  if (status === 'Withdrawn') return 'Withdrawn'
  return `Stage ${stageIndex(status) + 1} of ${STAGES.length}: ${STAGES[stageIndex(status)]}`
}
function barClass(status, i) {
  if (status === 'Not Selected' || status === 'Withdrawn') return i <= 1 ? 'bg-gray-300' : 'bg-gray-100'
  return i <= stageIndex(status) ? 'bg-brand-700' : 'bg-gray-100'
}
function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

onMounted(fetchApplications)
</script>
