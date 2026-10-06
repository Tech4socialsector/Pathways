<template>
  <div class="rounded-lg border bg-white p-4">
    <div class="mb-3 flex items-center justify-between gap-2">
      <div class="text-sm font-semibold text-gray-900">Pre-Recruitment Green Sheet</div>
      <StatusBadge v-if="current" :status="current.status" />
    </div>

    <div v-if="loading && !data" class="text-sm text-gray-500">Loading...</div>
    <div v-else-if="loadError" class="text-sm text-red-600">{{ loadError }}</div>
    <div v-else-if="data" class="flex flex-col gap-4">
      <div
        v-if="!job.track"
        class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-800"
      >
        Set a Recruitment Track on this job (Edit) before raising a Green Sheet.
      </div>
      <div
        v-else-if="!data.has_chain_template && (!current || current.docstatus === 0)"
        class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-800"
      >
        No active Approval Chain matches the '{{ job.track }}' track ({{ job.employment_type }}), so a Green
        Sheet cannot be submitted yet.
        <a
          v-if="perms.can_override_status"
          href="/desk/approval-chain-template/new"
          target="_blank"
          class="font-medium underline"
        >
          Create one
        </a>
        <span v-else>Ask an administrator to configure one.</span>
      </div>

      <!-- No sheet yet -->
      <template v-if="!current">
        <p class="text-sm text-gray-600">
          A Pre-Recruitment Green Sheet must be approved before this job can be advertised.
          <span v-if="perms.can_override_status">
            Your role may also change the job status directly.
          </span>
        </p>
        <div v-if="perms.can_create && job.track">
          <Button variant="solid" @click="openForm()">Create Green Sheet</Button>
        </div>
      </template>

      <!-- Current sheet -->
      <template v-else>
        <div class="flex flex-col gap-3 text-sm">
          <div class="flex flex-wrap gap-x-6 gap-y-1 text-gray-500">
            <span>{{ current.name }}</span>
            <span v-if="current.duration_of_ad_days">
              Advertisement duration: <span class="text-gray-900">{{ current.duration_of_ad_days }} days</span>
            </span>
          </div>
          <div>
            <div class="mb-1 text-gray-500">Justification</div>
            <div class="prose prose-sm max-w-none text-gray-900" v-html="toHtml(current.justification_note)" />
          </div>
        </div>

        <div v-if="current.status === 'Returned for Revision' && lastReturn" class="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          Returned by {{ lastReturn.approver_role || lastReturn.approver }}
          <span v-if="lastReturn.remarks">: “{{ lastReturn.remarks }}”</span>
        </div>
        <div v-if="current.status === 'Approved'" class="rounded border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          Approved. This job can now be advertised.
        </div>

        <div
          v-if="current.status === 'Under Approval' && !perms.can_act && data.act_blocked_reason"
          class="text-sm text-gray-500"
        >
          {{ data.act_blocked_reason }}
        </div>

        <div v-if="timelineSteps.length">
          <div class="mb-2 text-sm text-gray-500">Approval chain</div>
          <RecruitmentTimeline :steps="timelineSteps" />
        </div>

        <div class="flex flex-wrap gap-2">
          <template v-if="current.docstatus === 0">
            <Button v-if="perms.can_create" @click="openForm(current)">Edit</Button>
            <Button
              v-if="perms.can_submit"
              variant="solid"
              :disabled="!data.has_chain_template"
              :loading="busy === 'submit'"
              @click="run('submit', () => greenSheetService.submitGreenSheet(current.name), 'Submitted for approval.')"
            >
              Submit for Approval
            </Button>
            <Button
              v-if="perms.can_create"
              theme="red"
              variant="outline"
              @click="confirmDiscard = true"
            >
              Delete Draft
            </Button>
          </template>
          <template v-else>
            <Button v-if="perms.can_act" variant="solid" @click="openAction('Approved')">Approve</Button>
            <Button v-if="perms.can_act" variant="outline" @click="openAction('Returned for Revision')">
              Return for Revision
            </Button>
            <Button
              v-if="current.status === 'Returned for Revision' && perms.can_cancel && perms.can_create"
              variant="solid"
              :loading="busy === 'revise'"
              @click="revise"
            >
              Revise &amp; Resubmit
            </Button>
            <Button
              v-if="['Under Approval', 'Returned for Revision'].includes(current.status) && perms.can_cancel"
              theme="red"
              variant="outline"
              @click="confirmWithdraw = true"
            >
              Withdraw
            </Button>
          </template>
        </div>
      </template>

      <div v-if="logRows.length">
        <div class="mb-2 text-sm text-gray-500">Approval log</div>
        <ul class="flex flex-col gap-2 text-sm">
          <li v-for="(row, idx) in logRows" :key="idx" class="rounded border px-3 py-2">
            <div class="flex flex-wrap items-center gap-2">
              <StatusBadge :status="row.action" />
              <span class="text-gray-900">{{ row.approver_role || row.approver }}</span>
              <span class="text-xs text-gray-500">
                {{ row.approver_name || row.approver }} &middot; {{ row.channel }} &middot; {{ formatDate(row.acted_on) }}
              </span>
              <span v-if="row.is_override" class="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">
                recorded on behalf
              </span>
            </div>
            <div v-if="row.remarks" class="mt-1 text-gray-600">{{ row.remarks }}</div>
          </li>
        </ul>
      </div>

      <div v-if="history.length">
        <div class="mb-2 text-sm text-gray-500">Earlier Green Sheets</div>
        <ul class="flex flex-col gap-1 text-sm">
          <li v-for="sheet in history" :key="sheet.name" class="flex items-center justify-between gap-2">
            <span class="text-gray-700">{{ sheet.name }}</span>
            <StatusBadge :status="sheet.status" />
          </li>
        </ul>
      </div>
    </div>

    <!-- Create / edit draft -->
    <Dialog v-model="showForm" :options="{ title: form.name ? 'Edit Green Sheet' : 'Create Green Sheet', size: 'lg' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="formError" />
          <FormControl
            label="Justification Note"
            type="textarea"
            :rows="6"
            v-model="form.justification_note"
            placeholder="Why this position needs to be filled"
            required
          />
          <FormControl
            label="Advertisement Duration (days)"
            type="number"
            v-model="form.duration_of_ad_days"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button :loading="saving === 'draft'" :disabled="!!saving" @click="saveForm(false)">Save Draft</Button>
          <Button
            v-if="perms.can_submit"
            variant="solid"
            :loading="saving === 'submit'"
            :disabled="!!saving || !data?.has_chain_template"
            @click="saveForm(true)"
          >
            Save &amp; Submit for Approval
          </Button>
        </div>
      </template>
    </Dialog>

    <!-- Approve / return -->
    <Dialog
      v-model="showAction"
      :options="{ title: pendingAction === 'Approved' ? 'Approve Green Sheet' : 'Return for Revision' }"
    >
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="actionError" />
          <FormControl
            type="textarea"
            :label="pendingAction === 'Approved' ? 'Remarks (optional)' : 'Remarks'"
            v-model="actionRemarks"
            placeholder="Add any remarks or conditions"
          />
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :loading="busy === 'action'" @click="confirmAction">Confirm</Button>
      </template>
    </Dialog>

    <Dialog
      v-model="confirmWithdraw"
      :options="{
        title: 'Withdraw Green Sheet',
        message: 'This cancels the approval request and moves the job back to Draft. Continue?',
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" theme="red" :loading="busy === 'withdraw'" @click="withdraw">Withdraw</Button>
      </template>
    </Dialog>

    <Dialog
      v-model="confirmDiscard"
      :options="{ title: 'Delete Draft', message: 'Delete this draft Green Sheet?', size: 'sm' }"
    >
      <template #actions>
        <Button variant="solid" theme="red" :loading="busy === 'discard'" @click="discard">Delete</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { toast } from '@/utils/notify'
