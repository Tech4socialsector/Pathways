<template>
  <StaffLayout>
    <PageHeader
      title="Master Setup"
      subtitle="Reference data behind job openings, application forms, approvals and scoring. Set it up in the order shown."
    />

    <div class="min-h-0 flex-1 overflow-y-auto bg-gray-50/60">
      <div v-if="loading" class="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
        <div class="h-20 animate-pulse rounded-xl border bg-white" />
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <div v-for="i in 6" :key="i" class="h-44 animate-pulse rounded-xl border bg-white" />
        </div>
      </div>

      <div v-else-if="isPermissionError" class="p-6">
        <EmptyState title="You don't have access to Master Setup" description="Ask a Pathways administrator if you need to manage master records." />
      </div>

      <div v-else-if="error" class="p-6">
        <EmptyState title="Could not load Master Setup" :description="errorMessage">
          <template #action><Button @click="fetchMasterSetup">Try again</Button></template>
        </EmptyState>
      </div>

      <div v-else class="mx-auto flex max-w-7xl flex-col gap-6 p-4 md:p-6">
        <!-- Overview -->
        <section class="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div v-for="s in summary" :key="s.label" class="flex items-center gap-3 rounded-xl border bg-white p-4 shadow-sm">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg" :class="s.iconClass">
              <FeatherIcon :name="s.icon" class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <div class="text-sm text-gray-500">{{ s.label }}</div>
              <div class="mt-1 text-2xl font-semibold tabular-nums text-gray-900">{{ s.value }}</div>
            </div>
          </div>
        </section>

        <!-- Toolbar -->
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="w-full sm:w-80">
            <TextInput v-model="query" type="text" placeholder="Search masters, e.g. university, approver" aria-label="Search masters">
              <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
            </TextInput>
          </div>
          <div class="flex items-center gap-1 rounded-lg border bg-white p-1 text-sm" role="tablist" aria-label="Filter masters">
            <button
              v-for="f in filters"
              :key="f.value"
              type="button"
              role="tab"
              :aria-selected="filter === f.value"
              class="rounded-md px-3 py-1 font-medium transition"
              :class="filter === f.value ? 'bg-brand-700 text-white' : 'text-gray-600 hover:bg-gray-100'"
              @click="filter = f.value"
            >
              {{ f.label }} <span class="ml-1 tabular-nums opacity-75">{{ f.count }}</span>
            </button>
          </div>
        </div>

        <!-- Sections, in setup order -->
        <section v-for="stage in visibleStages" :key="stage.key" :aria-labelledby="`stage-${stage.key}`">
          <header class="mb-3 flex flex-wrap items-center gap-3">
            <span
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold"
              :class="stage.complete ? 'bg-brand-700 text-white' : 'border-2 border-brand-700 bg-white text-brand-700'"
            >
              <FeatherIcon v-if="stage.complete" name="check" class="h-4 w-4" />
              <template v-else>{{ stage.step }}</template>
            </span>
            <div class="min-w-0 flex-1">
              <h2 :id="`stage-${stage.key}`" class="font-heading text-lg font-semibold text-gray-900">
                Step {{ stage.step }} · {{ stage.title }}
              </h2>
              <p class="mt-0.5 text-p-sm text-gray-500">{{ stage.hint }}</p>
            </div>
            <span class="rounded-full bg-white px-2.5 py-1 text-sm font-medium tabular-nums text-gray-600 ring-1 ring-inset ring-gray-200">
              {{ stage.done }} of {{ stage.total }} set up
            </span>
          </header>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="m in stage.masters"
              :key="m.doctype"
              class="group relative isolate flex flex-col rounded-xl border bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md focus-within:border-brand-300"
            >
              <div class="flex flex-1 flex-col p-4">
                <div class="flex items-start gap-3">
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 transition group-hover:bg-brand-700 group-hover:text-white">
                    <FeatherIcon :name="m.icon" class="h-5 w-5" />
                  </span>
                  <div class="min-w-0 flex-1">
                    <h3 class="truncate text-base font-semibold text-gray-900">
                      <!-- Stretched link: the whole card opens the list -->
                      <RouterLink :to="listRoute(m.doctype)" class="outline-none after:absolute after:inset-0 after:rounded-xl focus-visible:underline">
                        {{ m.label }}
                      </RouterLink>
                    </h3>
                    <div class="mt-1.5 flex items-center gap-1.5 text-sm">
                      <template v-if="isDone(m)">
                        <span class="font-semibold tabular-nums text-gray-900">{{ m.total }}</span>
                        <span class="text-gray-500">{{ m.total === 1 ? 'record' : 'records' }}</span>
                        <template v-if="m.inactive">
                          <span class="text-gray-300">·</span>
                          <span class="text-gray-500">{{ m.inactive }} inactive</span>
                        </template>
                      </template>
                      <span v-else class="rounded-full bg-orange-50 px-2 py-0.5 text-xs font-medium text-orange-700">No records yet</span>
                    </div>
                  </div>
                  <FeatherIcon
                    :name="isDone(m) ? 'check-circle' : 'alert-circle'"
                    class="h-4 w-4 shrink-0"
                    :class="isDone(m) ? 'text-brand-600' : 'text-orange-500'"
                    :aria-label="isDone(m) ? 'Set up' : 'Not set up'"
                  />
                </div>

                <p class="mt-3 line-clamp-2 text-p-sm text-gray-600">{{ m.description }}</p>

                <p v-if="m.needs.length" class="mt-2 text-p-xs text-gray-500">
                  <span class="font-medium text-gray-600">Needs:</span>{{ ' ' }}
                  <template v-for="(n, i) in m.needs" :key="n">
                    <span :class="byLabel[n] && !isDone(byLabel[n]) ? 'font-medium text-orange-700' : ''">{{ n }}</span>{{ i < m.needs.length - 1 ? ', ' : '' }}
                  </template>
                </p>
              </div>

              <footer class="flex items-center justify-between gap-2 border-t px-4 py-2.5">
                <span class="truncate text-sm text-gray-500">
                  {{ m.last_updated ? `Updated ${formatDate(m.last_updated)}` : 'Never updated' }}
                </span>
                <!-- z-10 lifts the action above the card's stretched link -->
                <RouterLink
                  v-if="m.can_create"
                  :to="newRoute(m.doctype)"
                  class="relative z-10 inline-flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-sm font-medium text-brand-700 hover:bg-brand-50"
                  :aria-label="`New ${m.singular}`"
                >
                  <FeatherIcon name="plus" class="h-3.5 w-3.5" />
                  {{ isDone(m) ? 'New' : `Add first ${m.singular.toLowerCase()}` }}
                </RouterLink>
              </footer>
            </article>
          </div>
        </section>

        <div v-if="!visibleStages.length" class="rounded-xl border border-dashed bg-white p-10 text-center">
          <p class="text-sm text-gray-600">
            <template v-if="query.trim()">No masters match “{{ query.trim() }}”.</template>
            <template v-else>Every master has records. Nothing needs setting up.</template>
          </p>
          <Button class="mt-3" size="sm" @click="resetFilters">Show all masters</Button>
        </div>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Button, FeatherIcon, TextInput } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useMasterSetup } from '@/composables/useMasterSetup'
