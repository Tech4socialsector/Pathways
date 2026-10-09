<template>
  <StaffLayout>
    <PageHeader
      title="Interview Panel"
      :subtitle="data?.can_manage && !data?.is_panellist
        ? 'Final interviews and how far each panel has got with scoring.'
        : 'Your final interviews. Score each candidate on the Interview Assessment Form.'"
    />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div v-if="loading && !data" class="grid gap-3">
        <div v-for="i in 3" :key="i" class="h-24 animate-pulse rounded-xl border bg-white" />
      </div>
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <template v-else-if="data">
        <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <div v-for="t in tiles" :key="t.label" class="rounded-xl border bg-white p-4 shadow-sm">
            <div class="text-2xl font-bold tabular-nums" :class="t.tone || 'text-gray-900'">{{ t.value }}</div>
            <div class="mt-0.5 text-xs text-gray-500">{{ t.label }}</div>
          </div>
        </div>

        <div class="mb-4 flex flex-wrap items-center gap-2">
          <div class="flex rounded-lg bg-gray-100 p-1 text-sm" role="group" aria-label="Show">
            <button
              v-for="f in FILTERS"
              :key="f.key"
              type="button"
              class="rounded-md px-3 py-1"
              :class="filter === f.key ? 'bg-white font-semibold text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'"
              :aria-pressed="filter === f.key"
              @click="filter = f.key"
            >
              {{ f.label }}
            </button>
          </div>
          <div v-if="groups.length > 1" class="flex items-center gap-1">
            <Button size="sm" variant="ghost" icon-left="chevrons-down" @click="setAll(false)">Expand all</Button>
            <Button size="sm" variant="ghost" icon-left="chevrons-up" @click="setAll(true)">Collapse all</Button>
          </div>
          <input
            v-model="search"
            type="search"
            class="ml-auto w-64 rounded-md border-gray-300 text-sm focus:border-brand-700 focus:ring-brand-700"
            placeholder="Search candidate or job…"
            aria-label="Search"
          />
        </div>

        <div v-if="!groups.length" class="rounded-xl border border-dashed bg-white px-6 py-12 text-center text-sm text-gray-500">
          <FeatherIcon name="clipboard" class="mx-auto mb-2 h-6 w-6 text-gray-300" />
          <template v-if="!data.interviews.length">
            No final interviews yet. They appear here once the recruitment team schedules them for a committee you sit on.
          </template>
          <template v-else>Nothing matches.</template>
        </div>

        <section v-for="g in groups" :key="g.job_opening" class="mb-4 overflow-hidden rounded-xl border bg-white shadow-sm">
          <!-- Header: click to fold the job's candidates away -->
          <header class="flex flex-wrap items-center gap-3 bg-gray-50/70 px-4 py-3" :class="!isCollapsed(g) && 'border-b'">
            <button
              type="button"
              class="flex min-w-0 flex-1 items-center gap-3 text-left"
              :aria-expanded="!isCollapsed(g)"
              :aria-controls="`panel-${g.job_opening}`"
              @click="toggle(g)"
            >
              <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-gray-500 transition hover:bg-gray-200/70">
                <FeatherIcon name="chevron-right" class="h-4 w-4 transition-transform" :class="!isCollapsed(g) && 'rotate-90'" />
              </span>
              <span class="min-w-0">
                <span class="block truncate font-semibold text-gray-900">{{ g.job_title }}</span>
                <span class="block text-xs text-gray-500">
                  {{ g.rows.length }} candidate{{ g.rows.length === 1 ? '' : 's' }}
                  <template v-if="g.panelTotal"> · {{ g.fullyScored }} of {{ g.rows.length }} fully scored</template>
                </span>
              </span>
            </button>
            <div class="flex shrink-0 items-center gap-2">
              <span v-if="g.toScore" class="rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-medium text-orange-700">{{ g.toScore }} to score</span>
              <span v-else-if="g.anyMine" class="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">All scored</span>
              <Button v-if="g.anyMine" size="sm" variant="outline" icon-left="printer" @click="printMine(g)">My form (PDF)</Button>
              <Button size="sm" variant="outline" icon-left="grid" @click="router.push(`/panel/sheet/${g.job_opening}`)">Score sheet</Button>
            </div>
          </header>

          <div v-show="!isCollapsed(g)" :id="`panel-${g.job_opening}`" class="overflow-x-auto">
            <table class="w-full min-w-[760px] text-sm">
              <thead class="bg-white text-left text-xs uppercase tracking-wide text-gray-500">
                <tr class="border-b">
                  <th class="px-4 py-2.5 font-medium">Interview</th>
                  <th class="px-4 py-2.5 font-medium">Candidate</th>
                  <th class="px-4 py-2.5 font-medium">Mode</th>
                  <th class="px-4 py-2.5 font-medium">Panel progress</th>
                  <th v-if="g.anyMine" class="px-4 py-2.5 font-medium">Your score</th>
                  <th class="px-4 py-2.5 text-right font-medium"><span class="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody class="divide-y">
                <tr
                  v-for="iv in g.rows"
                  :key="iv.name"
                  class="cursor-pointer transition hover:bg-gray-50"
                  @click="router.push(`/panel/${iv.name}`)"
                >
                  <td class="whitespace-nowrap px-4 py-3">
                    <div class="font-medium text-gray-900">{{ dayjs(iv.scheduled_datetime).format('ddd, DD MMM') }}</div>
                    <div class="text-xs text-gray-500">{{ dayjs(iv.scheduled_datetime).format('h:mm A') }}</div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="font-medium text-gray-900">{{ iv.candidate_name }}</div>
                    <div class="font-mono text-xs text-gray-500">{{ iv.application_id }}</div>
                  </td>
                  <td class="px-4 py-3 text-gray-700">
                    <span class="inline-flex items-center gap-1.5">
                      <FeatherIcon :name="iv.mode === 'In-Person' ? 'map-pin' : 'video'" class="h-3.5 w-3.5 text-gray-400" />
                      {{ iv.mode === 'In-Person' ? iv.location || 'In person' : iv.meeting_platform || 'Online' }}
                    </span>
                  </td>
                  <td class="w-48 px-4 py-3 text-xs text-gray-600">
                    <template v-if="iv.scores?.panel_size">
                      <div class="tabular-nums">{{ iv.scores.scored }} of {{ iv.scores.panel_size }} scored</div>
                      <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-gray-100">
                        <div class="h-full rounded-full bg-brand-700" :style="{ width: `${Math.min(100, (iv.scores.scored / iv.scores.panel_size) * 100)}%` }" />
                      </div>
                      <div v-if="data.can_manage && iv.scores.scored" class="mt-1 tabular-nums">Avg {{ iv.scores.average }} / {{ iv.scores.max_score }}</div>
                    </template>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <td v-if="g.anyMine" class="px-4 py-3">
                    <span
                      v-if="iv.is_panellist && iv.my_score"
                      class="inline-flex items-center gap-1 whitespace-nowrap rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700"
                    >
                      <FeatherIcon name="check" class="h-3 w-3" />
                      {{ fmt(iv.my_score.total_score) }} / {{ fmt(iv.my_score.max_score) }}<template v-if="iv.my_score.verdict"> · {{ iv.my_score.verdict }}</template>
                    </span>
                    <span v-else-if="iv.is_panellist" class="whitespace-nowrap rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-medium text-orange-700">Not scored yet</span>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <td class="whitespace-nowrap px-4 py-3 text-right" @click.stop>
                    <div class="flex items-center justify-end gap-2">
                      <a v-if="iv.meeting_link && isUpcoming(iv)" :href="iv.meeting_link" target="_blank" rel="noopener">
                        <Button size="sm" variant="outline" icon-left="video">Join</Button>
                      </a>
                      <Button
                        size="sm"
                        :variant="iv.is_panellist && !iv.my_score ? 'solid' : 'outline'"
                        :class="iv.is_panellist && !iv.my_score ? BTN_BRAND : ''"
                        :icon-left="iv.is_panellist || data.can_manage ? 'edit-3' : 'eye'"
                        @click="router.push(`/panel/${iv.name}`)"
                      >
                        {{ iv.is_panellist ? (iv.my_score ? 'Edit score' : 'Score') : data.can_manage ? 'Enter scores' : 'View' }}
                      </Button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { panelService } from '@/services/panel'
