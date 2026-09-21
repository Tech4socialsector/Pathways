<template>
  <StaffLayout>
    <PageHeader title="Job Openings" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!jobs.length" title="No open job openings" />
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="px-4 py-2">Job Title</th>
              <th class="px-4 py-2">Track</th>
              <th class="px-4 py-2">Department</th>
              <th class="px-4 py-2">Vacancies</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="job in jobs"
              :key="job.name"
              class="cursor-pointer border-b last:border-0 hover:bg-gray-50"
              @click="$router.push(`/jobs/${job.name}`)"
            >
              <td class="px-4 py-2.5 font-medium text-gray-900">{{ job.job_title }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ job.track }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ job.department }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ job.vacancies }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useJobOpenings } from '@/composables/useJobOpenings'

const { jobs, loading, fetchJobs } = useJobOpenings()

onMounted(fetchJobs)
</script>
