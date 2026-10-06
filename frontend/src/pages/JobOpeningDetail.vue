<template>
  <StaffLayout>
    <PageHeader :title="job?.job_title || 'Job Opening'" :subtitle="job?.track">
      <template #actions>
        <Button
          v-if="permissions.can_write && job?.status === 'Approved'"
          variant="solid"
          :loading="changingStatus"
          @click="changeStatus('Advertised')"
        >
          Advertise
        </Button>
        <Button v-if="permissions.can_write && job" @click="openStatusDialog">Change Status</Button>
        <Button v-if="permissions.can_write && job" @click="openEditDialog">Edit</Button>
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
      <div v-if="loading && !job" class="text-sm text-gray-500">Loading...</div>
      <div v-else-if="job" class="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div class="flex flex-col gap-6 md:col-span-2">
          <div v-if="job.advertisement_url" class="rounded-lg border border-green-200 bg-green-50 p-4">
            <div class="mb-1 text-sm font-semibold text-gray-900">Advertisement Link</div>
            <p class="mb-3 text-sm text-gray-600">Share this link to post the job description publicly. Candidates can read it and apply.</p>
            <div class="flex flex-wrap items-center gap-2">
              <a
                :href="job.advertisement_url"
                target="_blank"
                rel="noopener"
                class="min-w-0 flex-1 truncate rounded border bg-white px-3 py-1.5 font-mono text-sm text-gray-800 hover:underline"
              >{{ job.advertisement_url }}</a>
              <Button icon-left="copy" @click="copyAdvertisementUrl">Copy</Button>
              <Button icon-left="external-link" :link="job.advertisement_url">Open</Button>
            </div>
          </div>
          <div class="rounded-lg border bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">Job Description</div>
            <div v-if="job.jd_text" class="prose prose-sm max-w-none" v-html="job.jd_text" />
            <div v-else class="text-sm text-gray-500">No description provided.</div>
            <a
              v-if="job.jd_attachment"
              :href="job.jd_attachment"
              target="_blank"
              rel="noopener"
              class="mt-3 inline-block text-sm font-medium text-blue-600 hover:underline"
            >JD Attachment: {{ job.jd_attachment.split('/').pop() }}</a>
          </div>
          <ApplicationFormPanel :job="job" :can-write="!!permissions.can_write" @saved="fetchJob(props.id)" />
          <GreenSheetPanel
            ref="greenSheetPanel"
            :job="job"
            @loaded="(d) => (greenSheet = d.current)"
            @changed="fetchJob(props.id)"
          />
        </div>
        <div class="self-start rounded-lg border bg-white p-4">
          <dl class="flex flex-col gap-3 text-sm">
            <div>
              <dt class="text-gray-500">Status</dt>
              <dd class="font-medium text-gray-900"><StatusBadge :status="job.status" /></dd>
            </div>
            <div v-if="job.track">
              <dt class="text-gray-500">Recruitment Track</dt>
              <dd class="font-medium text-gray-900">{{ job.track }}</dd>
            </div>
            <div v-if="job.designation">
              <dt class="text-gray-500">Designation</dt>
              <dd class="font-medium text-gray-900">{{ job.designation }}</dd>
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
            <div v-if="job.application_deadline">
              <dt class="text-gray-500">Applications close</dt>
              <dd class="font-medium text-gray-900">{{ dayjs(job.application_deadline).format('DD MMM YYYY, h:mm A') }}</dd>
            </div>
            <div v-if="job.reservation_breakdown?.length">
              <dt class="text-gray-500">Reservation Breakdown</dt>
              <dd class="font-medium text-gray-900">
                <div v-for="row in job.reservation_breakdown" :key="row.name">
                  {{ row.category }}: {{ row.vacancy_count }}
                </div>
              </dd>
            </div>
            <div v-if="job.pre_recruitment_green_sheet">
              <dt class="text-gray-500">Green Sheet</dt>
              <dd class="font-medium text-gray-900">{{ job.pre_recruitment_green_sheet }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <Dialog v-model="showEditDialog" :options="{ title: 'Edit Job Opening', size: '4xl' }">
      <template #body-content>
        <JobOpeningForm :form="form" :error="formError" :docname="props.id" />
      </template>
      <template #actions>
        <Button variant="solid" :loading="submitting" @click="submitEdit">Save</Button>
      </template>
    </Dialog>

    <Dialog v-model="showStatusDialog" :options="{ title: 'Change Status', size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-4">
          <ErrorMessage :message="statusError" />
          <div
            v-if="permissions.can_override_status"
            class="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800"
          >
            Your role may set any status directly, without Green Sheet approval.
          </div>
          <div v-else-if="!greenSheetApproved" class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-800">
            Approved and Advertised become available once the Pre-Recruitment Green Sheet is approved.
          </div>
          <FormControl label="Status" type="select" v-model="statusForm" :options="statusOptions" />
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :loading="changingStatus"
          :disabled="!statusForm || statusForm === job?.status"
          @click="submitStatus"
        >
          Update Status
        </Button>
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GreenSheetPanel from '@/components/jobs/GreenSheetPanel.vue'
import JobOpeningForm, { emptyJobForm } from '@/components/jobs/JobOpeningForm.vue'
import ApplicationFormPanel from '@/components/jobs/ApplicationFormPanel.vue'
import { useStaffJobOpeningDetail } from '@/composables/useJobOpenings'
import { jobOpeningService } from '@/services/jobOpenings'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

const { job, loading, permissions, fetchJob, fetchPermissions } = useStaffJobOpeningDetail()

const greenSheetPanel = ref(null)
const greenSheet = ref(null)

async function loadAll(id) {
  await Promise.all([fetchJob(id), fetchPermissions(id)])
}

onMounted(() => loadAll(props.id))
watch(() => props.id, (id) => loadAll(id))

const showEditDialog = ref(false)
const submitting = ref(false)
const formError = ref('')
const form = reactive(emptyJobForm())

function openEditDialog() {
  for (const key of Object.keys(emptyJobForm())) form[key] = job.value[key] ?? ''
  // Copy rows so cancelling the dialog doesn't change the page. Only the
  // editable fields are sent; saving replaces the child table.
  form.reservation_breakdown = (job.value.reservation_breakdown || []).map((r) => ({
    category: r.category,
    vacancy_count: r.vacancy_count,
  }))
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
    await loadAll(props.id)
    // Track may have changed, which decides the Green Sheet approval chain.
    greenSheetPanel.value?.reload()
  } catch (e) {
    formError.value = e?.messages?.[0] || 'Could not update the Job Opening.'
  } finally {
    submitting.value = false
  }
}

