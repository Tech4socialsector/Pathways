<template>
  <StaffLayout>
    <PageHeader :title="data ? `Consolidated Score Sheet` : 'Consolidated Score Sheet'" back-to="/panel">
      <template v-if="data" #meta>
        <span class="text-sm text-gray-500">
          {{ data.job.job_title }}<template v-if="data.job.position"> · {{ data.job.position }}</template><template v-if="data.interview_dates.length === 1"> · Interview {{ dayjs(data.interview_dates[0]).format('DD MMM YYYY') }}</template>
        </span>
      </template>
      <template v-if="data" #actions>
        <Dropdown :options="formMenu">
          <Button variant="outline" icon-left="printer" icon-right="chevron-down" :loading="printing">Assessment forms (PDF)</Button>
        </Dropdown>
        <Button variant="outline" icon-left="download" :loading="exporting" @click="exportSheet">Download Excel</Button>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div v-if="loading && !data" class="h-80 animate-pulse rounded-xl border bg-white" />
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <template v-else-if="data">
        <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-5">
          <div v-for="t in tiles" :key="t.label" class="rounded-xl border bg-white p-4 shadow-sm">
            <div class="text-2xl font-bold tabular-nums" :class="t.tone || 'text-gray-900'">{{ t.value }}</div>
            <div class="mt-0.5 text-xs text-gray-500">{{ t.label }}</div>
          </div>
        </div>

        <!-- Filters: which position's sheet, which interview day, and the panel -->
        <section class="mb-4 overflow-hidden rounded-xl border bg-white shadow-sm" aria-label="Score sheet filters">
          <div class="grid grid-cols-1 gap-5 p-4 lg:grid-cols-[minmax(0,1fr)_auto]">
            <!-- Position: each job opening has its own panel and rubric, so this opens that job's sheet -->
            <div class="min-w-0">
              <label for="sheet-position" class="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Position
                <span v-if="jobOptions.length > 1" class="rounded-full bg-gray-100 px-1.5 py-px text-[11px] font-medium normal-case tracking-normal text-gray-600">
                  {{ jobOptions.length }} with final interviews
                </span>
              </label>
              <div class="relative">
                <FeatherIcon name="briefcase" class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-700" />
                <select
                  id="sheet-position"
                  :value="job"
                  :disabled="jobOptions.length < 2"
                  class="h-10 w-full truncate rounded-lg border-gray-300 bg-white pl-9 pr-9 text-sm font-medium text-gray-900 shadow-sm focus:border-brand-500 focus:ring-brand-500 disabled:cursor-default disabled:bg-gray-50 disabled:opacity-100"
                  @change="router.push(`/panel/sheet/${$event.target.value}`)"
                >
                  <option v-for="j in jobOptions" :key="j.name" :value="j.name">{{ j.label }} · {{ j.count }} candidate{{ j.count === 1 ? '' : 's' }}</option>
                </select>
              </div>
              <p v-if="jobOptions.length < 2" class="mt-1 text-xs text-gray-500">The only position with final interviews.</p>
            </div>

            <!-- Interview day: the sheet, the Excel and the PDF forms follow it -->
            <div class="min-w-0">
              <span class="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">Interview date</span>
              <div class="flex flex-wrap items-center gap-2">
                <div class="flex flex-wrap rounded-lg bg-gray-100 p-1 text-sm" role="group" aria-label="Interview date">
                  <button
                    v-for="d in dateOptions"
                    :key="d.value"
                    type="button"
                    class="flex items-center gap-1.5 rounded-md px-3 py-1.5"
                    :class="date === d.value ? 'bg-white font-semibold text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'"
                    :aria-pressed="date === d.value"
                    @click="date = d.value"
                  >
                    {{ d.label }}
                    <span class="rounded-full px-1.5 text-[11px] tabular-nums" :class="date === d.value ? 'bg-brand-50 text-brand-700' : 'bg-white/70 text-gray-500'">{{ d.count }}</span>
                  </button>
                </div>
                <span class="text-sm text-gray-400">or</span>
                <input
                  v-model="date"
                  type="date"
                  class="h-9 rounded-lg border-gray-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
                  aria-label="Pick an interview date"
                />
                <Button v-if="date" size="sm" variant="ghost" icon-left="x" @click="date = ''">Clear</Button>
              </div>
            </div>
          </div>

          <p v-if="date" class="flex items-center gap-2 border-t bg-brand-50/50 px-4 py-2 text-xs text-brand-800">
            <FeatherIcon name="filter" class="h-3.5 w-3.5" />
            Showing and downloading only the candidates interviewed on {{ dayjs(date).format('DD MMM YYYY') }}.
          </p>

          <!-- Panel and scoring rule -->
          <div class="flex flex-wrap items-center gap-x-4 gap-y-2 border-t bg-gray-50/60 px-4 py-2.5 text-xs text-gray-600">
            <div class="flex min-w-0 flex-wrap items-center gap-1.5">
              <span class="font-medium text-gray-500">Panel</span>
              <span
                v-for="p in data.panel"
                :key="p.user"
                class="inline-flex items-center gap-1.5 rounded-full bg-white py-0.5 pl-0.5 pr-2.5 text-gray-800 ring-1 ring-inset ring-gray-200"
              >
                <span class="flex h-5 w-5 items-center justify-center rounded-full bg-brand-50 text-[10px] font-semibold text-brand-700">{{ initials(p.full_name) }}</span>
                {{ p.full_name }}
              </span>
              <span v-if="!data.panel.length" class="text-orange-700">no Selection Committee yet</span>
            </div>
            <span class="hidden h-4 w-px bg-gray-300 sm:block" aria-hidden="true" />
            <span>Out of <b class="font-semibold text-gray-800">{{ fmt(data.max_total) }}</b> · <b class="font-semibold text-gray-800">{{ fmt(data.pass_percent) }}%</b> needed for an offer</span>
            <label class="ml-auto flex cursor-pointer items-center gap-2 text-sm text-gray-700">
              Show each criterion
              <ToggleSwitch v-model="showCriteria" label="Show each criterion" />
            </label>
          </div>
        </section>

        <!-- Decision for the ticked candidates -->
        <div v-if="data.can_decide && selected.length" class="mb-3 flex flex-wrap items-center gap-2 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm">
          <span class="font-semibold text-brand-800">{{ selected.length }} selected</span>
          <div class="ml-auto flex flex-wrap gap-2">
            <Button v-for="o in OUTCOMES" :key="o.value" size="sm" variant="outline" :icon-left="o.icon" @click="askOutcome(selected, o.value)">{{ o.label }}</Button>
            <Button size="sm" variant="ghost" @click="selected = []">Clear</Button>
          </div>
        </div>

        <div v-if="!data.rows.length" class="rounded-xl border border-dashed bg-white px-6 py-12 text-center text-sm text-gray-500">
          {{ date ? `No final interviews on ${dayjs(date).format('DD MMM YYYY')}.` : 'No final interviews for this job yet.' }}
        </div>
        <div v-else class="overflow-x-auto rounded-xl border bg-white shadow-sm">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-xs text-gray-500">
              <tr>
                <th v-if="data.can_decide" :rowspan="showCriteria ? 2 : 1" class="w-10 px-3 py-2">
                  <input
                    type="checkbox"
                    class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                    :checked="decidable.length > 0 && selected.length === decidable.length"
                    :indeterminate.prop="selected.length > 0 && selected.length < decidable.length"
                    aria-label="Select all candidates"
                    @change="selected = $event.target.checked ? decidable.map((r) => r.application) : []"
                  />
                </th>
                <th :rowspan="showCriteria ? 2 : 1" class="px-3 py-2 text-left font-medium uppercase">#</th>
                <th :rowspan="showCriteria ? 2 : 1" class="min-w-[12rem] px-3 py-2 text-left font-medium uppercase">Candidate</th>
                <th
                  v-for="p in data.panel"
                  :key="p.user"
                  :colspan="showCriteria ? data.criteria.length + 1 : 1"
                  class="border-l px-3 py-2 text-center font-medium"
                >
                  {{ p.full_name }}
                </th>
                <th :rowspan="showCriteria ? 2 : 1" class="border-l px-3 py-2 text-center font-medium uppercase">Total of {{ data.panel.length }}</th>
                <th :rowspan="showCriteria ? 2 : 1" class="px-3 py-2 text-center font-medium uppercase">Average / {{ fmt(data.max_total) }}</th>
                <th :rowspan="showCriteria ? 2 : 1" class="px-3 py-2 text-center font-medium uppercase">Panel says</th>
                <th :rowspan="showCriteria ? 2 : 1" class="px-3 py-2 text-left font-medium uppercase">Decision</th>
              </tr>
              <tr v-if="showCriteria">
                <template v-for="p in data.panel" :key="'c-' + p.user">
                  <th v-for="(c, i) in data.criteria" :key="c.label" class="px-2 py-1.5 text-center font-normal" :class="i === 0 ? 'border-l' : ''" :title="c.label">
                    {{ short(c.label) }} <span class="text-gray-400">/{{ fmt(c.max_score) }}</span>
                  </th>
                  <th class="px-2 py-1.5 text-center font-semibold">Total</th>
                </template>
              </tr>
            </thead>
            <tbody class="divide-y">
              <template v-for="r in data.rows" :key="r.interview">
                <tr class="align-middle" :class="rowTone(r)">
                  <td v-if="data.can_decide" class="px-3 py-2.5">
                    <input
                      v-if="r.can_decide"
                      v-model="selected"
                      type="checkbox"
                      :value="r.application"
                      class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                      :aria-label="`Select ${r.candidate_name}`"
                    />
                  </td>
                  <td class="px-3 py-2.5 tabular-nums text-gray-500">{{ r.rank || '—' }}</td>
                  <td class="px-3 py-2.5">
                    <button type="button" class="flex items-center gap-1.5 text-left" :aria-expanded="open.has(r.interview)" @click="toggle(r.interview)">
                      <FeatherIcon :name="open.has(r.interview) ? 'chevron-down' : 'chevron-right'" class="h-3.5 w-3.5 shrink-0 text-gray-400" />
                      <span>
                        <span class="block font-medium text-gray-900">{{ r.candidate_name }}</span>
                        <span class="block font-mono text-xs text-gray-500">{{ r.application_id }}</span>
                      </span>
                    </button>
                  </td>
                  <template v-for="p in data.panel" :key="r.interview + p.user">
                    <template v-if="showCriteria">
                      <td v-for="(c, i) in data.criteria" :key="c.label" class="px-2 py-2.5 text-center tabular-nums" :class="i === 0 ? 'border-l' : ''">
                        {{ r.scores[p.user] ? fmt(r.scores[p.user].criteria[c.label]) : '' }}
                      </td>
                    </template>
                    <td class="px-2 py-2.5 text-center tabular-nums" :class="showCriteria ? 'font-semibold' : 'border-l'">
                      <span v-if="r.scores[p.user]" class="inline-flex items-center gap-1">
                        {{ fmt(r.scores[p.user].total) }}
                        <span v-if="r.scores[p.user].verdict" class="h-2 w-2 rounded-full" :class="VERDICT_DOT[r.scores[p.user].verdict]" :title="r.scores[p.user].verdict" />
                      </span>
                      <span v-else class="text-xs text-orange-600">pending</span>
                    </td>
                  </template>
                  <td class="border-l px-3 py-2.5 text-center tabular-nums">{{ r.scored ? fmt(r.total_of_all) : '—' }}</td>
                  <td class="px-3 py-2.5 text-center">
                    <template v-if="r.scored">
                      <div class="font-semibold tabular-nums text-gray-900">{{ fmt(r.average) }}</div>
                      <div class="text-xs" :class="r.meets_bar ? 'text-green-700' : 'text-orange-700'">{{ fmt(r.percent) }}%</div>
                    </template>
                    <span v-else class="text-gray-300">—</span>
                    <div v-if="r.scored && r.scored < data.panel.length" class="text-[11px] text-gray-500">{{ r.scored }} of {{ data.panel.length }} scored</div>
                  </td>
                  <td class="px-3 py-2.5">
                    <div class="flex flex-wrap justify-center gap-1">
                      <span v-for="v in VERDICT_LIST" v-show="r.verdicts[v.value]" :key="v.value" class="rounded-full px-1.5 py-0.5 text-[11px] font-medium" :class="v.tone">
                        {{ r.verdicts[v.value] }} {{ v.short }}
                      </span>
                    </div>
                  </td>
                  <td class="px-3 py-2.5">
                    <!-- The status is the control: click it to decide or change the decision. -->
                    <Dropdown v-if="data.can_decide && r.can_decide" :options="outcomeMenu(r)" placement="right">
                      <button
                        type="button"
                        class="inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-full px-3 text-xs font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                        :class="r.outcome ? [OUTCOME_TONE[r.outcome], 'hover:brightness-95'] : 'border border-dashed border-brand-300 bg-white text-brand-700 hover:border-brand-500 hover:bg-brand-50'"
                        :aria-label="r.outcome ? `Decision for ${r.candidate_name}: ${r.outcome}. Change` : `Decide for ${r.candidate_name}`"
                      >
                        <FeatherIcon v-if="r.outcome" :name="OUTCOME_ICON[r.outcome]" class="h-3.5 w-3.5" />
                        {{ r.outcome || 'Decide' }}
                        <FeatherIcon name="chevron-down" class="h-3.5 w-3.5 opacity-70" />
                      </button>
                    </Dropdown>
                    <span
                      v-else-if="r.outcome"
                      class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold"
                      :class="OUTCOME_TONE[r.outcome]"
                    >
                      <FeatherIcon :name="OUTCOME_ICON[r.outcome]" class="h-3.5 w-3.5" />{{ r.outcome }}
                    </span>
                    <span v-else class="whitespace-nowrap text-xs text-gray-500">{{ r.can_decide ? 'Not decided' : r.application_status }}</span>
                  </td>
                </tr>
                <!-- Each panellist's recommendation and comments -->
                <tr v-if="open.has(r.interview)" class="bg-gray-50/70">
                  <td :colspan="colCount" class="px-6 py-3">
                    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                      <div v-for="p in data.panel" :key="p.user" class="rounded-lg border bg-white p-3 text-sm">
                        <div class="flex items-center justify-between gap-2">
                          <span class="font-medium text-gray-900">{{ p.full_name }}</span>
                          <span v-if="r.scores[p.user]?.verdict" class="rounded-full px-2 py-0.5 text-[11px] font-medium" :class="VERDICT_TONE[r.scores[p.user].verdict]">{{ r.scores[p.user].verdict }}</span>
                        </div>
                        <template v-if="r.scores[p.user]">
                          <div class="mt-1 text-xs text-gray-600">
                            <span v-for="c in data.criteria" :key="c.label" class="mr-3">{{ c.label }} {{ fmt(r.scores[p.user].criteria[c.label]) }}/{{ fmt(c.max_score) }}</span>
                          </div>
                          <div v-if="r.scores[p.user].area" class="mt-1 text-xs text-gray-600">Specialization: {{ r.scores[p.user].area }}</div>
                          <p class="mt-1.5 whitespace-pre-line text-gray-700">{{ r.scores[p.user].comments || 'No comments.' }}</p>
                          <div v-if="r.scores[p.user].entered_by" class="mt-1 text-[11px] text-gray-400">Entered by {{ r.scores[p.user].entered_by }}</div>
                        </template>
                        <p v-else class="mt-1 text-xs text-orange-700">Has not scored yet.</p>
                      </div>
                    </div>
                    <div class="mt-2 flex gap-3 text-xs">
                      <router-link :to="`/panel/${r.interview}`" class="text-brand-700 hover:underline">Open assessment form</router-link>
                      <router-link :to="`/applications/${r.application}`" class="text-brand-700 hover:underline">Open application</router-link>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <p class="mt-2 text-xs text-gray-500">
          Ranked by average score. Click a candidate to see each panellist's recommendation and comments.
          A waitlisted candidate stays at "Interview Completed" on the candidate portal.
        </p>
      </template>
    </div>

    <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />
  </StaffLayout>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dropdown, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { panelService } from '@/services/panel'
