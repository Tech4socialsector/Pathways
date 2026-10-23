<template>
  <StaffLayout>
    <PageHeader :title="doc?.subject || 'Selection Green Sheet'" :breadcrumbs="breadcrumbs" :back-to="backTo">
      <template #meta>
        <div v-if="doc" class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm text-gray-600">
          <span class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-xs font-medium text-gray-700">{{ doc.name }}</span>
          <StatusBadge :status="doc.status" />
          <router-link :to="`/jobs/${job.name}`" class="flex items-center gap-1.5 hover:underline">
            <FeatherIcon name="briefcase" class="h-3.5 w-3.5 text-brand-700" />{{ job.job_title }}
          </router-link>
          <span v-if="job.track" class="flex items-center gap-1.5"><FeatherIcon name="git-branch" class="h-3.5 w-3.5 text-brand-700" />{{ job.track }} track</span>
          <span v-if="job.employment_type" class="flex items-center gap-1.5"><FeatherIcon name="user-check" class="h-3.5 w-3.5 text-brand-700" />{{ job.employment_type }}</span>
        </div>
      </template>
      <template v-if="doc" #actions>
        <Dropdown :options="printMenu">
          <Button variant="outline" icon-left="printer" icon-right="chevron-down">Print</Button>
        </Dropdown>
        <template v-if="editable">
          <Button :loading="busy === 'save'" :disabled="!!busy" @click="save(false)">Save Draft</Button>
          <Button
            v-if="perms.can_submit"
            variant="solid"
            :class="BTN_BRAND"
            :loading="busy === 'submit'"
            :disabled="!!busy || !data.has_chain_template"
            @click="save(true)"
          >
            Submit for Approval
          </Button>
        </template>
        <template v-if="perms.can_act">
          <Button variant="outline" @click="openAction('Returned for Revision')">Return</Button>
          <Button variant="solid" :class="BTN_DARK" @click="openAction('Approved')">Approve</Button>
        </template>
        <Button
          v-if="doc.status === 'Returned for Revision' && doc.docstatus === 1 && perms.can_cancel && perms.can_create"
          variant="solid"
          :class="BTN_BRAND"
          :loading="busy === 'revise'"
          @click="revise"
        >
          Revise &amp; Resubmit
        </Button>
        <Dropdown v-if="moreActions.length" :options="moreActions" placement="right">
          <Button variant="outline" icon="more-horizontal" aria-label="More actions" />
        </Dropdown>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50">
      <div v-if="loading && !data" class="p-6 text-sm text-gray-500">Loading...</div>
      <div v-else-if="loadError" class="m-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ loadError }}</div>
      <div v-else-if="data" class="grid grid-cols-1 gap-6 p-6 lg:grid-cols-3">
        <div class="flex min-w-0 flex-col gap-6 lg:col-span-2">
          <div v-if="data.newer_sheet" class="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800">
            This sheet was revised.
            <router-link :to="`/selection-green-sheets/${data.newer_sheet}`" class="font-medium underline">Open the revision ({{ data.newer_sheet }})</router-link>
          </div>
          <div v-if="returned && doc.status === 'Returned for Revision'" class="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            Returned by {{ returned.approver_role || returned.approver }}<span v-if="returned.remarks">: “{{ returned.remarks }}”</span>.
            <span v-if="perms.can_create && perms.can_cancel">Use Revise &amp; Resubmit to open an editable copy.</span>
          </div>
          <div
            v-if="!data.has_chain_template && doc.docstatus === 0"
            class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-800"
          >
            No active Approval Chain for the Post-Interview Green Sheet matches the '{{ job.track }}' track
            ({{ job.employment_type || 'any type' }}), so this sheet cannot be submitted yet. Configure one in Master Setup &gt; Approval Chains.
          </div>
          <ErrorMessage v-if="formError" :message="formError" />

          <SectionCard title="Selection Note" icon="file-text" subtitle="The narrative the approvers read (workflow step 24)">
            <template v-if="editable" #actions>
              <Button size="sm" variant="ghost" icon-left="refresh-cw" :loading="busy === 'refresh'" @click="confirmRefresh = true">Re-draft from outcomes</Button>
            </template>
            <div class="flex flex-col gap-4">
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormControl label="Subject" v-model="form.subject" :disabled="!editable" placeholder="Appointment of ... (1 Vacancy)" />
                <FormControl label="File Reference" v-model="form.file_reference" :disabled="!editable" placeholder="NLSIU-22022/13/2022-ADMN" />
              </div>
              <FormControl type="textarea" label="Selection Note" :rows="12" v-model="form.selection_note" :disabled="!editable" />
            </div>
          </SectionCard>

          <SectionCard title="Recruitment Process" icon="activity">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <FormControl type="date" label="Advertisement Published On" v-model="form.advertisement_published_on" :disabled="!editable" />
              <FormControl type="date" label="Advertisement Closed On" v-model="form.advertisement_closed_on" :disabled="!editable" />
              <FormControl type="date" label="Final Interview Date" v-model="form.interview_date" :disabled="!editable" />
              <FormControl type="number" label="Applications Received" v-model="form.applications_received" :disabled="!editable" />
              <FormControl type="number" label="Candidates Shortlisted" v-model="form.candidates_shortlisted" :disabled="!editable" />
              <FormControl type="number" label="Candidates Interviewed" v-model="form.candidates_interviewed" :disabled="!editable" />
            </div>
          </SectionCard>

          <SectionCard title="Recommendation" icon="award">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl type="select" label="Recommended Candidate" v-model="form.recommended_application" :options="candidateOptions" :disabled="!editable" />
              <FormControl type="select" label="Waitlisted Candidate" v-model="form.waitlist_application" :options="[{ label: '— None —', value: '' }, ...candidateOptions]" :disabled="!editable" />
              <FormControl
                type="select"
                label="Reference Checks"
                v-model="form.reference_check_status"
                :options="['', 'Satisfactory', 'Initiated', 'Pending']"
                :disabled="!editable"
              />
              <label class="flex items-center gap-2 self-end pb-1.5 text-sm text-gray-700">
                <input v-model="form.verbal_acceptance" type="checkbox" class="rounded border-gray-300 text-brand-700" :disabled="!editable" />
                Recommended candidate has verbally accepted
              </label>
            </div>
          </SectionCard>

          <SectionCard title="Appointment Details" icon="calendar">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Date of Appointment" v-model="form.date_of_appointment" :disabled="!editable" placeholder="Tentatively in May" />
              <FormControl label="Reports To" v-model="form.reports_to" :disabled="!editable" />
              <FormControl type="textarea" :rows="2" label="Duration / Contract Period" v-model="form.duration_of_appointment" :disabled="!editable" />
              <FormControl v-if="data.is_permanent" label="Probation Period" v-model="form.probation_period" :disabled="!editable" placeholder="One year" />
              <FormControl v-else type="textarea" :rows="2" label="Deliverables / Scope of Work" v-model="form.deliverables" :disabled="!editable" />
            </div>
          </SectionCard>

          <SectionCard v-if="data.is_permanent" title="Pay Fixation" icon="trending-up" subtitle="As per the non-teaching pay scales">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Pay Level(s) in Notification" v-model="form.advertised_pay_level" :disabled="!editable" placeholder="5/6/7/8" />
              <FormControl label="Pay Level Fixed" v-model="form.fixed_pay_level" :disabled="!editable" placeholder="Entry level 7 plus seven increments" />
              <FormControl type="number" label="Current Basic Salary / Month (Rs.)" v-model="form.current_basic_salary" :disabled="!editable" />
              <FormControl type="number" label="Current Gross Salary / Month (Rs.)" v-model="form.current_gross_salary" :disabled="!editable" />
              <FormControl type="number" label="Basic Pay Fixed / Month (Rs.)" v-model="form.basic_pay" :disabled="!editable" />
              <FormControl type="number" label="CTC / Month (Rs.)" v-model="form.ctc" :disabled="!editable" />
              <FormControl type="number" label="Gross Salary / Month (Rs.)" v-model="form.gross_salary" :disabled="!editable" />
            </div>
            <FormControl class="mt-4" type="textarea" :rows="3" label="Pay Fixation Rationale" v-model="form.pay_fixation_note" :disabled="!editable" />
          </SectionCard>

          <SectionCard v-if="data.show_funding" title="Funding" icon="dollar-sign">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormControl label="Project / Initiative" v-model="form.project_name" :disabled="!editable" />
              <FormControl label="Fund Availability" v-model="form.funding_source" :disabled="!editable" placeholder="NVF Grant" />
            </div>
          </SectionCard>

          <SectionCard
            title="Selected Candidates and Fees"
            icon="users"
            :subtitle="data.is_permanent ? 'Optional for permanent posts' : 'Printed as the fee table'"
          >
            <template v-if="editable" #actions>
              <Button size="sm" icon-left="plus" @click="addRow">Add row</Button>
            </template>
            <div v-if="!form.compensation_table.length" class="text-sm text-gray-500">No rows.</div>
            <div v-else class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead class="text-left text-xs text-gray-500">
                  <tr>
                    <th class="px-1 py-1 font-medium">Candidate</th>
                    <th class="px-1 py-1 font-medium">Experience</th>
                    <th class="px-1 py-1 font-medium">Highest Qualification</th>
                    <th class="px-1 py-1 font-medium">Salary / Fee per Month</th>
                    <th class="px-1 py-1 font-medium">Position Offered</th>
                    <th class="px-1 py-1 text-center font-medium">Insurance</th>
                    <th class="px-1 py-1 text-center font-medium">Leave</th>
                    <th v-if="editable" />
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in form.compensation_table" :key="idx" class="align-top">
                    <td class="min-w-[10rem] px-1 py-1">
                      <FormControl v-model="row.candidate_name" :disabled="!editable" />
                    </td>
                    <td class="min-w-[7rem] px-1 py-1"><FormControl v-model="row.years_experience" :disabled="!editable" /></td>
                    <td class="min-w-[7rem] px-1 py-1"><FormControl v-model="row.highest_qualification" :disabled="!editable" /></td>
                    <td class="min-w-[8rem] px-1 py-1"><FormControl type="number" v-model="row.recommended_salary" :disabled="!editable" /></td>
                    <td class="min-w-[8rem] px-1 py-1"><FormControl v-model="row.position_offered" :disabled="!editable" /></td>
                    <td class="px-1 py-2 text-center">
                      <input v-model="row.medical_insurance" type="checkbox" class="rounded border-gray-300 text-brand-700" :disabled="!editable" aria-label="Medical insurance" />
                    </td>
                    <td class="px-1 py-2 text-center">
                      <input v-model="row.leave_applicable" type="checkbox" class="rounded border-gray-300 text-brand-700" :disabled="!editable" aria-label="Leave applicable" />
                    </td>
                    <td v-if="editable" class="px-1 py-1">
                      <Button size="sm" variant="ghost" icon="trash-2" aria-label="Remove row" @click="form.compensation_table.splice(idx, 1)" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <FormControl class="mt-4" type="textarea" :rows="3" label="Additional Remarks" v-model="form.compensation_narrative" :disabled="!editable" />
          </SectionCard>
        </div>

        <div class="flex flex-col gap-6 self-start">
          <SectionCard title="Annexures" icon="paperclip" subtitle="Attached to the file of the post">
            <ul class="flex flex-col gap-2 text-sm">
              <li v-for="a in data.annexures" :key="a.field" class="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2">
                <div class="min-w-0">
                  <div class="text-gray-800">{{ a.label }}</div>
                  <a v-if="form[a.field]" :href="form[a.field]" target="_blank" rel="noopener" class="block max-w-[14rem] truncate text-xs text-brand-700 hover:underline">
                    {{ form[a.field].split('/').pop() }}
                  </a>
                  <span v-else class="text-xs text-gray-400">Not attached</span>
                </div>
                <div v-if="editable" class="flex items-center gap-1">
                  <FileUploader
                    file-types=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                    :upload-args="{ doctype: DOCTYPE, docname: doc.name, private: true }"
                    @success="(f) => (form[a.field] = f.file_url)"
                  >
                    <template #default="{ openFileSelector, uploading }">
                      <Button size="sm" :loading="uploading" @click="openFileSelector">{{ form[a.field] ? 'Replace' : 'Attach' }}</Button>
                    </template>
                  </FileUploader>
                  <Button v-if="form[a.field]" size="sm" variant="ghost" icon="x" aria-label="Remove" @click="form[a.field] = ''" />
                </div>
              </li>
            </ul>
            <p v-if="editable" class="mt-2 text-xs text-gray-500">
              Attachments are saved with the draft. For step 20, print the Panel Recommendation (Print menu), have the VC sign it and attach the scan here.
            </p>
          </SectionCard>

          <SectionCard v-if="doc.docstatus >= 1" title="Signed Green Sheet" icon="edit-3" subtitle="Workflow step 25">
            <div class="flex flex-wrap items-center gap-2 text-sm">
              <a v-if="doc.signed_copy_attachment" :href="doc.signed_copy_attachment" target="_blank" rel="noopener" class="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-brand-50">
                <FeatherIcon name="paperclip" class="h-3.5 w-3.5" />{{ doc.signed_copy_attachment.split('/').pop() }}
              </a>
              <span v-else class="text-gray-500">Not uploaded yet.</span>
              <template v-if="perms.can_upload_signed && doc.docstatus === 1">
                <FileUploader
                  file-types=".pdf,.jpg,.jpeg,.png"
                  :upload-args="{ doctype: DOCTYPE, docname: doc.name, private: true }"
                  @success="(f) => run('signed', () => postGreenSheetService.attachSignedCopy(doc.name, f.file_url), 'Signed copy uploaded.')"
                >
                  <template #default="{ openFileSelector, uploading }">
                    <Button size="sm" variant="outline" icon-left="upload" :loading="uploading || busy === 'signed'" @click="openFileSelector">
                      {{ doc.signed_copy_attachment ? 'Replace signed copy' : 'Upload signed copy' }}
                    </Button>
                  </template>
                </FileUploader>
                <Button v-if="doc.signed_copy_attachment" size="sm" variant="ghost" @click="run('signed', () => postGreenSheetService.attachSignedCopy(doc.name, null), 'Signed copy removed.')">Remove</Button>
              </template>
            </div>
          </SectionCard>

          <SectionCard title="Approval" icon="check-square">
            <div class="flex flex-col gap-4 text-sm">
              <div v-if="doc.status === 'Approved'" class="rounded border border-green-200 bg-green-50 px-3 py-2 text-green-800">
                Approved. Offers can now be made to the recommended (or waitlisted) candidate.
              </div>
              <div v-if="doc.status === 'Under Approval' && !perms.can_act && perms.act_blocked_reason" class="text-gray-500">
                {{ perms.act_blocked_reason }}
              </div>
              <RecruitmentTimeline v-if="timeline.length" :steps="timeline" />
              <p v-else class="text-gray-500">
                {{ doc.docstatus === 0 ? `The chain (${doc.approval_chain_template || 'none matched'}) is fixed when the sheet is submitted.` : 'No approval steps.' }}
              </p>
              <ApprovalLog :rows="logRows" class="border-t pt-3" />
            </div>
          </SectionCard>
        </div>
      </div>
    </div>

    <!-- Approve / return -->
    <Dialog v-model="showAction" :options="{ title: pendingAction === 'Approved' ? 'Approve Selection Green Sheet' : 'Return for Revision' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="actionError" />
          <FormControl
            type="textarea"
            :label="pendingAction === 'Approved' ? 'Remarks (optional)' : 'Reason for returning (required)'"
            v-model="actionRemarks"
            placeholder="Add any remarks or conditions"
          />
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :loading="busy === 'action'" @click="confirmAction">Confirm</Button>
      </template>
    </Dialog>

    <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />
    <Dialog
      v-model="confirmRefresh"
      :options="{
        title: 'Re-draft from outcomes',
        message: 'Replace the note, the process figures, the recommendation and the candidate rows with what is currently recorded for this job? Fees already entered for candidates who are still selected are kept.',
        size: 'md',
      }"
    >
      <template #actions>
        <Button variant="solid" :loading="busy === 'refresh'" @click="refresh">Re-draft</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dialog, Dropdown, ErrorMessage, FeatherIcon, FileUploader, FormControl } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ApprovalLog from '@/components/common/ApprovalLog.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import { chainTimeline, formatDateTime, lastReturn } from '@/components/selection/approvalTimeline'
