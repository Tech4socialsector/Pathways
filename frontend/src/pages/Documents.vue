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
        <template v-if="canShare" #bulk-actions="{ rows: chosen, clear }">
          <Button size="sm" variant="solid" icon-left="share-2" :class="BTN_BRAND" @click="openShare(chosen, clear)">Share with panel</Button>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-1.5" @click.stop>
            <Button
              v-if="canShare"
              size="sm"
              icon-left="share-2"
              :disabled="!row.document_count"
              :aria-label="`Share documents of ${row.application_id} with the panel`"
              title="Share with panel"
              @click="openShare([row])"
            >
              Share
            </Button>
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
      <template v-else>
        <div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div v-for="card in onboardingCards" :key="card.label" class="rounded-lg border bg-white px-4 py-3">
            <div class="text-xs text-gray-500">{{ card.label }}</div>
            <div class="text-xl font-semibold text-gray-900">{{ card.value }}</div>
          </div>
        </div>
        <DataTable
          export-name="onboarding-documents"
          :columns="collectionColumns"
          :rows="collections"
          :loading="collectionsLoading"
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
      </template>
    </div>

    <DocumentViewer
      v-model:open="viewerOpen"
      :title="`Applicant Documents - ${viewerRow?.application_id || ''}`"
      :documents="viewerDocs"
      :loading="viewerLoading"
      :download-all-url="viewerRow ? applicationService.downloadAllDocumentsUrl(viewerRow.name) : ''"
    />
    <SharePanelDialog v-model:open="share.open" :applications="share.applications" @saved="share.clear?.()" />
    <VerifyChecklistDialog v-model:open="checklistOpen" :collection="checklistName" @changed="loadCollections" />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { Button, FeatherIcon } from 'frappe-ui'
import { useRoute } from 'vue-router'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SharePanelDialog from '@/components/documents/SharePanelDialog.vue'
import VerifyChecklistDialog from '@/components/onboarding/VerifyChecklistDialog.vue'
import { documentService } from '@/services/documents'
import { applicationService } from '@/services/applications'
import { useSessionStore } from '@/stores/session'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const TABS = [
  { key: 'candidate', label: 'Candidate Documents' },
  { key: 'onboarding', label: 'Onboarding Verification' },
]
// ?tab=onboarding (e.g. from a joining) opens the verification tab.
const route = useRoute()
const tab = ref(route.query.tab === 'onboarding' ? 'onboarding' : 'candidate')

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
  { key: 'candidate_name', label: 'Candidates' },
  { key: 'application_id', label: 'Application IDs' },
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

// ----- share with the panel (recruitment team: whoever can schedule interviews)
const session = useSessionStore()
const canShare = computed(() => session.can('Interview', 'create'))
const share = reactive({ open: false, applications: [], clear: null })
function openShare(chosen, clear = null) {
  const withDocs = chosen.filter((r) => r.document_count)
  if (!withDocs.length) {
    toast({ title: 'None of these candidates has uploaded documents.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    return
  }
  // Each job has its own Selection Committee, so one job at a time.
  if (new Set(withDocs.map((r) => r.job_opening)).size > 1) {
    toast({ title: 'Choose candidates from one job opening at a time: each job has its own panel. Filter by job opening first.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    return
  }
  Object.assign(share, { open: true, applications: withDocs.map((r) => r.name), clear })
}

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
const collections = ref([])
const collectionsLoading = ref(false)
async function loadCollections() {
  collectionsLoading.value = true
  try {
    collections.value = await documentService.listOnboardingCollections()
  } finally {
    collectionsLoading.value = false
  }
}
watch(
  tab,
  (value) => {
    if (value === 'onboarding' && !collections.value.length) loadCollections()
  },
  { immediate: true },
)

const collectionColumns = [
  { key: 'candidate_name', label: 'Candidate', format: (r) => `${r.candidate_name || ''} ${r.application_id || ''}` },
  { key: 'job_title', label: 'Job Opening' },
  { key: 'progress', label: 'Verified', format: (r) => `${r.verified}/${r.total}` },
  { key: 'overall_status', label: 'Overall Status' },
  { key: 'joining_date', label: 'Joining', format: (r) => (r.joining_date ? dayjs(r.joining_date).format('DD MMM YYYY') : '') },
]
const onboardingCards = computed(() => {
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