import dayjs from 'dayjs'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
import { greenSheetService } from '@/services/greenSheets'
import { approvalService } from '@/services/approvals'

const DOCTYPE = 'Pre-Recruitment Green Sheet'

const props = defineProps({
  job: { type: Object, required: true },
})
const emit = defineEmits(['changed', 'loaded'])

const data = ref(null)
const loading = ref(false)
const loadError = ref('')

const current = computed(() => data.value?.current || null)
const perms = computed(() => data.value?.permissions || {})
const history = computed(() =>
  (data.value?.sheets || []).filter((s) => !current.value || s.name !== current.value.name),
)
const logRows = computed(() => [...(data.value?.chain?.log || [])].reverse())
const lastReturn = computed(() => logRows.value.find((r) => r.action === 'Returned for Revision'))

const timelineSteps = computed(() => {
  const chain = data.value?.chain
  if (!chain || !current.value) return []
  const log = chain.log || []
  return chain.steps.map((step) => {
    const entry = [...log].reverse().find((r) => r.sequence === step.sequence)
    let state = 'pending'
    if (step.completed) state = 'completed'
    else if (chain.status === 'Under Approval' && step.sequence === chain.current_level) state = 'current'
    else if (
      chain.status === 'Returned for Revision' &&
      entry?.action === 'Returned for Revision' &&
      entry === lastReturn.value
    )
      state = 'rejected'
    let detail = step.approver_role
    const who = entry?.approver_name || entry?.approver
    if (state === 'completed' && entry) detail = `Approved by ${who} · ${formatDate(entry.acted_on)}`
    else if (state === 'rejected' && entry) detail = `Returned by ${who} · ${formatDate(entry.acted_on)}`
    else if (state === 'current') detail = `Awaiting ${step.approver_role}`
    return { key: step.sequence, label: step.approver_label || step.approver_role, detail, state }
  })
})