import { toast } from '@/utils/notify'

const props = defineProps({ job: { type: String, required: true } })
const router = useRouter()

const OUTCOMES = [
  { value: 'Selected', label: 'Selected', icon: 'award' },
  { value: 'Waitlisted', label: 'Waitlist', icon: 'clock' },
  { value: 'Not Selected', label: 'Not selected', icon: 'x' },
]
const OUTCOME_ICON = { Selected: 'award', Waitlisted: 'clock', 'Not Selected': 'x-circle' }
const OUTCOME_TONE = {
  Selected: 'bg-green-100 text-green-800',
  Waitlisted: 'bg-amber-100 text-amber-800',
  'Not Selected': 'bg-gray-100 text-gray-600',
}
const VERDICT_LIST = [
  { value: 'Recommended', short: 'recommend', tone: 'bg-green-50 text-green-700' },
  { value: 'Waitlist', short: 'waitlist', tone: 'bg-amber-50 text-amber-700' },
  { value: 'Not Recommended', short: 'not rec.', tone: 'bg-red-50 text-red-700' },
]
const VERDICT_TONE = Object.fromEntries(VERDICT_LIST.map((v) => [v.value, v.tone]))
const VERDICT_DOT = { Recommended: 'bg-green-500', Waitlist: 'bg-amber-500', 'Not Recommended': 'bg-red-500' }

