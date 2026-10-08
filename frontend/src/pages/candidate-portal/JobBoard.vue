<template>
  <CandidatePortalLayout>
    <!-- Header -->
    <section class="border-b bg-gradient-to-b from-brand-50/70 to-white">
      <div class="mx-auto max-w-6xl px-4 pb-8 pt-12 sm:px-6 sm:pt-16">
        <p class="text-sm font-semibold uppercase tracking-wider text-brand-700">Careers at NLSIU</p>
        <div class="mt-3 max-w-2xl">
          <h1 class="font-heading text-3xl font-bold leading-tight text-gray-900 sm:text-[2.75rem]">Work with us</h1>
          <p class="mt-4 text-p-lg text-gray-600">
            Join India's leading law school. Explore current openings across teaching, research and administration.
          </p>
        </div>
        <ul v-if="jobs.length" class="mt-6 flex flex-wrap gap-2" aria-label="At a glance">
          <li
            v-for="stat in stats"
            :key="stat.label"
            class="inline-flex items-center gap-2 rounded-full bg-white px-3.5 py-1.5 text-sm text-gray-600 shadow-sm ring-1 ring-inset ring-gray-200"
          >
            <FeatherIcon :name="stat.icon" class="h-4 w-4 text-brand-700" />
            <span class="font-semibold tabular-nums text-gray-900">{{ stat.value }}</span>{{ stat.label }}
          </li>
        </ul>

        <!-- Search and filters -->
        <div v-if="jobs.length" class="mt-8 flex flex-col gap-3 rounded-2xl border bg-white p-2 shadow-sm md:flex-row md:items-center">
          <label class="flex min-w-0 flex-1 items-center gap-2 px-2">
            <FeatherIcon name="search" class="h-5 w-5 shrink-0 text-gray-400" />
            <span class="sr-only">Search openings</span>
            <input
              v-model="search"
              type="search"
              placeholder="Search by title, department or designation"
              class="min-w-0 flex-1 border-0 bg-transparent px-1 py-2.5 text-base text-gray-900 placeholder-gray-400 focus:ring-0"
            />
          </label>
          <div class="flex flex-wrap gap-2 md:flex-nowrap">
            <!-- Several values each; a job matches any chosen value. -->
            <MultiSelectFilter
              v-for="f in FILTERS"
              :key="f.key"
              v-model="selected[f.key]"
              class="min-w-0 flex-1 md:w-52 md:flex-none"
              size="lg"
              hide-label
              :label="f.label"
              :all-label="f.allLabel"
              :options="optionsFor(f.key)"
            />
            <select v-model="sort" class="filter-select" aria-label="Sort">
              <option value="closing">Closing soonest</option>
              <option value="newest">Newest first</option>
              <option value="title">Title (A–Z)</option>
            </select>
          </div>
        </div>

        <!-- Active filters, each removable -->
        <div v-if="activeChips.length" class="mt-3 flex flex-wrap items-center gap-2">
          <button
            v-for="chip in activeChips"
            :key="`${chip.key}:${chip.value}`"
            type="button"
            class="inline-flex items-center gap-1.5 rounded-full bg-white py-1 pl-3 pr-2 text-sm text-gray-700 ring-1 ring-inset ring-gray-200 hover:ring-brand-200"
            :aria-label="`Remove filter ${chip.value}`"
            @click="removeChip(chip)"
          >
            <span class="text-gray-500">{{ chip.label }}:</span> {{ chip.value }}
            <FeatherIcon name="x" class="h-3.5 w-3.5 text-gray-400" />
          </button>
          <button type="button" class="px-1 text-sm font-medium text-brand-700 hover:underline" @click="clearFilters">Clear all</button>
        </div>
      </div>
    </section>

    <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <!-- Loading -->
      <div v-if="loading" class="overflow-hidden rounded-2xl border bg-white" aria-busy="true">
        <div v-for="i in 4" :key="i" class="flex animate-pulse items-center gap-6 border-b px-6 py-5 last:border-0">
          <div class="flex-1">
            <div class="h-4 w-1/2 rounded bg-gray-100" />
            <div class="mt-3 h-3 w-1/3 rounded bg-gray-100" />
          </div>
          <div class="h-6 w-28 rounded-full bg-gray-100" />
        </div>
      </div>

      <!-- Nothing open -->
      <div v-else-if="!jobs.length" class="mx-auto max-w-lg py-12 text-center">
        <span class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-50 text-brand-700">
          <FeatherIcon name="briefcase" class="h-6 w-6" />
        </span>
        <h2 class="mt-4 font-heading text-xl font-bold text-gray-900">No open positions right now</h2>
        <p class="mt-2 text-p-base text-gray-600">New openings are posted here and on nls.ac.in. Please check back soon.</p>
        <a href="https://www.nls.ac.in" target="_blank" rel="noopener" class="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:underline">
          Visit nls.ac.in <FeatherIcon name="external-link" class="h-4 w-4" />
        </a>
      </div>

      <template v-else>
        <!-- Track tabs -->
        <div class="mb-6 flex items-center justify-between gap-4 border-b">
          <nav class="-mb-px flex gap-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden" aria-label="Filter by track">
            <button
              v-for="t in trackTabs"
              :key="t.key"
              type="button"
              class="flex shrink-0 items-center gap-2 border-b-2 px-3 pb-3 pt-1 text-base transition"
              :class="track === t.key ? 'border-brand-700 font-semibold text-brand-700' : 'border-transparent text-gray-600 hover:text-gray-900'"
              :aria-pressed="track === t.key"
              @click="track = t.key"
            >
              {{ t.label }}
              <span class="rounded-full px-2 py-0.5 text-xs tabular-nums" :class="track === t.key ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'">
                {{ t.count }}
              </span>
            </button>
          </nav>
          <p class="hidden shrink-0 pb-3 text-sm text-gray-500 sm:block" aria-live="polite">
            {{ visibleJobs.length }} {{ visibleJobs.length === 1 ? 'opening' : 'openings' }}
          </p>
        </div>

        <div v-if="!visibleJobs.length" class="rounded-2xl border border-dashed bg-white px-6 py-14 text-center">
          <p class="text-base font-medium text-gray-900">No openings match your search</p>
          <p class="mt-1 text-sm text-gray-500">Try a different keyword, or fewer filters.</p>
          <button type="button" class="mt-4 text-sm font-semibold text-brand-700 hover:underline" @click="clearFilters">Clear filters</button>
        </div>

        <!-- Openings, grouped by track -->
        <div v-else class="flex flex-col gap-10">
          <section v-for="group in groups" :key="group.track" :aria-labelledby="`track-${slug(group.track)}`">
            <div v-if="groups.length > 1" class="mb-3 flex items-center gap-2">
              <FeatherIcon :name="trackIcon(group.track)" class="h-4 w-4 text-brand-700" />
              <h2 :id="`track-${slug(group.track)}`" class="font-heading text-lg font-bold text-gray-900">{{ group.track }}</h2>
              <span class="text-sm text-gray-500">· {{ group.jobs.length }}</span>
            </div>
            <ul class="divide-y overflow-hidden rounded-2xl border bg-white shadow-sm">
              <li v-for="job in group.jobs" :key="job.name">
                <router-link
                  :to="`/portal/jobs/${job.name}`"
                  class="group flex flex-col gap-3 px-5 py-5 transition hover:bg-brand-50/40 focus:outline-none focus-visible:bg-brand-50/60 sm:flex-row sm:items-center sm:gap-6 sm:px-6"
                >
                  <span class="hidden h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700 transition group-hover:bg-brand-700 group-hover:text-white sm:flex">
                    <FeatherIcon :name="trackIcon(job.track)" class="h-5 w-5" />
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <h3 class="text-lg font-semibold leading-snug text-gray-900 group-hover:text-brand-700">{{ job.job_title }}</h3>
                      <span v-if="isNew(job)" class="rounded-full bg-brand-700 px-2 py-0.5 text-xs font-semibold text-white">New</span>
                    </div>
                    <p class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-600">
                      <span v-for="(m, i) in metaOf(job)" :key="m" class="inline-flex items-center gap-3">
                        <span v-if="i" class="h-1 w-1 rounded-full bg-gray-300" aria-hidden="true" />{{ m }}
                      </span>
                    </p>
                  </div>
                  <div class="flex shrink-0 items-center justify-between gap-4 sm:justify-end">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm"
                      :class="deadlineOf(job).urgent ? 'bg-orange-50 font-medium text-orange-700' : 'bg-gray-100 text-gray-700'"
                    >
                      <FeatherIcon name="clock" class="h-3.5 w-3.5" />{{ deadlineOf(job).text }}
                    </span>
                    <span class="hidden items-center gap-1 text-sm font-semibold text-brand-700 md:inline-flex">
                      View role <FeatherIcon name="arrow-right" class="h-4 w-4 transition group-hover:translate-x-0.5" />
                    </span>
                    <FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-300 md:hidden" />
                  </div>
                </router-link>
              </li>
            </ul>
          </section>
        </div>

      </template>

      <!-- How applying works: shown whenever the page is not loading. -->
      <section v-if="!loading" class="mt-14 rounded-2xl border bg-white p-6 shadow-sm sm:p-8" aria-labelledby="how-heading">
        <h2 id="how-heading" class="font-heading text-xl font-bold text-gray-900">How applying works</h2>
        <ol class="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
          <li v-for="(step, idx) in HOW_TO_APPLY" :key="step.title" class="flex gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
              <FeatherIcon :name="step.icon" class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <h3 class="text-base font-semibold text-gray-900">{{ idx + 1 }}. {{ step.title }}</h3>
              <p class="mt-1 text-p-sm text-gray-600">{{ step.text }}</p>
            </div>
          </li>
        </ol>
        <p class="mt-6 border-t pt-5 text-sm text-gray-500">
          Openings are also announced on
          <a href="https://www.nls.ac.in" target="_blank" rel="noopener" class="font-medium text-brand-700 hover:underline">nls.ac.in</a>.
          <template v-if="!session.isLoggedIn">
            Already applied?
            <a :href="loginUrl" class="font-medium text-brand-700 hover:underline">Log in to track your application</a>.
          </template>
        </p>
      </section>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import MultiSelectFilter from '@/components/common/MultiSelectFilter.vue'
