<template>
  <StaffLayout>
    <PageHeader title="Applications" />
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        :columns="columns"
        :rows="applications.data || []"
        :loading="applications.loading"
        :filters="filters"
        clickable
        empty-title="No applications yet"
        search-placeholder="Search applications..."
        @row-click="(app) => $router.push(`/applications/${app.name}`)"
      >
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template v-if="session.can('Application', 'delete')" #actions="{ row }">
          <Button variant="ghost" theme="red" icon="trash-2" @click="confirmDelete(row)" />
        </template>
      </DataTable>
    </div>

    <Dialog
      v-model="showDeleteConfirm"
      :options="{
        title: 'Delete Application',
        message: `Are you sure you want to delete application '${appToDelete?.application_id}'? This cannot be undone.`,
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" theme="red" :loading="deleting" @click="doDelete">Delete</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { ref } from 'vue'
import { Button } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useApplicationList } from '@/composables/useApplicationList'
import { applicationService } from '@/services/applications'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const applications = useApplicationList()

const columns = [
  { key: 'application_id', label: 'Application ID' },
  { key: 'candidate', label: 'Candidate' },
  { key: 'job_opening', label: 'Job Opening' },
  { key: 'status', label: 'Status' },
  { key: 'application_date', label: 'Applied On' },
]
const filters = [
  { key: 'status', label: 'Statuses' },
  { key: 'job_opening', label: 'Job Openings' },
]

const showDeleteConfirm = ref(false)
const appToDelete = ref(null)
const deleting = ref(false)

function confirmDelete(app) {
  appToDelete.value = app
  showDeleteConfirm.value = true
}

async function doDelete() {
  deleting.value = true
  try {
    await applicationService.deleteApplication(appToDelete.value.name)
    showDeleteConfirm.value = false
    toast({ title: 'Application deleted.', icon: 'check', iconClasses: 'text-green-500' })
    applications.reload()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not delete the application.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    deleting.value = false
  }
}
</script>
