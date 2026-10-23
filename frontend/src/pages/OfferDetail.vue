<template>
  <StaffLayout>
    <PageHeader :title="offer?.candidate_name || 'Offer'" back-to="/offers">
      <template #meta>
        <div v-if="offer" class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm text-gray-600">
          <span class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-xs font-medium text-gray-700">{{ offer.name }}</span>
          <StatusBadge :status="offer.stage" />
          <span class="flex items-center gap-1.5"><FeatherIcon name="briefcase" class="h-3.5 w-3.5 text-brand-700" />{{ offer.job_title }}</span>
          <RouterLink :to="`/applications/${offer.application}`" class="flex items-center gap-1.5 hover:text-brand-700">
            <FeatherIcon name="file-text" class="h-3.5 w-3.5 text-brand-700" />{{ offer.application_id || offer.application }}
          </RouterLink>
        </div>
      </template>
      <template #actions>
        <template v-if="offer">
          <Button variant="outline" icon-left="eye" @click="previewOpen = true">Preview Letter</Button>
          <Button v-if="perms.can_edit" :loading="busy === 'save'" icon-left="save" @click="save">Save Draft</Button>
          <Button v-if="perms.can_submit" variant="solid" icon-left="send" :class="BTN_BRAND" :loading="busy === 'submit'" @click="submitForReview">
            Submit for Review
          </Button>
          <Button v-if="perms.can_return" variant="outline" icon-left="corner-up-left" @click="openRemarks('return')">Return for Changes</Button>
          <Button v-if="perms.can_review" variant="solid" icon-left="check" :class="BTN_SUCCESS" @click="openRemarks('approve')">
            Approve for Signature
          </Button>
          <Button v-if="perms.can_sign" variant="solid" icon-left="edit-3" :class="BTN_BRAND" @click="openSign">Sign</Button>
          <Button v-if="perms.can_send" variant="solid" icon-left="mail" :class="BTN_BRAND" @click="openSend">Send to Candidate</Button>
        </template>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50">
      <div v-if="loading && !offer" class="p-6 text-sm text-gray-500">Loading...</div>
      <div v-else-if="loadError" class="p-6"><ErrorMessage :message="loadError" /></div>
      <div v-else-if="offer" class="grid gap-6 p-4 sm:p-6 xl:grid-cols-3">
        <!-- Draft form -->
        <div class="flex flex-col gap-6 xl:col-span-2">
          <div v-if="offer.review_remarks && offer.stage === 'Draft'" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <b>Returned for changes:</b> {{ offer.review_remarks }}
          </div>
          <div v-else-if="!perms.can_edit" class="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-600">
            {{ offer.stage === 'Draft' ? 'You can view this draft but not edit it.' : 'Only a draft can be edited. Return it for changes to edit it again.' }}
          </div>

          <SectionCard v-for="section in SECTIONS" :key="section.title" :title="section.title" :subtitle="section.subtitle" :icon="section.icon">
            <div class="grid gap-4 sm:grid-cols-2">
              <div v-for="f in section.fields" :key="f.key" :class="f.wide && 'sm:col-span-2'">
                <label class="mb-1 block text-xs font-medium text-gray-600">{{ f.label }}</label>
                <TextEditor
                  v-if="f.type === 'editor'"
                  :content="form[f.key] || ''"
                  :editable="!!perms.can_edit"
                  :fixed-menu="!!perms.can_edit"
                  editor-class="prose-sm max-w-none min-h-[8rem] px-3 py-2"
                  class="rounded border border-gray-300 bg-white"
                  @change="(html) => (form[f.key] = html)"
                />
                <FormControl
                  v-else-if="f.type === 'select'"
                  type="select"
                  :options="selectOptions(f)"
                  :model-value="form[f.key] || NONE"
                  :disabled="!perms.can_edit"
                  @update:model-value="(v) => (form[f.key] = v === NONE ? null : v)"
                />
                <FormControl
                  v-else
                  :type="f.type || 'text'"
                  :model-value="form[f.key] ?? ''"
                  :disabled="!perms.can_edit"
                  @update:model-value="(v) => (form[f.key] = v === '' ? null : v)"
                />
                <p v-if="f.hint" class="mt-1 text-xs text-gray-500">{{ f.hint }}</p>
              </div>
            </div>
          </SectionCard>
        </div>

        <!-- Side: progress, letter, signed copies, history -->
        <div class="flex flex-col gap-6">
          <SectionCard title="Progress" icon="git-commit">
            <RecruitmentTimeline :steps="progressSteps" />
          </SectionCard>

          <SectionCard title="Letter & Signature" icon="file-text">
            <dl class="flex flex-col gap-3 text-sm">
              <div>
                <dt class="text-xs text-gray-500">Template</dt>
                <dd class="font-medium text-gray-900">{{ offer.appointment_order_template || '—' }}</dd>
              </div>
              <div v-if="offer.reviewed_by">
                <dt class="text-xs text-gray-500">Reviewed</dt>
                <dd>{{ offer.reviewed_by }} · {{ fmtDateTime(offer.reviewed_on) }}</dd>
              </div>
              <div v-if="offer.signed_by">
                <dt class="text-xs text-gray-500">Signed ({{ offer.signature_source }})</dt>
                <dd>{{ offer.signed_by_name || offer.signed_by }} · {{ fmtDateTime(offer.signed_on) }}</dd>
                <img v-if="offer.registrar_signature" :src="offer.registrar_signature" alt="Signature" class="mt-2 max-h-16 rounded border bg-white p-1" />
              </div>
              <div v-if="offer.sent_on">
                <dt class="text-xs text-gray-500">Sent</dt>
                <dd>{{ fmtDateTime(offer.sent_on) }} · respond by {{ fmtDate(offer.acceptance_deadline) }}</dd>
              </div>
              <div v-if="offer.candidate_confirmed_doj">
                <dt class="text-xs text-gray-500">Candidate's joining date</dt>
                <dd class="font-medium text-gray-900">{{ fmtDate(offer.candidate_confirmed_doj) }}</dd>
              </div>
              <div v-if="offer.decline_reason">
                <dt class="text-xs text-gray-500">Decline reason</dt>
                <dd>{{ offer.decline_reason }}</dd>
              </div>
            </dl>
            <Button class="mt-4" size="sm" icon-left="download" :loading="busy === 'download'" @click="download">Download PDF</Button>
          </SectionCard>

          <SectionCard title="Signed Copies" icon="paperclip">
            <div class="flex flex-col gap-4 text-sm">
              <div>
                <div class="text-xs text-gray-500">Scanned Registrar-signed order (step 29)</div>
                <a v-if="offer.registrar_signed_scan" :href="offer.registrar_signed_scan" target="_blank" class="text-brand-700 hover:underline">
                  {{ fileName(offer.registrar_signed_scan) }}
                </a>
                <div v-else class="text-gray-500">Not uploaded</div>
                <FileUploader
                  v-if="perms.can_upload_scan"
                  file-types=".pdf,.jpg,.jpeg,.png"
                  :upload-args="{ private: true }"
                  @success="(f) => run('scan', () => offerService.uploadRegistrarScan(offer.name, f.file_url), 'Scanned copy saved.')"
                >
                  <template #default="{ openFileSelector, uploading }">
                    <Button class="mt-2" size="sm" icon-left="upload" :loading="uploading || busy === 'scan'" @click="openFileSelector">
                      {{ offer.registrar_signed_scan ? 'Replace scan' : 'Upload scan' }}
                    </Button>
                  </template>
                </FileUploader>
                <p v-else-if="!offer.registrar_signed_scan" class="mt-1 text-xs text-gray-500">Available once the order has been sent.</p>
              </div>
              <div>
                <div class="text-xs text-gray-500">Candidate's signed acceptance copy</div>
                <a v-if="offer.signed_copy_attachment" :href="offer.signed_copy_attachment" target="_blank" class="text-brand-700 hover:underline">
                  {{ fileName(offer.signed_copy_attachment) }}
                </a>
                <div v-else class="text-gray-500">Not received</div>
                <FileUploader
                  v-if="perms.can_upload_signed_copy"
                  file-types=".pdf,.jpg,.jpeg,.png"
                  :upload-args="{ private: true }"
                  @success="(f) => run('copy', () => offerService.uploadSignedCopy(offer.name, f.file_url), 'Signed copy saved.')"
                >
                  <template #default="{ openFileSelector, uploading }">
                    <Button class="mt-2" size="sm" variant="ghost" icon-left="upload" :loading="uploading || busy === 'copy'" @click="openFileSelector">
                      Upload on the candidate's behalf
                    </Button>
                  </template>
                </FileUploader>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="History" icon="clock">
            <ol v-if="offer.timeline?.length" class="flex flex-col gap-3 text-sm">
              <li v-for="(t, i) in offer.timeline" :key="i" class="border-l-2 border-brand-100 pl-3">
                <div class="font-medium text-gray-900">{{ t.action || t.to_status }}</div>
                <div class="text-xs text-gray-500">
                  {{ t.user_name || t.user }} · {{ fmtDateTime(t.timestamp) }}
                  <span v-if="t.from_status"> · {{ t.from_status }} → {{ t.to_status }}</span>
                </div>
                <div v-if="t.remarks" class="mt-0.5 text-xs italic text-gray-600">“{{ t.remarks }}”</div>
              </li>
            </ol>
            <div v-else class="text-sm text-gray-500">No history yet.</div>
          </SectionCard>

          <Button v-if="perms.can_delete" variant="ghost" theme="red" icon-left="trash-2" @click="removeDraft">Delete draft</Button>
        </div>
      </div>
    </div>

    <LetterPreviewDialog v-if="offer" v-model="previewOpen" :offer="offer.name" />

    <!-- Approve / return -->
    <Dialog v-model="remarksOpen" :options="{ title: remarksMode === 'approve' ? 'Approve for Signature' : 'Return for Changes' }">
      <template #body-content>
        <p class="mb-3 text-sm text-gray-600">
          {{ remarksMode === 'approve' ? 'The order goes to the signatory (Registrar) for signature.' : 'The order goes back to Draft. Say what needs to change.' }}
        </p>
        <FormControl type="textarea" :label="remarksMode === 'approve' ? 'Remarks (optional)' : 'What needs to change'" v-model="remarks" />
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button @click="remarksOpen = false">Cancel</Button>
          <Button
            variant="solid"
            :class="remarksMode === 'approve' ? BTN_SUCCESS : BTN_DANGER"
            :loading="busy === remarksMode"
            :disabled="remarksMode === 'return' && !remarks.trim()"
            @click="confirmRemarks"
          >
            {{ remarksMode === 'approve' ? 'Approve' : 'Return' }}
          </Button>
        </div>
      </template>
    </Dialog>

    <!-- Sign -->
    <Dialog v-model="signOpen" :options="{ title: 'Sign Appointment Order', size: 'lg' }">
      <template #body-content>
        <div class="flex flex-col gap-4 text-sm">
          <p class="text-gray-600">Preview the letter before signing. Your signature, name and the time are added to the letter.</p>
          <div v-if="offer?.has_saved_signature" class="flex flex-wrap gap-4">
            <label class="flex items-center gap-2"><input v-model="sign.mode" type="radio" value="saved" /> Use the saved signature</label>
            <label class="flex items-center gap-2"><input v-model="sign.mode" type="radio" value="draw" /> Draw a signature</label>
          </div>
          <template v-if="sign.mode === 'draw'">
            <SignaturePad v-model="sign.image" label="Registrar's signature" />
            <label class="flex items-center gap-2 text-gray-700">
              <input v-model="sign.saveAsDefault" type="checkbox" class="rounded border-gray-300" />
              Save this as the signature for future orders
            </label>
          </template>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button @click="previewOpen = true">Preview</Button>
          <Button @click="signOpen = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="busy === 'sign'" :disabled="sign.mode === 'draw' && !sign.image" @click="doSign">
            Sign
          </Button>
        </div>
      </template>
    </Dialog>

    <!-- Send -->
    <Dialog v-model="sendOpen" :options="{ title: 'Send to Candidate' }">
      <template #body-content>
        <div class="flex flex-col gap-3 text-sm">
          <p class="text-gray-600">
            Emails the signed appointment order (PDF attached) to {{ offer?.candidate_email }}. The candidate can also view it, accept or decline in
            the Careers portal.
          </p>
          <FormControl type="date" label="Acceptance deadline (blank = default from Settings)" v-model="sendDeadline" />
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button @click="sendOpen = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="busy === 'send'" @click="doSend">Send</Button>
        </div>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Button, Dialog, ErrorMessage, FeatherIcon, FileUploader, FormControl, TextEditor } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
