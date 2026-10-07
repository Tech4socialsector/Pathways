<template>
  <StaffLayout>
    <PageHeader
      title="Job Openings"
      subtitle="Manage and track all job openings across departments and employment types."
      :breadcrumbs="[{ label: 'Dashboard', to: '/' }, { label: 'Job Openings' }]"
    >
      <template #actions>
        <Button v-if="session.can('Job Opening', 'create')" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="openCreateDialog">
          New Job Opening
        </Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <DataTable
        ref="table"
        toolbar-panel
        :columns="columns"
        :extra-columns="extraColumns"
        :rows="jobs"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No job openings"
        search-placeholder="Search job openings..."
        export-name="job-openings"
        @row-click="(job) => router.push(`/jobs/${job.name}`)"
      >
      <!-- Status at a glance; a tab filters the list to that status. -->
      <template #above-toolbar>
      <nav v-if="jobs.length" class="-mx-1 flex gap-1 overflow-x-auto border-b" aria-label="Filter by status">
        <button
          v-for="t in statusTabs"
          :key="t.key"
          type="button"
          class="relative flex shrink-0 items-center gap-2 px-3 pb-3 pt-3 text-sm transition"
          :class="activeStatusTab === t.key ? 'font-semibold text-brand-700' : 'text-gray-600 hover:text-gray-900'"
          :aria-current="activeStatusTab === t.key ? 'true' : undefined"
          @click="table?.setFilter('status', t.key === ALL_TAB ? [] : [t.key])"
        >
          <span v-if="t.dot" class="h-2 w-2 rounded-full" :class="t.dot" />
          {{ t.label }}
          <span
            class="rounded-full px-1.5 text-xs font-semibold"
            :class="activeStatusTab === t.key ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'"
          >
            {{ t.count }}
          </span>
          <span v-if="activeStatusTab === t.key" class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-700" />
        </button>
      </nav>
      </template>
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template #card="{ row, selectable, selected, toggle }">
          <div class="flex items-start gap-3">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
              <FeatherIcon :name="trackIcon(row.track)" class="h-5 w-5" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-2">
                <div class="flex min-w-0 items-center gap-2">
                  <input
                    v-if="selectable"
                    type="checkbox"
                    class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                    :checked="selected"
                    :aria-label="`Select ${row.job_title}`"
                    @click.stop
                    @change="toggle($event.target.checked)"
                  />
                  <span class="truncate text-xs font-medium uppercase tracking-wide text-gray-500">{{ row.position || 'No job code' }}</span>
                </div>
                <div class="flex shrink-0 items-center gap-1" @click.stop>
                  <StatusBadge :status="row.status" />
                  <Dropdown :options="cardMenu(row)" placement="right">
                    <button type="button" class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-800" :aria-label="`Actions for ${row.job_title}`">
                      <FeatherIcon name="more-vertical" class="h-4 w-4" />
                    </button>
                  </Dropdown>
                </div>
              </div>
              <h3 class="mt-1 line-clamp-2 font-heading text-base font-semibold leading-snug text-gray-900 group-hover:text-brand-700" :title="row.job_title">
                {{ row.job_title }}
              </h3>
              <p class="mt-0.5 truncate text-sm text-gray-500" :title="row.department">{{ row.department }}</p>
            </div>
          </div>

          <div class="mt-3 flex flex-wrap gap-1.5 pl-[3.25rem]">
            <span v-if="row.track" class="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
              <FeatherIcon :name="trackIcon(row.track)" class="h-3 w-3" />{{ row.track }}
            </span>
            <span v-if="row.employment_type" class="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
              <FeatherIcon name="briefcase" class="h-3 w-3" />{{ row.employment_type }}
            </span>
          </div>

          <div class="mt-auto pt-4">
            <div class="flex items-center justify-between gap-3 border-t pt-3 text-xs">
              <div class="flex items-center gap-3 text-gray-600">
                <span class="flex items-center gap-1.5" :title="`${row.vacancies || 0} vacancies`">
                  <FeatherIcon name="users" class="h-3.5 w-3.5 text-gray-400" />
                  {{ row.vacancies || 0 }} {{ Number(row.vacancies) === 1 ? 'post' : 'posts' }}
                </span>
                <span class="h-3 w-px bg-gray-200" aria-hidden="true" />
                <span class="flex items-center gap-1.5" :title="`${row.applications || 0} applications`">
                  <FeatherIcon name="file-text" class="h-3.5 w-3.5 text-gray-400" />
                  {{ row.applications || 0 }} applied
                </span>
              </div>
              <span class="flex shrink-0 items-center gap-1.5" :class="deadlineInfo(row).tone" :title="deadlineInfo(row).title">
                <FeatherIcon :name="deadlineInfo(row).icon" class="h-3.5 w-3.5" />{{ deadlineInfo(row).text }}
              </span>
            </div>
          </div>
        </template>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dialog, Dropdown, FeatherIcon, FormControl } from 'frappe-ui'
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
// More fields users can add from the Columns menu.
const extraColumns = [
  { key: 'applications', label: 'Applications', align: 'right' },
  { key: 'has_committee', label: 'Committee' },
  {
    key: 'application_start',
    label: 'Applications Open',
    format: (row) => (row.application_start ? dayjs(row.application_start).format('DD MMM YYYY') : ''),
  },
  { key: 'pay_level', label: 'Pay Level' },
  { key: 'tenure_description', label: 'Tenure' },
  { key: 'shortlisting_ratio', label: 'Shortlisting Ratio', format: (row) => (row.shortlisting_ratio ? `1:${row.shortlisting_ratio}` : 'Default') },
  { key: 'creation', label: 'Created On', format: (row) => (row.creation ? dayjs(row.creation).format('DD MMM YYYY') : '') },
  { key: 'modified', label: 'Last Updated', format: (row) => (row.modified ? dayjs(row.modified).format('DD MMM YYYY, h:mm A') : '') },
  { key: 'name', label: 'Record ID' },
]
function deadlineInfo(row) {
  if (!row.application_deadline) return { text: 'No deadline', tone: 'text-gray-400', title: 'No application deadline set', icon: 'calendar' }
  const close = dayjs(row.application_deadline)
  const when = close.format('DD MMM YYYY')
  const title = `Applications close ${when}`
  if (row.status !== 'Advertised') return { text: when, tone: 'text-gray-500', title, icon: 'calendar' }
  const days = close.startOf('day').diff(dayjs().startOf('day'), 'day')
  if (days < 0) return { text: 'Deadline passed', tone: 'font-medium text-red-600', title, icon: 'alert-circle' }
  if (days === 0) return { text: 'Closes today', tone: 'font-medium text-orange-600', title, icon: 'clock' }
  return { text: `${days}d left`, tone: days <= 7 ? 'font-medium text-orange-600' : 'font-medium text-green-700', title, icon: 'clock' }
}

