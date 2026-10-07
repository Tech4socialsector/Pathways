<template>
  <StaffLayout>
    <PageHeader title="Job Openings">
      <template #actions>
        <Button
          v-if="session.can('Job Opening', 'create')"
          variant="solid"
          @click="openCreateDialog"
        >
          New Job Opening
        </Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        :columns="columns"
        :rows="jobs"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No job openings"
        search-placeholder="Search job openings..."
        export-name="job-openings"
        @row-click="(job) => router.push(`/jobs/${job.name}`)"
      >
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template v-if="session.can('Job Opening', 'write')" #bulk-actions="{ rows, clear }">
          <Button size="sm" variant="solid" icon-left="refresh-cw" :class="BTN_BRAND" @click="openBulk('status', rows, clear)">
            Change Status
          </Button>
          <Button
            v-if="session.can('Job Opening', 'delete')"
            size="sm"
            variant="solid"
            icon-left="trash-2"
            :class="BTN_DANGER"
            @click="openBulk('delete', rows, clear)"
          >
            Delete
          </Button>
        </template>
      </DataTable>
    </div>

    <Dialog v-model="showCreateDialog" :options="{ title: 'New Job Opening', size: '4xl' }">
      <template #body-content>
        <JobOpeningForm :form="form" :error="formError" />
      </template>
      <template #actions>
        <Button variant="solid" :loading="submitting" @click="submitCreate">Create</Button>
      </template>
    </Dialog>
    <Dialog v-model="bulk.statusOpen" :options="{ title: `Change status of ${bulk.rows.length} job opening(s)`, size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl label="New Status" type="select" v-model="bulk.status" :options="['', ...JOB_STATUSES]" />
          <p class="text-xs text-gray-500">
            Each job keeps its own rules: Approved / Advertised need an approved Green Sheet (unless your role may override)
            and Advertised needs a future deadline. Jobs that can't move are skipped and listed afterwards.
          </p>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :class="BTN_BRAND" :loading="bulk.running" :disabled="!bulk.status" @click="runBulk('status')">
          Update {{ bulk.rows.length }}
        </Button>
      </template>
    </Dialog>

    <Dialog
      v-model="bulk.deleteOpen"
      :options="{
        title: `Delete ${bulk.rows.length} job opening(s)?`,
        message: 'This cannot be undone. Jobs that have applications, green sheets or other linked records are skipped.',
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" :class="BTN_DANGER" :loading="bulk.running" @click="runBulk('delete')">Delete {{ bulk.rows.length }}</Button>
      </template>
    </Dialog>

    <BulkResultDialog :result="bulk.result" :label-for="labelFor" @close="bulk.result = null" />
  </StaffLayout>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BulkResultDialog from '@/components/common/BulkResultDialog.vue'
import { BTN_BRAND, BTN_DANGER } from '@/utils/buttonStyles'
import JobOpeningForm, { emptyJobForm } from '@/components/jobs/JobOpeningForm.vue'
import { useStaffJobOpenings } from '@/composables/useJobOpenings'
import { jobOpeningService } from '@/services/jobOpenings'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const router = useRouter()

const { jobs, loading, fetchJobs } = useStaffJobOpenings()

const columns = [
  { key: 'position', label: 'Job Code' },
  { key: 'job_title', label: 'Job Title' },
  { key: 'track', label: 'Track' },
  { key: 'department', label: 'Department' },
  { key: 'designation', label: 'Designation' },
  { key: 'employment_type', label: 'Employment Type' },
  { key: 'vacancies', label: 'Vacancies' },
  { key: 'status', label: 'Status' },
  {
    key: 'application_deadline',
    label: 'Applications Close',
    format: (row) => {
      if (!row.application_deadline) return ''
      const close = dayjs(row.application_deadline)
      const days = close.startOf('day').diff(dayjs().startOf('day'), 'day')
      const when = close.format('DD MMM YYYY')
      if (row.status !== 'Advertised') return when
      return days < 0 ? `${when} (passed)` : days === 0 ? `${when} (today)` : `${when} (${days}d left)`
    },
  },
]
const filters = [
  { key: 'status', label: 'Statuses' },
  { key: 'track', label: 'Tracks' },
  { key: 'department', label: 'Departments' },
  { key: 'employment_type', label: 'Employment Types' },
]

onMounted(() => {
  session.fetchRoles()
  fetchJobs({}, { limit_page_length: 0 })
})

// ----- bulk actions
const JOB_STATUSES = ['Draft', 'Pending Approval', 'Approved', 'Advertised', 'Closed', 'Filled', 'Cancelled']
const bulk = reactive({ rows: [], clear: null, status: '', statusOpen: false, deleteOpen: false, running: false, result: null })

function labelFor(name) {
  const job = jobs.value.find((j) => j.name === name)
  return job ? `${job.job_title} (${job.position || name})` : name
}

function openBulk(kind, rows, clear) {
  Object.assign(bulk, { rows, clear, status: '', statusOpen: kind === 'status', deleteOpen: kind === 'delete' })
}

async function runBulk(kind) {
  bulk.running = true
  const names = bulk.rows.map((r) => r.name)
  try {
    const result =
      kind === 'status' ? await jobOpeningService.bulkSetStatus(names, bulk.status) : await jobOpeningService.bulkDelete(names)
    bulk.statusOpen = bulk.deleteOpen = false
    bulk.clear?.()
    const verb = kind === 'status' ? `moved to ${bulk.status}` : 'deleted'
    toast({
      title: `${result.done.length} job opening(s) ${verb}${result.failed.length ? `, ${result.failed.length} skipped` : ''}.`,
      icon: result.failed.length ? 'alert-triangle' : 'check',
      iconClasses: result.failed.length ? 'text-orange-500' : 'text-green-500',
    })
    if (result.failed.length) bulk.result = result
    fetchJobs({}, { limit_page_length: 0 })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'The bulk action failed.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    bulk.running = false
  }
}

const showCreateDialog = ref(false)
const submitting = ref(false)
const formError = ref('')
const form = reactive(emptyJobForm())

function openCreateDialog() {
  Object.assign(form, emptyJobForm())
  formError.value = ''
  showCreateDialog.value = true
}

async function submitCreate() {
  formError.value = ''
  submitting.value = true
  try {
    const created = await jobOpeningService.createJob({ ...form })
    showCreateDialog.value = false
    toast({ title: 'Job Opening created.', icon: 'check', iconClasses: 'text-green-500' })
    router.push(`/jobs/${created.name}`)
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not create the Job Opening.'
  } finally {
    submitting.value = false
  }
}
</script>
