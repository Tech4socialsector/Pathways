<template>
  <StaffLayout>
    <PageHeader :title="doc ? doc.candidate_name || doc.name : 'Joining'" :subtitle="doc ? `${doc.designation || doc.job_title || ''} · ${doc.application_id || ''}` : ''" back-to="/joinings" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading && !doc" class="h-64 animate-pulse rounded-xl border bg-white" />
      <div v-else-if="error" class="rounded-xl border bg-white p-8 text-center text-sm text-gray-600">{{ error }}</div>
      <div v-else-if="doc" class="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div class="flex flex-col gap-6 xl:col-span-2">
          <!-- Status and the next step -->
          <div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white px-5 py-4 shadow-sm">
            <div class="flex items-center gap-3">
              <StatusBadge :status="doc.status" />
              <span class="text-sm text-gray-600">{{ STATUS_TEXT[doc.status] }}</span>
            </div>
            <div v-if="doc.can_write" class="flex flex-wrap gap-2">
              <template v-if="doc.status === 'Draft' || doc.status === 'No-show'">
                <Button variant="solid" icon-left="check" :class="BTN_BRAND" :loading="busy === 'Confirmed'" @click="ask('Confirmed')">
                  {{ doc.status === 'No-show' ? 'Confirm new date' : 'Confirm joining' }}
                </Button>
              </template>
              <template v-else-if="doc.status === 'Confirmed'">
                <Button variant="solid" icon-left="user-check" :class="BTN_SUCCESS" :disabled="!canMarkJoined" :title="canMarkJoined ? '' : 'Available from the date of joining'" :loading="busy === 'Joined'" @click="ask('Joined')">
                  Mark joined
                </Button>
                <Button icon-left="user-x" :loading="busy === 'No-show'" @click="ask('No-show')">No-show</Button>
                <Button variant="ghost" :loading="busy === 'Draft'" @click="ask('Draft')">Back to draft</Button>
              </template>
            </div>
          </div>

          <SectionCard title="Joining details" icon="calendar" subtitle="Workflow step 31: finalise with the selected candidate">
            <template v-if="editable" #actions>
              <Button size="sm" variant="solid" :class="BTN_BRAND" :disabled="!dirty" :loading="busy === 'save'" @click="save">Save</Button>
            </template>
            <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormControl v-model="form.confirmed_doj" type="date" label="Date of joining" :disabled="!editable" />
              <FormControl v-model="form.reporting_time" type="time" label="Reporting time" :disabled="!editable" />
              <FormControl v-model="form.reporting_location" label="Reporting location" :disabled="!editable" />
              <FormControl v-model="form.reporting_manager" label="Reporting manager" :disabled="!editable" />
              <div v-if="dateChanged && doc.status !== 'Draft'" class="md:col-span-2">
                <FormControl v-model="form.reschedule_reason" type="textarea" label="Reason for rescheduling" placeholder="e.g. Candidate's notice period was extended" />
                <p v-if="doc.status === 'Confirmed'" class="mt-1 text-xs text-orange-700">IT &amp; Facilities are emailed the new date when you save.</p>
              </div>
              <div class="md:col-span-2">
                <FormControl v-model="form.remarks" type="textarea" label="Remarks" :disabled="!editable" />
              </div>
            </div>
            <div v-if="doc.reschedule_count" class="mt-4 rounded-lg bg-orange-50 px-3 py-2 text-xs text-orange-800">
              Rescheduled {{ doc.reschedule_count }} time(s). Previous date: {{ formatDay(doc.previous_doj) }}<span v-if="doc.reschedule_reason">. Reason: {{ doc.reschedule_reason }}</span>
            </div>
          </SectionCard>

          <SectionCard title="People directory" icon="image" subtitle="Bio write-up (max 200 words, Word) and a non-passport photograph for the website">
            <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div v-for="f in ATTACHMENTS" :key="f.field">
                <div class="mb-1.5 text-sm text-gray-700">{{ f.label }}</div>
                <div class="flex flex-wrap items-center gap-2">
                  <a v-if="form[f.field]" :href="form[f.field]" target="_blank" rel="noopener" class="flex max-w-[16rem] items-center gap-1.5 truncate rounded bg-gray-50 px-2 py-1 text-sm text-brand-700 hover:underline">
                    <FeatherIcon name="paperclip" class="h-3.5 w-3.5 shrink-0" />{{ fileName(form[f.field]) }}
                  </a>
                  <FileUploader v-if="editable" :file-types="f.accept" :upload-args="{ private: true, doctype: 'Joining', docname: doc.name }" @success="(file) => (form[f.field] = file.file_url)">
                    <template #default="{ uploading, progress, openFileSelector }">
                      <Button size="sm" :loading="uploading" icon-left="upload" @click="openFileSelector">{{ uploading ? `${progress}%` : form[f.field] ? 'Replace' : 'Upload' }}</Button>
                    </template>
                  </FileUploader>
                  <span v-if="!form[f.field] && !editable" class="text-xs text-gray-400">Not uploaded</span>
                </div>
              </div>
            </div>
            <p v-if="editable && attachmentsDirty" class="mt-3 text-xs text-orange-700">Save to keep the new file.</p>
          </SectionCard>
        </div>

        <div class="flex flex-col gap-6">
          <SectionCard title="New joiner" icon="user">
            <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt class="text-gray-500">Application</dt>
              <dd><router-link :to="`/applications/${doc.application}`" class="text-brand-700 hover:underline">{{ doc.application_id }}</router-link></dd>
              <dt class="text-gray-500">Post</dt>
              <dd>{{ doc.job_title }}</dd>
              <dt class="text-gray-500">Department</dt>
              <dd>{{ doc.department || '-' }}</dd>
              <dt class="text-gray-500">Email</dt>
              <dd class="break-all">{{ doc.candidate_email }}</dd>
              <dt class="text-gray-500">Mobile</dt>
              <dd>{{ doc.candidate_mobile || '-' }}</dd>
              <template v-if="doc.confirmed_by">
                <dt class="text-gray-500">Confirmed by</dt>
                <dd>{{ doc.confirmed_by_name }}</dd>
              </template>
              <template v-if="doc.employee">
                <dt class="text-gray-500">Employee</dt>
                <dd class="font-mono text-xs">{{ doc.employee }}</dd>
              </template>
            </dl>
            <p v-if="doc.status === 'Joined' && !doc.employee" class="mt-3 rounded bg-orange-50 px-3 py-2 text-xs text-orange-800">
              The employee record is created once every mandatory joining document is verified.
            </p>
          </SectionCard>

          <SectionCard title="Joining documents" icon="file-text">
            <template v-if="doc.document_collection">
              <div class="flex items-center justify-between">
                <StatusBadge :status="doc.document_collection.overall_status" />
                <router-link to="/documents?tab=onboarding" class="text-sm text-brand-700 hover:underline">Verify documents</router-link>
              </div>
              <p v-if="doc.document_collection.onboarding_email_sent_on" class="mt-2 text-xs text-gray-500">
                Onboarding email sent {{ formatDateTime(doc.document_collection.onboarding_email_sent_on) }}
              </p>
            </template>
            <p v-else class="text-sm text-gray-500">No checklist yet.</p>
          </SectionCard>

          <SectionCard title="IT & Facilities" icon="monitor">
            <template v-if="doc.it_request">
              <div class="mb-2"><StatusBadge :status="doc.it_request.status" /></div>
              <ul class="flex flex-col gap-1 text-sm">
                <li v-for="t in IT_TASKS" :key="t.field" class="flex items-center gap-2" :class="doc.it_request[t.field] ? 'text-green-700' : 'text-gray-500'">
                  <FeatherIcon :name="doc.it_request[t.field] ? 'check-circle' : 'circle'" class="h-4 w-4" />{{ t.label }}
                </li>
              </ul>
              <p v-if="doc.it_request.official_email" class="mt-2 text-sm">Official email: <b>{{ doc.it_request.official_email }}</b></p>
            </template>
            <p v-else class="text-sm text-gray-500">IT &amp; Facilities are told when the joining is confirmed.</p>
          </SectionCard>
        </div>
      </div>
    </div>

    <ConfirmActionDialog
      v-model:open="confirm.open"
      :title="confirm.title"
      :message="confirm.message"
      :label="confirm.label"
      :run="applyStatus"
    />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { Button, FeatherIcon, FileUploader, FormControl } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import { joiningService } from '@/services/joining'