import { listRoute, newRoute } from '@/utils/masterForm'

const { categories, loading, error, fetchMasterSetup } = useMasterSetup()

onMounted(fetchMasterSetup)

const isPermissionError = computed(() => error.value?.exc_type === 'PermissionError' || error.value?.status === 403)

// Server messages are user-facing frappe.throw text; anything else
// (network failure, 500) gets a generic line instead of raw details.
const errorMessage = computed(() =>
  error.value?.status && error.value.status < 500 && error.value.messages?.[0]
    ? error.value.messages[0]
    : 'Something went wrong while loading master records. Please try again.',
)

// The order to fill the masters in: each one only links to masters set up
// before it (a Position needs its Track, Department, Designation and
// Document Types).
const STAGES = [
  {
    key: 'basics',
    title: 'Organisation',
    hint: 'Start here. Everything else links to these.',
    masters: [
      { doctype: 'Recruitment Track', needs: [] },
      { doctype: 'Department', needs: [] },
      { doctype: 'Designation', needs: ['Recruitment Tracks'] },
    ],
  },
  {
    key: 'form_lists',
    title: 'Application form lists',
    hint: 'Choices candidates pick from on the application form.',
    masters: [
      { doctype: 'Document Type Master', needs: [] },
      { doctype: 'Institution Master', needs: [] },
      { doctype: 'Specialization Master', needs: [] },
      { doctype: 'UGC NET Subject Master', needs: [] },
      { doctype: 'Candidate Source', needs: [] },
    ],
  },
  {
    key: 'positions',
    title: 'Positions',
    hint: 'Posts by job code. A new job opening copies its position.',
    masters: [{ doctype: 'Position', needs: ['Recruitment Tracks', 'Departments', 'Designations', 'Document Types'] }],
  },
  {
    key: 'approvals_scoring',
    title: 'Approvals and scoring',
    hint: 'Who approves green sheets, and how candidates are scored.',
    masters: [
      { doctype: 'Approval Chain Template', needs: ['Recruitment Tracks', 'approver roles'] },
      { doctype: 'Scoring Rubric Template', needs: ['Recruitment Tracks'] },
    ],
  },
]

