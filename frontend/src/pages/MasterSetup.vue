<template>
  <StaffLayout>
    <PageHeader
      title="Master Setup"
      subtitle="Reference data used by job openings, application forms, approvals and scoring."
      :breadcrumbs="[{ label: 'Dashboard', to: '/' }, { label: 'Master Setup' }]"
    />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div v-if="loading" class="mx-auto flex max-w-5xl flex-col gap-4" aria-busy="true">
        <div v-for="i in 3" :key="i" class="h-40 animate-pulse rounded-xl border bg-white" />
      </div>

      <EmptyState
        v-else-if="isPermissionError"
        title="You don't have access to Master Setup"
        description="Ask a Pathways administrator if you need to manage master records."
      />

      <EmptyState v-else-if="error" title="Could not load Master Setup" :description="errorMessage">
        <template #action>
          <Button @click="fetchMasterSetup">Try again</Button>
        </template>
      </EmptyState>

      <div v-else class="mx-auto flex max-w-5xl flex-col gap-6">
        <!-- Toolbar: search and category -->
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="w-full sm:w-80">
            <TextInput v-model="query" type="text" placeholder="Search masters">
              <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
            </TextInput>
          </div>
          <div class="flex items-center gap-3 text-sm text-gray-600">
            <span><b class="text-gray-900">{{ doneCount }}</b> of {{ orderedMasters.length }} set up</span>
            <div class="h-2 w-40 overflow-hidden rounded-full bg-gray-200">
              <div class="h-full rounded-full bg-brand-700 transition-all" :style="{ width: `${(doneCount / (orderedMasters.length || 1)) * 100}%` }" />
            </div>
          </div>
        </div>

        <p v-if="emptyMasters.length" class="flex items-start gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-2.5 text-sm text-orange-800">
          <FeatherIcon name="alert-circle" class="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Next to set up: <b>{{ emptyMasters[0].label }}</b>.
            <template v-if="emptyMasters.length > 1">Also empty: {{ emptyMasters.slice(1).map((m) => m.label).join(', ') }}.</template>
            Forms that use an empty master have nothing to choose from.
          </span>
        </p>

        <EmptyState
          v-if="!visibleStages.length"
          title="No masters match your search"
          :description="`Nothing found for “${query}”.`"
        />

        <!-- Setup order: one panel per stage, masters numbered in the order to fill them -->
        <section v-for="stage in visibleStages" :key="stage.key" class="overflow-hidden rounded-xl border bg-white shadow-sm">
          <header class="flex items-start gap-3 border-b bg-gray-50/80 px-5 py-3">
            <span
              class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
              :class="stage.done ? 'bg-green-600 text-white' : 'bg-brand-700 text-white'"
            >
              <FeatherIcon v-if="stage.done" name="check" class="h-3.5 w-3.5" />
              <template v-else>{{ stage.step }}</template>
            </span>
            <div class="min-w-0 flex-1">
              <h2 class="text-sm font-semibold text-gray-900">Step {{ stage.step }} · {{ stage.title }}</h2>
              <p class="text-xs text-gray-500">{{ stage.hint }}</p>
            </div>
            <span class="text-xs text-gray-500">{{ stage.masters.filter((m) => m.total).length }} / {{ stage.masters.length }} done</span>
          </header>
          <ul class="divide-y">
            <li
              v-for="master in stage.masters"
              :key="master.doctype"
              class="group grid cursor-pointer grid-cols-[2.25rem_minmax(0,1fr)_auto] items-center gap-4 px-5 py-3.5 transition hover:bg-gray-50 md:grid-cols-[2.25rem_minmax(0,1fr)_7rem_9rem_auto]"
              tabindex="0"
              @click="goTo(master.route)"
              @keydown.enter.self="goTo(master.route)"
            >
              <span
                class="flex h-9 w-9 items-center justify-center rounded-lg border text-sm font-semibold"
                :class="master.total ? 'border-green-200 bg-green-50 text-green-700' : 'border-orange-200 bg-orange-50 text-orange-700'"
                :title="master.total ? 'Set up' : 'Not set up yet'"
              >
                <FeatherIcon v-if="master.total" name="check" class="h-4 w-4" />
                <template v-else>{{ master.order }}</template>
              </span>
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold tabular-nums text-gray-400">{{ master.order }}.</span>
                  <FeatherIcon :name="master.icon" class="h-3.5 w-3.5 text-gray-400" />
                  <span class="font-medium text-gray-900 group-hover:text-brand-700">{{ master.label }}</span>
                </div>
                <div class="truncate text-sm text-gray-500" :title="master.description">{{ master.description }}</div>
                <div v-if="master.needs.length" class="mt-0.5 text-xs text-gray-400">Needs: {{ master.needs.join(', ') }}</div>
              </div>
              <div class="hidden text-sm md:block">
                <div class="font-semibold tabular-nums text-gray-900">{{ master.total || 0 }}</div>
                <div class="text-xs" :class="!master.total ? 'text-orange-700' : 'text-gray-500'">
                  <template v-if="!master.total">No records</template>
                  <template v-else-if="master.inactive">{{ master.inactive }} inactive</template>
                  <template v-else>{{ master.total === 1 ? 'record' : 'records' }}</template>
                </div>
              </div>
              <div class="hidden text-xs text-gray-500 md:block" :title="master.last_updated ? dayjs(master.last_updated).format('DD MMM YYYY, h:mm A') : ''">
                <div class="text-gray-400">Last updated</div>
                {{ master.last_updated ? dayjs(master.last_updated).format('DD MMM YYYY') : '—' }}
              </div>
              <div class="flex items-center gap-1" @click.stop>
                <Button v-if="master.can_create" size="sm" variant="ghost" icon-left="plus" :title="`New ${master.singular}`" @click="goTo(master.new_route)">
                  <span class="hidden lg:inline">New</span>
                </Button>
                <Button size="sm" variant="outline" @click="goTo(master.route)">Manage</Button>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, FeatherIcon, TextInput } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useMasterSetup } from '@/composables/useMasterSetup'

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

