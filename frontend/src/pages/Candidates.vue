<template>
  <StaffLayout>
    <PageHeader title="Candidate Master" subtitle="Everyone who has applied. Open a candidate to see all of their applications." />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <MatchingNote class="mb-4" />
      <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div v-for="t in tiles" :key="t.label" class="rounded-xl border bg-white p-4 shadow-sm">
          <div class="text-2xl font-bold tabular-nums text-gray-900">{{ t.value }}</div>
          <div class="mt-0.5 text-xs text-gray-500">{{ t.label }}</div>
        </div>
      </div>
      <DataTable
        export-name="candidates"
        :columns="columns"
        :extra-columns="extraColumns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No candidates yet"
        search-placeholder="Search name, email, mobile or candidate ID…"
        @row-click="(r) => router.push(`/candidates/${r.name}`)"
      >
        <template #cell-full_name="{ row }">
          <div class="font-medium text-gray-900">{{ row.full_name }}</div>
          <div class="text-xs text-gray-500">{{ row.email }}</div>
        </template>
        <template #cell-name="{ value }">
          <span class="font-mono text-xs text-gray-700">{{ value }}</span>
        </template>
        <template #cell-applications="{ row }">
          <span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700">{{ row.applications }}</span>
          <span v-if="row.active && row.active !== row.applications" class="ml-1 text-xs text-gray-500">{{ row.active }} active</span>
        </template>
        <template #cell-latest_status="{ row }">
          <StatusBadge v-if="row.latest_status" :status="row.latest_status" />
          <div v-if="row.latest_job" class="mt-0.5 max-w-[16rem] truncate text-xs text-gray-500">{{ row.latest_job }}</div>
        </template>
        <template #cell-mobile_number="{ row }">
          {{ row.mobile_number }}
          <span v-if="row.same_mobile" class="ml-1 rounded bg-amber-50 px-1.5 py-0.5 text-[11px] font-medium text-amber-700" title="Another candidate has the same mobile number">same mobile</span>
        </template>
      </DataTable>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MatchingNote from '@/components/candidates/MatchingNote.vue'
import { candidateService } from '@/services/candidates'
import { toast } from '@/utils/notify'

const router = useRouter()
const rows = ref([])
const loading = ref(false)

const columns = [
  { key: 'name', label: 'Candidate ID' },
  { key: 'full_name', label: 'Name' },
  { key: 'mobile_number', label: 'Mobile' },
  { key: 'applications', label: 'Applications', align: 'center' },
  { key: 'latest_status', label: 'Latest Application' },
  { key: 'creation', label: 'First Applied', format: (r) => (r.creation ? dayjs(r.creation).format('DD MMM YYYY') : '') },
]
const extraColumns = [
  { key: 'email', label: 'Email' },
  { key: 'gender', label: 'Gender' },
  { key: 'category', label: 'Category' },
  { key: 'date_of_birth', label: 'Date of Birth', format: (r) => (r.date_of_birth ? dayjs(r.date_of_birth).format('DD MMM YYYY') : '') },
  { key: 'tracks', label: 'Tracks' },
  { key: 'portal_account', label: 'Portal Account' },
]
const filters = [
  { key: 'latest_status', label: 'Latest Status' },
  { key: 'tracks', label: 'Tracks' },
  { key: 'gender', label: 'Gender' },
  { key: 'category', label: 'Category' },
  { key: 'portal_account', label: 'Portal Account' },
]

const tiles = computed(() => [
  { label: 'Candidates', value: rows.value.length },
  { label: 'Applied more than once', value: rows.value.filter((r) => r.applications > 1).length },
  { label: 'With an active application', value: rows.value.filter((r) => r.active).length },
  { label: 'Share a mobile number', value: rows.value.filter((r) => r.same_mobile).length },
])

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await candidateService.list()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not load candidates.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    loading.value = false
  }
})
</script>
