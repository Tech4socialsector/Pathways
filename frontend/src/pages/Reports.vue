<template>
  <StaffLayout>
    <PageHeader title="Reports" />
    <div class="flex-1 overflow-y-auto p-6">
      <div class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Recruitment Pipeline</div>
        <DataTable
        export-name="report"
          :columns="columns"
          :rows="report.data || []"
          :loading="report.loading"
          :filters="filters"
          row-key="job_opening"
          empty-title="No job openings to report on"
          search-placeholder="Search job openings..."
        />
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'

const report = createResource({
  url: 'frappe.desk.query_report.run',
  params: { report_name: 'Recruitment Pipeline' },
  transform: (data) => data?.result || [],
})

const columns = [
  { key: 'job_opening', label: 'Job Opening' },
  { key: 'track', label: 'Track' },
  { key: 'applied', label: 'Applied' },
  { key: 'shortlisted', label: 'Shortlisted' },
  { key: 'interviewed', label: 'Interviewed' },
  { key: 'offered', label: 'Offered' },
  { key: 'joined', label: 'Joined' },
]
const filters = [{ key: 'track', label: 'Tracks' }]

onMounted(() => report.fetch())
</script>