import { POST_GREEN_SHEET_DOCTYPE as DOCTYPE, postGreenSheetService, printUrl } from '@/services/postGreenSheets'
import { approvalService } from '@/services/approvals'
import { BTN_BRAND, BTN_DARK } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { useSessionStore } from '@/stores/session'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

// Step 3 of Selection for the recruitment team; approvers who reach it from
// My Approvals (CFO, Registrar, VC) do not have Selection.
const session = useSessionStore()
const inSelection = computed(() => session.hasMenu('selection'))
const breadcrumbs = computed(() => {
  const j = job.value
  if (!j?.name) return []
  return inSelection.value
    ? [
        { label: 'Selection', to: '/selection' },
        { label: j.job_title || j.name, to: `/selection/${j.name}?tab=green_sheet` },
        { label: 'Selection green sheet' },
      ]
    : [{ label: 'My Approvals', to: '/approvals' }, { label: 'Selection green sheet' }]
})
const backTo = computed(() => (inSelection.value && job.value?.name ? `/selection/${job.value.name}?tab=green_sheet` : '/approvals'))

const FIELDS = [
  'subject', 'file_reference', 'selection_note', 'advertisement_published_on', 'advertisement_closed_on',
  'applications_received', 'candidates_shortlisted', 'interview_date', 'candidates_interviewed',
  'recommended_application', 'waitlist_application', 'verbal_acceptance', 'reference_check_status',
  'date_of_appointment', 'duration_of_appointment', 'reports_to', 'probation_period', 'deliverables',
  'advertised_pay_level', 'fixed_pay_level', 'basic_pay', 'current_basic_salary', 'current_gross_salary',
  'ctc', 'gross_salary', 'pay_fixation_note', 'project_name', 'funding_source', 'compensation_narrative',
  'panel_recommendation_attachment', 'score_sheet_attachment', 'reference_check_attachment',
  'salary_proof_attachment', 'other_annexure_attachment',
]
const ROW_FIELDS = ['application', 'candidate_name', 'years_experience', 'highest_qualification', 'recommended_salary', 'position_offered', 'medical_insurance', 'leave_applicable']

