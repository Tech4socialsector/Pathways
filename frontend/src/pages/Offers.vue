<template>
  <StaffLayout>
    <PageHeader title="Offers" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="offers.loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!offers.data?.length" title="No offers yet" />
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="px-4 py-2">Application</th>
              <th class="px-4 py-2">Offer Date</th>
              <th class="px-4 py-2">Acceptance Deadline</th>
              <th class="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="offer in offers.data" :key="offer.name" class="border-b last:border-0">
              <td class="px-4 py-2.5 text-gray-700">{{ offer.application }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ offer.offer_date }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ offer.acceptance_deadline }}</td>
              <td class="px-4 py-2.5"><StatusBadge :status="offer.status" /></td>
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

const offers = createListResource({
  doctype: 'Offer Appointment Order',
  fields: ['name', 'application', 'offer_date', 'acceptance_deadline', 'status'],
  orderBy: 'creation desc',
  pageLength: 20,
  auto: true,
})
</script>
