<template>
  <Dialog v-model="show" :options="{ title: title, size: '4xl' }">
    <template #body-content>
      <div v-if="loading && !data" class="py-10 text-center text-sm text-gray-500">Loading…</div>
      <div v-else-if="data">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-gray-50 px-4 py-3 text-sm">
          <div class="min-w-0">
            <div class="font-medium text-gray-900">{{ data.candidate_name }} · <span class="font-mono text-xs">{{ data.application_id }}</span></div>
            <div class="text-xs text-gray-500">{{ data.job_title }}<span v-if="data.candidate_email"> · {{ data.candidate_email }}</span></div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-600">{{ data.summary.verified }}/{{ data.summary.total }} verified</span>
            <StatusBadge :status="data.overall_status" />
          </div>
        </div>
        <p v-if="!data.can_verify" class="mb-3 rounded bg-orange-50 px-3 py-2 text-xs text-orange-800">
          You can view these documents. Verifying them needs a role listed under Document Verifier Roles in Settings.
        </p>

        <!-- Add a document for this candidate only (the position's list is in Master Setup › Positions) -->
        <div v-if="data.can_verify" class="mb-3 flex flex-wrap items-end gap-2 rounded-lg border border-dashed px-3 py-2.5">
          <label class="block min-w-[14rem] flex-1">
            <span class="mb-1.5 block text-xs text-gray-600">Add a document for this candidate</span>
            <!-- Suggests onboarding documents not on the list; a new name becomes a new document type. -->
            <input
              v-model="adding.type"
              type="text"
              :list="`addable-${data.name}`"
              :placeholder="data.addable?.length ? 'Type or pick a document, e.g. Medical Fitness Certificate' : 'All listed documents are added: type a new document name'"
              class="h-8 w-full rounded border-gray-300 bg-white px-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-brand-500 focus:ring-brand-500"
              @keydown.enter.prevent="adding.type.trim() && addDocument()"
            />
            <datalist :id="`addable-${data.name}`">
              <option v-for="d in data.addable" :key="d.name" :value="d.name" />
            </datalist>
          </label>
          <div class="w-40">
            <FormControl v-model="adding.requirement" type="select" label="Requirement" :options="REQUIREMENTS" />
          </div>
          <Button icon-left="plus" :disabled="!adding.type.trim()" :loading="busy === 'add'" @click="addDocument">Add</Button>
          <p v-if="isNewType" class="w-full text-xs text-gray-500">“{{ adding.type.trim() }}” is not a document type yet: adding it also creates it in Master Setup › Document Types.</p>
        </div>

        <div class="overflow-x-auto rounded-lg border">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th class="px-3 py-2">Document</th>
                <th class="px-3 py-2">File</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="(row, i) in data.checklist" :key="row.document_type" class="align-top">
                <td class="px-3 py-2.5">
                  <div class="font-medium text-gray-900">{{ row.document_type }}</div>
                  <div class="text-xs" :class="row.requirement === 'Mandatory' ? 'text-red-700' : 'text-gray-500'">{{ row.requirement }}</div>
                </td>
                <td class="px-3 py-2.5">
                  <button v-if="row.file_url" type="button" class="flex items-center gap-1 text-brand-700 hover:underline" @click="preview(i)">
                    <FeatherIcon :name="row.kind === 'image' ? 'image' : 'file-text'" class="h-4 w-4" />
                    <span class="max-w-[14rem] truncate">{{ row.file_name }}</span>
                  </button>
                  <span v-else class="text-xs text-gray-400">Not uploaded</span>
                  <div v-if="row.submitted_on" class="text-xs text-gray-500">{{ formatDate(row.submitted_on) }}</div>
                </td>
                <td class="px-3 py-2.5">
                  <StatusBadge :status="row.status" />
                  <div v-if="row.status === 'Verified' && row.verified_by" class="mt-0.5 text-xs text-gray-500">by {{ row.verified_by }}</div>
                  <div v-if="row.rejection_reason && row.status !== 'Verified'" class="mt-1 max-w-xs text-xs text-red-700">{{ row.rejection_reason }}</div>
                </td>
                <td class="px-3 py-2.5 text-right">
                  <div v-if="data.can_verify" class="flex justify-end gap-1.5">
                    <Button
                      size="sm"
                      variant="solid"
                      icon-left="check"
                      :class="BTN_SUCCESS"
                      :disabled="!row.attachment || row.status === 'Verified'"
                      :loading="busy === row.document_type + ':verify'"
                      @click="verify(row)"
                    >
                      Verify
                    </Button>
                    <Button
                      size="sm"
                      icon-left="rotate-ccw"
                      :disabled="row.status === 'Requested' || row.status === 'Resubmission Requested'"
                      @click="askReason(row)"
                    >
                      Ask again
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      icon="trash-2"
                      :aria-label="`Remove ${row.document_type}`"
                      title="Remove from this candidate's checklist"
                      :loading="busy === row.document_type + ':remove'"
                      @click="askRemove(row)"
                    />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </Dialog>

  <Dialog v-model="reason.open" :options="{ title: 'Request resubmission', size: 'md' }">
    <template #body-content>
      <p class="mb-3 text-sm text-gray-600">
        <b>{{ reason.row?.document_type }}</b>: the candidate is emailed this reason and asked to upload the document again on the portal.
      </p>
      <FormControl v-model="reason.text" type="textarea" label="Reason" placeholder="e.g. The scan is unreadable; please upload a clearer copy." />
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="reason.open = false">Cancel</Button>
        <Button variant="solid" :class="BTN_DANGER" :disabled="!reason.text.trim()" :loading="busy === reason.row?.document_type + ':reject'" @click="reject">
          Request resubmission
        </Button>
      </div>
    </template>
  </Dialog>

  <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />

  <DocumentViewer v-model:open="viewerOpen" :title="`Joining documents - ${data?.candidate_name || ''}`" :documents="viewerDocs" :start-index="viewerIndex" />
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { documentService } from '@/services/documents'
import { BTN_DANGER, BTN_SUCCESS } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  collection: { type: String, default: '' },
})
const emit = defineEmits(['update:open', 'changed'])