import { BTN_BRAND } from '@/utils/buttonStyles'

const router = useRouter()
const data = ref(null)
const loading = ref(false)
const error = ref('')
const search = ref('')
const filter = ref('all')
const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'to_score', label: 'To score' },
  { key: 'scored', label: 'Scored' },
  { key: 'today', label: 'Today' },
]

const fmt = (n) => Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })
const isUpcoming = (iv) => ['Scheduled', 'Rescheduled'].includes(iv.status) && dayjs(iv.scheduled_datetime).add(3, 'hour').isAfter(dayjs())
const toScore = (iv) => iv.is_panellist && !iv.my_score

const rows = computed(() => data.value?.interviews || [])
const tiles = computed(() => {
  const list = rows.value
  const mine = list.filter((iv) => iv.is_panellist)
  const out = [
    { label: 'Final interviews', value: list.length },
    { label: 'Today', value: list.filter((iv) => dayjs(iv.scheduled_datetime).isSame(dayjs(), 'day')).length },
  ]
  if (mine.length) {
    out.push({ label: 'To score', value: mine.filter(toScore).length, tone: mine.some(toScore) ? 'text-orange-700' : '' })
    out.push({ label: 'Scored by you', value: mine.filter((iv) => iv.my_score).length, tone: 'text-green-700' })
  } else {
    out.push({ label: 'Fully scored', value: list.filter((iv) => iv.scores?.panel_size && iv.scores.scored >= iv.scores.panel_size).length, tone: 'text-green-700' })
    out.push({ label: 'Awaiting scores', value: list.filter((iv) => (iv.scores?.scored || 0) < (iv.scores?.panel_size || 0)).length, tone: 'text-orange-700' })
  }
  return out
})

