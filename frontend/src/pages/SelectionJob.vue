<template>
  <StaffLayout>
    <PageHeader :title="info?.job_title || 'Selection'" back-to="/selection">
      <template v-if="info" #meta>
        <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-600">
          <span class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-700">{{ info.name }}</span>
          <span v-if="info.track">{{ info.track }}</span>
          <span v-if="info.employment_type">· {{ info.employment_type }}</span>
          <StatusBadge v-if="info.job_status" :status="info.job_status" />
          <RouterLink :to="`/jobs/${info.name}`" class="text-brand-700 hover:underline">Open job</RouterLink>
        </div>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50/60">
      <div v-if="error" class="m-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <template v-else>
        <!-- The four steps, in order; a tick when a step is done. -->
        <nav class="sticky top-0 z-10 border-b bg-white px-4 sm:px-6" aria-label="Selection steps">
          <ol class="flex gap-1 overflow-x-auto" role="tablist">
            <li v-for="(s, i) in STEPS" :key="s.key">
              <button
                type="button"
                role="tab"
                :aria-selected="tab === s.key"
                class="flex items-center gap-2 whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium transition"
                :class="tab === s.key ? 'border-brand-700 text-brand-800' : 'border-transparent text-gray-600 hover:text-gray-900'"
                @click="setTab(s.key)"
              >
                <span
                  class="flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold"
                  :class="info?.done?.[s.key] ? 'bg-green-100 text-green-700' : tab === s.key ? 'bg-brand-700 text-white' : 'bg-gray-100 text-gray-600'"
                >
                  <FeatherIcon v-if="info?.done?.[s.key]" name="check" class="h-3.5 w-3.5" />
                  <template v-else>{{ i + 1 }}</template>
                </span>
                {{ s.label }}
                <span v-if="badge(s.key)" class="rounded-full bg-orange-100 px-1.5 text-[11px] font-semibold text-orange-800">{{ badge(s.key) }}</span>
              </button>
            </li>
          </ol>
        </nav>

        <div class="p-4 sm:p-6">
          <p v-if="info && hint" class="mb-4 flex items-start gap-2 rounded-lg border border-brand-100 bg-brand-50/60 px-4 py-3 text-sm text-gray-700">
            <FeatherIcon name="info" class="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />{{ hint }}
          </p>

          <ConsolidatedScores v-if="tab === 'scores'" :job="job" embedded @changed="load" />

          <RegretsThanks v-else-if="tab === 'regrets'" :job="job" :job-title="info?.job_title || ''" @changed="load" />

          <template v-else-if="tab === 'green_sheet'">
            <SelectionPanel v-if="info" :job="{ name: info.name, track: info.track, employment_type: info.employment_type }" in-selection />
          </template>

          <section v-else-if="tab === 'offers'" class="overflow-hidden rounded-xl border bg-white shadow-sm">
            <div v-if="!info" class="h-40 animate-pulse" />
            <div v-else-if="!info.candidates_for_offer.length" class="p-8 text-center text-sm text-gray-500">
              Nobody is selected or waitlisted yet. Record the decisions on the Scores &amp; decision step first.
            </div>
            <table v-else class="w-full text-sm">
              <thead class="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                <tr>
                  <th class="px-4 py-3">Candidate</th>
                  <th class="px-4 py-3">Decision</th>
                  <th class="px-4 py-3">Application status</th>
                  <th class="px-4 py-3">Offer</th>
                  <th class="px-4 py-3" />
                </tr>
              </thead>
              <tbody class="divide-y">
                <tr v-for="c in info.candidates_for_offer" :key="c.application">
                  <td class="px-4 py-3">
                    <RouterLink :to="`/applications/${c.application}`" class="font-medium text-gray-900 hover:text-brand-700">{{ c.candidate_name }}</RouterLink>
                    <div class="font-mono text-xs text-gray-500">{{ c.application_id }}</div>
                  </td>
                  <td class="px-4 py-3">
                    <span class="rounded-full px-2 py-0.5 text-xs font-semibold" :class="c.outcome === 'Selected' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'">{{ c.outcome }}</span>
                  </td>
                  <td class="px-4 py-3"><StatusBadge :status="c.application_status" /></td>
                  <td class="px-4 py-3">
                    <template v-if="c.offer">
                      <StatusBadge :status="c.offer.status" />
                      <div v-if="c.offer.candidate_confirmed_doj" class="mt-0.5 text-xs text-gray-500">Joining {{ dayjs(c.offer.candidate_confirmed_doj).format('DD MMM YYYY') }}</div>
                    </template>
                    <span v-else class="text-xs text-gray-400">No offer yet</span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <!-- Opens the offer, or creates one once the green sheet is approved (else says why not). -->
                    <ApplicationOfferAction :application="c.application" />
                  </td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </template>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConsolidatedScores from '@/pages/ConsolidatedScores.vue'
import RegretsThanks from '@/components/selection/RegretsThanks.vue'
import SelectionPanel from '@/components/selection/SelectionPanel.vue'
import ApplicationOfferAction from '@/components/offers/ApplicationOfferAction.vue'
import { selectionService } from '@/services/selection'
import { STEPS } from '@/utils/selectionSteps'

const props = defineProps({ job: { type: String, required: true } })
const route = useRoute()
const router = useRouter()

const info = ref(null)
const error = ref('')

// The open step lives in the URL (?tab=), so links and Back land on it.
const tab = computed(() => (STEPS.some((s) => s.key === route.query.tab) ? route.query.tab : 'scores'))
function setTab(key) {
  router.replace({ query: { ...route.query, tab: key === 'scores' ? undefined : key } })
}

function badge(key) {
  const i = info.value
  if (!i) return 0
  if (key === 'scores') return i.undecided
  if (key === 'regrets') return i.regrets.pending + (i.thanks.committee ? i.thanks.pending : 0)
  return 0
}

const hint = computed(() => {
  const i = info.value
  switch (tab.value) {
    case 'scores':
      return 'Check each panellist has scored, then click Decide on each candidate: Select, Waitlist or Not selected. The application status follows the decision.'
    case 'regrets':
      return i?.undecided
        ? `${i.undecided} candidate(s) are not decided yet. Decide everyone first, so nobody waiting is missed by the regrets.`
        : 'Send the regret to everyone not selected, and thank the panel. Keep waitlisted candidates until the post is filled.'
    case 'green_sheet':
      return i?.outcomes?.Selected
        ? 'Raise the Selection Green Sheet from the decisions, attach the VC-signed panel recommendation and submit it for approval.'
        : 'Nobody is selected yet, so there is no green sheet to raise.'
    case 'offers':
      return 'Once the green sheet is approved, create the offer for each selected candidate. Review, signature and sending happen on the offer page.'
    default:
      return ''
  }
})

async function load() {
  error.value = ''
  try {
    info.value = await selectionService.getJob(props.job)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load this job.'
  }
}
watch(() => props.job, () => {
  info.value = null
  load()
}, { immediate: true })
</script>
