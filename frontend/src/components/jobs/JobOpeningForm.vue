<template>
  <!-- Shared by the New and Edit Job Opening dialogs. Scrolls inside the
       dialog so the Job Description editor never pushes Save off-screen. -->
  <div class="-mx-1 flex max-h-[70vh] flex-col gap-4 overflow-y-auto px-1 pb-1">
    <ErrorMessage :message="error" />
    <FormControl label="Job Title" v-model="form.job_title" required />
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div>
        <span class="mb-1.5 block text-sm text-gray-700">Recruitment Track<span class="text-red-500">*</span></span>
        <Autocomplete
          placeholder="Select a track"
          :options="trackOptions.options.value"
          :model-value="form.track"
          @update:model-value="(opt) => (form.track = opt?.value ?? '')"
        />
      </div>
      <div>
        <span class="mb-1.5 block text-sm text-gray-700">Department<span class="text-red-500">*</span></span>
        <Autocomplete
          placeholder="Select a department"
          :options="departmentOptions.options.value"
          :model-value="form.department"
          @update:model-value="(opt) => (form.department = opt?.value ?? '')"
        />
      </div>
      <div>
        <span class="mb-1.5 block text-sm text-gray-700">Designation</span>
        <Autocomplete
          placeholder="Select a designation"
          :options="designationOptions.options.value"
          :model-value="form.designation"
          @update:model-value="(opt) => (form.designation = opt?.value ?? '')"
        />
      </div>
      <FormControl
        label="Employment Type"
        type="select"
        v-model="form.employment_type"
        :options="EMPLOYMENT_TYPES"
        required
      />
      <FormControl label="Vacancies" type="number" v-model="form.vacancies" required />
      <FormControl label="Pay Level" v-model="form.pay_level" />
    </div>
    <FormControl label="Tenure Description" type="textarea" v-model="form.tenure_description" />

    <!-- Mirrors the DocType: the section shows once a track is chosen. -->
    <div v-if="form.track">
      <div class="mb-1.5 text-sm text-gray-700">Reservation Category Breakdown</div>
      <p class="mb-2 text-xs text-gray-500">Applicable primarily to teaching posts.</p>
      <div class="overflow-hidden rounded border">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th class="w-12 px-3 py-2">No.</th>
              <th class="px-3 py-2">Category<span class="text-red-500">*</span></th>
              <th class="px-3 py-2">Vacancy Count<span class="text-red-500">*</span></th>
              <th class="w-12 px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!form.reservation_breakdown.length">
              <td colspan="4" class="px-3 py-3 text-center text-gray-500">No reservation rows.</td>
            </tr>
            <tr v-for="(row, idx) in form.reservation_breakdown" :key="idx" class="border-b last:border-0">
              <td class="px-3 py-1.5 text-gray-500">{{ idx + 1 }}</td>
              <td class="px-3 py-1.5">
                <FormControl type="select" v-model="row.category" :options="RESERVATION_CATEGORIES" />
              </td>
              <td class="px-3 py-1.5">
                <FormControl type="number" v-model="row.vacancy_count" />
              </td>
              <td class="px-3 py-1.5 text-right">
                <Button variant="ghost" icon="x" @click="form.reservation_breakdown.splice(idx, 1)" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="mt-2 flex items-center justify-between text-xs text-gray-500">
        <Button size="sm" icon-left="plus" @click="form.reservation_breakdown.push({ category: '', vacancy_count: null })">
          Add Row
        </Button>
        <span v-if="form.reservation_breakdown.length">
          Reserved: {{ reservedTotal }} of {{ form.vacancies || 0 }} vacancies
        </span>
      </div>
    </div>

    <div>
      <span class="mb-1.5 block text-sm text-gray-700">JD Attachment</span>
      <div class="flex flex-wrap items-center gap-2">
        <a
          v-if="form.jd_attachment"
          :href="form.jd_attachment"
          target="_blank"
          rel="noopener"
          class="max-w-xs truncate text-sm text-blue-600 hover:underline"
        >{{ form.jd_attachment.split('/').pop() }}</a>
        <FileUploader
          file-types=".pdf,.doc,.docx"
          :upload-args="{ doctype: 'Job Opening', docname: docname || undefined, private: false }"
          @success="(file) => (form.jd_attachment = file.file_url)"
        >
          <template #default="{ openFileSelector, uploading, progress }">
            <Button icon-left="paperclip" :loading="uploading" @click="openFileSelector">
              {{ uploading ? `Uploading ${progress}%` : form.jd_attachment ? 'Replace' : 'Attach' }}
            </Button>
          </template>
        </FileUploader>
        <Button v-if="form.jd_attachment" variant="ghost" @click="form.jd_attachment = ''">Remove</Button>
      </div>
      <p class="mt-1 text-xs text-gray-500">PDF or Word. Shown publicly on the job posting once advertised.</p>
    </div>

    <div>
      <span class="mb-1.5 block text-sm text-gray-700">Job Description</span>
      <TextEditor
        :content="form.jd_text"
        placeholder="Role summary, responsibilities, eligibility and qualifications..."
        :fixed-menu="true"
        editor-class="prose-sm max-w-none min-h-[14rem] px-3 py-2"
        class="rounded border border-gray-300 bg-white"
        @change="(html) => (form.jd_text = html)"
      />
    </div>
  </div>
</template>

<script>
export const EMPLOYMENT_TYPES = ['Permanent', 'Consultant', 'Grant-funded', 'Contract']
// Options of Reservation Category Row.category.
export const RESERVATION_CATEGORIES = ['', 'General', 'SC', 'ST', 'OBC', 'EWS', 'PWD']

export function emptyJobForm() {
  return {
    job_title: '',
    track: '',
    department: '',
    designation: '',
    employment_type: '',
    vacancies: 1,
    tenure_description: '',
    pay_level: '',
    reservation_breakdown: [],
    jd_attachment: '',
    jd_text: '',
  }
}
</script>

<script setup>
import { computed, onMounted } from 'vue'
import { Autocomplete, Button, ErrorMessage, FileUploader, FormControl, TextEditor } from 'frappe-ui'
import { useRecruitmentTrackOptions, useDepartmentOptions, useDesignationOptions } from '@/composables/useMasterData'

const props = defineProps({
  // Reactive object owned by the parent; fields are edited in place.
  form: { type: Object, required: true },
  error: { type: String, default: '' },
  // Set when editing, so an uploaded JD is attached to the Job Opening.
  docname: { type: String, default: '' },
})

const reservedTotal = computed(() =>
  props.form.reservation_breakdown.reduce((sum, row) => sum + (Number(row.vacancy_count) || 0), 0),
)

const trackOptions = useRecruitmentTrackOptions()
const departmentOptions = useDepartmentOptions()
const designationOptions = useDesignationOptions()

onMounted(() => {
  trackOptions.fetch()
  departmentOptions.fetch()
  designationOptions.fetch()
})
</script>