function errorText(e, fallback) {
  return e?.messages?.[0] || e?.message || fallback
}

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A') : ''
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
}

// Notes saved from this panel are plain text; ones written in the Desk
// Text Editor are HTML.
function isHtml(text) {
  return /<\/?[a-z][\s\S]*>/i.test(text)
}

function toHtml(text) {
  if (!text) return '<span class="text-gray-500">—</span>'
  return isHtml(text) ? text : escapeHtml(text).replace(/\n/g, '<br>')
}

function toPlainText(text) {
  if (!text || !isHtml(text)) return text || ''
  const doc = new DOMParser().parseFromString(text.replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '</p>\n'), 'text/html')
  return (doc.body.textContent || '').trim()
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    data.value = await greenSheetService.getJobGreenSheets(props.job.name)
    emit('loaded', data.value)
  } catch (e) {
    loadError.value = errorText(e, 'Could not load the Green Sheet.')
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.job.name, load)
defineExpose({ reload: load })

function notifySuccess(title) {
  toast({ title, icon: 'check', iconClasses: 'text-green-500' })
}

function notifyError(e, fallback) {
  toast({ title: errorText(e, fallback), icon: 'alert-triangle', iconClasses: 'text-red-500' })
}

async function afterChange() {
  await load()
  emit('changed')
}

// Create / edit form
const showForm = ref(false)
const saving = ref('')
const formError = ref('')
const form = reactive({ name: null, justification_note: '', duration_of_ad_days: '' })

function openForm(sheet = null) {
  Object.assign(form, {
    name: sheet?.name || null,
    justification_note: toPlainText(sheet?.justification_note),
    duration_of_ad_days: sheet?.duration_of_ad_days || '',
  })
  formError.value = ''
  showForm.value = true
}

async function saveForm(submit) {
  formError.value = ''
  if (!form.justification_note?.trim()) {
    formError.value = 'Justification Note is required.'
    return
  }
  const days = form.duration_of_ad_days === '' || form.duration_of_ad_days == null ? null : Number(form.duration_of_ad_days)
  if (days !== null && (!Number.isInteger(days) || days < 0)) {
    formError.value = 'Advertisement Duration must be a whole number of days.'
    return
  }
  saving.value = submit ? 'submit' : 'draft'
  try {
    await greenSheetService.saveGreenSheet(
      props.job.name,
      { justification_note: form.justification_note.trim(), duration_of_ad_days: days },
      { name: form.name, submit },
    )
    showForm.value = false
    notifySuccess(submit ? 'Green Sheet submitted for approval.' : 'Green Sheet saved as draft.')
  } catch (e) {
    formError.value = errorText(e, 'Could not save the Green Sheet.')
  } finally {
    saving.value = ''
  }
  // A failed submit may still have saved the draft, so always refresh.
  await afterChange()
}

// Simple one-click actions
const busy = ref('')

async function run(key, fn, successTitle) {
  if (busy.value) return false
  busy.value = key
  try {
    await fn()
    notifySuccess(successTitle)
    return true
  } catch (e) {
    notifyError(e, 'Something went wrong.')
    return false
  } finally {
    busy.value = ''
    await afterChange()
  }
}

const confirmWithdraw = ref(false)
async function withdraw() {
  const ok = await run('withdraw', () => greenSheetService.withdrawGreenSheet(current.value.name), 'Green Sheet withdrawn.')
  if (ok) confirmWithdraw.value = false
}

const confirmDiscard = ref(false)
async function discard() {
  const ok = await run('discard', () => greenSheetService.deleteGreenSheetDraft(current.value.name), 'Draft deleted.')
  if (ok) confirmDiscard.value = false
}

async function revise() {
  const ok = await run('revise', () => greenSheetService.reviseGreenSheet(current.value.name), 'Revision draft created.')
  if (ok && current.value?.docstatus === 0) openForm(current.value)
}

// Approve / return
const showAction = ref(false)
const pendingAction = ref('')
const actionRemarks = ref('')
const actionError = ref('')

function openAction(action) {
  pendingAction.value = action
  actionRemarks.value = ''
  actionError.value = ''
  showAction.value = true
}

async function confirmAction() {
  if (busy.value || !current.value) return
  actionError.value = ''
  if (pendingAction.value === 'Returned for Revision' && !actionRemarks.value.trim()) {
    actionError.value = 'Please add remarks explaining what needs to be revised.'
    return
  }
  busy.value = 'action'
  try {
    await approvalService.recordApprovalAction(DOCTYPE, current.value.name, pendingAction.value, actionRemarks.value.trim())
    showAction.value = false
    notifySuccess(pendingAction.value === 'Approved' ? 'Approved.' : 'Returned for revision.')
  } catch (e) {
    actionError.value = errorText(e, 'Could not record the action.')
  } finally {
    busy.value = ''
  }
  await afterChange()
}
</script>
