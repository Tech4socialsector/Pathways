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
        export-name="applications"
        @row-click="(app) => $router.push(`/applications/${app.name}`)"
      >
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template #cell-eligibility_status="{ value }">
          <span
            class="rounded-full px-2 py-0.5 text-xs font-medium"
            :class="value === 'Eligible' ? 'bg-green-50 text-green-700' : value === 'Not Eligible' ? 'bg-red-50 text-red-700' : 'bg-orange-50 text-orange-700'"
          >{{ value === 'Pending' || !value ? 'To check' : value }}</span>
        </template>
        <template #bulk-actions="{ rows, clear }">
          <Button size="sm" variant="solid" icon-left="filter" :class="BTN_DARK" @click="openBulkEligibility(rows, clear)">
            Mark Eligibility
          </Button>
          <Button size="sm" icon-left="archive" :link="applicationService.documentsZipUrl({ applications: rows.map((r) => r.name) })">
            Download Documents
          </Button>
          <Button size="sm" variant="solid" icon-left="refresh-cw" :class="BTN_BRAND" @click="openBulkStatus(rows, clear)">
            Change Status
          </Button>
          <Button
            v-if="session.can('Application', 'delete')"
            size="sm"
            variant="solid"
            icon-left="trash-2"
            :class="BTN_DANGER"
            @click="openBulkDelete(rows, clear)"
          >
            Delete
          </Button>
        </template>
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
    <Dialog v-model="bulk.statusOpen" :options="{ title: `Change status of ${bulk.rows.length} application(s)`, size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <FormControl label="New Status" type="select" v-model="bulk.status" :options="['', ...STATUSES]" />
          <FormControl label="Remarks" type="textarea" v-model="bulk.remarks" placeholder="Optional. Recorded on each application's timeline." />
          <p class="text-xs text-gray-500">Applications you can't move to this status are skipped and listed afterwards.</p>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :class="BTN_BRAND" :loading="bulk.running" :disabled="!bulk.status" @click="runBulkStatus">
          Update {{ bulk.rows.length }}
        </Button>
      </template>
    </Dialog>

    <Dialog
      v-model="bulk.deleteOpen"
      :options="{
        title: `Delete ${bulk.rows.length} application(s)?`,
        message: 'This cannot be undone. Applications with status history or other linked records are skipped.',
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" :class="BTN_DANGER" :loading="bulk.running" @click="runBulkDelete">Delete {{ bulk.rows.length }}</Button>
      </template>
    </Dialog>

    <Dialog v-model="bulk.eligibilityOpen" :options="{ title: `Eligibility of ${bulk.rows.length} application(s)`, size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="opt in [{ v: true, l: 'Eligible' }, { v: false, l: 'Not eligible' }]"
              :key="opt.l"
              type="button"
              class="rounded-lg border px-3 py-2 text-sm font-semibold"
              :class="bulk.eligible === opt.v ? (opt.v ? 'border-green-600 bg-green-50 text-green-800' : 'border-red-600 bg-red-50 text-red-800') : 'border-gray-200'"
              @click="bulk.eligible = opt.v"
            >
              {{ opt.l }}
            </button>
          </div>
          <FormControl v-if="!bulk.eligible" label="Reason" type="textarea" v-model="bulk.reason" placeholder="Applies to every selected application" />
          <p class="text-xs text-gray-500">
            Eligible moves Submitted applications to Under Review; Not eligible moves them to Not Selected. Only the recruitment
            team or each job's committee can mark eligibility; others are skipped.
          </p>
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :class="BTN_BRAND"
          :loading="bulk.running"
          :disabled="!bulk.eligible && !bulk.reason.trim()"
          @click="runBulkEligibility"
        >
          Update {{ bulk.rows.length }}
        </Button>
      </template>
    </Dialog>

    <BulkResultDialog :result="bulk.result" :label-for="labelFor" @close="bulk.result = null" />
  </StaffLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import dayjs from 'dayjs'
import { Button } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import BulkResultDialog from '@/components/common/BulkResultDialog.vue'
import { BTN_BRAND, BTN_DANGER, BTN_DARK } from '@/utils/buttonStyles'
import { scoringService } from '@/services/scoring'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useApplicationList } from '@/composables/useApplicationList'
import { applicationService } from '@/services/applications'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const applications = useApplicationList()

const columns = [
  { key: 'application_id', label: 'Application ID' },
  { key: 'candidate_name', label: 'Candidate', format: (row) => row.candidate_name || row.candidate },
  { key: 'job_title', label: 'Job Opening', format: (row) => row.job_title || row.job_opening },
  { key: 'eligibility_status', label: 'Eligibility' },
  { key: 'status', label: 'Status' },
  { key: 'application_date', label: 'Applied On', format: (row) => (row.application_date ? dayjs(row.application_date).format('DD MMM YYYY') : '') },
]
const filters = [
  { key: 'eligibility_status', label: 'Eligibility' },
  { key: 'status', label: 'Statuses' },
  { key: 'job_title', label: 'Job Openings' },
]

// ----- bulk actions
const STATUSES = [
  'Submitted', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Interview Completed', 'Selected',
  'Offer Extended', 'Offer Accepted', 'Offer Declined', 'Documents Pending', 'Documents Verified', 'Joined',
  'Not Selected', 'Withdrawn',
]
const bulk = reactive({
  rows: [],
  clear: null,
  status: '',
  remarks: '',
  eligible: true,
  reason: '',
  statusOpen: false,
  deleteOpen: false,
  eligibilityOpen: false,
  running: false,
  result: null,
})

function labelFor(name) {
  const row = (applications.data || []).find((r) => r.name === name)
  return row ? `${row.application_id} · ${row.candidate_name || row.candidate}` : name
}

function openBulkStatus(rows, clear) {
  Object.assign(bulk, { rows, clear, status: '', remarks: '', statusOpen: true })
}

function openBulkEligibility(rows, clear) {
  Object.assign(bulk, { rows, clear, eligible: true, reason: '', eligibilityOpen: true })
}

function runBulkEligibility() {
  runBulk(
    (names) => scoringService.bulkSetEligibility(names, bulk.eligible, bulk.reason),
    bulk.eligible ? 'marked eligible' : 'marked not eligible',
  )
}

function openBulkDelete(rows, clear) {
  Object.assign(bulk, { rows, clear, deleteOpen: true })
}

async function runBulk(call, verb) {
  bulk.running = true
  try {
    const result = await call(bulk.rows.map((r) => r.name))
    bulk.statusOpen = bulk.deleteOpen = bulk.eligibilityOpen = false
    bulk.clear?.()
    toast({
      title: `${result.done.length} application(s) ${verb}${result.failed.length ? `, ${result.failed.length} skipped` : ''}.`,
      icon: result.failed.length ? 'alert-triangle' : 'check',
      iconClasses: result.failed.length ? 'text-orange-500' : 'text-green-500',
    })
    if (result.failed.length) bulk.result = result
    applications.reload()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'The bulk action failed.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    bulk.running = false
  }
}

function runBulkStatus() {
  runBulk((names) => applicationService.bulkSetStatus(names, bulk.status, bulk.remarks), `moved to ${bulk.status}`)
}

function runBulkDelete() {
  runBulk((names) => applicationService.bulkDelete(names), 'deleted')
}

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
