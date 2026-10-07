<template>
  <StaffLayout>
    <PageHeader title="Documents" subtitle="Documents uploaded by candidates with their applications" />
    <div class="flex-1 overflow-y-auto p-6">
      <div class="mb-5 flex gap-1 border-b">
        <button
          v-for="t in TABS"
          :key="t.key"
          class="-mb-px border-b-2 px-4 py-2 text-sm font-medium"
          :class="tab === t.key ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
          @click="tab = t.key"
        >
          {{ t.label }}
        </button>
      </div>

      <!-- Candidate documents: one row per application -->
      <DataTable
        export-name="documents"
        v-if="tab === 'candidate'"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No applications with documents yet"
        search-placeholder="Search candidate, application or job..."
        @row-click="(row) => $router.push(`/applications/${row.name}`)"
      >
        <template #cell-candidate_name="{ row }">
          <div class="font-medium text-gray-900">{{ row.candidate_name || row.candidate }}</div>
          <div class="text-xs text-gray-500">{{ row.candidate_email }}</div>
        </template>
        <template #cell-document_count="{ value }">
          <span
            class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
            :class="value ? 'bg-indigo-50 text-indigo-700' : 'bg-gray-100 text-gray-500'"
          >
            <FeatherIcon name="paperclip" class="h-3 w-3" />{{ value }}
          </span>
        </template>
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-1.5">
            <Button size="sm" icon-left="eye" :disabled="!row.document_count" @click="openViewer(row)">View</Button>
            <Button
              size="sm"
              icon="download"
              :disabled="!row.document_count"
              :link="applicationService.downloadAllDocumentsUrl(row.name)"
              :aria-label="`Download all documents of ${row.application_id} as one PDF`"
              title="Download all as one PDF"
            />
          </div>
        </template>
      </DataTable>

      <!-- Post-offer onboarding verification checklists -->
      <DataTable
        export-name="documents"
        v-else
        :columns="collectionColumns"
        :rows="collections.data || []"
        :loading="collections.loading"
        :filters="[{ key: 'overall_status', label: 'Statuses' }]"
        empty-title="No onboarding checklists yet"
        search-placeholder="Search onboarding checklists..."
      >
        <template #cell-overall_status="{ value }"><StatusBadge :status="value" /></template>
      </DataTable>
    </div>

    <DocumentViewer
      v-model:open="viewerOpen"
      :title="`Applicant Documents - ${viewerRow?.application_id || ''}`"
      :documents="viewerDocs"
      :loading="viewerLoading"
      :download-all-url="viewerRow ? applicationService.downloadAllDocumentsUrl(viewerRow.name) : ''"
    />
  </StaffLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { Button, FeatherIcon, createListResource } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { applicationService } from '@/services/applications'

const TABS = [
  { key: 'candidate', label: 'Candidate Documents' },
  { key: 'onboarding', label: 'Onboarding Verification' },
]
const tab = ref('candidate')

// ----- candidate documents
const rows = ref([])
const loading = ref(false)

const columns = [
  { key: 'application_id', label: 'Application ID' },
  { key: 'candidate_name', label: 'Candidate', format: (r) => `${r.candidate_name || ''} ${r.candidate_email || ''}` },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'document_count', label: 'Documents' },
  { key: 'status', label: 'Status' },
  { key: 'application_date', label: 'Applied On', format: (r) => (r.application_date ? dayjs(r.application_date).format('DD MMM YYYY') : '') },
]
const filters = [
  { key: 'job_title', label: 'Job Openings' },
  { key: 'status', label: 'Statuses' },
]

async function load() {
  loading.value = true
  try {
    rows.value = await applicationService.listApplicationDocuments()
  } finally {
    loading.value = false
  }
}

onMounted(load)

// ----- viewer
const viewerOpen = ref(false)
const viewerRow = ref(null)
const viewerDocs = ref([])
const viewerLoading = ref(false)

async function openViewer(row) {
  viewerRow.value = row
  viewerDocs.value = []
  viewerOpen.value = true
  viewerLoading.value = true
  try {
    viewerDocs.value = (await applicationService.getApplicationDocuments(row.name)).documents
  } finally {
    viewerLoading.value = false
  }
}

// ----- onboarding checklists (post-offer verification)
const collections = createListResource({
  doctype: 'Document Collection',
  fields: ['name', 'application', 'overall_status'],
  orderBy: 'creation desc',
  // DataTable searches, filters and paginates client-side, so load all rows.
  pageLength: 1000,
  auto: true,
})

const collectionColumns = [
  { key: 'application', label: 'Application' },
  { key: 'overall_status', label: 'Overall Status' },
]
</script>
