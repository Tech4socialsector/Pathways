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
          <div class="min-w-0">
            <router-link :to="`/jobs/${item.job_opening}`" class="text-sm font-medium text-gray-900 hover:underline">
              {{ item.job_title || item.job_opening }}
            </router-link>
            <div class="text-xs text-gray-500">
              {{ item.doctype }} {{ item.name }} &middot; awaiting {{ item.approver_label }}
              <span v-if="item.is_override" class="ml-1 rounded bg-amber-50 px-1.5 py-0.5 text-amber-700">
                on behalf (override)
              </span>
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
import EmptyState from '@/components/common/EmptyState.vue'
import { usePendingApprovals } from '@/composables/useApprovals'

const { approvals, loading, fetchApprovals, act } = usePendingApprovals()

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
