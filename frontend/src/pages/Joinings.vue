<template>
  <StaffLayout>
    <PageHeader title="Joinings" subtitle="New joiners: finalise the date of joining, tell IT & Facilities, and mark them joined" />
    <div class="flex-1 overflow-y-auto p-6">
      <!-- Offers accepted before onboarding started automatically -->
      <div v-if="pending.length" class="mb-5 rounded-xl border border-orange-200 bg-orange-50 p-4">
        <div class="mb-2 flex items-center gap-2 text-sm font-semibold text-orange-900">
          <FeatherIcon name="alert-circle" class="h-4 w-4" />
          {{ pending.length }} accepted offer(s) without a joining
        </div>
        <p class="mb-3 text-xs text-orange-800">Starting onboarding creates the joining and the document checklist, and emails the onboarding instructions to the candidate.</p>
        <div class="flex flex-col gap-2">
          <div v-for="p in pending" :key="p.offer" class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white px-3 py-2 text-sm">
            <span>
              <b>{{ p.candidate_name }}</b> <span class="font-mono text-xs text-gray-500">{{ p.application_id }}</span>
              <span v-if="p.candidate_confirmed_doj" class="text-gray-600"> · DOJ {{ formatDay(p.candidate_confirmed_doj) }}</span>
            </span>
            <Button size="sm" variant="solid" :class="BTN_BRAND" :loading="starting === p.offer" @click="start(p)">Start onboarding</Button>
          </div>
        </div>
      </div>

      <div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div v-for="card in cards" :key="card.label" class="rounded-lg border bg-white px-4 py-3">
          <div class="text-xs text-gray-500">{{ card.label }}</div>
          <div class="text-xl font-semibold text-gray-900">{{ card.value }}</div>
        </div>
      </div>

      <DataTable
        export-name="joinings"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No joinings yet"
        search-placeholder="Search name, application or designation..."
        @row-click="(row) => $router.push(`/joinings/${row.name}`)"
      >
        <template #cell-candidate_name="{ row }">
          <div class="font-medium text-gray-900">{{ row.candidate_name }}</div>
          <div class="font-mono text-xs text-gray-500">{{ row.application_id }}</div>
        </template>
        <template #cell-confirmed_doj="{ row }">
          <span>{{ formatDay(row.confirmed_doj) }}</span>
          <span v-if="row.reschedule_count" class="ml-1 rounded bg-orange-50 px-1 text-[11px] text-orange-700" :title="`Rescheduled ${row.reschedule_count} time(s)`">rescheduled</span>
        </template>
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template #cell-document_status="{ value }"><StatusBadge :status="value" /></template>
        <template #cell-it_status="{ value }"><StatusBadge v-if="value" :status="value" /><span v-else class="text-xs text-gray-400">Not sent</span></template>
      </DataTable>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { Button, FeatherIcon } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { joiningService } from '@/services/joining'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const rows = ref([])
const pending = ref([])
const loading = ref(false)
const starting = ref('')

const formatDay = (value) => (value ? dayjs(value).format('DD MMM YYYY') : '')

const columns = [
  { key: 'candidate_name', label: 'New Joiner', format: (r) => `${r.candidate_name || ''} ${r.application_id || ''}` },
  { key: 'designation', label: 'Designation' },
  { key: 'department', label: 'Department' },
  { key: 'confirmed_doj', label: 'Date of Joining', format: (r) => formatDay(r.confirmed_doj) },
  { key: 'status', label: 'Status' },
  { key: 'document_status', label: 'Documents' },
  { key: 'it_status', label: 'IT & Facilities' },
]
const filters = [
  { key: 'status', label: 'Statuses' },
  { key: 'department', label: 'Departments' },
  { key: 'document_status', label: 'Documents' },
]

const cards = computed(() => {
  const upcoming = rows.value.filter((r) => r.status === 'Confirmed' && r.confirmed_doj && !dayjs(r.confirmed_doj).isBefore(dayjs(), 'day'))
  return [
    { label: 'To confirm', value: rows.value.filter((r) => r.status === 'Draft').length },
    { label: 'Confirmed, upcoming', value: upcoming.length },
    { label: 'Joined this month', value: rows.value.filter((r) => r.status === 'Joined' && dayjs(r.confirmed_doj).isSame(dayjs(), 'month')).length },
    { label: 'No-show', value: rows.value.filter((r) => r.status === 'No-show').length },
  ]
})

async function load() {
  loading.value = true
  try {
    const res = await joiningService.listJoinings()
    rows.value = res.joinings || []
    pending.value = res.pending_offers || []
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not load joinings.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    loading.value = false
  }
}

async function start(p) {
  starting.value = p.offer
  try {
    await joiningService.startOnboarding(p.offer)
    toast({ title: `Onboarding started for ${p.candidate_name}.`, icon: 'check', iconClasses: 'text-green-500' })
    await load()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not start onboarding.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    starting.value = ''
  }
}

onMounted(load)
</script>