import { useJobOpenings } from '@/composables/useJobOpenings'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const { jobs, loading, fetchJobs } = useJobOpenings()
const session = useSessionStore()
const loginUrl = `/login?redirect-to=${encodeURIComponent('/pathways/portal/applications')}`

const HOW_TO_APPLY = [
  { icon: 'search', title: 'Find your role', text: 'Read the posting and the official notification, and check the documents you need.' },
  { icon: 'edit-3', title: 'Apply online', text: 'No account needed. Apply with your personal email; the form saves your progress on this device.' },
  { icon: 'mail', title: 'Track your application', text: 'We email you a portal login when you submit, so you can follow each stage.' },
]

// Applications that opened in the last 7 days.
function isNew(job) {
  if (!job.application_start) return false
  const start = dayjs(job.application_start)
  return !start.isAfter(dayjs()) && dayjs().diff(start, 'day') < 7
}

// Search and filters live in the URL, so a shared link or Back keeps them.
const SORTS = ['closing', 'newest', 'title']
const search = ref(String(route.query.q || ''))
const track = ref(String(route.query.track || 'all'))
const sort = ref(SORTS.includes(route.query.sort) ? route.query.sort : 'closing')

// Multi-select filters, kept in the URL as repeated keys
// (?department=Finance&department=Law).
const FILTERS = [
  { key: 'department', label: 'Department', allLabel: 'All departments' },
  { key: 'employment_type', label: 'Employment', allLabel: 'All employment types' },
]
const fromQuery = (v) => [].concat(v ?? []).map(String).filter(Boolean)
const selected = reactive(Object.fromEntries(FILTERS.map((f) => [f.key, fromQuery(route.query[f.key])])))

