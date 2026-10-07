<template>
  <StaffLayout>
    <PageHeader title="My Pending Approvals" />
    <div class="flex-1 overflow-y-auto p-6">
      <DataTable
        export-name="approvals"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        row-key="key"
        clickable
        @row-click="openReview"
        empty-title="Nothing pending your approval"
        search-placeholder="Search approvals..."
      >
        <template #cell-job_title="{ row }">
          <span class="font-medium text-gray-900">{{ row.job_title }}</span>
        </template>
        <template #cell-approver_label="{ row }">
          {{ row.approver_label }}
          <span v-if="row.is_override" class="ml-1 rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">
            on behalf (override)
          </span>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-2" @click.stop>
            <Button variant="ghost" icon-left="eye" @click="openReview(row)">View</Button>
            <Button variant="outline" @click="openDialog(row, 'Returned for Revision')">Return</Button>
            <Button variant="solid" :class="BTN_DARK" @click="openDialog(row, 'Approved')">Approve</Button>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Review: what the approver is signing off -->
    <Dialog v-model="reviewOpen" :options="{ size: '4xl' }">
      <template #body>
        <div class="flex max-h-[85vh] flex-col">
          <div class="flex items-start justify-between gap-4 border-b px-6 py-4">
            <div class="min-w-0">
              <div class="text-xs font-bold uppercase tracking-wide text-brand-700">{{ reviewItem?.doctype }}</div>
              <h2 class="mt-0.5 truncate text-xl font-semibold text-gray-900">{{ review?.job?.title || reviewItem?.job_title }}</h2>
              <p class="mt-0.5 text-sm text-gray-500">
                {{ reviewItem?.name }}
                <template v-if="review"> · Raised by {{ review.raised_by }} on {{ formatDate(review.raised_on) }}</template>
              </p>
            </div>
            <Button variant="ghost" icon="x" @click="reviewOpen = false" />
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div v-if="reviewLoading" class="py-10 text-center text-sm text-gray-500">Loading…</div>
            <ErrorMessage v-else-if="reviewError" :message="reviewError" />
            <div v-else-if="review" class="grid grid-cols-1 gap-6 lg:grid-cols-5">
              <div class="flex flex-col gap-6 lg:col-span-3">
                <section v-if="review.job">
                  <div class="mb-2 flex items-center justify-between">
                    <h3 class="text-xs font-bold uppercase tracking-wide text-brand-700">Job</h3>
                    <router-link :to="`/jobs/${review.job.name}`" class="text-xs font-medium text-brand-700 hover:underline">Open job page</router-link>
                  </div>
                  <dl class="grid grid-cols-2 gap-x-6 gap-y-3 rounded-lg border p-4 text-sm">
                    <div v-for="f in review.job.fields" :key="f.label">
                      <dt class="text-xs text-gray-500">{{ f.label }}</dt>
                      <dd class="text-gray-900">{{ f.value }}</dd>
                    </div>
                  </dl>
                </section>

                <section v-if="review.fields.length">
                  <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Details</h3>
                  <div class="flex flex-col gap-3 rounded-lg border p-4 text-sm">
                    <div v-for="f in review.fields" :key="f.label">
                      <div class="text-xs text-gray-500">{{ f.label }}</div>
                      <div v-if="f.html" class="prose prose-sm max-w-none text-gray-900" v-html="f.value" />
                      <div v-else class="text-gray-900">{{ f.value }}</div>
                    </div>
                  </div>
                </section>

                <section v-for="t in review.tables" :key="t.label">
                  <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">{{ t.label }}</h3>
                  <div class="overflow-x-auto rounded-lg border">
                    <table class="w-full text-sm">
                      <thead class="bg-gray-50 text-left text-xs text-gray-500">
                        <tr><th v-for="c in t.columns" :key="c" class="px-3 py-2 font-medium">{{ c }}</th></tr>
                      </thead>
                      <tbody>
                        <tr v-for="(r, i) in t.rows" :key="i" class="border-t">
                          <td v-for="(v, j) in r" :key="j" class="px-3 py-2 text-gray-900">{{ v }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>

                <section v-if="review.files.length">
                  <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Documents</h3>
                  <div class="flex flex-col gap-2">
                    <component
                      :is="f.url ? 'a' : 'div'"
                      v-for="f in review.files"
                      :key="f.label"
                      :href="f.url || undefined"
                      target="_blank"
                      class="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                      :class="f.url ? 'hover:border-brand-200 hover:bg-brand-50' : 'opacity-60'"
                    >
                      <span class="flex items-center gap-2 text-gray-800"><FeatherIcon name="paperclip" class="h-4 w-4 text-brand-700" />{{ f.label }}</span>
                      <span class="text-xs" :class="f.url ? 'text-brand-700' : 'text-gray-500'">{{ f.url ? 'Open' : 'Not attached' }}</span>
                    </component>
                  </div>
                </section>
              </div>

              <section class="lg:col-span-2">
                <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Approval chain</h3>
                <ol class="flex flex-col gap-2">
                  <li
                    v-for="step in review.chain.steps"
                    :key="step.sequence"
                    class="flex items-start gap-3 rounded-lg border px-3 py-2.5 text-sm"
                    :class="stepState(step) === 'current' ? 'border-brand-200 bg-brand-50' : ''"
                  >
                    <span
                      class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                      :class="{
                        'bg-green-100 text-green-700': stepState(step) === 'done',
                        'bg-brand-700 text-white': stepState(step) === 'current',
                        'bg-gray-100 text-gray-500': stepState(step) === 'waiting',
                      }"
                    >
                      <FeatherIcon v-if="stepState(step) === 'done'" name="check" class="h-3.5 w-3.5" />
                      <template v-else>{{ step.sequence }}</template>
                    </span>
                    <div class="min-w-0">
                      <div class="font-medium text-gray-900">{{ step.approver_label }}</div>
                      <div class="text-xs text-gray-500">{{ stepNote(step) }}</div>
                    </div>
                  </li>
                </ol>
              </section>
            </div>
          </div>

          <div class="flex justify-end gap-2 border-t px-6 py-3">
            <Button variant="outline" @click="openDialog(reviewItem, 'Returned for Revision')">Return</Button>
            <Button variant="solid" :class="BTN_DARK" @click="openDialog(reviewItem, 'Approved')">Approve</Button>
          </div>
        </div>
      </template>
    </Dialog>

    <Dialog v-model="dialogOpen" :options="{ title: dialogTitle }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <ErrorMessage :message="actionError" />
          <div
            v-if="selectedItem?.is_override"
            class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
          >
            You are recording this on behalf of {{ selectedItem.approver_label }}. It will be flagged as an override in the
            approval log.
          </div>
          <FormControl
            v-if="selectedItem?.is_override"
            type="select"
            label="How was it given?"
            v-model="channel"
            :options="['Signature', 'Email', 'Digital']"
          />
          <FormControl
            type="textarea"
            :label="selectedAction === 'Approved' ? 'Remarks (optional)' : 'Reason for returning (required)'"
            v-model="remarks"
            placeholder="Add any remarks or conditions"
          />
        </div>
      </template>
      <template #actions>
        <Button
          variant="solid"
          :loading="submitting"
          :disabled="selectedAction !== 'Approved' && !remarks.trim()"
          @click="confirmAction"
        >
          Confirm
        </Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dialog, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import { BTN_DARK } from '@/utils/buttonStyles'