const show = computed({ get: () => props.open, set: (v) => emit('update:open', v) })
const data = ref(null)
const loading = ref(false)
const busy = ref('')
const title = computed(() => (data.value ? `Verify joining documents: ${data.value.candidate_name || ''}` : 'Verify joining documents'))

async function load() {
  if (!props.collection) return
  loading.value = true
  try {
    data.value = await documentService.getCollection(props.collection)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not load the checklist.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    loading.value = false
  }
}
watch(
  () => [props.open, props.collection],
  ([open]) => {
    if (open) {
      data.value = null
      load()
    }
  },
)

// ----- preview: only uploaded rows
const viewerOpen = ref(false)
const viewerIndex = ref(0)
const viewerDocs = computed(() =>
  (data.value?.checklist || []).filter((r) => r.file_url).map((r) => ({ label: r.document_type, file_url: r.file_url, file_name: r.file_name, kind: r.kind })),
)
function preview(i) {
  const url = data.value.checklist[i].file_url
  viewerIndex.value = Math.max(0, viewerDocs.value.findIndex((d) => d.file_url === url))
  viewerOpen.value = true
}

async function verify(row) {
  busy.value = row.document_type + ':verify'
  try {
    await documentService.verifyDocument(data.value.name, row.document_type, true)
    toast({ title: `${row.document_type} verified.`, icon: 'check', iconClasses: 'text-green-500' })
    await load()
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not verify the document.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

const reason = reactive({ open: false, row: null, text: '' })
function askReason(row) {
  Object.assign(reason, { open: true, row, text: '' })
}
async function reject() {
  const row = reason.row
  busy.value = row.document_type + ':reject'
  try {
    await documentService.verifyDocument(data.value.name, row.document_type, false, reason.text.trim())
    toast({ title: 'Resubmission requested. The candidate is emailed the reason.', icon: 'check', iconClasses: 'text-green-500' })
    reason.open = false
    await load()
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not request resubmission.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

// ----- add / remove documents for this candidate
const REQUIREMENTS = ['Mandatory', 'Optional', 'If Applicable'].map((r) => ({ label: r, value: r }))
const adding = reactive({ type: '', requirement: 'Mandatory' })
const isNewType = computed(() => {
  const t = adding.type.trim().toLowerCase()
  if (!t || !data.value) return false
  return ![...(data.value.addable || []).map((d) => d.name), ...data.value.checklist.map((r) => r.document_type)].some((n) => n.toLowerCase() === t)
})
// Start from the document type's own requirement.
watch(
  () => adding.type,
  (t) => {
    const d = data.value?.addable?.find((x) => x.name === t)
    if (d?.requirement) adding.requirement = d.requirement
  },
)
async function addDocument() {
  busy.value = 'add'
  try {
    data.value = await documentService.addChecklistDocument(data.value.name, adding.type.trim(), adding.requirement)
    toast({ title: `${adding.type.trim()} added. The candidate can upload it on the portal.`, icon: 'check', iconClasses: 'text-green-500' })
    adding.type = ''
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not add the document.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

const confirmBox = reactive({ open: false, title: '', message: '', label: '', theme: 'red', run: null })
function askRemove(row) {
  Object.assign(confirmBox, {
    open: true,
    title: `Remove ${row.document_type}?`,
    message:
      `${data.value.candidate_name} will no longer be asked for ${row.document_type}.` +
      (row.attachment ? ' The file they uploaded is kept with their documents but leaves this checklist.' : ''),
    label: 'Remove',
    theme: 'red',
    run: async () => {
      busy.value = row.document_type + ':remove'
      try {
        data.value = await documentService.removeChecklistDocument(data.value.name, row.document_type)
        toast({ title: `${row.document_type} removed.`, icon: 'check', iconClasses: 'text-green-500' })
        emit('changed')
      } catch (e) {
        toast({ title: e?.messages?.[0] || 'Could not remove the document.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
      } finally {
        busy.value = ''
      }
    },
  })
}

const formatDate = (value) => (value ? dayjs(value).format('DD MMM YYYY, h:mm A') : '')
</script>