const data = ref(null)
const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const showCriteria = ref(false)
const selected = ref([])
const open = ref(new Set())
// Other positions with final interviews; the current one is always listed.
const jobOptions = computed(() => {
  const jobs = data.value?.jobs || []
  const label = (j) => (j.position && j.position !== j.job_title ? `${j.job_title} · ${j.position}` : j.job_title)
  const list = jobs.map((j) => ({ name: j.name, label: label(j), count: j.count }))
  if (data.value && !list.some((j) => j.name === props.job)) list.unshift({ name: props.job, label: label(data.value.job), count: data.value.rows.length })
  return list
})
// '' = all dates
const date = ref('')
const dateOptions = computed(() => {
  const ds = data.value?.dates || []
  return [
    { value: '', label: 'All dates', count: ds.reduce((n, d) => n + d.count, 0) },
    ...ds.map((d) => ({ value: d.date, label: dayjs(d.date).format('ddd, DD MMM YYYY'), count: d.count })),
  ]
})
watch(date, () => {
  selected.value = []
  load()
})
const confirmBox = reactive({ open: false, title: '', message: '', label: '', theme: 'gray', run: null })

const fmt = (n) => (n === null || n === undefined || n === '' ? '' : Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 }))
function initials(name) {
  const words = String(name || '').replace(/@.*/, '').split(/[\s._-]+/).filter(Boolean)
  return words.slice(0, 2).map((w) => w[0].toUpperCase()).join('') || '?'
}
const short = (label) => label.split(' ').map((w) => w[0]).join('')
const decidable = computed(() => (data.value?.rows || []).filter((r) => r.can_decide))
const colCount = computed(() => {
  const d = data.value
  if (!d) return 1
  return (d.can_decide ? 1 : 0) + 2 + d.panel.length * (showCriteria.value ? d.criteria.length + 1 : 1) + 4
})
const tiles = computed(() => {
  const rows = data.value?.rows || []
  const n = data.value?.panel.length || 0
  return [
    { label: 'Candidates', value: rows.length },
    { label: 'Fully scored', value: rows.filter((r) => n && r.scored >= n).length },
    { label: `Meet the ${fmt(data.value?.pass_percent)}% bar`, value: rows.filter((r) => r.meets_bar).length, tone: 'text-green-700' },
    { label: 'Selected', value: rows.filter((r) => r.outcome === 'Selected').length, tone: 'text-green-700' },
    { label: 'Waitlisted', value: rows.filter((r) => r.outcome === 'Waitlisted').length, tone: 'text-amber-700' },
  ]
})