import SignaturePad from '@/components/common/SignaturePad.vue'
import LetterPreviewDialog from '@/components/offers/LetterPreviewDialog.vue'
import { OFFER_STAGES } from '@/components/offers/offerStages'
import { offerService } from '@/services/offers'
import { BTN_BRAND, BTN_DANGER, BTN_SUCCESS } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

const offer = ref(null)
const loading = ref(false)
const loadError = ref('')
const busy = ref('')
const options = reactive({ templates: [], designations: [], departments: [] })
const form = reactive({})
const previewOpen = ref(false)
const remarksOpen = ref(false)
const remarksMode = ref('approve')
const remarks = ref('')
const signOpen = ref(false)
const sign = reactive({ mode: 'draw', image: '', saveAsDefault: false })
const sendOpen = ref(false)
const sendDeadline = ref('')

const perms = computed(() => offer.value?.perms || {})

// frappe-ui's select drops '' options, so "none" needs a sentinel.
const NONE = '__none__'
const EMPLOYMENT_TYPES = ['Permanent', 'Consultant', 'Grant-funded', 'Contract']
const SECTIONS = [
  {
    title: 'Appointment Details',
    subtitle: 'What the letter offers (workflow step 26).',
    icon: 'briefcase',
    fields: [
      { key: 'appointment_order_template', label: 'Appointment Order Template', type: 'select', source: 'templates' },
      { key: 'reference_number', label: 'Letter Reference No.', hint: 'Defaults to the offer ID.' },
      { key: 'designation', label: 'Designation', type: 'select', source: 'designations' },
      { key: 'department', label: 'Department', type: 'select', source: 'departments' },
      { key: 'employment_type', label: 'Employment Type', type: 'select', list: EMPLOYMENT_TYPES },
      { key: 'proposed_doj', label: 'Proposed Date of Joining', type: 'date' },
      { key: 'place_of_posting', label: 'Place of Posting' },
      { key: 'reporting_to', label: 'Reporting To' },
      { key: 'probation_period', label: 'Probation Period', hint: 'e.g. one year' },
      { key: 'contract_period', label: 'Contract Period', hint: 'Contract, consultant and project posts.' },
      { key: 'contract_end_date', label: 'Contract End Date', type: 'date' },
    ],
  },
  {
    title: 'Compensation',
    subtitle: 'Finalised against the advertisement and pay scales (workflow step 22).',
    icon: 'credit-card',
    fields: [
      { key: 'pay_level', label: 'Pay Level', hint: 'e.g. Level 10, VII CPC' },
      { key: 'pay_scale', label: 'Pay Scale' },
      { key: 'gross_monthly_salary', label: 'Gross Monthly Salary (INR)', type: 'number' },
      { key: 'consolidated_fee', label: 'Consolidated Fee per Month (INR)', type: 'number' },
      { key: 'allowances', label: 'Allowances', type: 'textarea', wide: true },
      { key: 'compensation_remarks', label: 'Compensation Remarks', type: 'textarea', wide: true, hint: 'How the pay was finalised. Internal; not printed.' },
    ],
  },
  {
    title: 'Verbal Offer',
    subtitle: 'The call informing the candidate (workflow step 23). Internal; not printed.',
    icon: 'phone',
    fields: [
      { key: 'verbal_offer_date', label: 'Date', type: 'date' },
      { key: 'verbal_offer_compensation', label: 'Compensation Discussed' },
      { key: 'verbal_offer_notes', label: 'Notes (salary, joining date)', type: 'textarea', wide: true },
    ],
  },
  {
    title: 'Terms',
    subtitle: 'Extra terms printed in the letter, if any.',
    icon: 'list',
    fields: [{ key: 'terms', label: 'Terms and Conditions', type: 'editor', wide: true }],
  },
]
const FIELD_KEYS = SECTIONS.flatMap((s) => s.fields.map((f) => f.key))

