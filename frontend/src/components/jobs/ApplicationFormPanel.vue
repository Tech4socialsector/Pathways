<template>
  <SectionCard title="Application Form" icon="edit-3" subtitle="What candidates are asked when they apply">
    <template #actions>
      <Button
        v-if="job.status === 'Advertised'"
        variant="outline"
        icon-left="eye"
        class="!border-brand-200 !bg-white !text-brand-700 hover:!bg-brand-50"
        :link="`/pathways/portal/jobs/${job.name}/apply`"
      >
        Preview
      </Button>
      <Button
        v-if="canWrite && !editing"
        variant="solid"
        icon-left="edit-2"
        class="!bg-brand-700 !text-white hover:!bg-brand-800"
        @click="startEdit"
      >
        Edit
      </Button>
    </template>

    <!-- Read view -->
    <div v-if="!editing" class="flex flex-col gap-5 text-sm">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div v-if="job.application_start" class="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2.5 sm:col-span-2">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-700">
            <FeatherIcon name="unlock" class="h-4 w-4" />
          </div>
          <div>
            <div class="text-xs text-gray-600">Applications open from</div>
            <div class="font-semibold text-gray-900">{{ formatDateTime(job.application_start) }}</div>
          </div>
        </div>
        <div class="flex items-center gap-3 rounded-lg bg-brand-50 px-3 py-2.5">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
            <FeatherIcon name="calendar" class="h-4 w-4" />
          </div>
          <div>
            <div class="text-xs text-gray-600">Deadline</div>
            <div class="font-semibold text-gray-900">
              {{ job.application_deadline ? formatDateTime(job.application_deadline) : 'Not set' }}
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2.5">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-700">
            <FeatherIcon name="book-open" class="h-4 w-4" />
          </div>
          <div>
            <div class="text-xs text-gray-600">Postgraduate degree</div>
            <div class="font-semibold text-gray-900">{{ job.require_postgraduate ? 'Mandatory' : 'Optional' }}</div>
          </div>
        </div>
      </div>
      <div v-if="!job.application_deadline" class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-orange-800">
        Set an application deadline before advertising this job.
      </div>

      <div>
        <div class="mb-2 flex items-center gap-2 font-semibold text-gray-900">
          Eligibility questions
          <span class="rounded-full bg-gray-100 px-2 text-xs font-normal text-gray-600">{{ job.screening_questions?.length || 0 }}</span>
        </div>
        <ol v-if="job.screening_questions?.length" class="flex flex-col gap-2">
          <li v-for="(q, idx) in job.screening_questions" :key="q.name" class="flex gap-3 rounded-lg border border-gray-100 px-3 py-2.5">
            <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-700 text-xs font-bold text-white">
              {{ idx + 1 }}
            </span>
            <div class="min-w-0">
              <div class="text-gray-900">{{ q.question }}</div>
              <div class="mt-1.5 flex flex-wrap gap-1.5 text-xs">
                <span class="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600">{{ q.answer_type }}</span>
                <span v-if="q.is_mandatory" class="rounded bg-brand-100 px-1.5 py-0.5 font-medium text-brand-800">Required</span>
                <span v-if="q.ask_details_if_yes" class="rounded px-1.5 py-0.5 font-medium text-brand-700">Details if Yes</span>
                <span v-if="q.show_if_previous_answer" class="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600">
                  Only if previous answer is “{{ q.show_if_previous_answer }}”
                </span>
              </div>
            </div>
          </li>
        </ol>
        <div v-else class="text-gray-500">No eligibility questions.</div>
      </div>

      <div>
        <details class="group mb-5 rounded-lg border border-gray-200">
          <summary class="flex cursor-pointer list-none items-center justify-between px-3 py-2.5 font-semibold text-gray-900">
            <span class="flex items-center gap-2">
              <FeatherIcon name="book-open" class="h-4 w-4 text-brand-700" />Instructions for this post
              <span v-if="!job.application_instructions" class="text-xs font-normal text-gray-500">(none — only the general ones)</span>
            </span>
            <FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-500 transition group-open:rotate-180" />
          </summary>
          <div class="border-t px-3 py-3">
            <div v-if="job.application_instructions" class="prose prose-sm max-w-none" v-html="job.application_instructions" />
            <p class="mt-2 text-xs text-gray-500">General instructions for every form are set in Settings &rsaquo; General.</p>
          </div>
        </details>
        <div class="mb-2 font-semibold text-gray-900">Supporting documents</div>
        <div v-if="job.required_documents?.length" class="flex flex-col gap-3">
          <div v-for="group in documentGroups" :key="group.label">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500">{{ group.label }} · {{ group.items.length }}</div>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="d in group.items"
                :key="d.name"
                class="inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs"
                :class="group.required ? 'border-gray-300 bg-white text-gray-800' : 'border-dashed border-gray-300 text-gray-600'"
              >
                <FeatherIcon name="file" class="h-3 w-3 text-brand-700" />{{ d.document_type }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-500">Default list — active Document Types marked for Application.</div>
        <p class="mt-3 flex items-center gap-1.5 text-xs text-gray-500">
          <FeatherIcon name="info" class="h-3.5 w-3.5" />
          Resume, SOP, degree certificates and transcripts are always asked for.
        </p>
      </div>
    </div>

    <!-- Edit view -->
    <div v-else class="flex flex-col gap-4">
      <ErrorMessage :message="error" />
      <div
        v-if="job.status === 'Advertised'"
        class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        This job is live. Changes apply to new applicants only; submitted applications keep the answers they gave.
      </div>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormControl
          label="Applications open from (optional)"
          type="datetime-local"
          v-model="form.application_start"
          description="Empty: open as soon as the job is advertised."
        />
        <FormControl label="Application Deadline" type="datetime-local" v-model="form.application_deadline" />
        <label class="flex items-center gap-2 self-end pb-2 text-sm text-gray-700">
          <input v-model="form.require_postgraduate" type="checkbox" class="rounded border-gray-300" />
          Post Graduate degree is required
        </label>
      </div>

      <div>
        <span class="mb-1.5 block text-sm text-gray-700">Instructions for this post</span>
        <TextEditor
          :content="form.application_instructions"
          placeholder="Shown with the general instructions when candidates open the form..."
          :fixed-menu="true"
          editor-class="prose-sm max-w-none min-h-[8rem] px-3 py-2"
          class="rounded border border-gray-300 bg-white"
          @change="(html) => (form.application_instructions = html)"
        />
      </div>

      <div>
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm text-gray-700">Screening questions</span>
          <Button size="sm" variant="ghost" @click="addQuestion">+ Add question</Button>
        </div>
        <div v-for="(q, idx) in form.screening_questions" :key="idx" class="mb-3 rounded border p-3">
          <div class="mb-2 flex items-start gap-2">
            <span class="pt-1.5 text-xs text-gray-500">{{ idx + 1 }}.</span>
            <FormControl class="flex-1" type="textarea" :rows="2" v-model="q.question" placeholder="Question" />
            <div class="flex flex-col">
              <Button size="sm" variant="ghost" :disabled="idx === 0" aria-label="Move up" @click="move(idx, -1)">
                <FeatherIcon name="arrow-up" class="h-3.5 w-3.5" />
              </Button>
              <Button size="sm" variant="ghost" aria-label="Remove" @click="form.screening_questions.splice(idx, 1)">
                <FeatherIcon name="trash-2" class="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
          <div class="grid grid-cols-1 gap-3 pl-5 sm:grid-cols-2">
            <FormControl
              type="select"
              label="Answer type"
              v-model="q.answer_type"
              :options="['Yes/No', 'Single Choice', 'Short Text', 'Long Text', 'Number']"
            />
            <div class="flex flex-col justify-end gap-1 pb-1 text-sm text-gray-700">
              <label class="flex items-center gap-2">
                <input v-model="q.is_mandatory" type="checkbox" class="rounded border-gray-300" /> Required
              </label>
              <label v-if="q.answer_type === 'Yes/No'" class="flex items-center gap-2">
                <input v-model="q.ask_details_if_yes" type="checkbox" class="rounded border-gray-300" /> Ask for details
                if Yes
              </label>
            </div>
            <FormControl
              v-if="q.answer_type === 'Single Choice'"
              class="sm:col-span-2"
              type="textarea"
              :rows="3"
              label="Choices (one per line)"
              v-model="q.options"
            />
            <FormControl
              v-if="q.answer_type === 'Yes/No' && q.ask_details_if_yes"
              class="sm:col-span-2"
              label="Details prompt"
              v-model="q.details_label"
              placeholder="Please describe the relevant work experience in brief."
            />
            <FormControl
              v-if="idx > 0"
              class="sm:col-span-2"
              label="Show only if the previous answer is"
              v-model="q.show_if_previous_answer"
              :placeholder="previousOptions(idx) ? `e.g. ${previousOptions(idx)}` : 'Leave empty to always show'"
              description="Leave empty to always show this question."
            />
          </div>
        </div>
      </div>

      <div>
        <div class="mb-2 text-sm text-gray-700">Supporting documents</div>
        <p class="mb-2 text-xs text-gray-500">
          Leave all unticked to use the default list. Manage document types in Master Setup &rsaquo; Document Types.
        </p>
        <div class="flex flex-col gap-1.5">
          <div v-for="dt in documentTypes" :key="dt.name" class="flex items-center justify-between gap-2 text-sm">
            <label class="flex items-center gap-2 text-gray-700">
              <input type="checkbox" class="rounded border-gray-300" :checked="!!docRow(dt.name)" @change="toggleDoc(dt.name, $event.target.checked)" />
              {{ dt.name }}
            </label>
            <label v-if="docRow(dt.name)" class="flex items-center gap-1.5 text-xs text-gray-600">
              <input v-model="docRow(dt.name).is_mandatory" type="checkbox" class="rounded border-gray-300" /> Required
            </label>
          </div>
          <div v-if="!documentTypes.length" class="text-sm text-gray-500">No active Document Types for applications.</div>
        </div>
      </div>

      <div class="flex justify-end gap-2">
        <Button @click="editing = false">Cancel</Button>
        <Button variant="solid" :loading="saving" @click="save">Save</Button>
      </div>
    </div>
  </SectionCard>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { Button, ErrorMessage, FeatherIcon, FormControl, TextEditor, call } from 'frappe-ui'
import { toast } from '@/utils/notify'
import dayjs from 'dayjs'
import { jobOpeningService } from '@/services/jobOpenings'
import SectionCard from '@/components/common/SectionCard.vue'

const props = defineProps({
  job: { type: Object, required: true },
  canWrite: { type: Boolean, default: false },
})
const emit = defineEmits(['saved'])

const editing = ref(false)
const saving = ref(false)
const error = ref('')
const documentTypes = ref([])
const form = reactive({
  application_deadline: '',
  application_start: '',
  require_postgraduate: false,
  application_instructions: '',
  screening_questions: [],
  required_documents: [],
})

const documentGroups = computed(() => {
  const docs = props.job.required_documents || []
  return [
    { label: 'Required', required: true, items: docs.filter((d) => d.is_mandatory) },
    { label: 'Optional', required: false, items: docs.filter((d) => !d.is_mandatory) },
  ].filter((group) => group.items.length)
})

// Answers the question above can have, as a hint for the condition.
function previousOptions(idx) {
  const prev = form.screening_questions[idx - 1]
  if (!prev) return ''
  if (prev.answer_type === 'Yes/No') return 'Yes'
  if (prev.answer_type === 'Single Choice') return (prev.options || '').split('\n').filter(Boolean).slice(-1)[0] || ''
  return ''
}

function formatDateTime(value) {
  return dayjs(value).format('DD MMM YYYY, h:mm A')
}

async function startEdit() {
  error.value = ''
  Object.assign(form, {
    application_deadline: props.job.application_deadline
      ? dayjs(props.job.application_deadline).format('YYYY-MM-DDTHH:mm')
      : '',
    require_postgraduate: !!props.job.require_postgraduate,
    application_start: props.job.application_start ? dayjs(props.job.application_start).format('YYYY-MM-DDTHH:mm') : '',
    application_instructions: props.job.application_instructions || '',
    screening_questions: (props.job.screening_questions || []).map((q) => ({
      question: q.question,
      answer_type: q.answer_type,
      options: q.options || '',
      is_mandatory: !!q.is_mandatory,
      ask_details_if_yes: !!q.ask_details_if_yes,
      details_label: q.details_label || '',
      show_if_previous_answer: q.show_if_previous_answer || '',
    })),
    required_documents: (props.job.required_documents || []).map((d) => ({
      document_type: d.document_type,
      is_mandatory: !!d.is_mandatory,
    })),
  })
  editing.value = true
  try {
    documentTypes.value = await call('frappe.client.get_list', {
      doctype: 'Document Type Master',
      filters: { is_active: 1, used_in: ['in', ['Application', 'Both']] },
      fields: ['name', 'requirement'],
      order_by: 'creation asc',
      limit_page_length: 0,
    })
  } catch {
    documentTypes.value = []
  }
}

function addQuestion() {
  form.screening_questions.push({
    question: '',
    answer_type: 'Yes/No',
    options: '',
    is_mandatory: true,
    ask_details_if_yes: false,
    details_label: '',
    show_if_previous_answer: '',
  })
}

function move(idx, delta) {
  const list = form.screening_questions
  const [item] = list.splice(idx, 1)
  list.splice(idx + delta, 0, item)
}

function docRow(name) {
  return form.required_documents.find((d) => d.document_type === name)
}

function toggleDoc(name, checked) {
  if (checked && !docRow(name)) {
    const master = documentTypes.value.find((d) => d.name === name)
    form.required_documents.push({ document_type: name, is_mandatory: master?.requirement === 'Mandatory' })
  } else if (!checked) {
    form.required_documents = form.required_documents.filter((d) => d.document_type !== name)
  }
}

async function save() {
  error.value = ''
  const blank = form.screening_questions.findIndex((q) => !q.question.trim())
  if (blank !== -1) {
    error.value = `Question ${blank + 1} is empty.`
    return
  }
  saving.value = true
  try {
    await jobOpeningService.updateJob(props.job.name, {
      application_deadline: form.application_deadline
        ? dayjs(form.application_deadline).format('YYYY-MM-DD HH:mm:ss')
        : null,
      require_postgraduate: form.require_postgraduate ? 1 : 0,
      application_start: form.application_start ? dayjs(form.application_start).format('YYYY-MM-DD HH:mm:ss') : null,
      application_instructions: form.application_instructions,
      screening_questions: form.screening_questions.map((q, idx) => ({
        question: q.question.trim(),
        answer_type: q.answer_type,
        options: q.answer_type === 'Single Choice' ? q.options : '',
        is_mandatory: q.is_mandatory ? 1 : 0,
        ask_details_if_yes: q.answer_type === 'Yes/No' && q.ask_details_if_yes ? 1 : 0,
        details_label: q.details_label,
        show_if_previous_answer: idx > 0 ? (q.show_if_previous_answer || '').trim() : '',
      })),
      required_documents: form.required_documents.map((d) => ({
        document_type: d.document_type,
        is_mandatory: d.is_mandatory ? 1 : 0,
      })),
    })
    editing.value = false
    toast({ title: 'Application form saved.', icon: 'check', iconClasses: 'text-green-500' })
    emit('saved')
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not save the application form.'
  } finally {
    saving.value = false
  }
}
</script>
