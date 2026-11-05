<template>
  <StaffLayout>
    <PageHeader title="Panel Honorarium" subtitle="External experts on Selection Committees: enter their honorarium and bank details, then send them to the Finance team">
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
      <p v-else-if="!data.finance_email_enabled && !loading" class="mb-4 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
        The “Honorarium details to Finance” email is switched off in Email Setup, so nothing can be sent to Finance.
      </p>

      <DataTable
        export-name="panel-honorarium"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        toolbar-panel
        empty-title="No external experts yet. Mark a panellist as “External expert” on a job's Selection Committee."
        search-placeholder="Search expert or position..."
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
        <template #cell-details="{ row }">
          <span v-if="!row.missing.length" class="rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">Complete</span>
          <span v-else class="text-xs text-orange-700">Missing: {{ row.missing.join(', ') }}</span>
          <div v-if="row.bank_name || row.bank_account_number" class="mt-0.5 text-xs text-gray-500">
            {{ row.bank_name }}<template v-if="row.bank_account_number"> · ••••{{ row.bank_account_number.slice(-4) }}</template>
          </div>
        </template>
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
          <div v-if="row.sent_to_finance_on" class="mt-0.5 text-[11px] text-gray-500">
            {{ fmtDate(row.sent_to_finance_on) }}<template v-if="row.sent_to_finance_by_name"> · {{ row.sent_to_finance_by_name }}</template>
          </div>
        </template>
        <template #actions="{ row }">
          <div v-if="data.can_write" class="flex justify-end gap-1">
            <Button size="sm" variant="outline" icon-left="edit-2" @click="openEdit(row)">{{ row.missing.length ? 'Enter details' : 'Edit' }}</Button>
            <Button
              v-if="!row.missing.length"
              size="sm"
              :variant="row.status === 'Sent to Finance' ? 'ghost' : 'solid'"
              icon-left="send"
              :class="row.status === 'Sent to Finance' ? '' : BTN_BRAND"
              @click="openPreview([row])"
            >
              {{ row.status === 'Sent to Finance' ? 'Send again' : 'Send to Finance' }}
            </Button>
          </div>
        </template>
        <template #bulk-actions="{ rows: picked, clear }">
          <Button v-if="data.can_write" size="sm" icon-left="send" @click="openPreview(picked, clear)">Send to Finance</Button>
        </template>
      </DataTable>
      <p class="mt-2 text-xs text-gray-500">
        Only external experts are paid an honorarium. Enter the details, preview the email and send it: the Finance team gets one email per expert with
        the documents attached. The Finance address and wording are in Email Setup › “Honorarium details to Finance”.
      </p>
    </div>

    <!-- Enter / edit details -->
    <Dialog v-model="edit.open" :options="{ title: edit.row ? `Honorarium · ${edit.row.panellist_name || edit.row.panellist}` : 'Honorarium', size: '2xl' }">
      <template #body-content>
        <div v-if="edit.row" class="flex flex-col gap-5 text-sm">
          <p class="text-gray-600">{{ edit.row.job_title }} · External expert · {{ edit.row.panellist }}</p>

          <section class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <FormControl v-model="edit.f.amount" type="number" label="Honorarium amount (₹) *" :min="0" />
            <FormControl v-model="edit.f.pan_number" label="PAN *" placeholder="ABCDE1234F" maxlength="10" />
          </section>

          <section>
            <h3 class="mb-2 text-sm font-semibold text-gray-900">Bank account</h3>
            <div class="grid grid-cols-1 gap-3 rounded-xl border bg-gray-50/60 p-4 sm:grid-cols-2">
              <FormControl v-model="edit.f.account_holder_name" label="Account holder name *" placeholder="As in the bank records" />
              <FormControl v-model="edit.f.bank_account_number" label="Account number *" placeholder="Digits only" inputmode="numeric" />
              <FormControl v-model="edit.f.bank_name" label="Bank name *" placeholder="e.g. State Bank of India" />
              <FormControl v-model="edit.f.bank_branch" label="Branch" placeholder="e.g. Nagarbhavi, Bengaluru" />
              <FormControl v-model="edit.f.ifsc_code" label="IFSC code *" placeholder="e.g. SBIN0001234" maxlength="11" />
            </div>
          </section>

          <section>
            <h3 class="mb-2 text-sm font-semibold text-gray-900">Documents <span class="font-normal text-gray-500">(attached to the email to Finance)</span></h3>
            <ul class="divide-y overflow-hidden rounded-xl border">
              <li v-for="d in DOCS" :key="d.field" class="flex flex-wrap items-center gap-3 px-3 py-2.5">
                <FeatherIcon name="file-text" class="h-4 w-4 shrink-0 text-gray-400" />
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-medium text-gray-900">{{ d.label }}</p>
                  <a v-if="edit.f[d.field]" :href="edit.f[d.field]" target="_blank" rel="noopener" class="block truncate text-xs text-brand-700 hover:underline">
                    {{ edit.f[d.field].split('/').pop() }}
                  </a>
                  <p v-else class="text-xs text-gray-500">Not attached</p>
                </div>
                <FileUploader
                  file-types=".pdf,.jpg,.jpeg,.png"
                  :upload-args="{ doctype: 'Panel Honorarium', docname: edit.row.name, private: true }"
                  @success="(f) => (edit.f[d.field] = f.file_url)"
                >
                  <template #default="{ openFileSelector, uploading }">
                    <Button size="sm" icon-left="paperclip" :loading="uploading" @click="openFileSelector">{{ edit.f[d.field] ? 'Replace' : 'Attach' }}</Button>
                  </template>
                </FileUploader>
                <Button v-if="edit.f[d.field]" size="sm" variant="ghost" @click="edit.f[d.field] = ''">Remove</Button>
              </li>
            </ul>
          </section>

          <FormControl v-model="edit.f.remarks" type="textarea" label="Remarks (included in the email)" :rows="2" />
          <p v-if="edit.error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{{ edit.error }}</p>
        </div>
      </template>
      <template #actions>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="text-xs text-gray-500">* needed before sending to Finance</p>
          <div class="flex gap-2">
            <Button variant="ghost" @click="edit.open = false">Cancel</Button>
            <Button :loading="edit.busy === 'save'" :disabled="!!edit.busy" @click="saveEdit(false)">Save</Button>
            <Button variant="solid" icon-left="eye" :class="BTN_BRAND" :loading="edit.busy === 'preview'" :disabled="!!edit.busy" @click="saveEdit(true)">
              Save &amp; preview email
            </Button>
          </div>
        </div>
      </template>
    </Dialog>

    <!-- Preview, then send -->
    <EmailPreviewDialog v-model="preview.open" :preview="preview.data" :loading="preview.loading" :error="preview.error" hide-addresses>
      <template #header>
        <div class="flex flex-col gap-3 rounded-lg border px-4 py-3">
          <FormControl v-model="preview.to" label="To *" placeholder="finance@nls.ac.in (separate several with commas)" />
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <FormControl v-model="preview.cc" label="CC" placeholder="Optional" />
            <FormControl v-model="preview.bcc" label="BCC" placeholder="Optional" />
          </div>
          <label v-if="preview.data?.can_remember" class="flex items-center gap-2 text-xs text-gray-600">
            <input v-model="preview.remember" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            Remember To and CC for next time (saved in Email Setup)
          </label>
          <p v-if="addressError" class="text-xs text-red-600">{{ addressError }}</p>
        </div>
      </template>
      <template #actions>
        <span v-if="preview.rows.length > 1" class="mr-auto self-center text-xs text-gray-500">
          Showing {{ preview.rows[0].panellist_name }}'s email; {{ preview.rows.length }} emails will go, one per expert.
        </span>
        <Button
          v-if="preview.data && !preview.error"
          variant="solid"
          icon-left="send"
          :class="BTN_BRAND"
          :loading="preview.sending"
          :disabled="!preview.data.enabled || !!addressError"
          @click="send"
        >
          {{ preview.rows.length > 1 ? `Send ${preview.rows.length} emails` : 'Send to Finance' }}
        </Button>
      </template>
    </EmailPreviewDialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FileUploader, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmailPreviewDialog from '@/components/common/EmailPreviewDialog.vue'