function selectOptions(f) {
  const values = [...(f.list || (f.source === 'templates' ? options.templates.map((t) => t.name) : options[f.source] || []))]
  // A value that is no longer active still shows.
  if (form[f.key] && !values.includes(form[f.key])) values.unshift(form[f.key])
  return [{ label: '—', value: NONE }, ...values.map((v) => ({ label: v, value: v }))]
}

const fmtDate = (d) => (d ? dayjs(d).format('DD MMM YYYY') : '')
const fmtDateTime = (d) => (d ? dayjs(d).format('DD MMM YYYY, h:mm A') : '')
const fileName = (url) => decodeURIComponent((url || '').split('/').pop())

const OUTCOMES = ['Accepted', 'Declined', 'Expired']
const progressSteps = computed(() => {
  const stage = offer.value?.stage
  const idx = OFFER_STAGES.indexOf(stage)
  const steps = OFFER_STAGES.slice(0, 5).map((s, i) => ({
    key: s,
    label: s,
    state: i < idx ? 'completed' : i === idx ? 'current' : 'pending',
  }))
  steps.push({
    key: 'outcome',
    label: OUTCOMES.includes(stage) ? stage : 'Candidate response',
    state: stage === 'Accepted' ? 'completed' : OUTCOMES.includes(stage) ? 'rejected' : 'pending',
  })
  return steps
})