import { BTN_BRAND, BTN_SUCCESS } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({ id: { type: String, required: true } })

const FIELDS = ['confirmed_doj', 'reporting_location', 'reporting_time', 'reporting_manager', 'reschedule_reason', 'remarks', 'bio_writeup_attachment', 'directory_photo_attachment']
const ATTACHMENTS = [
  { field: 'bio_writeup_attachment', label: 'Bio write-up', accept: '.doc,.docx,.pdf' },
  { field: 'directory_photo_attachment', label: 'Directory photo', accept: '.jpg,.jpeg,.png' },
]
const IT_TASKS = [
  { field: 'laptop_arranged', label: 'Laptop arranged' },
  { field: 'official_email_created', label: 'NLS email ID created' },
  { field: 'access_card_issued', label: 'Access card issued' },
  { field: 'seating_arranged', label: 'Seating arranged' },
]
const STATUS_TEXT = {
  Draft: 'Date given by the candidate. Finalise it with them, then confirm.',
  Confirmed: 'Date finalised. IT & Facilities have been told.',
  Joined: 'Joined.',
  'No-show': 'Did not report on the date. Agree a new date and confirm again.',
}

const doc = ref(null)
const loading = ref(false)
const error = ref('')
const busy = ref('')
const form = reactive({})

const editable = computed(() => doc.value?.can_write && doc.value.status !== 'Joined')
const dateChanged = computed(() => doc.value && (form.confirmed_doj || '') !== (doc.value.confirmed_doj || ''))
const dirty = computed(() => doc.value && FIELDS.some((f) => (form[f] || '') !== (doc.value[f] || '')))
const attachmentsDirty = computed(() => doc.value && ATTACHMENTS.some((a) => (form[a.field] || '') !== (doc.value[a.field] || '')))
const canMarkJoined = computed(() => doc.value?.confirmed_doj && !dayjs(doc.value.confirmed_doj).isAfter(dayjs(), 'day'))