const groups = computed(() => {
  const q = search.value.trim().toLowerCase()
  const map = new Map()
  for (const iv of rows.value) {
    if (filter.value === 'to_score' && !toScore(iv)) continue
    if (filter.value === 'scored' && !(iv.my_score || (!iv.is_panellist && iv.scores?.scored))) continue
    if (filter.value === 'today' && !dayjs(iv.scheduled_datetime).isSame(dayjs(), 'day')) continue
    if (q && ![iv.candidate_name, iv.application_id, iv.job_title].some((v) => (v || '').toLowerCase().includes(q))) continue
    if (!map.has(iv.job_opening)) map.set(iv.job_opening, { job_opening: iv.job_opening, job_title: iv.job_title, rows: [] })
    map.get(iv.job_opening).rows.push(iv)
  }
  return [...map.values()].map((g) => ({
    ...g,
    toScore: g.rows.filter(toScore).length,
    anyMine: g.rows.some((iv) => iv.is_panellist),
    panelTotal: g.rows.some((iv) => iv.scores?.panel_size),
    fullyScored: g.rows.filter((iv) => iv.scores?.panel_size && iv.scores.scored >= iv.scores.panel_size).length,
  }))
})

// Folded job groups, remembered in this browser (all open by default).
const COLLAPSE_KEY = 'pathways-panel-collapsed'
function readCollapsed() {
  try {
    return new Set(JSON.parse(localStorage.getItem(COLLAPSE_KEY) || '[]'))
  } catch {
    return new Set()
  }
}
const collapsed = ref(readCollapsed())
function persistCollapsed() {
  try {
    localStorage.setItem(COLLAPSE_KEY, JSON.stringify([...collapsed.value]))
  } catch {
    // storage unavailable: the choice lasts for this visit only
  }
}
// While searching every group shows its matches; folds return when cleared.
const isCollapsed = (g) => !search.value.trim() && collapsed.value.has(g.job_opening)
function toggle(g) {
  const next = new Set(collapsed.value)
  next.has(g.job_opening) ? next.delete(g.job_opening) : next.add(g.job_opening)
  collapsed.value = next
  persistCollapsed()
}
function setAll(fold) {
  collapsed.value = fold ? new Set(groups.value.map((g) => g.job_opening)) : new Set()
  persistCollapsed()
}

async function printMine(g) {
  try {
    await panelService.downloadForms(g.job_opening, g.job_title)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not create your form.'
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await panelService.getMyPanel()
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load your interviews.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>
