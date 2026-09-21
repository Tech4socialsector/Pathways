<template>
  <StaffLayout>
    <PageHeader title="Interviews" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="interviews.loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!interviews.data?.length" title="No interviews scheduled" />
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="px-4 py-2">Application</th>
              <th class="px-4 py-2">Round</th>
              <th class="px-4 py-2">Scheduled</th>
              <th class="px-4 py-2">Mode</th>
              <th class="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="iv in interviews.data" :key="iv.name" class="border-b last:border-0">
              <td class="px-4 py-2.5 text-gray-700">{{ iv.application }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ iv.round_type }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ formatDate(iv.scheduled_datetime) }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ iv.mode }}</td>
              <td class="px-4 py-2.5"><StatusBadge :status="iv.status" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { createListResource } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const interviews = createListResource({
  doctype: 'Interview',
  fields: ['name', 'application', 'round_type', 'scheduled_datetime', 'mode', 'status'],
  orderBy: 'scheduled_datetime desc',
  pageLength: 20,
  auto: true,
})

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
</script>
