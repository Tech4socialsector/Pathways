<template>
  <StaffLayout>
    <PageHeader title="Applications" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="applications.loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!applications.data?.length" title="No applications yet" />
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="px-4 py-2">Application ID</th>
              <th class="px-4 py-2">Job Opening</th>
              <th class="px-4 py-2">Status</th>
              <th class="px-4 py-2">Applied On</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="app in applications.data"
              :key="app.name"
              class="cursor-pointer border-b last:border-0 hover:bg-gray-50"
              @click="$router.push(`/applications/${app.name}`)"
            >
              <td class="px-4 py-2.5 font-medium text-gray-900">{{ app.application_id }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ app.job_opening }}</td>
              <td class="px-4 py-2.5"><StatusBadge :status="app.status" /></td>
              <td class="px-4 py-2.5 text-gray-600">{{ app.application_date }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="applications.hasNextPage" class="mt-4">
        <Button @click="applications.next()">Load more</Button>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { Button } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useApplicationList } from '@/composables/useApplicationList'

const applications = useApplicationList()
</script>
