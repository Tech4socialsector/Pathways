<template>
  <StaffLayout>
    <PageHeader
      :title="job?.job_title || 'Job Opening'"
      :breadcrumbs="[{ label: 'Job Openings', to: '/jobs' }, { label: job?.job_title || 'Job Opening' }]"
    >
      <template #meta>
        <div v-if="job" class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm text-gray-600">
          <span v-if="job.position" class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-xs font-medium text-gray-700">{{ job.position }}</span>
          <StatusBadge :status="job.status" />
          <span class="flex items-center gap-1.5"><FeatherIcon name="home" class="h-3.5 w-3.5 text-brand-700" />{{ job.department }}</span>
          <span v-if="job.track" class="flex items-center gap-1.5"><FeatherIcon name="git-branch" class="h-3.5 w-3.5 text-brand-700" />{{ job.track }} track</span>
        </div>
      </template>
      <template #actions>
        <Button
          v-if="permissions.can_write && job?.status === 'Approved'"
          variant="solid"
          class="!bg-brand-700 !text-white hover:!bg-brand-800"
          :loading="changingStatus"
          @click="changeStatus('Advertised')"
        >
          Advertise
        </Button>
        <Button
          v-if="permissions.can_write && job"
          variant="solid"
          icon-left="edit-2"
          class="!bg-brand-700 !text-white hover:!bg-brand-800"
          @click="openEditDialog"
        >
          Edit
        </Button>
        <Dropdown v-if="job && moreActions.length" :options="moreActions" placement="right">
          <Button variant="outline" icon="more-horizontal" aria-label="More actions" />
        </Dropdown>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto bg-gray-50">
      <div v-if="loading && !job" class="p-6 text-sm text-gray-500">Loading...</div>
      <div v-else-if="job" class="mx-auto flex max-w-7xl flex-col gap-6 p-6">
        <!-- Key facts -->
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <div
            v-for="fact in facts"
            :key="fact.label"
            class="flex items-center gap-3 rounded-xl border px-4 py-3.5"
            :class="FACT_THEMES[fact.theme].card"
          >
            <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full" :class="FACT_THEMES[fact.theme].icon">
              <FeatherIcon :name="fact.icon" class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <div class="text-xs font-medium uppercase tracking-wide text-gray-600">{{ fact.label }}</div>
              <div class="text-xl font-bold leading-tight text-gray-900">{{ fact.value }}</div>
              <div class="truncate text-xs" :class="fact.tone || 'text-gray-600'" :title="fact.hint">{{ fact.hint }}</div>
            </div>
          </div>
        </div>

        <!-- Public link -->
        <div
          v-if="publicUrl"
          class="flex flex-wrap items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3.5"
        >
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
            <FeatherIcon name="globe" class="h-5 w-5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-bold text-brand-700">Live on the job board</div>
            <a
              :href="publicUrl"
              target="_blank"
              rel="noopener"
              class="block truncate font-mono text-xs text-gray-700 hover:underline"
            >{{ publicUrl }}</a>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" icon-left="copy" :class="BRAND_OUTLINE" @click="copyAdvertisementUrl">Copy link</Button>
            <Button variant="outline" icon-left="external-link" :class="BRAND_OUTLINE" :link="publicUrl">Open</Button>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div class="flex min-w-0 flex-col gap-6 lg:col-span-2">
            <SectionCard title="Job Description" icon="file-text">
              <div v-if="job.jd_text" class="prose prose-sm max-w-none text-gray-800" v-html="job.jd_text" />
              <div v-else class="text-sm text-gray-500">No description provided.</div>
              <a
                v-if="job.jd_attachment"
                :href="job.jd_attachment"
                target="_blank"
                rel="noopener"
                class="mt-4 inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                <FeatherIcon name="paperclip" class="h-3.5 w-3.5" />{{ job.jd_attachment.split('/').pop() }}
              </a>
            </SectionCard>
            <ApplicationFormPanel :job="job" :can-write="!!permissions.can_write" @saved="fetchJob(props.id)" />
            <GreenSheetPanel
              ref="greenSheetPanel"
              :job="job"
              @loaded="(d) => (greenSheet = d.current)"
              @changed="fetchJob(props.id)"
            />
          </div>

          <div class="flex flex-col gap-6 self-start">
            <SectionCard title="Position" icon="briefcase">
              <dl class="flex flex-col divide-y divide-gray-100 text-sm">
                <div v-for="row in positionRows" :key="row.label" class="flex justify-between gap-4 py-2 first:pt-0 last:pb-0">
                  <dt class="shrink-0 text-gray-500">{{ row.label }}</dt>
                  <dd class="text-right font-medium text-gray-900" :class="row.mono && 'font-mono text-xs'">{{ row.value }}</dd>
                </div>
              </dl>
            </SectionCard>
            <SectionCard v-if="job.tenure_description || job.reservation_breakdown?.length" title="Terms" icon="clipboard">
              <div class="flex flex-col gap-4 text-sm">
                <div v-if="job.tenure_description">
                  <div class="mb-1 text-gray-500">Tenure</div>
                  <div class="text-gray-900">{{ job.tenure_description }}</div>
                </div>
                <div v-if="job.reservation_breakdown?.length">
                  <div class="mb-1.5 text-gray-500">Reservation</div>
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="row in job.reservation_breakdown"
                      :key="row.name"
                      class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700"
                    >{{ row.category }} · {{ row.vacancy_count }}</span>
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>
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
import { Dropdown, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import GreenSheetPanel from '@/components/jobs/GreenSheetPanel.vue'
import JobOpeningForm, { emptyJobForm } from '@/components/jobs/JobOpeningForm.vue'
import ApplicationFormPanel from '@/components/jobs/ApplicationFormPanel.vue'
import { useStaffJobOpeningDetail } from '@/composables/useJobOpenings'
import { jobOpeningService } from '@/services/jobOpenings'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

const { job, loading, permissions, fetchJob, fetchPermissions } = useStaffJobOpeningDetail()

const moreActions = computed(() =>
  [
    permissions.value.can_write && { label: 'Change Status', icon: 'refresh-cw', onClick: openStatusDialog },
    permissions.value.can_delete && { label: 'Delete', icon: 'trash-2', onClick: () => (showDeleteConfirm.value = true) },
  ].filter(Boolean),
)

function plural(n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`
}

const BRAND_OUTLINE = '!border-brand-200 !bg-white !text-brand-700 hover:!bg-brand-50'

const FACT_THEMES = {
  brand: { card: 'border-brand-100 bg-brand-50/70', icon: 'bg-brand-100 text-brand-700' },
  green: { card: 'border-green-200 bg-green-50', icon: 'bg-green-100 text-green-700' },
  orange: { card: 'border-orange-200 bg-orange-50', icon: 'bg-orange-100 text-orange-700' },
  gray: { card: 'border-gray-200 bg-gray-50', icon: 'bg-gray-200 text-gray-600' },
  blue: { card: 'border-blue-200 bg-blue-50', icon: 'bg-blue-100 text-blue-700' },
}

const facts = computed(() => {
  const j = job.value
  const counts = j.application_counts || {}
  const total = Object.values(counts).reduce((sum, n) => sum + n, 0)
  const shortlisted = counts.Shortlisted || 0
  const reserved = (j.reservation_breakdown || []).map((r) => `${r.vacancy_count} ${r.category}`).join(' · ')

  let deadline = { value: 'Not set', hint: 'Set one before advertising', tone: 'text-orange-700', theme: 'orange' }
  if (j.application_deadline) {
    const close = dayjs(j.application_deadline)
    const days = close.startOf('day').diff(dayjs().startOf('day'), 'day')
    deadline = {
      value: close.format('DD MMM YYYY'),
      hint:
        days < 0
          ? `Closed ${plural(-days, 'day')} ago`
          : days === 0
            ? `Closes today at ${close.format('h:mm A')}`
            : `${plural(days, 'day')} left · ${close.format('h:mm A')}`,
      tone: days < 0 ? 'text-gray-600' : days <= 3 ? 'text-orange-700' : 'text-green-700',
      theme: days < 0 ? 'gray' : days <= 3 ? 'orange' : 'green',
    }
  }

  return [
    { label: 'Applications', icon: 'file-text', theme: 'brand', value: total, hint: total ? `${shortlisted} shortlisted` : 'None yet' },
    { label: 'Vacancies', icon: 'users', theme: 'brand', value: j.vacancies, hint: reserved || 'Unreserved' },
    { label: 'Applications close', icon: 'calendar', ...deadline },
    { label: 'Employment', icon: 'briefcase', theme: 'blue', value: j.employment_type || '—', hint: j.pay_level || 'Pay level not set' },
  ]
})

const positionRows = computed(() => {
  const j = job.value
  const p = j.position_detail || {}
  return [
    { label: 'Job Code', value: j.position, mono: true },
    { label: 'Designation', value: j.designation },
    { label: 'Department', value: j.department },
    { label: 'Track', value: j.track },
    { label: 'Reports To', value: p.reports_to },
    { label: 'Hiring Manager', value: p.hiring_manager_role?.replace(/^Pathways /, '') },
  ].filter((row) => row.value)
})

// The stored advertisement_url uses the host the job was saved from (the
// site name when saved outside a request); show the link for the host
// staff are actually using. Its presence still means the job is live.
const publicUrl = computed(() =>
  job.value?.advertisement_url ? `${window.location.origin}/pathways/portal/jobs/${job.value.name}` : '',
)

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
    await navigator.clipboard.writeText(publicUrl.value)
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