import { approvalService } from '@/services/approvals'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import { usePendingApprovals } from '@/composables/useApprovals'

const { approvals, loading, fetchApprovals, act } = usePendingApprovals()

const columns = [
  { key: 'job_title', label: 'Job Opening' },
  { key: 'doctype', label: 'Type' },
  { key: 'name', label: 'Document' },
  { key: 'approver_label', label: 'Awaiting' },
]
const filters = [
  { key: 'doctype', label: 'Types' },
  { key: 'job_title', label: 'Job Openings' },
]
// A document name is only unique within its doctype.
const rows = computed(() =>
  approvals.value.map((a) => ({ ...a, job_title: a.job_title || a.job_opening, key: `${a.doctype}-${a.name}` })),
)

// ----- review dialog
const reviewOpen = ref(false)
const reviewItem = ref(null)
const review = ref(null)
const reviewLoading = ref(false)
const reviewError = ref('')

async function openReview(row) {
  reviewItem.value = row
  review.value = null
  reviewError.value = ''
  reviewOpen.value = true
  reviewLoading.value = true
  try {
    review.value = await approvalService.getApprovalDocument(row.doctype, row.name)
  } catch (e) {
    reviewError.value = e?.messages?.[0] || 'Could not load the document.'
  } finally {
    reviewLoading.value = false
  }
}

function stepLog(step) {
  return [...(review.value?.chain?.log || [])].reverse().find((l) => l.sequence === step.sequence)
}
function stepState(step) {
  if (step.completed) return 'done'
  return step.sequence === review.value?.chain?.current_level ? 'current' : 'waiting'
}
function stepNote(step) {
  const log = stepLog(step)
  if (step.completed && log) return `Approved by ${log.approver_name || log.approver} · ${formatDate(log.acted_on)}`
  if (stepState(step) === 'current') return 'Awaiting decision'
  return 'Waiting'
}
function formatDate(value) {
  if (!value) return ''
  return new Date(String(value).replace(' ', 'T')).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

const dialogOpen = ref(false)
const selectedItem = ref(null)
const selectedAction = ref(null)
const remarks = ref('')
const channel = ref('Digital')
const actionError = ref('')
const submitting = ref(false)

const dialogTitle = computed(() =>
  selectedAction.value === 'Approved' ? 'Approve' : 'Return for Revision',
)

function openDialog(item, action) {
  selectedItem.value = item
  selectedAction.value = action
  remarks.value = ''
  channel.value = item.is_override ? 'Signature' : 'Digital'
  actionError.value = ''
  dialogOpen.value = true
}

async function confirmAction() {
  if (!selectedItem.value) return
  submitting.value = true
  actionError.value = ''
  try {
    await act(selectedItem.value.doctype, selectedItem.value.name, selectedAction.value, remarks.value, channel.value)
    dialogOpen.value = false
    reviewOpen.value = false
    toast({
      title: selectedAction.value === 'Approved' ? 'Approved.' : 'Returned for revision.',
      icon: 'check',
      iconClasses: 'text-green-500',
    })
  } catch (e) {
    actionError.value = e?.messages?.[0] || 'Could not record the action.'
  } finally {
    submitting.value = false
  }
}

// The bell links here with ?open=<doctype>::<name> to review one record.
const route = useRoute()
const router = useRouter()
function openFromQuery() {
  const key = route.query.open
  if (!key || loading.value) return
  const [doctype, name] = String(key).split('::')
  const row = rows.value.find((r) => r.doctype === doctype && r.name === name) || { doctype, name, job_title: '' }
  openReview(row)
  router.replace({ query: {} })
}
watch(() => route.query.open, openFromQuery)

onMounted(async () => {
  await fetchApprovals()
  openFromQuery()
})
</script>
