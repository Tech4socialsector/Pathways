<template>
  <CandidatePortalLayout>
    <!-- Hero -->
    <section class="bg-gradient-to-br from-brand-900 via-brand-800 to-brand-600 text-white">
      <div class="mx-auto max-w-6xl px-6 py-12">
        <div class="text-xs font-semibold uppercase tracking-wider text-white/70">Careers at NLSIU</div>
        <h1 class="mt-2 text-3xl font-bold leading-tight sm:text-4xl">Work with us</h1>
        <p class="mt-2 max-w-2xl text-white/80">
          Join India's leading law school. Explore current openings across teaching, research and administration.
        </p>

        <div class="mt-6 flex max-w-xl items-center gap-2 rounded-lg bg-white p-1.5 shadow-lg">
          <FeatherIcon name="search" class="ml-2 h-5 w-5 shrink-0 text-gray-400" />
          <input
            v-model="search"
            type="search"
            placeholder="Search by title, department or designation"
            class="min-w-0 flex-1 border-0 bg-transparent px-1 py-2 text-gray-900 placeholder-gray-400 focus:ring-0"
            aria-label="Search openings"
          />
        </div>

        <dl v-if="jobs.length" class="mt-8 flex flex-wrap gap-x-10 gap-y-4">
          <div v-for="stat in stats" :key="stat.label">
            <dt class="text-xs uppercase tracking-wide text-white/70">{{ stat.label }}</dt>
            <dd class="text-2xl font-bold">{{ stat.value }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <div class="mx-auto max-w-6xl px-6 py-8">
      <div v-if="loading" class="py-10 text-sm text-gray-500">Loading openings...</div>
      <EmptyState
        v-else-if="!jobs.length"
        title="No open positions right now"
        description="New openings are posted here and on nls.ac.in. Please check back soon."
      />

      <template v-else>
        <!-- Track tabs + sort -->
        <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap gap-2" role="tablist" aria-label="Filter by track">
            <button
              v-for="t in trackTabs"
              :key="t.key"
              role="tab"
              :aria-selected="track === t.key"
              class="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-medium transition"
              :class="track === t.key ? 'border-brand-700 bg-brand-700 text-white' : 'border-gray-200 bg-white text-gray-700 hover:border-brand-200 hover:text-brand-700'"
              @click="track = t.key"
            >
              {{ t.label }}
              <span class="rounded-full px-1.5 text-xs" :class="track === t.key ? 'bg-white/20' : 'bg-gray-100 text-gray-600'">{{ t.count }}</span>
            </button>
          </div>
          <label class="flex items-center gap-2 text-sm text-gray-600">
            Sort
            <select v-model="sort" class="rounded-md border-gray-200 py-1.5 pl-3 pr-8 text-sm focus:border-brand-700 focus:ring-brand-700">
              <option value="closing">Closing soonest</option>
              <option value="title">Title (A–Z)</option>
            </select>
          </label>
        </div>

        <div v-if="!visibleJobs.length" class="rounded-xl border border-dashed bg-white py-12 text-center text-sm text-gray-500">
          No openings match your search.
          <button class="ml-1 font-semibold text-brand-700 hover:underline" @click="clearFilters">Clear filters</button>
        </div>

        <div v-else class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          <router-link
            v-for="job in visibleJobs"
            :key="job.name"
            :to="`/portal/jobs/${job.name}`"
            class="group flex flex-col rounded-xl border border-gray-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-700"
          >
            <div class="flex flex-1 flex-col p-5">
              <div class="flex items-center justify-between gap-2">
                <span class="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700">
                  <FeatherIcon :name="trackIcon(job.track)" class="h-3.5 w-3.5" />{{ job.track }}
                </span>
              </div>
              <h2 class="mt-3 text-lg font-bold leading-snug text-gray-900 group-hover:text-brand-700">{{ job.job_title }}</h2>
              <p class="mt-1 flex items-start gap-1.5 text-sm text-gray-600">
                <FeatherIcon name="home" class="mt-0.5 h-3.5 w-3.5 shrink-0 text-gray-400" />{{ job.department }}
              </p>
              <div class="mt-4 flex flex-wrap gap-2 text-xs">
                <span v-if="job.employment_type" class="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-gray-700">
                  <FeatherIcon name="briefcase" class="h-3 w-3" />{{ job.employment_type }}
                </span>
                <span class="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-gray-700">
                  <FeatherIcon name="users" class="h-3 w-3" />{{ job.vacancies }} vacanc{{ job.vacancies == 1 ? 'y' : 'ies' }}
                </span>
                <span v-if="job.pay_level" class="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-gray-700">
                  <FeatherIcon name="credit-card" class="h-3 w-3" />{{ job.pay_level }}
                </span>
              </div>
            </div>
            <div class="flex items-center justify-between gap-2 border-t px-5 py-3 text-sm">
              <span class="flex items-center gap-1.5" :class="deadlineOf(job).urgent ? 'font-semibold text-orange-700' : 'text-gray-600'">
                <FeatherIcon name="clock" class="h-4 w-4" />{{ deadlineOf(job).text }}
              </span>
              <span class="inline-flex items-center gap-1 font-semibold text-brand-700">
                View &amp; apply <FeatherIcon name="arrow-right" class="h-4 w-4 transition group-hover:translate-x-0.5" />
              </span>
            </div>
          </router-link>
        </div>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useJobOpenings } from '@/composables/useJobOpenings'

const { jobs, loading, fetchJobs } = useJobOpenings()

const search = ref('')
const track = ref('all')
const sort = ref('closing')

const TRACK_ICONS = { Faculty: 'book-open', Research: 'search', Admin: 'briefcase' }
function trackIcon(name) {
  return TRACK_ICONS[name] || 'layers'
}

const stats = computed(() => [
  { label: 'Open positions', value: jobs.value.length },
  { label: 'Vacancies', value: jobs.value.reduce((sum, j) => sum + (Number(j.vacancies) || 0), 0) },
  { label: 'Departments', value: new Set(jobs.value.map((j) => j.department)).size },
])

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

const visibleJobs = computed(() => {
  const term = search.value.trim().toLowerCase()
  const list = jobs.value.filter((j) => {
    if (track.value !== 'all' && j.track !== track.value) return false
    if (!term) return true
    return [j.job_title, j.department, j.designation, j.track].some((v) => String(v || '').toLowerCase().includes(term))
  })
  return [...list].sort((a, b) =>
    sort.value === 'title'
      ? a.job_title.localeCompare(b.job_title)
      : String(a.application_deadline || '9999').localeCompare(String(b.application_deadline || '9999')),
  )
})

function deadlineOf(job) {
  if (job.application_start && dayjs(job.application_start).isAfter(dayjs())) {
    return { text: `Opens ${dayjs(job.application_start).format('D MMM YYYY')}`, urgent: false }
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
}

onMounted(fetchJobs)
</script>