const data = ref(null)
const loading = ref(false)
const loadError = ref('')
const formError = ref('')
const busy = ref('')
const form = reactive({ compensation_table: [] })

const doc = computed(() => data.value?.doc || null)
const job = computed(() => data.value?.job || {})
const perms = computed(() => data.value?.permissions || {})
const editable = computed(() => doc.value?.docstatus === 0 && !!perms.value.can_create)
const timeline = computed(() => chainTimeline(data.value?.chain))
const returned = computed(() => lastReturn(data.value?.chain))
const logRows = computed(() => [...(data.value?.chain?.log || [])].reverse())
const candidateOptions = computed(() => (data.value?.candidates || []).map((c) => ({ label: c.label, value: c.value })))

const printMenu = computed(() => [
  { label: 'Green Sheet', icon: 'file-text', onClick: () => window.open(printUrl(props.id), '_blank') },
  { label: 'Panel Recommendation (for VC)', icon: 'award', onClick: () => window.open(printUrl(props.id, 'Panel Recommendation'), '_blank') },
])

const moreActions = computed(() => {
  const d = doc.value
  if (!d) return []
  return [
    editable.value && { label: 'Delete Draft', icon: 'trash-2', onClick: () => ask('Delete Draft', 'Delete this draft Selection Green Sheet?', 'Delete', () => run('delete', () => postGreenSheetService.deleteDraft(d.name), 'Draft deleted.', () => router.push(`/jobs/${d.job_opening}`))) },
    d.docstatus === 1 && ['Under Approval', 'Returned for Revision'].includes(d.status) && perms.value.can_cancel && {
      label: 'Withdraw',
      icon: 'x-circle',
      onClick: () => ask('Withdraw', 'Cancel this approval request? The sheet cannot be resubmitted; raise a new one from the job page.', 'Withdraw', () => run('withdraw', () => postGreenSheetService.withdrawSheet(d.name), 'Selection Green Sheet withdrawn.')),
    },
  ].filter(Boolean)
})