let urlTimer = null
watch([search, track, sort, () => FILTERS.map((f) => selected[f.key].join('\u0000'))], () => {
  clearTimeout(urlTimer)
  urlTimer = setTimeout(() => {
    const query = {
      q: search.value.trim() || undefined,
      track: track.value !== 'all' ? track.value : undefined,
      ...Object.fromEntries(FILTERS.map((f) => [f.key, selected[f.key].length ? [...selected[f.key]] : undefined])),
      sort: sort.value !== 'closing' ? sort.value : undefined,
    }
    router.replace({ query: Object.fromEntries(Object.entries(query).filter(([, v]) => v !== undefined)) })
  }, 300)
})

const TRACK_ICONS = { Faculty: 'book-open', Research: 'search', Admin: 'briefcase' }
const trackIcon = (name) => TRACK_ICONS[name] || 'layers'
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-')

const stats = computed(() => [
  { icon: 'briefcase', ...counted(jobs.value.length, 'open position', 'open positions') },
  { icon: 'users', ...counted(jobs.value.reduce((sum, j) => sum + (Number(j.vacancies) || 0), 0), 'vacancy', 'vacancies') },
  { icon: 'home', ...counted(new Set(jobs.value.map((j) => j.department).filter(Boolean)).size, 'department', 'departments') },
])
function counted(value, one, many) {
  return { value, label: value === 1 ? one : many }
}

