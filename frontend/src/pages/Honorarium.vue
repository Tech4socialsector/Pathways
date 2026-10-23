<template>
  <StaffLayout>
    <PageHeader title="Panel Honorarium" subtitle="Thank-you and honorarium for Selection Committee panellists (workflow step 33)">
      <template #actions>
        <Button variant="outline" icon-left="download" :loading="exporting" @click="exportList">Download Excel</Button>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div v-for="t in tiles" :key="t.label" class="rounded-xl border bg-white p-4 shadow-sm">
          <div class="text-2xl font-bold tabular-nums" :class="t.tone">{{ t.value }}</div>
          <div class="mt-0.5 text-xs text-gray-500">{{ t.label }}</div>
        </div>
      </div>

      <div v-if="error" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>

      <DataTable
        export-name="panel-honorarium"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        toolbar-panel
        empty-title="No honoraria yet. They are created by “Send thank-you to panel” on a job's consolidated score sheet."
        search-placeholder="Search panellist or position..."
      >
        <template #above-toolbar>
          <div class="flex flex-wrap gap-1 border-b pb-2 pt-2" role="tablist" aria-label="Status">
            <button
              v-for="s in STATUS_TABS"
              :key="s.value"
              type="button"
              role="tab"
              class="rounded-md px-3 py-1.5 text-sm"
              :class="status === s.value ? 'bg-brand-50 font-semibold text-brand-800' : 'text-gray-600 hover:bg-gray-100'"
              :aria-selected="status === s.value"
              @click="status = s.value"
            >
              {{ s.label }}
            </button>
          </div>
        </template>
        <template #cell-panellist_name="{ row }">
          <div class="font-medium text-gray-900">{{ row.panellist_name || row.panellist }}</div>
          <div class="text-xs text-gray-500">{{ row.panellist }}</div>
        </template>
        <template #cell-amount="{ row }">
          <span class="tabular-nums">{{ money(row.amount) }}</span>
        </template>
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
          <div v-if="row.status === 'Paid'" class="mt-0.5 text-[11px] text-gray-500">
            {{ fmtDate(row.paid_on) }}<template v-if="row.payment_reference"> · {{ row.payment_reference }}</template>
          </div>
          <div v-else-if="row.approved_by_name" class="mt-0.5 text-[11px] text-gray-500">by {{ row.approved_by_name }}</div>
        </template>
        <template #cell-paperwork="{ row }">
          <span class="text-xs" :class="row.pan_number ? 'text-gray-700' : 'text-orange-700'">{{ row.pan_number || 'No PAN' }}</span>
          <a v-if="row.bank_consent_form" :href="row.bank_consent_form" target="_blank" rel="noopener" class="ml-2 text-xs text-brand-700 hover:underline">Bank form</a>
          <span v-else class="ml-2 text-xs text-orange-700">No bank form</span>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-1">
            <Button v-if="data.can_approve && row.status === 'Pending'" size="sm" variant="outline" @click="askApprove([row])">Approve</Button>
            <Button v-if="data.can_write && row.status === 'Approved'" size="sm" variant="outline" @click="openPaid([row])">Mark paid</Button>
            <Button v-if="data.can_write" size="sm" variant="ghost" icon="edit-2" :aria-label="`Edit ${row.panellist_name}`" @click="openEdit(row)" />
          </div>
        </template>
        <template #bulk-actions="{ rows: picked, clear }">
          <Button v-if="data.can_approve" size="sm" icon-left="check" @click="askApprove(picked, clear)">Approve</Button>
          <Button v-if="data.can_write" size="sm" icon-left="credit-card" @click="openPaid(picked, clear)">Mark paid</Button>
        </template>
      </DataTable>
      <p class="mt-2 text-xs text-gray-500">
        Pending → Approved (by an honorarium approver, Pathways Settings › Panel Honorarium) → Paid. Default amounts and
        “external experts only” are set in Pathways Settings.
      </p>
    </div>

    <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />

    <!-- Mark paid -->
    <Dialog v-model="paid.open" :options="{ title: `Mark ${paid.rows.length === 1 ? 'honorarium' : paid.rows.length + ' honoraria'} paid`, size: 'sm' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl v-model="paid.date" type="date" label="Paid on" />
          <FormControl v-model="paid.reference" label="Payment reference" placeholder="e.g. UTR / voucher number" />
          <p v-if="paid.rows.some((r) => r.status !== 'Approved')" class="text-xs text-orange-700">Only approved honoraria are marked paid; the others are skipped.</p>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="paid.open = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="paid.busy" @click="markPaid">Mark paid</Button>
        </div>
      </template>
    </Dialog>

    <!-- Edit details -->
    <Dialog v-model="edit.open" :options="{ title: edit.row ? `Honorarium · ${edit.row.panellist_name || edit.row.panellist}` : 'Honorarium', size: 'md' }">
      <template #body-content>
        <div v-if="edit.row" class="flex flex-col gap-3">
          <p class="text-sm text-gray-600">{{ edit.row.job_title }} · {{ edit.row.is_external ? 'External expert' : 'Internal panellist' }}</p>
          <FormControl
            v-model="edit.amount"
            type="number"
            label="Amount"
            :disabled="!['Pending', 'Not applicable'].includes(edit.row.status)"
            :description="['Pending', 'Not applicable'].includes(edit.row.status) ? '' : 'The amount cannot change after approval.'"
          />
          <FormControl v-model="edit.pan" label="PAN" placeholder="ABCDE1234F" />
          <div>
            <div class="mb-1.5 text-xs text-gray-600">Bank details / consent form</div>
            <div class="flex flex-wrap items-center gap-2">
              <a v-if="edit.form" :href="edit.form" target="_blank" rel="noopener" class="truncate text-sm text-brand-700 hover:underline">{{ edit.form.split('/').pop() }}</a>
              <FileUploader
                file-types=".pdf,.jpg,.jpeg,.png"
                :upload-args="{ doctype: 'Panel Honorarium', docname: edit.row.name, private: true }"
                @success="(f) => (edit.form = f.file_url)"
              >
                <template #default="{ openFileSelector, uploading }">
                  <Button size="sm" icon-left="paperclip" :loading="uploading" @click="openFileSelector">{{ edit.form ? 'Replace' : 'Attach' }}</Button>
                </template>
              </FileUploader>
              <Button v-if="edit.form" size="sm" variant="ghost" @click="edit.form = ''">Remove</Button>
            </div>
            <p class="mt-1 text-xs text-gray-500">Attach the signed form; do not type account numbers here.</p>
          </div>
          <FormControl v-model="edit.remarks" type="textarea" label="Remarks" :rows="2" />
          <label v-if="['Pending', 'Not applicable'].includes(edit.row.status)" class="flex items-center gap-2 text-sm text-gray-700">
            <input v-model="edit.notApplicable" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            No honorarium for this panellist (Not applicable)
          </label>
          <p v-if="edit.error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ edit.error }}</p>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="edit.open = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="edit.busy" @click="saveEdit">Save</Button>
        </div>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FileUploader, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import { honorariumService } from '@/services/honorarium'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const STATUS_TABS = [
  { value: '', label: 'All' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Approved', label: 'Approved' },
  { value: 'Paid', label: 'Paid' },
  { value: 'Not applicable', label: 'Not applicable' },
]
const columns = [
  { key: 'panellist_name', label: 'Panellist' },
  { key: 'job_title', label: 'Position' },
  { key: 'panel_type', label: 'Type' },
  { key: 'amount', label: 'Amount', align: 'right' },
  { key: 'status', label: 'Status' },
  { key: 'paperwork', label: 'PAN / bank form', sortable: false },
  { key: 'thanked', label: 'Thanked on' },
]
const filters = [
  { key: 'job_title', label: 'Positions' },
  { key: 'panel_type', label: 'Types' },
]

const data = ref({ rows: [], can_approve: false, can_write: false })
const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const status = ref('')

const money = (n) => Number(n || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const fmtDate = (d) => (d ? dayjs(d).format('DD MMM YYYY') : '')
const rows = computed(() =>
  (data.value.rows || []).map((r) => ({
    ...r,
    panel_type: r.is_external ? 'External expert' : 'Internal',
    thanked: r.thanks_sent_on ? dayjs(r.thanks_sent_on).format('DD MMM YYYY') : 'Not yet',
  })),
)
const sum = (s) => (data.value.rows || []).filter((r) => r.status === s).reduce((n, r) => n + Number(r.amount || 0), 0)
const tiles = computed(() => [
  { label: 'Panellists', value: (data.value.rows || []).length, tone: 'text-gray-900' },
  { label: 'Pending approval', value: money(sum('Pending')), tone: 'text-orange-700' },
  { label: 'Approved, to pay', value: money(sum('Approved')), tone: 'text-brand-700' },
  { label: 'Paid', value: money(sum('Paid')), tone: 'text-green-700' },
])

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await honorariumService.list('', status.value)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load the honoraria.'
  } finally {
    loading.value = false
  }
}
watch(status, load, { immediate: true })

