<template>
  <StaffLayout>
    <PageHeader title="Dashboard" :subtitle="`Welcome, ${session.fullName}`" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="!session.rolesLoaded || loading" class="text-sm text-gray-500">Loading...</div>
      <div v-else-if="!session.canViewPipeline" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="link in shortcuts"
          :key="link.to"
          :to="link.to"
          class="rounded-lg border bg-white p-4 hover:border-gray-400"
        >
          <div class="text-sm font-semibold text-gray-900">{{ link.label }}</div>
          <div class="mt-0.5 text-sm text-gray-500">{{ link.description }}</div>
        </router-link>
        <EmptyState v-if="!shortcuts.length" class="col-span-full" title="Nothing assigned to you yet" />
      </div>
      <template v-else>
        <div class="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <button
            v-for="card in adminCards"
            :key="card.key"
            class="group flex items-start justify-between gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-700"
            :title="`Show ${card.label.toLowerCase()}`"
            @click="openDrilldown(card.key, card.label)"
          >
            <div class="min-w-0">
              <div class="text-2xl font-bold text-gray-900">{{ card.value }}</div>
              <div class="mt-1 text-xs text-gray-500 group-hover:text-brand-700">{{ card.label }}</div>
            </div>
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700 group-hover:bg-brand-700 group-hover:text-white">
              <FeatherIcon :name="card.icon" class="h-4 w-4" />
            </div>
          </button>
        </div>

        <div v-if="adminDashboard.funnel.value.length" class="mb-8 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="mb-4 flex items-baseline justify-between gap-2">
            <div class="text-sm font-semibold text-gray-900">Recruitment Pipeline</div>
            <div class="text-xs text-gray-500">Click a stage to see its applications</div>
          </div>
          <PipelineFunnelChart
            :stages="adminDashboard.funnel.value"
            @select="(stage) => openDrilldown(`funnel:${stage.label}`, `Pipeline: ${stage.label}`, 'Reached this stage or beyond')"
          />
        </div>

        <div v-if="recruiterSummary.summary.value" class="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Upcoming Interviews</div>
            <EmptyState
              v-if="!recruiterSummary.summary.value.upcoming_interviews?.length"
              title="No upcoming interviews"
            />
            <ul v-else class="flex flex-col gap-2">
              <li v-for="iv in recruiterSummary.summary.value.upcoming_interviews" :key="iv.name">
                <router-link
                  :to="`/applications/${iv.application}`"
                  class="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-brand-50"
                >
                  <span class="text-gray-700">{{ iv.application }} &middot; {{ iv.round_type }}</span>
                  <span class="text-gray-500">{{ formatDate(iv.scheduled_datetime) }}</span>
                </router-link>
              </li>
            </ul>
          </div>

          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Needs Attention</div>
            <ul class="-mx-2 flex flex-col text-sm text-gray-700">
              <li v-for="item in attentionItems" :key="item.key">
                <button
                  class="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left hover:bg-brand-50"
                  @click="openDrilldown(item.key, item.title)"
                >
                  <span
                    class="flex h-7 min-w-7 items-center justify-center rounded-full px-2 text-xs font-bold"
                    :class="item.count ? 'bg-brand-700 text-white' : 'bg-gray-100 text-gray-500'"
                  >{{ item.count }}</span>
                  <span class="flex-1">{{ item.label }}</span>
                  <FeatherIcon name="chevron-right" class="h-4 w-4 text-gray-400" />
                </button>
              </li>
            </ul>
          </div>
        </div>
      </template>
    </div>

    <DrilldownDialog
      v-model:open="drilldown.open"
      :bucket="drilldown.bucket"
      :title="drilldown.title"
      :description="drilldown.description"
    />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PipelineFunnelChart from '@/components/common/PipelineFunnelChart.vue'
import DrilldownDialog from '@/components/common/DrilldownDialog.vue'
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
    { key: 'total_applications', icon: 'inbox', label: 'Total Applications', value: s.total_applications },
    { key: 'screening_pending', icon: 'clock', label: 'Screening Pending', value: s.screening_pending },
    { key: 'shortlisted', icon: 'check-circle', label: 'Shortlisted', value: s.shortlisted },
    { key: 'interviews_scheduled', icon: 'video', label: 'Interviews Scheduled', value: s.interviews_scheduled },
    { key: 'selected', icon: 'star', label: 'Selected', value: s.selected },
    { key: 'offers_released', icon: 'send', label: 'Offers Released', value: s.offers_released },
    { key: 'offers_accepted', icon: 'thumbs-up', label: 'Offers Accepted', value: s.offers_accepted },
    { key: 'documents_pending', icon: 'file', label: 'Documents Pending', value: s.documents_pending },
    { key: 'joined', icon: 'user-check', label: 'Joined', value: s.joined },
    { key: 'rejected', icon: 'x-circle', label: 'Not Selected', value: s.rejected },
  ]
})

const attentionItems = computed(() => {
  const s = recruiterSummary.summary.value || {}
  return [
    { key: 'feedback_pending', count: s.feedback_pending_count || 0, label: 'interview(s) awaiting feedback', title: 'Interviews Awaiting Feedback' },
    { key: 'document_checklists', count: s.documents_pending || 0, label: 'document checklist(s) pending', title: 'Document Checklists Pending' },
    { key: 'offers_awaiting', count: s.offers_pending || 0, label: 'offer(s) awaiting candidate response', title: 'Offers Awaiting Response' },
  ]
})

// One dialog for every drill-down: cards, pipeline stages, attention items.
const drilldown = reactive({ open: false, bucket: '', title: '', description: '' })

function openDrilldown(bucket, title, description = '') {
  Object.assign(drilldown, { open: true, bucket, title, description })
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

const SHORTCUTS = [
  { key: 'approvals', to: '/approvals', label: 'My Approvals', description: 'Green Sheets waiting for your decision.' },
  { key: 'applications', to: '/applications', label: 'Applications', description: 'Applications assigned to your committee.' },
  { key: 'interviews', to: '/interviews', label: 'Interviews', description: 'Interviews you are part of.' },
  { key: 'jobs', to: '/jobs', label: 'Job Openings', description: 'Positions and their approval status.' },
  { key: 'offers', to: '/offers', label: 'Offers', description: 'Offer and appointment orders.' },
]
const shortcuts = computed(() => SHORTCUTS.filter((s) => session.hasMenu(s.key)))

onMounted(async () => {
  await session.fetchRoles()
  // Pipeline numbers are only served to users who can see every application.
  if (session.canViewPipeline) {
    adminDashboard.fetchSummary()
    recruiterSummary.fetchSummary()
  }
})
</script>
