<template>
  <!-- Workflow steps 4-5: the official notification and its corrigenda. -->
  <SectionCard title="Notification & Corrigenda" icon="file-text" subtitle="Official advertisement, extensions and changes">
    <template #actions>
      <Button v-if="data?.can_issue_corrigendum" size="sm" variant="solid" icon-left="calendar" :class="BTN_BRAND" @click="openCorrigendum">
        Extend / Corrigendum
      </Button>
    </template>

    <div v-if="loading && !data" class="text-sm text-gray-500">Loading...</div>
    <div v-else-if="data" class="flex flex-col gap-5 text-sm">
      <!-- Notification -->
      <div v-if="!editing">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wide text-brand-700">Notification</span>
          <Button v-if="data.can_edit" size="sm" variant="ghost" icon-left="edit-2" @click="startEdit">Edit</Button>
        </div>
        <div v-if="!n" class="rounded-lg border border-dashed px-3 py-3 text-gray-500">
          No notification details yet. Add the notification number, date and the official link or PDF.
        </div>
        <dl v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <dt class="text-xs text-gray-500">Notification No.</dt>
            <dd class="font-medium text-gray-900">{{ n.notification_number || '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-500">Dated</dt>
            <dd class="font-medium text-gray-900">{{ n.publish_date ? formatDate(n.publish_date) : '—' }}</dd>
          </div>
          <div v-if="n.notification_url" class="sm:col-span-2">
            <dt class="text-xs text-gray-500">Official link</dt>
            <dd><a :href="n.notification_url" target="_blank" rel="noopener" class="break-all text-brand-700 hover:underline">{{ n.notification_url }}</a></dd>
          </div>
          <div v-if="n.notification_attachment">
            <a :href="n.notification_attachment" target="_blank" rel="noopener" class="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium hover:border-brand-200 hover:text-brand-700">
              <FeatherIcon name="paperclip" class="h-3.5 w-3.5" /> Notification PDF
            </a>
          </div>
        </dl>
      </div>
      <div v-else class="flex flex-col gap-3">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <FormControl label="Notification No." v-model="form.notification_number" placeholder="e.g. Notification No. 14/2026" />
          <FormControl label="Dated" type="date" v-model="form.publish_date" />
        </div>
        <FormControl label="Official link" v-model="form.notification_url" placeholder="https://www.nls.ac.in/news-events/..." />
        <div class="flex flex-wrap items-center gap-2">
          <a v-if="form.notification_attachment" :href="form.notification_attachment" target="_blank" class="text-xs text-brand-700 hover:underline">
            {{ form.notification_attachment.split('/').pop() }}
          </a>
          <FileUploader file-types=".pdf" :upload-args="{ doctype: 'Job Opening', docname: job.name, private: false }" @success="(f) => (form.notification_attachment = f.file_url)">
            <template #default="{ openFileSelector, uploading }">
              <Button size="sm" icon-left="paperclip" :loading="uploading" @click="openFileSelector">
                {{ form.notification_attachment ? 'Replace PDF' : 'Attach notification PDF' }}
              </Button>
            </template>
          </FileUploader>
          <Button v-if="form.notification_attachment" size="sm" variant="ghost" @click="form.notification_attachment = ''">Remove</Button>
        </div>
        <ErrorMessage :message="error" />
        <div class="flex gap-2">
          <Button variant="solid" :class="BTN_BRAND" :loading="saving" @click="saveNotice">Save</Button>
          <Button variant="ghost" @click="editing = false">Cancel</Button>
        </div>
      </div>

      <!-- Corrigenda -->
      <div>
        <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Corrigenda · {{ data.corrigenda.length }}</div>
        <div v-if="!data.corrigenda.length" class="text-gray-500">None issued.</div>
        <ol v-else class="flex flex-col gap-2">
          <li v-for="c in data.corrigenda" :key="c.name" class="rounded-lg border border-gray-200 px-3 py-2.5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="font-semibold text-gray-900">
                <template v-if="c.changed_field === 'Closing Date'">
                  Deadline extended to {{ formatDateTime(c.new_value) }}
                </template>
                <template v-else>Change: {{ c.new_value }}</template>
              </span>
              <a
                v-if="c.corrigendum_attachment"
                :href="c.corrigendum_attachment"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline"
              >
                <FeatherIcon name="paperclip" class="h-3.5 w-3.5" /> PDF
              </a>
            </div>
            <div v-if="c.changed_field === 'Closing Date' && c.previous_value" class="text-xs text-gray-500">
              Was {{ formatDateTime(c.previous_value) }}
            </div>
            <div v-if="c.remarks && c.changed_field === 'Closing Date'" class="mt-1 text-gray-700">{{ c.remarks }}</div>
            <div class="mt-1 text-xs text-gray-500">{{ formatDate(c.corrigendum_date) }} · signed by {{ c.signed_by_name || c.signed_by }}</div>
          </li>
        </ol>
      </div>
    </div>

    <Dialog v-model="corr.open" :options="{ title: 'Issue Corrigendum', size: 'lg' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <div class="flex gap-2">
            <button
              v-for="opt in CHANGE_TYPES"
              :key="opt.value"
              type="button"
              class="flex-1 rounded-lg border px-3 py-2 text-left text-sm"
              :class="corr.changed_field === opt.value ? 'border-brand-700 bg-brand-50 text-brand-800' : 'border-gray-200 hover:border-gray-300'"
              @click="corr.changed_field = opt.value"
            >
              <div class="font-semibold">{{ opt.label }}</div>
              <div class="text-xs text-gray-500">{{ opt.hint }}</div>
            </button>
          </div>
          <template v-if="corr.changed_field === 'Closing Date'">
            <div class="rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-700">
              Current deadline: <span class="font-semibold">{{ job.application_deadline ? formatDateTime(job.application_deadline) : 'not set' }}</span>
              <span v-if="job.status === 'Closed'" class="block text-xs text-orange-700">This ad has closed; extending re-opens it for applications.</span>
            </div>
            <FormControl label="New closing date and time" type="datetime-local" v-model="corr.new_value" :min="minDate" />
          </template>
          <FormControl
            :label="corr.changed_field === 'Closing Date' ? 'Remarks (optional)' : 'What changes'"
            type="textarea"
            v-model="corr.remarks"
            :placeholder="corr.changed_field === 'Closing Date' ? 'e.g. Extended to receive more applications.' : 'e.g. Essential qualification revised to ...'"
          />
          <div class="flex flex-wrap items-center gap-2">
            <FileUploader file-types=".pdf" :upload-args="{ doctype: 'Job Opening', docname: job.name, private: false }" @success="(f) => (corr.attachment = f.file_url)">
              <template #default="{ openFileSelector, uploading }">
                <Button size="sm" icon-left="paperclip" :loading="uploading" @click="openFileSelector">
                  {{ corr.attachment ? 'Replace corrigendum PDF' : 'Attach corrigendum PDF' }}
                </Button>
              </template>
            </FileUploader>
            <span v-if="corr.attachment" class="text-xs text-gray-600">{{ corr.attachment.split('/').pop() }}</span>
          </div>
          <p class="text-xs text-gray-500">Published on the job posting. You sign it as {{ session.fullName }}.</p>
          <ErrorMessage :message="corr.error" />
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :class="BTN_BRAND" :loading="corr.saving" :disabled="!canIssue" @click="issue">Issue corrigendum</Button>
      </template>
    </Dialog>
  </SectionCard>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FeatherIcon, FileUploader, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { jobNoticeService } from '@/services/jobNotice'
import { useSessionStore } from '@/stores/session'

const props = defineProps({ job: { type: Object, required: true } })
const emit = defineEmits(['changed'])
const session = useSessionStore()

const data = ref(null)
const loading = ref(false)
const n = computed(() => data.value?.notification)

async function load() {
  loading.value = true
  try {
    data.value = await jobNoticeService.getNotice(props.job.name)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.job.name, load)

// ----- notification
const editing = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive({ notification_number: '', publish_date: '', notification_url: '', notification_attachment: '' })

function startEdit() {
  Object.assign(form, {
    notification_number: n.value?.notification_number || '',
    publish_date: n.value?.publish_date || '',
    notification_url: n.value?.notification_url || '',
    notification_attachment: n.value?.notification_attachment || '',
  })
  error.value = ''
  editing.value = true
}

async function saveNotice() {
  saving.value = true
  error.value = ''
  try {
    data.value = await jobNoticeService.saveNotice(props.job.name, { ...form })
    editing.value = false
    toast({ title: 'Notification saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not save the notification.'
  } finally {
    saving.value = false
  }
}

// ----- corrigendum
const CHANGE_TYPES = [
  { value: 'Closing Date', label: 'Extend deadline', hint: 'Moves the closing date' },
  { value: 'Other', label: 'Other change', hint: 'Recorded and published' },
]
const corr = reactive({ open: false, changed_field: 'Closing Date', new_value: '', remarks: '', attachment: '', saving: false, error: '' })
const minDate = dayjs().add(1, 'hour').format('YYYY-MM-DDTHH:mm')
const canIssue = computed(() =>
  corr.changed_field === 'Closing Date' ? !!corr.new_value && dayjs(corr.new_value).isAfter(dayjs()) : !!corr.remarks.trim(),
)

function openCorrigendum() {
  const suggested = dayjs(props.job.application_deadline || undefined).add(7, 'day').hour(17).minute(0)
  Object.assign(corr, {
    open: true,
    changed_field: 'Closing Date',
    new_value: suggested.isAfter(dayjs()) ? suggested.format('YYYY-MM-DDTHH:mm') : '',
    remarks: '',
    attachment: '',
    error: '',
  })
}

async function issue() {
  corr.saving = true
  corr.error = ''
  try {
    data.value = await jobNoticeService.issueCorrigendum(props.job.name, {
      changed_field: corr.changed_field,
      new_value: corr.changed_field === 'Closing Date' ? dayjs(corr.new_value).format('YYYY-MM-DD HH:mm:ss') : null,
      remarks: corr.remarks,
      corrigendum_attachment: corr.attachment || null,
    })
    corr.open = false
    toast({
      title: corr.changed_field === 'Closing Date' ? `Deadline extended to ${formatDateTime(corr.new_value)}.` : 'Corrigendum issued.',
      icon: 'check',
      iconClasses: 'text-green-500',
    })
    emit('changed')
  } catch (e) {
    corr.error = e?.messages?.[0] || 'Could not issue the corrigendum.'
  } finally {
    corr.saving = false
  }
}

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}
function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A') : ''
}
</script>