function report(r, verb) {
  toast({ title: `${r.updated} ${verb}.`, icon: 'check', iconClasses: 'text-green-500' })
  if (r.skipped?.length) toast({ title: `Skipped: ${r.skipped.join('; ')}`, icon: 'alert-triangle', iconClasses: 'text-orange-500' })
}
function failed(e, fallback) {
  toast({ title: e?.messages?.[0] || fallback, icon: 'alert-triangle', iconClasses: 'text-red-500' })
}

const confirmBox = reactive({ open: false, title: '', message: '', label: '', theme: 'gray', run: null })
function askApprove(picked, clear) {
  const total = picked.filter((r) => r.status === 'Pending').reduce((n, r) => n + Number(r.amount || 0), 0)
  Object.assign(confirmBox, {
    open: true,
    title: 'Approve honorarium?',
    message:
      picked.length === 1
        ? `Approve ${money(picked[0].amount)} for ${picked[0].panellist_name}?`
        : `Approve ${picked.length} honoraria, ${money(total)} in all? Records that are not pending, or have no amount, are skipped.`,
    label: 'Approve',
    theme: 'gray',
    run: async () => {
      try {
        report(await honorariumService.approve(picked.map((r) => r.name)), 'approved')
        clear?.()
        await load()
      } catch (e) {
        failed(e, 'Could not approve.')
      }
    },
  })
}

