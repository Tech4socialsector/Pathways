<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-2xl px-6 py-10">
      <h1 class="mb-6 text-2xl font-semibold text-gray-900">My Applications</h1>
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState
        v-else-if="!applications.length"
        title="No applications yet"
        description="Browse open positions to get started."
      >
        <template #action>
          <Button variant="solid" @click="$router.push('/portal/jobs')">View Openings</Button>
        </template>
      </EmptyState>
      <div v-else class="flex flex-col gap-3">
        <div
          v-for="app in applications"
          :key="app.name"
          class="cursor-pointer rounded-lg border bg-white p-4 hover:border-gray-300"
          @click="$router.push(`/portal/applications/${app.name}`)"
        >
          <div class="flex items-center justify-between">
            <div class="font-medium text-gray-900">{{ app.job_opening }}</div>
            <StatusBadge :status="app.status" />
          </div>
          <div class="mt-1 text-xs text-gray-500">
            {{ app.application_id }} &middot; Applied {{ app.application_date }}
          </div>
        </div>
      </div>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import { Button } from 'frappe-ui'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useMyApplications } from '@/composables/useApplications'

const { applications, loading, fetchApplications } = useMyApplications()

onMounted(fetchApplications)
</script>