// Choices with how many openings each has, so empty choices are never offered.
function optionsFor(key) {
  const counts = {}
  for (const j of jobs.value) if (j[key]) counts[j[key]] = (counts[j[key]] || 0) + 1
  return Object.keys(counts)
    .sort()
    .map((value) => ({ label: value, value, count: counts[value] }))
}

const activeChips = computed(() =>
  FILTERS.flatMap((f) => selected[f.key].map((value) => ({ key: f.key, label: f.label, value }))),
)
function removeChip(chip) {
  selected[chip.key] = selected[chip.key].filter((v) => v !== chip.value)
}

const trackTabs = computed(() => {
  const counts = {}
  for (const j of jobs.value) counts[j.track] = (counts[j.track] || 0) + 1
  return [
    { key: 'all', label: 'All openings', count: jobs.value.length },
    ...Object.keys(counts)
      .sort()
      .map((name) => ({ key: name, label: name, count: counts[name] })),
  ]
})

// Values from an old link that no longer have openings are dropped,
// rather than leaving an empty list.
watch(jobs, () => {
  if (track.value !== 'all' && !trackTabs.value.some((t) => t.key === track.value)) track.value = 'all'
  for (const f of FILTERS) {
    const available = new Set(jobs.value.map((j) => j[f.key]).filter(Boolean))
    selected[f.key] = selected[f.key].filter((v) => available.has(v))
  }
})

const visibleJobs = computed(() => {
  const term = search.value.trim().toLowerCase()
  const list = jobs.value.filter((j) => {
    if (track.value !== 'all' && j.track !== track.value) return false
    for (const f of FILTERS) if (selected[f.key].length && !selected[f.key].includes(j[f.key])) return false
    if (!term) return true
    return [j.job_title, j.department, j.designation, j.track].some((v) => String(v || '').toLowerCase().includes(term))
  })
  // The server lists jobs newest first, so "Newest" keeps its order.
  if (sort.value === 'newest') return list
  const byClosing = (a, b) => String(a.application_deadline || '9999').localeCompare(String(b.application_deadline || '9999'))
  return [...list].sort(sort.value === 'title' ? (a, b) => a.job_title.localeCompare(b.job_title) : byClosing)
})

// Grouped by track in the order the tabs show; one group when a track is picked.
const groups = computed(() => {
  const map = new Map()
  for (const j of visibleJobs.value) {
    const key = j.track || 'Other'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(j)
  }
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([t, list]) => ({ track: t, jobs: list }))
})

function metaOf(job) {
  const vacancies = Number(job.vacancies) || 0
  const pay = String(job.pay_level || '').trim()
  return [
    job.department,
    job.employment_type,
    vacancies ? `${vacancies} ${vacancies === 1 ? 'post' : 'posts'}` : '',
    pay ? (/^\d/.test(pay) ? `Pay level ${pay}` : pay) : '',
  ].filter(Boolean)
}

function deadlineOf(job) {
  if (job.application_start && dayjs(job.application_start).isAfter(dayjs())) {
    return { text: `Opens ${dayjs(job.application_start).format('D MMM')}`, urgent: false }
  }
  if (!job.application_deadline) return { text: 'Open until filled', urgent: false }
  const close = dayjs(job.application_deadline)
  const days = close.startOf('day').diff(dayjs().startOf('day'), 'day')
  return {
    text: days <= 0 ? 'Closes today' : days <= 7 ? `Closes in ${days} day${days === 1 ? '' : 's'}` : `Apply by ${close.format('D MMM YYYY')}`,
    urgent: days <= 3,
  }
}

function clearFilters() {
  search.value = ''
  track.value = 'all'
  for (const f of FILTERS) selected[f.key] = []
}

onMounted(fetchJobs)
</script>

<style scoped>
.filter-select {
  @apply h-11 min-w-0 flex-1 rounded-xl border-gray-200 bg-gray-50 pl-3 pr-9 text-sm text-gray-800 focus:border-brand-700 focus:ring-brand-700 md:w-48 md:flex-none;
}
</style>