function rowTone(r) {
  if (r.outcome === 'Selected') return 'bg-green-50/60'
  if (r.outcome === 'Waitlisted') return 'bg-amber-50/60'
  if (r.outcome === 'Not Selected') return 'text-gray-500'
  return ''
}
function toggle(name) {
  const s = new Set(open.value)
  s.has(name) ? s.delete(name) : s.add(name)
  open.value = s
}

function outcomeMenu(r) {
  const items = OUTCOMES.filter((o) => o.value !== r.outcome).map((o) => ({
    label: o.value === 'Selected' ? 'Select' : o.value === 'Waitlisted' ? 'Waitlist' : 'Not selected',
    icon: o.icon,
    onClick: () => askOutcome([r.application], o.value),
  }))
  if (r.outcome) items.push({ label: 'Clear decision', icon: 'rotate-ccw', onClick: () => askOutcome([r.application], '') })
  return [{ group: 'Decision', hideLabel: true, items }]
}

function askOutcome(apps, outcome) {
  const rows = data.value.rows.filter((r) => apps.includes(r.application))
  const who = rows.length === 1 ? rows[0].candidate_name : `${rows.length} candidates`
  const unscored = rows.filter((r) => r.scored < data.value.panel.length).length
  const text = {
    Selected: `Mark ${who} as selected? The application moves to Selected, ready for the offer.`,
    Waitlisted: `Waitlist ${who}? They stay at "Interview Completed" and can be selected later.`,
    'Not Selected': `Mark ${who} as not selected? The application moves to Not Selected. No email is sent now.`,
    '': `Clear the decision for ${who}? The application goes back to Interview Completed.`,
  }[outcome]
  Object.assign(confirmBox, {
    open: true,
    title: outcome ? `${OUTCOMES.find((o) => o.value === outcome).label}?` : 'Clear decision?',
    message: text + (unscored && outcome ? ` Note: ${unscored === 1 && rows.length === 1 ? 'not every panellist has scored yet' : `${unscored} of them are not fully scored yet`}.` : ''),
    label: outcome ? 'Confirm' : 'Clear decision',
    theme: outcome === 'Not Selected' ? 'red' : 'gray',
    run: () => setOutcome(apps, outcome),
  })
}