// A master counts as set up once it has at least one record.
const isDone = (m) => (m?.total || 0) > 0

const byDoctype = computed(() => Object.fromEntries(categories.value.flatMap((c) => c.masters).map((m) => [m.doctype, m])))

const stages = computed(() => {
  const placed = new Set()
  const out = STAGES.map((st, i) => ({
    ...st,
    step: i + 1,
    masters: st.masters
      .filter((m) => byDoctype.value[m.doctype])
      .map((m) => {
        placed.add(m.doctype)
        return { ...byDoctype.value[m.doctype], needs: m.needs }
      }),
  }))
  // Masters added to the server registry but not placed above still show.
  const rest = Object.values(byDoctype.value).filter((m) => !placed.has(m.doctype))
  if (rest.length) {
    out.push({ key: 'other', title: 'Other', hint: 'More reference data.', step: out.length + 1, masters: rest.map((m) => ({ ...m, needs: [] })) })
  }
  return out
    .filter((st) => st.masters.length)
    .map((st, i) => {
      const done = st.masters.filter(isDone).length
      return { ...st, step: i + 1, done, total: st.masters.length, complete: done === st.masters.length }
    })
})

const allMasters = computed(() => stages.value.flatMap((st) => st.masters))
const byLabel = computed(() => Object.fromEntries(allMasters.value.map((m) => [m.label, m])))

const summary = computed(() => {
  const masters = allMasters.value
  const done = masters.filter(isDone).length
  return [
    { label: 'Masters', value: masters.length, icon: 'grid', iconClass: 'bg-gray-100 text-gray-700' },
    { label: 'Set up', value: done, icon: 'check-circle', iconClass: 'bg-brand-50 text-brand-700' },
    { label: 'Need setup', value: masters.length - done, icon: 'alert-circle', iconClass: masters.length - done ? 'bg-orange-50 text-orange-700' : 'bg-gray-100 text-gray-500' },
    { label: 'Total records', value: masters.reduce((n, m) => n + (m.total || 0), 0).toLocaleString('en-IN'), icon: 'database', iconClass: 'bg-gray-100 text-gray-700' },
  ]
})

const query = ref('')
const filter = ref('all')
const filters = computed(() => [
  { value: 'all', label: 'All', count: allMasters.value.length },
  { value: 'todo', label: 'Need setup', count: allMasters.value.filter((m) => !isDone(m)).length },
])

const visibleStages = computed(() => {
  const q = query.value.trim().toLowerCase()
  return stages.value
    .map((st) => ({
      ...st,
      masters: st.masters.filter(
        (m) =>
          (filter.value === 'all' || !isDone(m)) &&
          (!q || [m.label, m.singular, m.description, m.doctype, ...(m.keywords || [])].join(' ').toLowerCase().includes(q)),
      ),
    }))
    .filter((st) => st.masters.length)
})

function resetFilters() {
  query.value = ''
  filter.value = 'all'
}

function formatDate(value) {
  return dayjs(value).format('DD MMM YYYY')
}
</script>
