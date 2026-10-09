<template>
  <!-- Import applications from the Excel template (or a CSV with the same
       columns): check the file first, then import the rows that pass. -->
  <Dialog :model-value="open" :options="{ title: 'Import applications', size: '4xl' }" @update:model-value="close">
    <template #body-content>
      <div class="flex flex-col gap-4 text-sm">
        <!-- 1. Template -->
        <div class="flex flex-wrap items-center gap-3 rounded-lg border bg-gray-50 px-4 py-3">
          <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-gray-700 ring-1 ring-gray-300">1</span>
          <div class="min-w-0 flex-1">
            <div class="font-medium text-gray-900">Download the template</div>
            <div class="text-xs text-gray-600">One row per application. Columns marked * are required; the Job Openings sheet lists the IDs to use.</div>
          </div>
          <Button icon-left="download" :loading="state.downloading" @click="downloadTemplate">Download template</Button>
        </div>

        <!-- 2. File -->
        <div class="flex flex-wrap items-center gap-3 rounded-lg border px-4 py-3">
          <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-gray-700 ring-1 ring-gray-300">2</span>
          <div class="min-w-0 flex-1">
            <div class="font-medium text-gray-900">Upload the filled file</div>
            <div class="truncate text-xs text-gray-600">{{ file.name || 'Excel (.xlsx) or CSV, up to 500 rows and 5 MB.' }}</div>
          </div>
          <input ref="input" type="file" accept=".xlsx,.csv" class="hidden" @change="pick" />
          <Button icon-left="upload" :loading="state.checking" :disabled="state.importing" @click="input?.click()">{{ file.name ? 'Choose another file' : 'Choose file' }}</Button>
        </div>

        <p v-if="state.error" class="whitespace-pre-line rounded-md bg-red-50 px-3 py-2 text-red-700">{{ state.error }}</p>

        <!-- 3. Check -->
        <template v-if="preview && !result">
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span class="font-medium text-gray-900">{{ preview.total }} row{{ preview.total === 1 ? '' : 's' }} found</span>
            <span class="text-gray-700">{{ preview.valid }} ready to import</span>
            <span v-if="invalid" class="text-red-700">{{ invalid }} with problems (skipped)</span>
            <span class="text-gray-500">{{ preview.new_candidates }} new candidate{{ preview.new_candidates === 1 ? '' : 's' }}</span>
            <label v-if="invalid" class="ml-auto flex items-center gap-2 text-gray-600">
              <input v-model="onlyProblems" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
              Show only rows with problems
            </label>
          </div>
          <div class="max-h-[40vh] overflow-auto rounded-lg border">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-gray-50 text-xs text-gray-600">
                <tr>
                  <th class="px-3 py-2 text-left font-medium">Row</th>
                  <th class="px-3 py-2 text-left font-medium">Candidate</th>
                  <th class="px-3 py-2 text-left font-medium">Job opening</th>
                  <th class="px-3 py-2 text-left font-medium">Status</th>
                  <th class="px-3 py-2 text-left font-medium">Check</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                <tr v-for="r in shownRows" :key="r.row" class="align-top">
                  <td class="px-3 py-2 tabular-nums text-gray-500">{{ r.row }}</td>
                  <td class="px-3 py-2">
                    <div class="text-gray-900">{{ r.full_name || '—' }}</div>
                    <div class="text-xs text-gray-500">{{ r.email }}</div>
                  </td>
                  <td class="px-3 py-2">
                    <div class="text-gray-900">{{ r.job_title || r.job_opening || '—' }}</div>
                    <div v-if="r.job_title" class="font-mono text-xs text-gray-500">{{ r.job_opening }}</div>
                  </td>
                  <td class="px-3 py-2 text-gray-700">{{ r.status }}</td>
                  <td class="px-3 py-2">
                    <ul v-if="r.errors.length" class="list-disc pl-4 text-xs text-red-700">
                      <li v-for="e in r.errors" :key="e">{{ e }}</li>
                    </ul>
                    <span v-else class="text-xs text-gray-600">OK · {{ r.candidate_status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex flex-col gap-2 rounded-lg border px-4 py-3">
            <div class="text-xs font-semibold uppercase tracking-wide text-gray-500">Emails to candidates</div>
            <label class="flex items-start gap-2.5">
              <input v-model="form.sendAcknowledgement" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
              <span>Send the "Application received" email</span>
            </label>
            <label class="flex items-start gap-2.5">
              <input v-model="form.sendLogin" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
              <span>
                Create a candidate portal login for new candidates and email it
                <span class="block text-xs text-gray-500">Without this, new candidates have no login until they apply on the portal themselves.</span>
              </span>
            </label>
          </div>
        </template>

        <!-- Result -->
        <div v-if="result" class="flex flex-col gap-3">
          <div class="rounded-lg border px-4 py-3">
            <div class="font-medium text-gray-900">{{ result.done.length }} application{{ result.done.length === 1 ? '' : 's' }} imported</div>
            <div v-if="result.failed.length" class="text-red-700">{{ result.failed.length }} row{{ result.failed.length === 1 ? '' : 's' }} not imported</div>
          </div>
          <div v-if="result.failed.length" class="max-h-[40vh] overflow-auto rounded-lg border">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-gray-50 text-xs text-gray-600">
                <tr>
                  <th class="px-3 py-2 text-left font-medium">Row</th>
                  <th class="px-3 py-2 text-left font-medium">Candidate</th>
                  <th class="px-3 py-2 text-left font-medium">Problem</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                <tr v-for="f in result.failed" :key="f.row" class="align-top">
                  <td class="px-3 py-2 tabular-nums text-gray-500">{{ f.row }}</td>
                  <td class="px-3 py-2 text-gray-900">{{ f.full_name || '—' }}</td>
                  <td class="px-3 py-2 text-xs text-red-700">{{ f.error }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-xs text-gray-500">Fix those rows in the file and import it again: rows already imported are reported as already applied, not added twice.</p>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" :disabled="state.importing" @click="close(false)">{{ result ? 'Done' : 'Cancel' }}</Button>
        <Button
          v-if="!result"
          variant="solid"
          :class="BTN_BRAND"
          icon-left="upload-cloud"
          :loading="state.importing"
          :disabled="!preview?.valid || state.checking"
          @click="runImport"
        >
          Import {{ preview?.valid || '' }} application{{ preview?.valid === 1 ? '' : 's' }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog } from 'frappe-ui'
import { applicationService } from '@/services/applications'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['update:open', 'imported'])

const input = ref(null)
const file = reactive({ name: '', content: '' })
const state = reactive({ downloading: false, checking: false, importing: false, error: '' })
const form = reactive({ sendAcknowledgement: false, sendLogin: false })
const preview = ref(null)
const result = ref(null)
const onlyProblems = ref(false)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    Object.assign(file, { name: '', content: '' })
    Object.assign(state, { downloading: false, checking: false, importing: false, error: '' })
    Object.assign(form, { sendAcknowledgement: false, sendLogin: false })
    preview.value = null
    result.value = null
    onlyProblems.value = false
  },
)

