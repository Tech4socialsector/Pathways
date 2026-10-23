<template>
  <StaffLayout>
    <PageHeader title="Offers" subtitle="Appointment orders from draft through review, the Registrar's signature and the candidate's response.">
      <template #actions>
        <Button v-if="canCreate" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="createOpen = true">Create Offer</Button>
      </template>
    </PageHeader>
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <DataTable
        ref="table"
        toolbar-panel
        export-name="offers"
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filters="filters"
        clickable
        empty-title="No offers yet"
        search-placeholder="Search offers..."
        @row-click="(row) => router.push(`/offers/${row.name}`)"
      >
        <template #above-toolbar>
          <nav
            v-if="rows.length"
            class="-mx-1 flex gap-1 overflow-x-auto overflow-y-hidden shadow-[inset_0_-1px_0_theme(colors.gray.200)] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            aria-label="Filter by status"
          >
            <button
              v-for="t in statusTabs"
              :key="t.key"
              type="button"
              class="relative flex shrink-0 items-center gap-2 px-3 pb-3 pt-3 text-sm transition"
              :class="activeTab === t.key ? 'font-semibold text-brand-700' : 'text-gray-600 hover:text-gray-900'"
              :aria-current="activeTab === t.key ? 'true' : undefined"
              @click="table?.setFilter('stage', t.key === ALL ? [] : [t.key])"
            >
              <span v-if="t.dot" class="h-2 w-2 rounded-full" :class="t.dot" />
              {{ t.label }}
              <span
                class="rounded-full px-1.5 text-xs font-semibold"
                :class="activeTab === t.key ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'"
              >
                {{ t.count }}
              </span>
              <span v-if="activeTab === t.key" class="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-brand-700" />
            </button>
          </nav>
        </template>
        <template #cell-stage="{ value }"><StatusBadge :status="value" /></template>
      </DataTable>
    </div>
    <CreateOfferDialog v-model="createOpen" @created="(name) => router.push(`/offers/${name}`)" />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import CreateOfferDialog from '@/components/offers/CreateOfferDialog.vue'
import { offerService } from '@/services/offers'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { OFFER_STAGES, STAGE_DOTS } from '@/components/offers/offerStages'

const router = useRouter()
const table = ref(null)
const rows = ref([])
const loading = ref(false)
const canCreate = ref(false)
const createOpen = ref(false)

const fmt = (d) => (d ? dayjs(d).format('DD MMM YYYY') : '')
const columns = [
  { key: 'candidate_name', label: 'Candidate' },
  { key: 'application_id', label: 'Application' },
  { key: 'job_title', label: 'Job' },
  { key: 'designation', label: 'Designation' },
  { key: 'stage', label: 'Status' },
  { key: 'proposed_doj', label: 'Proposed DOJ', format: (r) => fmt(r.proposed_doj) },
  { key: 'acceptance_deadline', label: 'Respond By', format: (r) => fmt(r.acceptance_deadline) },
]
const filters = [
  { key: 'stage', label: 'Statuses' },
  { key: 'job_title', label: 'Jobs' },
  { key: 'designation', label: 'Designations' },
]

const ALL = '__all__'
const statusTabs = computed(() => {
  const counts = {}
  for (const r of rows.value) counts[r.stage] = (counts[r.stage] || 0) + 1
  return [
    { key: ALL, label: 'All', count: rows.value.length },
    ...OFFER_STAGES.filter((s) => counts[s]).map((s) => ({ key: s, label: s, count: counts[s], dot: STAGE_DOTS[s] })),
  ]
})
const activeTab = computed(() => {
  const chosen = table.value?.filterValues?.stage || []
  if (!chosen.length) return ALL
  return chosen.length === 1 ? chosen[0] : null
})

async function load() {
  loading.value = true
  try {
    const res = await offerService.getOffers()
    rows.value = res.offers || []
    canCreate.value = !!res.can_create
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not load offers.', icon: 'alert-triangle' })
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
