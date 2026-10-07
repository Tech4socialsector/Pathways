<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <!-- Welcome -->
      <div class="relative overflow-hidden rounded-2xl bg-brand-700 px-6 py-7 text-white shadow-sm">
        <div class="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10" aria-hidden="true" />
        <div class="absolute -bottom-16 right-24 h-32 w-32 rounded-full bg-white/5" aria-hidden="true" />
        <div class="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <p class="text-sm text-white/80">Welcome back,</p>
            <h1 class="font-heading text-2xl font-bold">{{ session.fullName }}</h1>
            <p class="mt-1 text-sm text-white/80">Track each application here. Updates also come to your email.</p>
          </div>
          <Button variant="outline" icon-left="search" class="!border-white/40 !bg-white !text-brand-700 hover:!bg-brand-50" @click="$router.push('/portal/jobs')">
            Browse openings
          </Button>
        </div>
      </div>

      <!-- Summary -->
      <div v-if="applications.length" class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div v-for="c in summary" :key="c.label" class="flex items-center gap-3 rounded-xl border bg-white p-4 shadow-sm">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full" :class="c.tone">
            <FeatherIcon :name="c.icon" class="h-5 w-5" />
          </span>
          <div>
            <div class="text-2xl font-bold leading-none text-gray-900">{{ c.value }}</div>
            <div class="mt-1 text-xs text-gray-500">{{ c.label }}</div>
          </div>
        </div>
      </div>

      <div class="mt-8 mb-3 flex items-center justify-between">
        <h2 class="text-xs font-bold uppercase tracking-wide text-brand-700">My applications</h2>
        <span v-if="applications.length" class="text-xs text-gray-500">{{ applications.length }} total</span>
      </div>

      <div v-if="loading" class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div v-for="i in 2" :key="i" class="h-56 animate-pulse rounded-2xl border bg-white" />
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

      <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <router-link
          v-for="app in applications"
          :key="app.name"
          :to="`/portal/applications/${app.name}`"
          class="group flex flex-col overflow-hidden rounded-2xl border bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md"
        >
          <div class="h-1.5" :class="closed(app.status) ? 'bg-gray-300' : 'bg-brand-700'" />
          <div class="flex flex-1 flex-col p-5">
            <div class="flex items-start gap-3">
              <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                <FeatherIcon :name="trackIcon(app.track)" class="h-5 w-5" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="font-heading text-lg font-bold leading-snug text-gray-900 group-hover:text-brand-700">
                  {{ app.job_title || app.job_opening }}
                </div>
                <div class="mt-0.5 truncate text-sm text-gray-500">{{ app.department }}</div>
              </div>
              <StatusBadge :status="app.status" />
            </div>

            <div class="mt-3 flex flex-wrap gap-1.5 text-xs">
              <span v-if="app.track" class="rounded-full bg-gray-100 px-2 py-0.5 text-gray-700">{{ app.track }}</span>
              <span class="rounded-full bg-gray-100 px-2 py-0.5 font-mono text-gray-700">{{ app.application_id }}</span>
            </div>

            <!-- Stage stepper -->
            <div class="mt-5">
              <div class="flex items-center">
                <template v-for="(s, i) in STAGES" :key="s">
                  <span
                    class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                    :class="dotClass(app.status, i)"
                    :title="s"
                  >
                    <FeatherIcon v-if="dotState(app.status, i) === 'done'" name="check" class="h-3 w-3" />
                    <template v-else>{{ i + 1 }}</template>
                  </span>
                  <span v-if="i < STAGES.length - 1" class="h-0.5 flex-1" :class="dotState(app.status, i + 1) === 'done' || dotState(app.status, i + 1) === 'current' ? 'bg-brand-700' : 'bg-gray-200'" />
                </template>
              </div>
              <div class="mt-2 text-sm font-medium" :class="closed(app.status) ? 'text-gray-600' : 'text-brand-700'">
                {{ stageLabel(app.status) }}
              </div>
            </div>

            <div class="flex-1 pt-5" />
            <div class="flex items-center justify-between border-t pt-3 text-xs text-gray-500">
              <span class="flex items-center gap-1.5"><FeatherIcon name="calendar" class="h-3.5 w-3.5" />Applied {{ formatDate(app.application_date) }}</span>
              <span class="flex items-center gap-1 font-semibold text-brand-700">
                View details <FeatherIcon name="arrow-right" class="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
              </span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useMyApplications } from '@/composables/useApplications'
import { useSessionStore } from '@/stores/session'
import { BTN_BRAND } from '@/utils/buttonStyles'

const session = useSessionStore()
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
  'Offer Declined': 4,
  'Offer Accepted': 5,
  'Documents Pending': 5,
  'Documents Verified': 5,
  Joined: 5,
}

const closed = (status) => status === 'Not Selected' || status === 'Withdrawn'
const stageIndex = (status) => STAGE_OF[status] ?? 1

function dotState(status, i) {
  if (closed(status)) return i <= 1 ? 'done' : 'off'
  const idx = stageIndex(status)
  if (i < idx || (status === 'Joined' && i === idx)) return 'done'
  return i === idx ? 'current' : 'todo'
}
function dotClass(status, i) {
  return {
    done: closed(status) ? 'bg-gray-400 text-white' : 'bg-brand-700 text-white',
    current: 'bg-white text-brand-700 ring-2 ring-brand-700',
    todo: 'bg-gray-100 text-gray-400',
    off: 'bg-gray-100 text-gray-300',
  }[dotState(status, i)]
}
function stageLabel(status) {
  if (status === 'Not Selected') return 'Not taken forward'
  if (status === 'Withdrawn') return 'Withdrawn'
  return `Stage ${stageIndex(status) + 1} of ${STAGES.length}: ${STAGES[stageIndex(status)]}`
}
function trackIcon(track) {
  return { Faculty: 'book-open', Research: 'search', Admin: 'briefcase' }[track] || 'file-text'
}
function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

const summary = computed(() => {
  const apps = applications.value
  const active = apps.filter((a) => !closed(a.status) && a.status !== 'Joined')
  return [
    { label: 'Applications', value: apps.length, icon: 'file-text', tone: 'bg-brand-50 text-brand-700' },
    { label: 'In progress', value: active.length, icon: 'clock', tone: 'bg-orange-50 text-orange-600' },
    { label: 'Shortlisted or further', value: apps.filter((a) => stageIndex(a.status) >= 2 && !closed(a.status)).length, icon: 'star', tone: 'bg-green-50 text-green-600' },
    { label: 'Interviews', value: apps.filter((a) => a.status === 'Interview Scheduled').length, icon: 'calendar', tone: 'bg-blue-50 text-blue-600' },
  ]
})

onMounted(fetchApplications)
</script>