const invalid = computed(() => (preview.value ? preview.value.total - preview.value.valid : 0))
const shownRows = computed(() => (preview.value?.rows || []).filter((r) => !onlyProblems.value || r.errors.length))

function close(value = false) {
  // Never close in the middle of an import.
  if (state.importing) return
  emit('update:open', value)
}

async function downloadTemplate() {
  state.downloading = true
  try {
    await applicationService.downloadImportTemplate()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the template.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    state.downloading = false
  }
}

function readFile(f) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(f)
  })
}

async function pick(event) {
  const f = event.target.files?.[0]
  // Choosing the same file again must still fire change.
  event.target.value = ''
  if (!f) return
  state.error = ''
  preview.value = null
  if (!/\.(xlsx|csv)$/i.test(f.name)) {
    state.error = 'Choose an Excel (.xlsx) or CSV file.'
    return
  }
  if (f.size > 5 * 1024 * 1024) {
    state.error = 'The file is larger than 5 MB.'
    return
  }
  state.checking = true
  try {
    const content = await readFile(f)
    Object.assign(file, { name: f.name, content })
    preview.value = await applicationService.previewImport(f.name, content)
    onlyProblems.value = false
    if (!preview.value.total) state.error = 'No applications found in the file. Fill in rows below the header (the grey help row is ignored).'
  } catch (e) {
    Object.assign(file, { name: '', content: '' })
    state.error = e?.messages?.join('\n') || 'Could not read the file.'
  } finally {
    state.checking = false
  }
}

async function runImport() {
  state.importing = true
  state.error = ''
  try {
    result.value = await applicationService.runImport(file.name, file.content, form)
    if (result.value.done.length) {
      toast({ title: `${result.value.done.length} application${result.value.done.length === 1 ? '' : 's'} imported.`, icon: 'check', iconClasses: 'text-green-500' })
      emit('imported')
    }
  } catch (e) {
    state.error = e?.messages?.join('\n') || 'The import did not finish. Nothing was saved.'
  } finally {
    state.importing = false
  }
}
</script>
