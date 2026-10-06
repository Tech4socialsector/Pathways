<template>
  <StaffLayout>
    <PageHeader title="Job Openings">
      <template #actions>
        <Button
          v-if="session.hasAnyRole(['System Manager', 'Pathways Admin', 'Pathways Recruiter'])"
          variant="solid"
          @click="openCreateDialog"
        >
          New Job Opening
        </Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="!jobs.length" title="No job openings" />
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th class="px-4 py-2">Job Title</th>
              <th class="px-4 py-2">Track</th>
              <th class="px-4 py-2">Department</th>
              <th class="px-4 py-2">Vacancies</th>
              <th class="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="job in jobs"
              :key="job.name"
              class="cursor-pointer border-b last:border-0 hover:bg-gray-50"
              @click="$router.push(`/jobs/${job.name}`)"
            >
              <td class="px-4 py-2.5 font-medium text-gray-900">{{ job.job_title }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ job.track }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ job.department }}</td>
              <td class="px-4 py-2.5 text-gray-600">{{ job.vacancies }}</td>
              <td class="px-4 py-2.5"><StatusBadge :status="job.status" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Dialog v-model="showCreateDialog" :options="{ title: 'New Job Opening', size: 'xl' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="formError" />
          <FormControl label="Job Title" v-model="form.job_title" required />
          <div class="grid grid-cols-2 gap-4">
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
          </div>
          <div class="grid grid-cols-2 gap-4">
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
              :options="employmentTypeOptions"
              required
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <FormControl label="Vacancies" type="number" v-model="form.vacancies" required />
            <FormControl label="Pay Level" v-model="form.pay_level" />
          </div>
          <FormControl label="Tenure Description" type="textarea" v-model="form.tenure_description" />
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :loading="submitting" @click="submitCreate">Create</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast, Autocomplete } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useStaffJobOpenings } from '@/composables/useJobOpenings'
import { jobOpeningService } from '@/services/jobOpenings'
import { useSessionStore } from '@/stores/session'
import { useRecruitmentTrackOptions, useDepartmentOptions, useDesignationOptions } from '@/composables/useMasterData'

const session = useSessionStore()
const router = useRouter()

const { jobs, loading, fetchJobs } = useStaffJobOpenings()
const trackOptions = useRecruitmentTrackOptions()
const departmentOptions = useDepartmentOptions()
const designationOptions = useDesignationOptions()

onMounted(() => {
  session.fetchRoles()
  fetchJobs()
})

const employmentTypeOptions = ['Permanent', 'Consultant', 'Grant-funded', 'Contract']

const showCreateDialog = ref(false)
const submitting = ref(false)
const formError = ref('')

function emptyForm() {
  return {
    job_title: '',
    track: '',
    department: '',
    designation: '',
    employment_type: '',
    vacancies: 1,
    tenure_description: '',
    pay_level: '',
  }
}

const form = reactive(emptyForm())

function openCreateDialog() {
  trackOptions.fetch()
  departmentOptions.fetch()
  designationOptions.fetch()
  Object.assign(form, emptyForm())
  formError.value = ''
  showCreateDialog.value = true
}

async function submitCreate() {
  formError.value = ''
  submitting.value = true
  try {
    const created = await jobOpeningService.createJob({ ...form })
    showCreateDialog.value = false
    toast({ title: 'Job Opening created.', icon: 'check', iconClasses: 'text-green-500' })
    router.push(`/jobs/${created.name}`)
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not create the Job Opening.'
  } finally {
    submitting.value = false
  }
}
</script>
