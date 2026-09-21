<template>
  <StaffLayout>
    <PageHeader :title="job?.job_title || 'Job Opening'" :subtitle="job?.track">
      <template #actions>
        <Button v-if="permissions.can_write" @click="openEditDialog">Edit</Button>
        <Button
          v-if="permissions.can_delete"
          theme="red"
          variant="outline"
          @click="showDeleteConfirm = true"
        >
          Delete
        </Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <div v-else-if="job" class="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div class="rounded-lg border bg-white p-4 md:col-span-2">
          <div class="mb-3 text-sm font-semibold text-gray-900">Job Description</div>
          <div v-if="job.jd_text" class="prose prose-sm max-w-none" v-html="job.jd_text" />
          <div v-else class="text-sm text-gray-500">No description provided.</div>
        </div>
        <div class="rounded-lg border bg-white p-4">
          <dl class="flex flex-col gap-3 text-sm">
            <div>
              <dt class="text-gray-500">Status</dt>
              <dd class="font-medium text-gray-900"><StatusBadge :status="job.status" /></dd>
            </div>
            <div>
              <dt class="text-gray-500">Department</dt>
              <dd class="font-medium text-gray-900">{{ job.department }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">Employment Type</dt>
              <dd class="font-medium text-gray-900">{{ job.employment_type }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">Vacancies</dt>
              <dd class="font-medium text-gray-900">{{ job.vacancies }}</dd>
            </div>
            <div v-if="job.pay_level">
              <dt class="text-gray-500">Pay Level</dt>
              <dd class="font-medium text-gray-900">{{ job.pay_level }}</dd>
            </div>
            <div v-if="job.tenure_description">
              <dt class="text-gray-500">Tenure</dt>
              <dd class="font-medium text-gray-900">{{ job.tenure_description }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <Dialog v-model="showEditDialog" :options="{ title: 'Edit Job Opening', size: 'xl' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="formError" />
          <FormControl label="Job Title" v-model="form.job_title" required />
          <div class="grid grid-cols-2 gap-4">
            <FormControl label="Recruitment Track" v-model="form.track" required />
            <FormControl label="Department" v-model="form.department" required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <FormControl label="Designation" v-model="form.designation" />
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
        <Button variant="solid" :loading="submitting" @click="submitEdit">Save</Button>
      </template>
    </Dialog>

    <Dialog
      v-model="showDeleteConfirm"
      :options="{
        title: 'Delete Job Opening',
        message: `Are you sure you want to delete '${job?.job_title}'? This cannot be undone.`,
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" theme="red" :loading="deleting" @click="confirmDelete">Delete</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useStaffJobOpeningDetail } from '@/composables/useJobOpenings'
import { jobOpeningService } from '@/services/jobOpenings'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

const { job, loading, permissions, fetchJob, fetchPermissions } = useStaffJobOpeningDetail()

function loadAll(id) {
  fetchJob(id)
  fetchPermissions(id)
}

onMounted(() => loadAll(props.id))
watch(() => props.id, (id) => loadAll(id))

const employmentTypeOptions = ['Permanent', 'Consultant', 'Grant-funded', 'Contract']

const showEditDialog = ref(false)
const submitting = ref(false)
const formError = ref('')
const form = reactive({
  job_title: '',
  track: '',
  department: '',
  designation: '',
  employment_type: '',
  vacancies: 1,
  tenure_description: '',
  pay_level: '',
})

function openEditDialog() {
  Object.assign(form, {
    job_title: job.value.job_title,
    track: job.value.track,
    department: job.value.department,
    designation: job.value.designation,
    employment_type: job.value.employment_type,
    vacancies: job.value.vacancies,
    tenure_description: job.value.tenure_description,
    pay_level: job.value.pay_level,
  })
  formError.value = ''
  showEditDialog.value = true
}

async function submitEdit() {
  formError.value = ''
  submitting.value = true
  try {
    await jobOpeningService.updateJob(props.id, { ...form })
    showEditDialog.value = false
    toast({ title: 'Job Opening updated.', icon: 'check', iconClasses: 'text-green-500' })
    loadAll(props.id)
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not update the Job Opening.'
  } finally {
    submitting.value = false
  }
}

const showDeleteConfirm = ref(false)
const deleting = ref(false)

async function confirmDelete() {
  deleting.value = true
  try {
    await jobOpeningService.deleteJob(props.id)
    showDeleteConfirm.value = false
    toast({ title: 'Job Opening deleted.', icon: 'check', iconClasses: 'text-green-500' })
    router.push('/jobs')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not delete the Job Opening.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    deleting.value = false
  }
}
</script>
