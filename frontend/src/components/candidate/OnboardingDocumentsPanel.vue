<template>
  <!-- Joining documents (workflow step 34): shown once the offer is accepted -->
  <section v-if="data?.checklist?.length" id="onboarding-documents" class="mb-6 scroll-mt-20 rounded-xl border bg-white p-5 shadow-sm">
    <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
      <div>
        <div class="text-xs font-bold uppercase tracking-wide text-brand-700">Joining documents</div>
        <p class="mt-1 text-sm text-gray-600">
          Please upload a scanned copy of each document. The People and Culture team will verify them before you join.
          Bring the originals and a photocopy on your day of joining.
        </p>
      </div>
      <StatusBadge :status="data.overall_status" />
    </div>

    <div v-if="joining" class="mb-4 flex flex-wrap gap-x-6 gap-y-1 rounded-lg bg-brand-50 px-4 py-3 text-sm text-brand-900">
      <span v-if="joining.confirmed_doj"><FeatherIcon name="calendar" class="mr-1 inline h-4 w-4" />Joining on <b>{{ formatDay(joining.confirmed_doj) }}</b><span v-if="joining.status !== 'Confirmed' && joining.status !== 'Joined'"> (to be confirmed)</span></span>
      <span v-if="joining.reporting_location"><FeatherIcon name="map-pin" class="mr-1 inline h-4 w-4" />{{ joining.reporting_location }}</span>
      <span v-if="joining.reporting_time"><FeatherIcon name="clock" class="mr-1 inline h-4 w-4" />{{ formatTime(joining.reporting_time) }}</span>
    </div>

    <div class="mb-3 h-2 overflow-hidden rounded-full bg-gray-100" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">
      <div class="h-full rounded-full bg-green-600 transition-all" :style="{ width: progress + '%' }" />
    </div>
    <p class="mb-4 text-xs text-gray-500">
      {{ data.summary.verified }} of {{ data.summary.total }} verified · {{ data.summary.submitted }} awaiting verification
      <span v-if="data.summary.resubmission" class="font-medium text-red-700"> · {{ data.summary.resubmission }} to upload again</span>
    </p>

    <ul class="divide-y rounded-lg border">
      <li v-for="row in data.checklist" :key="row.document_type" class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2 text-sm font-medium text-gray-900">
            {{ row.document_type }}
            <span class="rounded px-1.5 py-0.5 text-[11px] font-medium" :class="row.requirement === 'Mandatory' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-600'">
              {{ row.requirement }}
            </span>
          </div>
          <div class="mt-0.5 text-xs text-gray-500">
            {{ row.formats.map((f) => f.toUpperCase()).join(', ') }} · max {{ row.max_size_mb }} MB
            <template v-if="row.file_url">
              ·
              <a :href="row.file_url" target="_blank" rel="noopener" class="text-brand-700 hover:underline">{{ row.file_name }}</a>
            </template>
          </div>
          <div v-if="row.status === 'Resubmission Requested' && row.rejection_reason" class="mt-1.5 flex items-start gap-1.5 rounded bg-red-50 px-2 py-1.5 text-xs text-red-800">
            <FeatherIcon name="alert-circle" class="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span><b>Please upload again:</b> {{ row.rejection_reason }}</span>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="tone(row.status)">{{ label(row.status) }}</span>
          <FileUploader
            v-if="canUpload(row)"
            :file-types="row.formats.map((f) => '.' + f).join(',')"
            :upload-args="{ private: true }"
            :validate-file="(file) => validate(file, row)"
            @success="(file) => onUploaded(row, file)"
          >
            <template #default="{ uploading, progress: pct, error: uploadError, openFileSelector }">
              <div class="flex flex-col items-end">
                <Button size="sm" :variant="row.attachment ? 'outline' : 'solid'" :class="row.attachment ? '' : BTN_BRAND" :loading="uploading || saving === row.document_type" @click="openFileSelector">
                  <template #prefix><FeatherIcon name="upload" class="h-3.5 w-3.5" /></template>
                  {{ uploading ? `Uploading ${pct}%` : row.attachment ? 'Replace' : 'Upload' }}
                </Button>
                <span v-if="uploadError" class="mt-1 text-xs text-red-600">{{ uploadError }}</span>
              </div>
            </template>
          </FileUploader>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { Button, FeatherIcon, FileUploader } from 'frappe-ui'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { documentService } from '@/services/documents'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  application: { type: String, required: true },
  // Staff opening the candidate page see the list but cannot upload.
  canEdit: { type: Boolean, default: true },
})

const data = ref(null)
const saving = ref('')
const joining = computed(() => data.value?.joining || null)
const progress = computed(() => {
  const s = data.value?.summary
  return s?.total ? Math.round((s.verified / s.total) * 100) : 0
})

async function load() {
  try {
    data.value = await documentService.getMyDocumentChecklist(props.application)
  } catch {
    data.value = null
  }
}

const canUpload = (row) => props.canEdit && row.status !== 'Verified'

const LABELS = { Requested: 'Not uploaded', Submitted: 'Awaiting verification', 'Under Verification': 'Awaiting verification', Verified: 'Verified', 'Resubmission Requested': 'Upload again' }
const label = (status) => LABELS[status] || status
function tone(status) {
  if (status === 'Verified') return 'bg-green-50 text-green-700'
  if (status === 'Resubmission Requested') return 'bg-red-50 text-red-700'
  if (status === 'Submitted' || status === 'Under Verification') return 'bg-blue-50 text-blue-700'
  return 'bg-gray-100 text-gray-600'
}

// UX only: the server re-checks the owner, format and size.
function validate(file, row) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (row.formats.length && !row.formats.includes(ext)) return `Allowed formats: ${row.formats.map((f) => f.toUpperCase()).join(', ')}`
  if (row.max_size_mb && file.size > row.max_size_mb * 1024 * 1024) return `File is larger than ${row.max_size_mb} MB`
  return null
}

async function onUploaded(row, file) {
  saving.value = row.document_type
  try {
    await documentService.uploadDocument(data.value.name, row.document_type, file.file_url)
    toast({ title: `${row.document_type} uploaded.`, icon: 'check', iconClasses: 'text-green-500' })
    await load()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save the document. Please try again.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    saving.value = ''
  }
}

const formatDay = (value) => (value ? dayjs(value).format('dddd, DD MMMM YYYY') : '')
const formatTime = (value) => (value ? dayjs(`2000-01-01 ${value}`).format('h:mm A') : '')

onMounted(load)
watch(() => props.application, load)
defineExpose({ reload: load })
</script>