import { honorariumService } from '@/services/honorarium'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const STATUS_TABS = [
  { value: '', label: 'All' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Sent to Finance', label: 'Sent to Finance' },
]
const DOCS = [
  { field: 'pan_card_copy', label: 'PAN card copy' },
  { field: 'bank_consent_form', label: 'Cancelled cheque / bank consent form' },
  { field: 'supporting_document', label: 'Other document' },
]
const FIELDS = ['amount', 'pan_number', 'account_holder_name', 'bank_account_number', 'bank_name', 'bank_branch', 'ifsc_code', 'remarks', ...DOCS.map((d) => d.field)]
const columns = [
  { key: 'panellist_name', label: 'External expert' },
  { key: 'job_title', label: 'Position' },
  { key: 'amount', label: 'Amount', align: 'right' },
  { key: 'details', label: 'Details', sortable: false },
  { key: 'status', label: 'Status' },
  { key: 'thanked', label: 'Thanked on' },
]
const filters = [
  { key: 'job_title', label: 'Positions' },
  { key: 'details_label', label: 'Details' },
]

const data = ref({ rows: [], can_write: false, finance_email_enabled: true })
const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const status = ref('')

const money = (n) => Number(n || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const fmtDate = (d) => (d ? dayjs(d).format('DD MMM YYYY') : '')
const rows = computed(() =>
  (data.value.rows || []).map((r) => ({
    ...r,
    details_label: r.missing.length ? 'Details missing' : 'Complete',
    thanked: r.thanks_sent_on ? dayjs(r.thanks_sent_on).format('DD MMM YYYY') : 'Not yet',
  })),
)
const tiles = computed(() => {
  const all = data.value.rows || []
  const pending = all.filter((r) => r.status === 'Pending')
  const sent = all.filter((r) => r.status === 'Sent to Finance')
  return [
    { label: 'External experts', value: all.length, tone: 'text-gray-900' },
    { label: 'Details to enter', value: pending.filter((r) => r.missing.length).length, tone: 'text-orange-700' },
    { label: 'Ready to send', value: pending.filter((r) => !r.missing.length).length, tone: 'text-brand-700' },
    { label: 'Sent to Finance', value: `${sent.length} · ${money(sent.reduce((n, r) => n + Number(r.amount || 0), 0))}`, tone: 'text-green-700' },
  ]
})

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
watch(status, load)
onMounted(async () => {
  // External experts added to a committee since the last visit get their record.
  try {
    await honorariumService.syncExternalPanellists()
  } catch {
    // Listing still works without it.
  }
  await load()
})

// ----- enter / edit details
const edit = reactive({ open: false, row: null, f: {}, busy: '', error: '' })
function openEdit(row) {
  Object.assign(edit, { open: true, row, f: Object.fromEntries(FIELDS.map((k) => [k, row[k] ?? ''])), busy: '', error: '' })
}
async function saveEdit(thenPreview) {
  edit.busy = thenPreview ? 'preview' : 'save'
  edit.error = ''
  try {
    await honorariumService.update(edit.row.name, edit.f)
    await load()
    const fresh = data.value.rows.find((r) => r.name === edit.row.name)
    if (thenPreview && fresh?.missing.length) {
      edit.error = `Saved. Enter ${fresh.missing.join(', ')} to preview the email.`
      return
    }
    edit.open = false
    if (thenPreview) openPreview([fresh || edit.row])
    else toast({ title: 'Saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    edit.error = e?.messages?.[0] || 'Could not save.'
  } finally {
    edit.busy = ''
  }
}

// ----- preview, then send (one email per expert; the first is previewed)
const preview = reactive({ open: false, rows: [], data: null, loading: false, error: '', sending: false, clear: null, to: '', cc: '', bcc: '', remember: false })
const splitEmails = (v) => (v || '').split(/[,;\s]+/).filter(Boolean)
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const addressError = computed(() => {
  if (!splitEmails(preview.to).length) return "Enter the Finance team's email address in To."
  const bad = [preview.to, preview.cc, preview.bcc].flatMap(splitEmails).filter((e) => !EMAIL.test(e))
  return bad.length ? `Not a valid email address: ${bad.join(', ')}` : ''
})
async function openPreview(picked, clear = null) {
  const incomplete = picked.filter((r) => r.missing.length)
  const ready = picked.filter((r) => !r.missing.length)
  if (incomplete.length) {
    toast({
      title: `Details missing for ${incomplete.map((r) => r.panellist_name).join(', ')}: ${ready.length ? 'they are left out' : 'enter them first'}.`,
      icon: 'alert-triangle',
      iconClasses: 'text-orange-500',
    })
  }
  if (!ready.length) return
  Object.assign(preview, { open: true, rows: ready, data: null, loading: true, error: '', sending: false, clear, to: '', cc: '', bcc: '', remember: false })
  try {
    preview.data = await honorariumService.previewFinanceEmail(ready[0].name)
    // Start from Email Setup's addresses; whatever is here when Send is clicked is used.
    preview.to = preview.data.recipients.map((r) => r.email).join(', ')
    preview.cc = (preview.data.cc || []).join(', ')
    preview.bcc = (preview.data.bcc || []).join(', ')
    preview.remember = !preview.to
  } catch (e) {
    preview.error = e?.messages?.[0] || 'Could not build the email preview.'
  } finally {
    preview.loading = false
  }
}
async function send() {
  preview.sending = true
  try {
    const r = await honorariumService.sendToFinance(preview.rows.map((x) => x.name), {
      to: preview.to,
      cc: preview.cc,
      bcc: preview.bcc,
      remember: preview.remember ? 1 : 0,
    })
    toast({ title: `Sent to Finance: ${r.sent} email${r.sent === 1 ? '' : 's'}.`, icon: 'check', iconClasses: 'text-green-500' })
    if (r.skipped?.length) toast({ title: `Skipped: ${r.skipped.join('; ')}`, icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    preview.open = false
    preview.clear?.()
    await load()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not send.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    preview.sending = false
  }
}

async function exportList() {
  exporting.value = true
  try {
    await honorariumService.exportList('', status.value)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the list.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    exporting.value = false
  }
}
</script>
