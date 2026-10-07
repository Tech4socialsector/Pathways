<template>
  <StaffLayout>
    <PageHeader title="Interviews" />
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        export-name="interviews"
        :columns="columns"
        :rows="interviews.data || []"
        :loading="interviews.loading"
        :filters="filters"
        empty-title="No interviews scheduled"
        search-placeholder="Search interviews..."
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

const interviews = createListResource({
  doctype: 'Interview',
  fields: ['name', 'application', 'round_type', 'scheduled_datetime', 'mode', 'status'],
  orderBy: 'scheduled_datetime desc',
  // DataTable searches, filters and paginates client-side, so load all rows.
  pageLength: 1000,
  auto: true,
})

const columns = [
  { key: 'application', label: 'Application' },
  { key: 'round_type', label: 'Round' },
  { key: 'scheduled_datetime', label: 'Scheduled', format: (row) => formatDate(row.scheduled_datetime) },
  { key: 'mode', label: 'Mode' },
  { key: 'status', label: 'Status' },
]
const filters = [
  { key: 'status', label: 'Statuses' },
  { key: 'round_type', label: 'Rounds' },
  { key: 'mode', label: 'Modes' },
]

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
</script>
