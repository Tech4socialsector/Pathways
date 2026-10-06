<template>
  <StaffLayout>
    <PageHeader title="Job Openings">
      <template #actions>
        <Button
          v-if="session.can('Job Opening', 'create')"
          variant="solid"
          @click="openCreateDialog"
        >
          New Job Opening
        </Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        :columns="columns"
        :rows="jobs"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No job openings"
        search-placeholder="Search job openings..."
        @row-click="(job) => router.push(`/jobs/${job.name}`)"
      >
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      </DataTable>
    </div>

    <Dialog v-model="showCreateDialog" :options="{ title: 'New Job Opening', size: '4xl' }">
      <template #body-content>
        <JobOpeningForm :form="form" :error="formError" />
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
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import JobOpeningForm, { emptyJobForm } from '@/components/jobs/JobOpeningForm.vue'
import { useStaffJobOpenings } from '@/composables/useJobOpenings'
import { jobOpeningService } from '@/services/jobOpenings'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const router = useRouter()

const { jobs, loading, fetchJobs } = useStaffJobOpenings()

const columns = [
  { key: 'position', label: 'Job Code' },
  { key: 'job_title', label: 'Job Title' },
  { key: 'track', label: 'Track' },
  { key: 'department', label: 'Department' },
  { key: 'designation', label: 'Designation' },
  { key: 'employment_type', label: 'Employment Type' },
  { key: 'vacancies', label: 'Vacancies' },
  { key: 'status', label: 'Status' },
]
const filters = [
  { key: 'status', label: 'Statuses' },
  { key: 'track', label: 'Tracks' },
  { key: 'department', label: 'Departments' },
  { key: 'employment_type', label: 'Employment Types' },
]

onMounted(() => {
  session.fetchRoles()
  fetchJobs({}, { limit_page_length: 0 })
})

const showCreateDialog = ref(false)
const submitting = ref(false)
const formError = ref('')
const form = reactive(emptyJobForm())

function openCreateDialog() {
  Object.assign(form, emptyJobForm())
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
