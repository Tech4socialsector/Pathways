<template>
  <StaffLayout>
    <PageHeader title="Offers" />
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        export-name="offers"
        :columns="columns"
        :rows="offers.data || []"
        :loading="offers.loading"
        :filters="filters"
        empty-title="No offers yet"
        search-placeholder="Search offers..."
      >
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      </DataTable>
    </div>
  </StaffLayout>
</template>

<script setup>
import { createListResource } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const offers = createListResource({
  doctype: 'Offer Appointment Order',
  fields: ['name', 'application', 'offer_date', 'acceptance_deadline', 'status'],
  orderBy: 'creation desc',
  // DataTable searches, filters and paginates client-side, so load all rows.
  pageLength: 1000,
  auto: true,
})

const columns = [
  { key: 'application', label: 'Application' },
  { key: 'offer_date', label: 'Offer Date' },
  { key: 'acceptance_deadline', label: 'Acceptance Deadline' },
  { key: 'status', label: 'Status' },
]
const filters = [{ key: 'status', label: 'Statuses' }]
</script>