const paid = reactive({ open: false, rows: [], date: '', reference: '', busy: false, clear: null })
function openPaid(picked, clear) {
  Object.assign(paid, { open: true, rows: picked, date: dayjs().format('YYYY-MM-DD'), reference: '', busy: false, clear })
}
async function markPaid() {
  paid.busy = true
  try {
    report(await honorariumService.markPaid(paid.rows.map((r) => r.name), paid.date, paid.reference), 'marked paid')
    paid.open = false
    paid.clear?.()
    await load()
  } catch (e) {
    failed(e, 'Could not mark paid.')
  } finally {
    paid.busy = false
  }
}

const edit = reactive({ open: false, row: null, amount: 0, pan: '', form: '', remarks: '', notApplicable: false, busy: false, error: '' })
function openEdit(row) {
  Object.assign(edit, {
    open: true,
    row,
    amount: row.amount || 0,
    pan: row.pan_number || '',
    form: row.bank_consent_form || '',
    remarks: row.remarks || '',
    notApplicable: row.status === 'Not applicable',
    busy: false,
    error: '',
  })
}
async function saveEdit() {
  edit.busy = true
  edit.error = ''
  const editable = ['Pending', 'Not applicable'].includes(edit.row.status)
  try {
    await honorariumService.update(edit.row.name, {
      amount: editable ? edit.amount : undefined,
      pan_number: edit.pan,
      bank_consent_form: edit.form,
      remarks: edit.remarks,
      not_applicable: editable ? (edit.notApplicable ? 1 : 0) : undefined,
    })
    toast({ title: 'Saved.', icon: 'check', iconClasses: 'text-green-500' })
    edit.open = false
    await load()
  } catch (e) {
    edit.error = e?.messages?.[0] || 'Could not save.'
  } finally {
    edit.busy = false
  }
}

async function exportList() {
  exporting.value = true
  try {
    await honorariumService.exportList('', status.value)
  } catch (e) {
    failed(e, 'Could not download the list.')
  } finally {
    exporting.value = false
  }
}
</script>