function fill(data) {
  offer.value = data
  for (const k of FIELD_KEYS) form[k] = data[k] ?? null
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [data, opts] = await Promise.all([offerService.getOffer(props.id), offerService.getFormOptions()])
    Object.assign(options, opts || {})
    fill(data)
  } catch (e) {
    loadError.value = e?.messages?.[0] || 'Could not load this offer.'
  } finally {
    loading.value = false
  }
}

async function run(key, fn, message) {
  busy.value = key
  try {
    const result = await fn()
    if (result && typeof result === 'object' && result.name) fill(result)
    else await load()
    if (message) toast({ title: message, icon: 'check' })
    return true
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Something went wrong.', icon: 'alert-triangle' })
    return false
  } finally {
    busy.value = ''
  }
}

const formData = () => Object.fromEntries(FIELD_KEYS.map((k) => [k, form[k]]))
const save = () => run('save', () => offerService.updateOffer(offer.value.name, formData()), 'Draft saved.')

function submitForReview() {
  // Save what is on screen first, so the reviewer sees the latest draft.
  return run(
    'submit',
    async () => {
      await offerService.updateOffer(offer.value.name, formData())
      return offerService.submitForReview(offer.value.name)
    },
    'Submitted for review.',
  )
}

function openRemarks(mode) {
  remarksMode.value = mode
  remarks.value = ''
  remarksOpen.value = true
}