function fillForm(d) {
  for (const f of FIELDS) form[f] = d[f] ?? ''
  form.verbal_acceptance = !!d.verbal_acceptance
  form.compensation_table = (d.compensation_table || []).map((r) => {
    const row = {}
    for (const f of ROW_FIELDS) row[f] = r[f] ?? ''
    row.medical_insurance = !!r.medical_insurance
    row.leave_applicable = !!r.leave_applicable
    return row
  })
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    data.value = await postGreenSheetService.getSheet(props.id)
    fillForm(data.value.doc)
  } catch (e) {
    loadError.value = e?.messages?.[0] || 'Could not load the Selection Green Sheet.'
  } finally {
    loading.value = false
  }
}
watch(() => props.id, load, { immediate: true })

function addRow() {
  form.compensation_table.push({
    application: '', candidate_name: '', years_experience: '', highest_qualification: '', recommended_salary: '',
    position_offered: job.value.job_title || '', medical_insurance: !data.value?.is_permanent, leave_applicable: !data.value?.is_permanent,
  })
}

function payload() {
  const out = {}
  for (const f of FIELDS) out[f] = form[f] === '' ? null : form[f]
  out.verbal_acceptance = form.verbal_acceptance ? 1 : 0
  out.compensation_table = form.compensation_table
    .filter((r) => (r.candidate_name || '').trim())
    .map((r) => ({ ...r, recommended_salary: r.recommended_salary === '' ? null : r.recommended_salary, medical_insurance: r.medical_insurance ? 1 : 0, leave_applicable: r.leave_applicable ? 1 : 0 }))
  return out
}

