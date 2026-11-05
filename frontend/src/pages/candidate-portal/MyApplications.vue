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
            <p class="mt-1 text-sm text-white/80">The jobs you have applied for. Updates come to your email.</p>
          </div>
          <Button variant="outline" icon-left="search" class="!border-white/40 !bg-white !text-brand-700 hover:!bg-brand-50" @click="$router.push('/portal/jobs')">
            Browse openings
          </Button>
        </div>
      </div>

      <!-- Drafts: started, not yet submitted, job still open -->
      <template v-if="drafts.length">
        <div class="mt-8 mb-3 flex items-center justify-between">
          <h2 class="text-xs font-bold uppercase tracking-wide text-brand-700">Drafts — not yet submitted</h2>
          <span class="text-xs text-gray-500">{{ drafts.length }} draft{{ drafts.length === 1 ? '' : 's' }}</span>
        </div>
        <div class="flex flex-col divide-y overflow-hidden rounded-2xl border bg-white shadow-sm">
          <router-link
            v-for="d in drafts"
            :key="d.job_opening"
            :to="`/portal/jobs/${d.job_opening}/apply`"
            class="group flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-4 transition hover:bg-brand-50/40"
          >
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
              <FeatherIcon name="edit-3" class="h-5 w-5" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="font-semibold text-gray-900 group-hover:text-brand-700">{{ d.job_title || d.job_opening }}</div>
              <div class="mt-0.5 text-xs text-gray-500">
                Saved {{ formatDateTime(d.saved_at) }}<template v-if="d.application_deadline"> · Applications close {{ formatDateTime(d.application_deadline) }}</template>
              </div>
            </div>
            <span class="flex items-center gap-1 text-sm font-semibold text-brand-700">
              Continue <FeatherIcon name="arrow-right" class="h-4 w-4 transition group-hover:translate-x-0.5" />
            </span>
          </router-link>
        </div>
      </template>

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
          <div class="h-1.5 bg-brand-700" />
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
            </div>

            <div class="mt-3 flex flex-wrap gap-1.5 text-xs">
              <span v-if="app.track" class="rounded-full bg-gray-100 px-2 py-0.5 text-gray-700">{{ app.track }}</span>
              <span class="rounded-full bg-gray-100 px-2 py-0.5 font-mono text-gray-700">{{ app.application_id }}</span>
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
import { onMounted, ref } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useMyApplications } from '@/composables/useApplications'
import { applicationService } from '@/services/applications'
import { useSessionStore } from '@/stores/session'
import { BTN_BRAND } from '@/utils/buttonStyles'

const session = useSessionStore()
const { applications, loading, fetchApplications } = useMyApplications()

function trackIcon(track) {
  return { Faculty: 'book-open', Research: 'search', Admin: 'briefcase' }[track] || 'file-text'
}
function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

const drafts = ref([])
function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A [IST]') : ''
}

onMounted(() => {
  fetchApplications()
  applicationService
    .getMyDrafts()
    .then((rows) => (drafts.value = rows || []))
    .catch(() => (drafts.value = []))
})
</script>
