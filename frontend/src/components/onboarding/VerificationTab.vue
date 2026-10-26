<template>
  <!-- Post-offer onboarding verification checklists -->
  <div>
    <div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div v-for="card in cards" :key="card.label" class="rounded-lg border bg-white px-4 py-3">
        <div class="text-xs text-gray-500">{{ card.label }}</div>
        <div class="text-xl font-semibold text-gray-900">{{ card.value }}</div>
      </div>
    </div>
    <DataTable
      export-name="onboarding-documents"
      :columns="columns"
      :rows="collections"
      :loading="loading"
      :filters="[{ key: 'overall_status', label: 'Statuses' }, { key: 'job_title', label: 'Job Openings' }]"
      clickable
      empty-title="No onboarding checklists yet"
      search-placeholder="Search candidate, application or job..."
      @row-click="openChecklist"
    >
      <template #cell-candidate_name="{ row }">
        <div class="font-medium text-gray-900">{{ row.candidate_name }}</div>
        <div class="font-mono text-xs text-gray-500">{{ row.application_id }}</div>
      </template>
      <template #cell-progress="{ row }">
        <div class="flex items-center gap-2">
          <div class="h-1.5 w-20 overflow-hidden rounded-full bg-gray-100">
            <div class="h-full bg-green-600" :style="{ width: (row.total ? (row.verified / row.total) * 100 : 0) + '%' }" />
          </div>
          <span class="text-xs text-gray-600">{{ row.verified }}/{{ row.total }}</span>
          <span v-if="row.submitted" class="rounded-full bg-blue-50 px-1.5 text-xs text-blue-700">{{ row.submitted }} to check</span>
        </div>
      </template>
      <template #cell-overall_status="{ value }"><StatusBadge :status="value" /></template>
      <template #actions="{ row }">
        <div class="flex justify-end" @click.stop>
          <Button size="sm" icon-left="check-square" @click="openChecklist(row)">Review</Button>
        </div>
      </template>
    </DataTable>

    <VerifyChecklistDialog v-model:open="checklistOpen" :collection="checklistName" @changed="load" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { Button } from 'frappe-ui'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import VerifyChecklistDialog from '@/components/onboarding/VerifyChecklistDialog.vue'
import { documentService } from '@/services/documents'

const collections = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    collections.value = await documentService.listOnboardingCollections()
  } finally {
    loading.value = false
  }
}
onMounted(load)

const columns = [
  { key: 'candidate_name', label: 'Candidate', format: (r) => `${r.candidate_name || ''} ${r.application_id || ''}` },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'progress', label: 'Verified', format: (r) => `${r.verified}/${r.total}` },
  { key: 'overall_status', label: 'Overall Status' },
  { key: 'joining_date', label: 'Joining', format: (r) => (r.joining_date ? dayjs(r.joining_date).format('DD MMM YYYY') : '') },
]
const cards = computed(() => {
  const rows = collections.value
  return [
    { label: 'Checklists', value: rows.length },
    { label: 'Awaiting verification', value: rows.filter((r) => r.submitted).length },
    { label: 'Resubmission requested', value: rows.filter((r) => r.overall_status === 'Resubmission Requested').length },
    { label: 'Complete', value: rows.filter((r) => r.overall_status === 'Complete').length },
  ]
})

const checklistOpen = ref(false)
const checklistName = ref('')
function openChecklist(row) {
  checklistName.value = row.name
  checklistOpen.value = true
}
</script>