async function confirmRemarks() {
  const ok =
    remarksMode.value === 'approve'
      ? await run('approve', () => offerService.approveOffer(offer.value.name, remarks.value), 'Approved for signature.')
      : await run('return', () => offerService.returnOffer(offer.value.name, remarks.value), 'Returned to draft.')
  if (ok) remarksOpen.value = false
}

function openSign() {
  Object.assign(sign, { mode: offer.value?.has_saved_signature ? 'saved' : 'draw', image: '', saveAsDefault: false })
  signOpen.value = true
}

async function doSign() {
  const ok = await run(
    'sign',
    () =>
      offerService.signOffer(offer.value.name, {
        signature: sign.mode === 'draw' ? sign.image : null,
        useSavedSignature: sign.mode === 'saved',
        saveAsDefault: sign.saveAsDefault,
      }),
    'Signed.',
  )
  if (ok) signOpen.value = false
}

function openSend() {
  sendDeadline.value = ''
  sendOpen.value = true
}

async function doSend() {
  if (await run('send', () => offerService.sendOffer(offer.value.name, sendDeadline.value), 'Sent to the candidate.')) sendOpen.value = false
}

async function download() {
  busy.value = 'download'
  try {
    await offerService.downloadLetter(offer.value.name)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the letter.', icon: 'alert-triangle' })
  } finally {
    busy.value = ''
  }
}

async function removeDraft() {
  if (!window.confirm('Delete this draft offer?')) return
  try {
    await offerService.deleteOffer(offer.value.name)
    router.push('/offers')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not delete the draft.', icon: 'alert-triangle' })
  }
}

onMounted(load)
watch(() => props.id, load)
</script>