async function save(submit) {
  formError.value = ''
  if (!form.recommended_application) {
    formError.value = 'Choose the recommended candidate.'
    return
  }
  busy.value = submit ? 'submit' : 'save'
  try {
    await postGreenSheetService.saveSheet(props.id, payload(), { submit })
    toast({ title: submit ? 'Submitted for approval.' : 'Draft saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not save the sheet.'
  } finally {
    busy.value = ''
  }
  // A failed submit may still have saved the draft.
  await load()
}

async function run(key, fn, successTitle, after) {
  if (busy.value) return false
  busy.value = key
  try {
    await fn()
    toast({ title: successTitle, icon: 'check', iconClasses: 'text-green-500' })
    if (after) {
      after()
      return true
    }
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Something went wrong.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
  await load()
  return true
}

const confirmRefresh = ref(false)
async function refresh() {
  await run('refresh', () => postGreenSheetService.refreshFromOutcomes(props.id), 'Re-drafted from the recorded outcomes.')
  confirmRefresh.value = false
}

async function revise() {
  if (busy.value) return
  busy.value = 'revise'
  try {
    const name = await postGreenSheetService.reviseSheet(props.id)
    toast({ title: 'Revision draft created.', icon: 'check', iconClasses: 'text-green-500' })
    router.push(`/selection-green-sheets/${name}`)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not revise the sheet.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

// Confirmations
const confirmBox = reactive({ open: false, title: '', message: '', label: '', theme: 'red', run: null })
function ask(title, message, label, run) {
  Object.assign(confirmBox, { open: true, title, message, label, theme: 'red', run })
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
  if (busy.value) return
  actionError.value = ''
  if (pendingAction.value === 'Returned for Revision' && !actionRemarks.value.trim()) {
    actionError.value = 'Please explain what needs to be revised.'
    return
  }
  busy.value = 'action'
  try {
    await approvalService.recordApprovalAction(DOCTYPE, props.id, pendingAction.value, actionRemarks.value.trim())
    showAction.value = false
    toast({ title: pendingAction.value === 'Approved' ? 'Approved.' : 'Returned for revision.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    actionError.value = e?.messages?.[0] || 'Could not record the action.'
  } finally {
    busy.value = ''
  }
  await load()
}
</script>
