<template>
  <!-- Workflow step 14: the job's Shortlisting Note: the note to the
       Selection Committee, the final shortlist with remarks, and
       attachments. Printable as PDF and shareable with the panel. -->
  <Dialog :model-value="open" :options="{ title: `Shortlisting Note: ${jobTitle}`, size: '3xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div v-if="state.loading" class="h-56 animate-pulse rounded-lg bg-gray-100" />
      <p v-else-if="state.error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ state.error }}</p>
      <div v-else-if="data" class="flex flex-col gap-4 text-sm">
        <div>
          <div class="mb-1.5 text-xs font-medium text-gray-700">Note to the Selection Committee</div>
          <TextEditor
            v-if="data.can_edit"
            :key="editorKey"
            :content="form.note"
            :fixed-menu="true"
            editor-class="prose-sm max-w-none min-h-[10rem] px-3 py-2"
            class="rounded border border-gray-300 bg-white"
            @change="(html) => (form.note = html)"
          />
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div v-else class="prose-sm rounded-lg border bg-gray-50 px-3 py-2" v-html="data.note || '<p>No note yet.</p>'" />
        </div>

        <div>
          <div class="mb-1.5 flex items-baseline justify-between">
            <span class="text-xs font-medium text-gray-700">Final shortlist</span>
            <span class="text-xs text-gray-500">{{ data.final_shortlist.length }} candidate{{ data.final_shortlist.length === 1 ? '' : 's' }}</span>
          </div>
          <p v-if="!data.final_shortlist.length" class="rounded-lg border border-dashed px-3 py-4 text-center text-gray-500">
            No one yet. On the Interviews panel, tick candidates and choose “Add to final shortlist”.
          </p>
          <table v-else class="w-full rounded-lg border text-sm">
            <thead class="bg-gray-50 text-left text-xs text-gray-500">
              <tr><th class="px-3 py-2 font-medium">Candidate</th><th class="px-3 py-2 font-medium">Round 1 (HR)</th><th class="w-2/5 px-3 py-2 font-medium">Remarks</th></tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="r in data.final_shortlist" :key="r.application" class="align-top">
                <td class="px-3 py-2">
                  <div class="font-medium text-gray-900">{{ r.candidate_name }}</div>
                  <div class="font-mono text-xs text-gray-500">{{ r.application_id }}</div>
                </td>
                <td class="px-3 py-2 text-xs text-gray-700">{{ r.hr_outcome || '—' }}</td>
                <td class="px-3 py-2">
                  <textarea
                    v-if="data.can_edit"
                    v-model="form.remarks[r.application]"
                    rows="2"
                    class="w-full rounded-md border-gray-300 text-sm focus:border-brand-700 focus:ring-brand-700"
                    :aria-label="`Remarks for ${r.candidate_name}`"
                  />
                  <span v-else class="whitespace-pre-line">{{ r.remarks || '—' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <div class="mb-1.5 text-xs font-medium text-gray-700">Attachments</div>
          <ul v-if="form.attachments.length" class="mb-2 flex flex-col gap-1.5">
            <li v-for="(a, i) in form.attachments" :key="a.attachment + i" class="flex items-center gap-2">
              <FeatherIcon name="paperclip" class="h-4 w-4 shrink-0 text-gray-400" />
              <input
                v-if="data.can_edit"
                v-model="a.label"
                class="min-w-0 flex-1 rounded-md border-gray-300 py-1 text-sm focus:border-brand-700 focus:ring-brand-700"
                :aria-label="`Label for attachment ${i + 1}`"
              />
              <span v-else class="flex-1">{{ a.label }}</span>
              <a :href="a.attachment" target="_blank" rel="noopener" class="text-xs text-brand-700 hover:underline">Open</a>
              <Button v-if="data.can_edit" size="sm" variant="ghost" icon="x" :aria-label="`Remove ${a.label}`" @click="form.attachments.splice(i, 1)" />
            </li>
          </ul>
          <FileUploader v-if="data.can_edit" :upload-args="{ doctype: 'Job Opening', docname: jobOpening, private: true }" @success="onUpload">
            <template #default="{ openFileSelector, uploading }">
              <Button size="sm" icon-left="paperclip" :loading="uploading" @click="openFileSelector">Attach a file</Button>
            </template>
          </FileUploader>
        </div>

        <p v-if="data.prepared_by_name" class="text-xs text-gray-500">
          Prepared by {{ data.prepared_by_name }}<template v-if="data.prepared_on"> · last updated {{ dayjs(data.prepared_on).format('DD MMM YYYY, h:mm A [IST]') }}</template>
        </p>
        <p v-if="form.error" class="rounded-md bg-red-50 px-3 py-2 text-red-700">{{ form.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex flex-wrap justify-end gap-2">
        <Button v-if="data?.name" variant="outline" icon-left="printer" class="mr-auto" @click="print">Print (PDF)</Button>
        <Button variant="ghost" @click="emit('update:open', false)">Close</Button>
        <Button v-if="data?.can_edit" variant="solid" :class="BTN_BRAND" :loading="form.saving" @click="save">Save note</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FileUploader, TextEditor } from 'frappe-ui'
import dayjs from 'dayjs'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  jobOpening: { type: String, required: true },
  jobTitle: { type: String, default: '' },
})
const emit = defineEmits(['update:open', 'saved'])

const data = ref(null)
const state = reactive({ loading: false, error: '' })
const form = reactive({ note: '', remarks: {}, attachments: [], saving: false, error: '' })
const editorKey = ref(0)

function fill(d) {
  data.value = d
  form.note = d.note || ''
  form.remarks = Object.fromEntries(d.final_shortlist.map((r) => [r.application, r.remarks || '']))
  form.attachments = d.attachments.map((a) => ({ label: a.label, attachment: a.attachment }))
  editorKey.value++
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    state.loading = true
    state.error = ''
    form.error = ''
    try {
      fill(await interviewService.getShortlistingNote(props.jobOpening))
    } catch (e) {
      state.error = e?.messages?.[0] || 'Could not load the Shortlisting Note.'
    } finally {
      state.loading = false
    }
  },
)

function onUpload(file) {
  form.attachments.push({ label: (file.file_name || file.file_url.split('/').pop()).replace(/\.[^.]+$/, ''), attachment: file.file_url })
}

async function save() {
  form.saving = true
  form.error = ''
  try {
    fill(await interviewService.saveShortlistingNote(props.jobOpening, { note: form.note, attachments: form.attachments, remarks: form.remarks }))
    toast({ title: 'Shortlisting Note saved.', icon: 'check', iconClasses: 'text-green-500' })
    emit('saved')
  } catch (e) {
    form.error = e?.messages?.[0] || 'Could not save the note.'
  } finally {
    form.saving = false
  }
}

async function print() {
  try {
    await interviewService.downloadShortlistingNote(props.jobOpening, props.jobTitle)
  } catch (e) {
    form.error = e?.messages?.[0] || 'Could not create the PDF. Save the note first.'
  }
}
</script>
