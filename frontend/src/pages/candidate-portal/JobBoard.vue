<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-3xl px-6 py-10">
      <h1 class="mb-1 text-2xl font-semibold text-gray-900">Work with Us</h1>
      <p class="mb-6 text-sm text-gray-500">Current openings at National Law School of India University</p>

      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!jobs.length" title="No open positions right now" />
      <div v-else class="flex flex-col gap-3">
        <div
          v-for="job in jobs"
          :key="job.name"
          class="cursor-pointer rounded-lg border bg-white p-4 hover:border-gray-300"
          @click="$router.push(`/portal/jobs/${job.name}/apply`)"
        >
          <div class="font-medium text-gray-900">{{ job.job_title }}</div>
          <div class="mt-1 text-sm text-gray-500">
            {{ job.department }} &middot; {{ job.employment_type }} &middot; {{ job.vacancies }} vacancy(ies)
          </div>
        </div>
      </div>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useJobOpenings } from '@/composables/useJobOpenings'

const { jobs, loading, fetchJobs } = useJobOpenings()

onMounted(fetchJobs)
</script>