const ALL_STATUSES = ['Draft', 'Pending Approval', 'Approved', 'Advertised', 'Closed', 'Filled', 'Cancelled']
// Statuses reachable only through an approved Green Sheet (mirrors
// JobOpening.validate_status_transition); Pending Approval is set
// automatically when a Green Sheet is submitted.
const APPROVAL_GATED = ['Approved', 'Advertised']

const greenSheetApproved = computed(
  () => greenSheet.value?.docstatus === 1 && greenSheet.value?.status === 'Approved',
)

const statusOptions = computed(() => {
  const current = job.value?.status
  return ALL_STATUSES.filter((s) => {
    if (s === current || permissions.value.can_override_status) return true
    if (s === 'Pending Approval') return false
    if (APPROVAL_GATED.includes(s)) return greenSheetApproved.value
    return true
  })
})

const showStatusDialog = ref(false)
const statusForm = ref('')
const statusError = ref('')
const changingStatus = ref(false)

function openStatusDialog() {
  statusForm.value = job.value.status
  statusError.value = ''
  showStatusDialog.value = true
}

async function changeStatus(status) {
  if (changingStatus.value) return false
  changingStatus.value = true
  statusError.value = ''
  try {
    await jobOpeningService.updateJob(props.id, { status })
    toast({
      title:
        status === 'Advertised'
          ? 'Job advertised. The public advertisement link is ready to share.'
          : `Status changed to ${status}.`,
      icon: 'check',
      iconClasses: 'text-green-500',
    })
    return true
  } catch (e) {
    const message = e?.messages?.[0] || 'Could not change the status.'
    statusError.value = message
    if (!showStatusDialog.value) {
      toast({ title: message, icon: 'alert-triangle', iconClasses: 'text-red-500' })
    }
    return false
  } finally {
    changingStatus.value = false
    await fetchJob(props.id)
  }
}

async function copyAdvertisementUrl() {
  try {
    await navigator.clipboard.writeText(job.value.advertisement_url)
    toast({ title: 'Advertisement link copied.', icon: 'check', iconClasses: 'text-green-500' })
  } catch {
    toast({ title: 'Could not copy. Select the link and copy it manually.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

async function submitStatus() {
  if (await changeStatus(statusForm.value)) showStatusDialog.value = false
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
