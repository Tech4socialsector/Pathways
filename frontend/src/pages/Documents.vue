<template>
  <StaffLayout>
    <PageHeader title="Document Collection" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="collections.loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!collections.data?.length" title="No document checklists yet" />
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="px-4 py-2">Application</th>
              <th class="px-4 py-2">Overall Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in collections.data" :key="row.name" class="border-b last:border-0">
              <td class="px-4 py-2.5 text-gray-700">{{ row.application }}</td>
              <td class="px-4 py-2.5"><StatusBadge :status="row.overall_status" /></td>
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

const collections = createListResource({
  doctype: 'Document Collection',
  fields: ['name', 'application', 'overall_status'],
  orderBy: 'creation desc',
  pageLength: 20,
  auto: true,
})
</script>