const query = ref('')

// The order to fill the masters in: each one only links to masters set up
// before it (e.g. a Position needs its Track, Department, Designation and
// Document Types).
const STAGES = [
  {
    key: 'basics', title: 'Organisation basics', hint: 'Tracks first: designations, approval chains and rubrics belong to a track.',
    masters: [
      { doctype: 'Recruitment Track', needs: [] },
      { doctype: 'Department', needs: [] },
      { doctype: 'Designation', needs: ['Recruitment Tracks'] },
    ],
  },
  {
    key: 'form_lists', title: 'Application form lists', hint: 'The choices candidates pick from on the application form.',
    masters: [
      { doctype: 'Document Type Master', needs: [] },
      { doctype: 'Institution Master', needs: [] },
      { doctype: 'Specialization Master', needs: [] },
      { doctype: 'UGC NET Subject Master', needs: [] },
      { doctype: 'Candidate Source', needs: [] },
    ],
  },
  {
    key: 'positions', title: 'Positions', hint: 'Each post with its job code and default application form. Job openings are created from these.',
    masters: [{ doctype: 'Position', needs: ['Recruitment Tracks', 'Departments', 'Designations', 'Document Types'] }],
  },
  {
    key: 'approvals_scoring', title: 'Approvals and scoring', hint: 'Who approves green sheets, and how committees score candidates, per track.',
    masters: [
      { doctype: 'Approval Chain Template', needs: ['Recruitment Tracks', 'staff users with the approver roles'] },
      { doctype: 'Scoring Rubric Template', needs: ['Recruitment Tracks'] },
    ],
  },
]

const byDoctype = computed(() => Object.fromEntries(categories.value.flatMap((c) => c.masters).map((m) => [m.doctype, m])))

const stages = computed(() => {
  let order = 0
  const placed = new Set()
  const out = STAGES.map((st, i) => {
    const masters = st.masters
      .filter((m) => byDoctype.value[m.doctype])
      .map((m) => {
        placed.add(m.doctype)
        return { ...byDoctype.value[m.doctype], needs: m.needs, order: ++order }
      })
    return { ...st, step: i + 1, masters }
  })
  // Any master not in the list above goes last.
  const rest = Object.values(byDoctype.value).filter((m) => !placed.has(m.doctype))
  if (rest.length) {
    out.push({ key: 'other', title: 'Other', hint: 'Anything else.', step: out.length + 1, masters: rest.map((m) => ({ ...m, needs: [], order: ++order })) })
  }
  return out.filter((st) => st.masters.length).map((st) => ({ ...st, done: st.masters.every((m) => m.total) }))
})

const orderedMasters = computed(() => stages.value.flatMap((st) => st.masters))
const doneCount = computed(() => orderedMasters.value.filter((m) => m.total).length)
const emptyMasters = computed(() => orderedMasters.value.filter((m) => !m.total))

function matches(master, stage, q) {
  return [master.label, master.singular, master.description, master.doctype, stage.title, ...(master.keywords || [])]
    .join(' ')
    .toLowerCase()
    .includes(q)
}

const visibleStages = computed(() => {
  const q = query.value.trim().toLowerCase()
  return stages.value
    .map((st) => ({ ...st, masters: q ? st.masters.filter((m) => matches(m, st, q)) : st.masters }))
    .filter((st) => st.masters.length)
})

function goTo(href) {
  window.location.href = href
}
</script>
