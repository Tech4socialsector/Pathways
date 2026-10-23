<template>
  <StaffLayout>
    <PageHeader title="Selection" subtitle="After the final interviews: decide, send regrets and thanks, raise the selection green sheet and make the offer." />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-4 sm:p-6">
      <div v-if="loading && !rows.length" class="h-64 animate-pulse rounded-xl border bg-white" />
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <EmptyState
        v-else-if="!rows.length"
        title="No final interviews yet"
        description="Jobs appear here once their final interviews are scheduled (Job page > Interviews > Schedule Final)."
      />
      <template v-else>
        <div class="mb-4 flex flex-wrap items-center gap-2">
          <div class="w-full sm:w-72">
            <TextInput v-model="search" type="text" placeholder="Search jobs" aria-label="Search jobs">
              <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
            </TextInput>
          </div>
          <div class="flex items-center gap-1 rounded-lg border bg-white p-1 text-sm" role="tablist" aria-label="Filter by progress">
            <button
              v-for="t in TABS"
              :key="t.value"
              type="button"
              role="tab"
              :aria-selected="tab === t.value"
              class="rounded-md px-3 py-1 font-medium transition"
              :class="tab === t.value ? 'bg-brand-700 text-white' : 'text-gray-600 hover:bg-gray-100'"
              @click="tab = t.value"
            >
              {{ t.label }} <span class="ml-1 text-xs opacity-80">{{ counts[t.value] }}</span>
            </button>
          </div>
        </div>

        <div class="overflow-x-auto rounded-xl border bg-white shadow-sm">
          <table class="w-full min-w-[900px] text-sm">
            <thead class="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              <tr>
                <th class="px-4 py-3">Job</th>
                <th class="px-3 py-3 text-center">Scored</th>
                <th class="px-3 py-3 text-center">Decisions</th>
                <th class="px-3 py-3 text-center">Regrets</th>
                <th class="px-3 py-3 text-center">Panel thanks</th>
                <th class="px-3 py-3">Green sheet</th>
                <th class="px-3 py-3">Offers</th>
                <th class="px-4 py-3">Next step</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="r in shown" :key="r.name" class="cursor-pointer transition hover:bg-gray-50" @click="open(r)">
                <td class="px-4 py-3">
                  <RouterLink :to="`/selection/${r.name}`" class="font-medium text-gray-900 hover:text-brand-700" @click.stop>{{ r.job_title }}</RouterLink>
                  <div class="text-xs text-gray-500">{{ [r.position, r.track, r.employment_type].filter(Boolean).join(' · ') }}</div>
                </td>
                <td class="px-3 py-3 text-center tabular-nums">{{ r.fully_scored }}/{{ r.candidates }}</td>
                <td class="px-3 py-3 text-center">
                  <div class="flex flex-wrap justify-center gap-1 text-[11px] font-medium">
                    <span v-if="r.outcomes.Selected" class="rounded-full bg-green-100 px-2 py-0.5 text-green-800">{{ r.outcomes.Selected }} selected</span>
                    <span v-if="r.outcomes.Waitlisted" class="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">{{ r.outcomes.Waitlisted }} waitlist</span>
                    <span v-if="r.outcomes['Not Selected']" class="rounded-full bg-gray-100 px-2 py-0.5 text-gray-600">{{ r.outcomes['Not Selected'] }} not sel.</span>
                    <span v-if="r.undecided" class="rounded-full border border-dashed border-brand-300 px-2 py-0.5 text-brand-700">{{ r.undecided }} to decide</span>
                  </div>
                </td>
                <td class="px-3 py-3 text-center text-xs">
                  <span v-if="r.regrets.pending" class="font-medium text-orange-700">{{ r.regrets.pending }} to send</span>
                  <span v-else-if="r.regrets.sent" class="text-green-700">✓ {{ r.regrets.sent }} sent</span>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="px-3 py-3 text-center text-xs">
                  <span v-if="!r.thanks.committee" class="text-gray-400">—</span>
                  <span v-else-if="r.thanks.pending" class="font-medium text-orange-700">{{ r.thanks.pending }} of {{ r.thanks.panel_size }} to thank</span>
                  <span v-else class="text-green-700">✓ thanked</span>
                </td>
                <td class="px-3 py-3"><StatusBadge v-if="r.green_sheet" :status="r.green_sheet.status" /><span v-else class="text-xs text-gray-400">Not raised</span></td>
                <td class="px-3 py-3 text-xs">
                  <template v-if="r.offers.total">
                    {{ r.offers.total }} made<template v-if="r.offers.Accepted"> · {{ r.offers.Accepted }} accepted</template>
                  </template>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="px-4 py-3">
                  <span v-if="r.next_step" class="inline-flex items-center gap-1 text-xs font-medium text-brand-700">
                    {{ STEP_LABEL[r.next_step] }} <FeatherIcon name="arrow-right" class="h-3 w-3" />
                  </span>
                  <span v-else class="text-xs font-medium text-green-700">✓ Complete</span>
                </td>
              </tr>
              <tr v-if="!shown.length">
                <td colspan="8" class="px-4 py-10 text-center text-sm text-gray-500">No jobs match.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { FeatherIcon, TextInput } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { selectionService } from '@/services/selection'
import { STEP_LABEL } from '@/utils/selectionSteps'

const router = useRouter()
const rows = ref([])
const loading = ref(false)
const error = ref('')
const search = ref('')
const tab = ref('open')
const TABS = [
  { value: 'open', label: 'In progress' },
  { value: 'done', label: 'Complete' },
  { value: 'all', label: 'All' },
]

const counts = computed(() => ({
  open: rows.value.filter((r) => r.next_step).length,
  done: rows.value.filter((r) => !r.next_step).length,
  all: rows.value.length,
}))
const shown = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter(
    (r) =>
      (tab.value === 'all' || (tab.value === 'open' ? r.next_step : !r.next_step)) &&
      (!q || [r.job_title, r.position, r.track, r.name].some((v) => String(v || '').toLowerCase().includes(q))),
  )
})

function open(r) {
  router.push({ path: `/selection/${r.name}`, query: r.next_step ? { tab: r.next_step } : {} })
}

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await selectionService.listJobs()
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load the selection list.'
  } finally {
    loading.value = false
  }
})
</script>
