<template>
  <StaffLayout>
    <PageHeader title="My Pending Approvals" />
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        row-key="key"
        empty-title="Nothing pending your approval"
        search-placeholder="Search approvals..."
      >
        <template #cell-job_title="{ row }">
          <router-link :to="`/jobs/${row.job_opening}`" class="hover:underline">{{ row.job_title }}</router-link>
        </template>
        <template #cell-approver_label="{ row }">
          {{ row.approver_label }}
          <span v-if="row.is_override" class="ml-1 rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">
            on behalf (override)
          </span>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="openDialog(row, 'Returned for Revision')">Return</Button>
            <Button variant="solid" @click="openDialog(row, 'Approved')">Approve</Button>
          </div>
        </template>
      </DataTable>
    </div>

    <Dialog v-model="dialogOpen" :options="{ title: dialogTitle }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <ErrorMessage :message="actionError" />
          <div
            v-if="selectedItem?.is_override"
            class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
          >
            You are recording this on behalf of {{ selectedItem.approver_label }}. It will be flagged as an override in the
            approval log.
          </div>
          <FormControl
            v-if="selectedItem?.is_override"
            type="select"
            label="How was it given?"
            v-model="channel"
            :options="['Signature', 'Email', 'Digital']"
          />
          <FormControl
            type="textarea"
            :label="selectedAction === 'Approved' ? 'Remarks (optional)' : 'Reason for returning (required)'"
            v-model="remarks"
            placeholder="Add any remarks or conditions"
          />
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :loading="submitting"
          :disabled="selectedAction !== 'Approved' && !remarks.trim()"
          @click="confirmAction"
        >
          Confirm
        </Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import { usePendingApprovals } from '@/composables/useApprovals'

const { approvals, loading, fetchApprovals, act } = usePendingApprovals()

const columns = [
  { key: 'job_title', label: 'Job Opening' },
  { key: 'doctype', label: 'Type' },
  { key: 'name', label: 'Document' },
  { key: 'approver_label', label: 'Awaiting' },
]
const filters = [
  { key: 'doctype', label: 'Types' },
  { key: 'job_title', label: 'Job Openings' },
]
// A document name is only unique within its doctype.
const rows = computed(() =>
  approvals.value.map((a) => ({ ...a, job_title: a.job_title || a.job_opening, key: `${a.doctype}-${a.name}` })),
)

const dialogOpen = ref(false)
const selectedItem = ref(null)
const selectedAction = ref(null)
const remarks = ref('')
const channel = ref('Digital')
const actionError = ref('')
const submitting = ref(false)

const dialogTitle = computed(() =>
  selectedAction.value === 'Approved' ? 'Approve' : 'Return for Revision',
)

function openDialog(item, action) {
  selectedItem.value = item
  selectedAction.value = action
  remarks.value = ''
  channel.value = item.is_override ? 'Signature' : 'Digital'
  actionError.value = ''
  dialogOpen.value = true
}

async function confirmAction() {
  if (!selectedItem.value) return
  submitting.value = true
  actionError.value = ''
  try {
    await act(selectedItem.value.doctype, selectedItem.value.name, selectedAction.value, remarks.value, channel.value)
    dialogOpen.value = false
    toast({
      title: selectedAction.value === 'Approved' ? 'Approved.' : 'Returned for revision.',
      icon: 'check',
      iconClasses: 'text-green-500',
    })
  } catch (e) {
    actionError.value = e?.messages?.[0] || 'Could not record the action.'
  } finally {
    submitting.value = false
  }
}

onMounted(fetchApprovals)
</script>