// One icon per track, on the card and its track chip.
function trackIcon(track) {
  return { Faculty: 'book-open', Research: 'search', Admin: 'briefcase' }[track] || 'file-text'
}

// The card's ⋮ menu.
function cardMenu(row) {
  const items = [
    { label: 'Open', icon: 'external-link', onClick: () => router.push(`/jobs/${row.name}`) },
    { label: 'View applications', icon: 'file-text', onClick: () => router.push({ path: '/applications', query: { job: row.name } }) },
  ]
  if (row.status === 'Advertised') {
    items.push({ label: 'View public posting', icon: 'globe', onClick: () => window.open(`/pathways/portal/jobs/${row.name}`, '_blank') })
  }
  if (session.can('Job Opening', 'write')) {
    items.push({ label: 'Change status', icon: 'refresh-cw', onClick: () => openBulk('status', [row], null) })
  }
  if (session.can('Job Opening', 'delete')) {
    items.push({ label: 'Delete', icon: 'trash-2', onClick: () => openBulk('delete', [row], null) })
  }
  return [{ group: 'Actions', hideLabel: true, items }]
}

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

// ----- status tabs (only statuses that have jobs, in workflow order)
const ALL_TAB = '__all__'
const STATUS_DOTS = {
  Draft: 'bg-orange-400',
  'Pending Approval': 'bg-yellow-400',
  Approved: 'bg-blue-500',
  Advertised: 'bg-green-500',
  Closed: 'bg-gray-400',
  Filled: 'bg-teal-500',
  Cancelled: 'bg-red-500',
}
const table = ref(null)
const statusTabs = computed(() => {
  const counts = {}
  for (const j of jobs.value) counts[j.status] = (counts[j.status] || 0) + 1
  const known = JOB_STATUSES.filter((s) => counts[s])
  const other = Object.keys(counts).filter((s) => !JOB_STATUSES.includes(s)).sort()
  return [
    { key: ALL_TAB, label: 'All', count: jobs.value.length },
    ...[...known, ...other].map((s) => ({ key: s, label: s, count: counts[s], dot: STATUS_DOTS[s] || 'bg-gray-400' })),
  ]
})
// A tab is active when the Status filter holds exactly that status (or nothing, for All).
const activeStatusTab = computed(() => {
  const chosen = table.value?.filterValues?.status || []
  if (!chosen.length) return ALL_TAB
  return chosen.length === 1 ? chosen[0] : null
})
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