function setDoc(value) {
  doc.value = value
  for (const f of FIELDS) form[f] = value[f] || ''
  if (form.reporting_time) form.reporting_time = form.reporting_time.slice(0, 5)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    setDoc(await joiningService.getJoining(props.id))
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load this joining.'
  } finally {
    loading.value = false
  }
}

function values() {
  return Object.fromEntries(FIELDS.map((f) => [f, form[f] || null]))
}

async function save() {
  if (dateChanged.value && doc.value.status !== 'Draft' && !form.reschedule_reason?.trim()) {
    toast({ title: 'Please give the reason for rescheduling.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    return
  }
  busy.value = 'save'
  try {
    setDoc(await joiningService.saveJoining(props.id, values()))
    toast({ title: 'Saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

const ASK = {
  Confirmed: ['Confirm the joining?', 'The date of joining is finalised and IT & Facilities are emailed to arrange a laptop and an NLS email ID.', 'Confirm'],
  Joined: ['Mark as joined?', 'The application is marked Joined. The employee record is created once all mandatory documents are verified.', 'Mark joined'],
  'No-show': ['Mark as no-show?', 'Use this when the new joiner did not report on the date. You can confirm a new date later.', 'Mark no-show'],
  Draft: ['Move back to draft?', 'The joining is no longer confirmed. IT & Facilities are not told automatically.', 'Back to draft'],
}
const confirm = reactive({ open: false, status: '', title: '', message: '', label: '' })
function ask(status) {
  if (status === 'Confirmed' && !form.confirmed_doj) {
    toast({ title: 'Set the date of joining first.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    return
  }
  const [title, message, label] = ASK[status]
  Object.assign(confirm, { open: true, status, title, message, label })
}
async function applyStatus() {
  const status = confirm.status
  busy.value = status
  try {
    setDoc(await joiningService.setStatus(props.id, status, editable.value ? values() : null))
    toast({ title: `Joining ${status === 'Draft' ? 'moved back to draft' : status.toLowerCase()}.`, icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not update the joining.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = ''
  }
}

const formatDay = (value) => (value ? dayjs(value).format('DD MMM YYYY') : '')
const formatDateTime = (value) => (value ? dayjs(value).format('DD MMM YYYY, h:mm A') : '')
const fileName = (url) => decodeURIComponent((url || '').split('/').pop())

onMounted(load)
watch(() => props.id, load)
</script>
