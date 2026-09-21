<template>
  <StaffLayout>
    <PageHeader title="Reports" />
    <div class="flex-1 overflow-y-auto p-6">
      <div class="rounded-lg border bg-white p-4">
        <div class="mb-3 text-sm font-semibold text-gray-900">Recruitment Pipeline</div>
        <div v-if="report.loading" class="text-sm text-gray-500">Loading...</div>
        <EmptyState v-else-if="!report.data?.length" title="No job openings to report on" />
        <table v-else class="w-full text-sm">
          <thead class="border-b text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="py-2">Job Opening</th>
              <th class="py-2">Track</th>
              <th class="py-2">Applied</th>
              <th class="py-2">Shortlisted</th>
              <th class="py-2">Interviewed</th>
              <th class="py-2">Offered</th>
              <th class="py-2">Joined</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in report.data" :key="row.job_opening" class="border-b last:border-0">
              <td class="py-2 text-gray-900">{{ row.job_opening }}</td>
              <td class="py-2 text-gray-600">{{ row.track }}</td>
              <td class="py-2 text-gray-600">{{ row.applied }}</td>
              <td class="py-2 text-gray-600">{{ row.shortlisted }}</td>
              <td class="py-2 text-gray-600">{{ row.interviewed }}</td>
              <td class="py-2 text-gray-600">{{ row.offered }}</td>
              <td class="py-2 text-gray-600">{{ row.joined }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const report = createResource({
  url: 'frappe.desk.query_report.run',
  params: { report_name: 'Recruitment Pipeline' },
  transform: (data) => data?.result || [],
})

onMounted(() => report.fetch())
</script>
