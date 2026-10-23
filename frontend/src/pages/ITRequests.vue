<template>
  <StaffLayout>
    <PageHeader title="IT Requests" subtitle="New joiners: arrange a laptop, create the NLS email ID, access card and seating" />
    <div class="flex-1 overflow-y-auto p-6">
      <div class="mb-4 grid grid-cols-3 gap-3">
        <div v-for="card in cards" :key="card.label" class="rounded-lg border bg-white px-4 py-3">
          <div class="text-xs text-gray-500">{{ card.label }}</div>
          <div class="text-xl font-semibold text-gray-900">{{ card.value }}</div>
        </div>
      </div>

      <DataTable
        export-name="it-requests"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="[{ key: 'status', label: 'Statuses' }, { key: 'department', label: 'Departments' }]"
        clickable
        empty-title="No IT requests yet"
        search-placeholder="Search name, designation or email..."
        @row-click="openRequest"
      >
        <template #cell-employee_name="{ row }">
          <div class="font-medium text-gray-900">{{ row.employee_name }}</div>
          <div class="text-xs text-gray-500">{{ row.designation }}</div>
        </template>
        <template #cell-tasks="{ row }">
          <div class="flex gap-1.5">
            <span v-for="t in TASKS" :key="t.field" :title="t.label" class="flex h-6 w-6 items-center justify-center rounded-full" :class="row[t.field] ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-400'">
              <FeatherIcon :name="t.icon" class="h-3.5 w-3.5" />
            </span>
          </div>
        </template>
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template #actions="{ row }">
          <div class="flex justify-end" @click.stop>
            <Button size="sm" :icon-left="row.status === 'Completed' ? 'eye' : 'edit-2'" @click="openRequest(row)">{{ row.status === 'Completed' ? 'View' : 'Update' }}</Button>
          </div>
        </template>
      </DataTable>
    </div>

    <Dialog v-model="edit.open" :options="{ title: edit.row ? `IT & Facilities: ${edit.row.employee_name}` : 'IT & Facilities', size: 'xl' }">
      <template #body-content>
        <div v-if="edit.row" class="flex flex-col gap-4 text-sm">
          <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 rounded-lg bg-gray-50 px-4 py-3">
            <dt class="text-gray-500">Designation</dt><dd>{{ edit.row.designation || '-' }}</dd>
            <dt class="text-gray-500">Department</dt><dd>{{ edit.row.department || '-' }}</dd>
            <dt class="text-gray-500">Date of joining</dt><dd class="font-medium">{{ formatDay(edit.row.date_of_joining) }}</dd>
            <dt class="text-gray-500">Reporting at</dt><dd>{{ edit.row.reporting_location || '-' }}</dd>
            <dt class="text-gray-500">Personal email</dt><dd class="break-all">{{ edit.row.personal_email || '-' }}</dd>
            <dt class="text-gray-500">Mobile</dt><dd>{{ edit.row.mobile_number || '-' }}</dd>
          </dl>
          <div class="flex flex-col gap-2">
            <label v-for="t in TASKS" :key="t.field" class="flex items-center gap-2">
              <input v-model="edit.values[t.field]" type="checkbox" class="rounded border-gray-300" :disabled="readOnly" />
              <span>{{ t.label }}</span>
              <span v-if="t.required" class="text-xs text-red-600">required to complete</span>
            </label>
          </div>
          <FormControl v-model="edit.values.official_email" type="email" label="Official (NLS) email ID" placeholder="firstname.lastname@nls.ac.in" :disabled="readOnly" />
          <FormControl v-model="edit.values.remarks" type="textarea" label="Remarks" :disabled="readOnly" />
          <p v-if="edit.row.status === 'Completed'" class="rounded bg-green-50 px-3 py-2 text-xs text-green-800">
            Completed by {{ edit.row.completed_by_name }} on {{ formatDateTime(edit.row.completed_on) }}.
          </p>
        </div>
      </template>
      <template v-if="!readOnly" #actions>
        <div class="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" @click="edit.open = false">Cancel</Button>
          <Button :loading="busy === 'save'" @click="save(false)">Save progress</Button>
          <Button variant="solid" icon-left="check" :class="BTN_SUCCESS" :disabled="!canComplete" :loading="busy === 'complete'" @click="save(true)">
            Complete &amp; notify recruiter
          </Button>
        </div>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import dayjs from 'dayjs'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { itRequestService } from '@/services/joining'
import { BTN_SUCCESS } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const TASKS = [
  { field: 'laptop_arranged', label: 'Laptop arranged', icon: 'monitor', required: true },
  { field: 'official_email_created', label: 'NLS email ID created', icon: 'mail', required: true },
  { field: 'access_card_issued', label: 'Access card issued', icon: 'credit-card' },
  { field: 'seating_arranged', label: 'Seating arranged', icon: 'home' },
]

const rows = ref([])
const loading = ref(false)
const canWrite = ref(false)
const busy = ref('')

const formatDay = (value) => (value ? dayjs(value).format('DD MMM YYYY') : '')
const formatDateTime = (value) => (value ? dayjs(value).format('DD MMM YYYY, h:mm A') : '')

const columns = [
  { key: 'employee_name', label: 'New Joiner', format: (r) => `${r.employee_name || ''} ${r.designation || ''}` },
  { key: 'department', label: 'Department' },
  { key: 'date_of_joining', label: 'Date of Joining', format: (r) => formatDay(r.date_of_joining) },
  { key: 'tasks', label: 'Done', format: (r) => TASKS.filter((t) => r[t.field]).map((t) => t.label).join(', ') },
  { key: 'official_email', label: 'Official Email' },
  { key: 'status', label: 'Status' },
]
const cards = computed(() => [
  { label: 'Pending', value: rows.value.filter((r) => r.status === 'Pending').length },
  { label: 'In progress', value: rows.value.filter((r) => r.status === 'In Progress').length },
  { label: 'Completed', value: rows.value.filter((r) => r.status === 'Completed').length },
])

async function load() {
  loading.value = true
  try {
    const res = await itRequestService.listRequests()
    rows.value = res.requests || []
    canWrite.value = !!res.can_write
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not load IT requests.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    loading.value = false
  }
}

const edit = reactive({ open: false, row: null, values: {} })
const readOnly = computed(() => !canWrite.value || edit.row?.status === 'Completed')
const canComplete = computed(() => edit.values.laptop_arranged && edit.values.official_email_created && (edit.values.official_email || '').trim())

function openRequest(row) {
  edit.row = row
  edit.values = {
    ...Object.fromEntries(TASKS.map((t) => [t.field, !!row[t.field]])),
    official_email: row.official_email || '',
    remarks: row.remarks || '',
  }
  edit.open = true
}

async function save(complete) {
  busy.value = complete ? 'complete' : 'save'
  try {
    const updated = await itRequestService.saveRequest(edit.row.name, edit.values, complete)
    const index = rows.value.findIndex((r) => r.name === updated.name)
    if (index >= 0) rows.value[index] = { ...rows.value[index], ...updated }
    toast({ title: complete ? 'Completed. The recruitment team has been notified.' : 'Saved.', icon: 'check', iconClasses: 'text-green-500' })
    edit.open = false
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

onMounted(load)
</script>
