<template>
  <StaffLayout>
    <PageHeader title="My Pending Approvals" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!approvals.length" title="Nothing pending your approval" />
      <div v-else class="flex flex-col gap-3">
        <div
          v-for="item in approvals"
          :key="`${item.doctype}-${item.name}`"
          class="flex items-center justify-between rounded-lg border bg-white p-4"
        >
          <div>
            <div class="text-sm font-medium text-gray-900">{{ item.name }}</div>
            <div class="text-xs text-gray-500">
              {{ item.doctype }} &middot; {{ item.job_opening }} &middot; awaiting {{ item.approver_label }}
            </div>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" @click="openDialog(item, 'Returned for Revision')">Return</Button>
            <Button variant="solid" @click="openDialog(item, 'Approved')">Approve</Button>
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model="dialogOpen" :options="{ title: dialogTitle }">
      <template #body-content>
        <FormControl
          type="textarea"
          label="Remarks (optional)"
          v-model="remarks"
          placeholder="Add any remarks or conditions"
        />
      </template>
      <template #actions>
        <Button variant="solid" :loading="submitting" @click="confirmAction">Confirm</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, Dialog, FormControl } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { usePendingApprovals } from '@/composables/useApprovals'

const { approvals, loading, fetchApprovals, act } = usePendingApprovals()

const dialogOpen = ref(false)
const selectedItem = ref(null)
const selectedAction = ref(null)
const remarks = ref('')
const submitting = ref(false)

const dialogTitle = computed(() =>
  selectedAction.value === 'Approved' ? 'Approve' : 'Return for Revision',
)

function openDialog(item, action) {
  selectedItem.value = item
  selectedAction.value = action
  remarks.value = ''
  dialogOpen.value = true
}

async function confirmAction() {
  if (!selectedItem.value) return
  submitting.value = true
  try {
    await act(selectedItem.value.doctype, selectedItem.value.name, selectedAction.value, remarks.value)
    dialogOpen.value = false
  } finally {
    submitting.value = false
  }
}

onMounted(fetchApprovals)
</script>