async function setOutcome(apps, outcome) {
  try {
    const r = await panelService.setOutcome(apps, outcome)
    toast({ title: outcome ? `${r.updated} marked ${outcome.toLowerCase()}.` : 'Decision cleared.', icon: 'check', iconClasses: 'text-green-500' })
    if (r.skipped?.length) toast({ title: `Not changed: ${r.skipped.join(', ')}`, icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    selected.value = []
    await load()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not record the decision.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

// The Interview Assessment Form of every panellist (one page each), or one.
const printing = ref(false)
const formMenu = computed(() => [
  {
    group: 'Assessment forms',
    hideLabel: true,
    items: [
      { label: 'All panellists', icon: 'users', onClick: () => printForms(null) },
      ...(data.value?.panel || []).map((p) => ({ label: p.full_name, icon: 'user', onClick: () => printForms(p.user) })),
    ],
  },
])
async function printForms(panelist) {
  printing.value = true
  try {
    await panelService.downloadForms(props.job, data.value.job.job_title, panelist, date.value)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not create the forms.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    printing.value = false
  }
}

async function exportSheet() {
  exporting.value = true
  try {
    await panelService.exportConsolidated(props.job, data.value.job.job_title, date.value)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the sheet.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    exporting.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await panelService.getConsolidated(props.job, date.value)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load the score sheet.'
  } finally {
    loading.value = false
  }
}
watch(
  () => props.job,
  () => {
    date.value = ''
    load()
  },
  { immediate: true },
)
</script>
