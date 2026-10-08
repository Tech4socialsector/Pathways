<template>
  <StaffLayout>
    <PageHeader
      title="Master Setup"
      subtitle="Reference data behind job openings, application forms, approvals and scoring. Set it up in the order shown."
      :breadcrumbs="[{ label: 'Dashboard', to: '/' }, { label: 'Master Setup' }]"
    />
    <div class="flex min-h-0 flex-1 overflow-hidden bg-gray-50/60">
      <div v-if="loading" class="flex-1 p-6"><div class="h-64 animate-pulse rounded-xl border bg-white" /></div>

      <div v-else-if="isPermissionError" class="flex-1 p-6">
        <EmptyState title="You don't have access to Master Setup" description="Ask a Pathways administrator if you need to manage master records." />
      </div>

      <div v-else-if="error" class="flex-1 p-6">
        <EmptyState title="Could not load Master Setup" :description="errorMessage">
          <template #action><Button @click="fetchMasterSetup">Try again</Button></template>
        </EmptyState>
      </div>

      <template v-else>
        <!-- Masters, in setup order -->
        <aside class="flex w-80 shrink-0 flex-col border-r bg-white">
          <div class="border-b p-3">
            <TextInput v-model="query" type="text" placeholder="Search masters">
              <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
            </TextInput>
          </div>
          <nav class="min-h-0 flex-1 overflow-y-auto p-2" aria-label="Masters">
            <div v-for="stage in visibleStages" :key="stage.key" class="mb-3">
              <div class="px-2 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {{ stage.step }}. {{ stage.title }}
              </div>
              <button
                v-for="m in stage.masters"
                :key="m.doctype"
                type="button"
                class="group flex w-full items-center gap-3 rounded-md border-l-2 px-2.5 py-2 text-left text-sm transition"
                :class="selected?.doctype === m.doctype ? 'border-brand-700 bg-brand-50 text-brand-800' : 'border-transparent text-gray-700 hover:bg-gray-50'"
                :aria-current="selected?.doctype === m.doctype ? 'true' : undefined"
                @click="select(m)"
              >
                <FeatherIcon :name="m.icon" class="h-4 w-4 shrink-0" :class="selected?.doctype === m.doctype ? 'text-brand-700' : 'text-gray-400'" />
                <span class="min-w-0 flex-1 truncate" :class="selected?.doctype === m.doctype && 'font-semibold'">{{ m.label }}</span>
                <span class="shrink-0 text-xs tabular-nums" :class="m.total ? 'text-gray-500' : 'font-semibold text-orange-600'">{{ m.total || 0 }}</span>
              </button>
            </div>
            <p v-if="!visibleStages.length" class="px-2 py-6 text-center text-sm text-gray-500">No masters match “{{ query }}”.</p>
          </nav>
        </aside>

        <!-- Selected master -->
        <main v-if="selected" class="min-w-0 flex-1 overflow-y-auto p-6">
          <div class="mx-auto flex max-w-4xl flex-col gap-5">
            <section class="rounded-xl border bg-white shadow-sm">
              <div class="flex flex-wrap items-start justify-between gap-4 border-b p-5">
                <div class="flex min-w-0 items-start gap-4">
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                    <FeatherIcon :name="selected.icon" class="h-5 w-5" />
                  </span>
                  <div class="min-w-0">
                    <div class="text-xs font-medium uppercase tracking-wide text-gray-500">Step {{ selected.step }} · {{ selected.stageTitle }}</div>
                    <h2 class="mt-0.5 font-heading text-xl font-semibold text-gray-900">{{ selected.label }}</h2>
                    <p class="mt-0.5 text-sm text-gray-600">{{ selected.description }}</p>
                  </div>
                </div>
                <div class="flex shrink-0 gap-2">
                  <Button variant="outline" icon-left="list" @click="goTo(selected.route)">Open full list</Button>
                  <Button v-if="selected.can_create" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="goTo(selected.new_route)">
                    New {{ selected.singular }}
                  </Button>
                </div>
              </div>
              <dl class="grid grid-cols-2 divide-x divide-y sm:grid-cols-4 sm:divide-y-0">
                <div v-for="f in facts" :key="f.label" class="px-5 py-4">
                  <dt class="text-xs text-gray-500">{{ f.label }}</dt>
                  <dd class="mt-1 text-lg font-semibold tabular-nums" :class="f.tone || 'text-gray-900'">{{ f.value }}</dd>
                </div>
              </dl>
            </section>

            <section class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div class="rounded-xl border bg-white p-5 shadow-sm">
                <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">Set up after</h3>
                <p v-if="!selected.needs.length" class="mt-2 text-sm text-gray-700">Nothing. This master can be set up first.</p>
                <ul v-else class="mt-2 flex flex-wrap gap-1.5">
                  <li v-for="n in selected.needs" :key="n">
                    <button
                      v-if="byLabel[n]"
                      type="button"
                      class="rounded-md border px-2 py-0.5 text-sm text-gray-700 hover:border-brand-200 hover:text-brand-700"
                      @click="select(byLabel[n])"
                    >{{ n }}</button>
                    <span v-else class="rounded-md border px-2 py-0.5 text-sm text-gray-600">{{ n }}</span>
                  </li>
                </ul>
              </div>
              <div class="rounded-xl border bg-white p-5 shadow-sm">
                <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">Used by</h3>
                <p class="mt-2 text-sm text-gray-700">{{ selected.usedBy }}</p>
              </div>
            </section>

            <section class="overflow-hidden rounded-xl border bg-white shadow-sm">
              <header class="flex items-center justify-between border-b px-5 py-3">
                <h3 class="text-sm font-semibold text-gray-900">Recently updated</h3>
                <button type="button" class="text-sm font-medium text-brand-700 hover:underline" @click="goTo(selected.route)">
                  View all {{ selected.total || 0 }}
                </button>
              </header>
              <div v-if="records.loading" class="p-5 text-sm text-gray-500">Loading…</div>
              <div v-else-if="records.error" class="p-5 text-sm text-red-700">{{ records.error }}</div>
              <div v-else-if="!records.rows.length" class="flex flex-col items-center gap-2 p-8 text-center text-sm text-gray-500">
                No {{ selected.label.toLowerCase() }} yet.
                <Button v-if="selected.can_create" size="sm" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="goTo(selected.new_route)">
                  Add the first {{ selected.singular.toLowerCase() }}
                </Button>
              </div>
              <table v-else class="w-full text-sm">
                <thead class="bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <tr>
                    <th class="px-5 py-2 font-medium">Name</th>
                    <th v-if="records.rows.some((r) => r.active !== null)" class="px-5 py-2 font-medium">Status</th>
                    <th class="px-5 py-2 text-right font-medium">Last updated</th>
                  </tr>
                </thead>
                <tbody class="divide-y">
                  <tr v-for="r in records.rows" :key="r.name" class="cursor-pointer hover:bg-gray-50" @click="goTo(r.route)">
                    <td class="px-5 py-2.5">
                      <div class="font-medium text-gray-900">{{ r.title }}</div>
                      <div v-if="r.title !== r.name" class="text-xs text-gray-500">{{ r.name }}</div>
                    </td>
                    <td v-if="records.rows.some((x) => x.active !== null)" class="px-5 py-2.5">
                      <span
                        v-if="r.active !== null"
                        class="rounded-full px-2 py-0.5 text-xs font-medium"
                        :class="r.active ? 'bg-gray-100 text-gray-700' : 'bg-orange-50 text-orange-700'"
                      >{{ r.active ? 'Active' : 'Inactive' }}</span>
                    </td>
                    <td class="px-5 py-2.5 text-right text-gray-500">{{ dayjs(r.modified).format('DD MMM YYYY') }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
          </div>
        </main>
      </template>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, FeatherIcon, TextInput } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useMasterSetup } from '@/composables/useMasterSetup'
import { masterSetupService } from '@/services/masterSetup'
import { BTN_BRAND } from '@/utils/buttonStyles'

const route = useRoute()
const router = useRouter()
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
    masters: [
      { doctype: 'Recruitment Track', needs: [], usedBy: 'Designations, positions, job openings, approval chains and scoring rubrics.' },
      { doctype: 'Department', needs: [], usedBy: 'Positions and job openings.' },
      { doctype: 'Designation', needs: ['Recruitment Tracks'], usedBy: 'Positions and job openings.' },
    ],
  },
  {
    key: 'form_lists',
    title: 'Application form lists',
    masters: [
      { doctype: 'Document Type Master', needs: [], usedBy: 'Required documents on positions and job openings, and the uploads on applications.' },
      { doctype: 'Institution Master', needs: [], usedBy: 'The college / university list on the application form.' },
      { doctype: 'Specialization Master', needs: [], usedBy: 'The specialisation question on Faculty application forms.' },
      { doctype: 'UGC NET Subject Master', needs: [], usedBy: 'The NET subject question on Faculty application forms.' },
      { doctype: 'Candidate Source', needs: [], usedBy: '"Where did you hear about us" on the application form, and the Source report.' },
    ],
  },
  {
    key: 'positions',
    title: 'Positions',
    masters: [
      {
        doctype: 'Position',
        needs: ['Recruitment Tracks', 'Departments', 'Designations', 'Document Types'],
        usedBy: 'Job openings: a new job opening copies its position\'s details and application form.',
      },
    ],
  },
  {
    key: 'approvals_scoring',
    title: 'Approvals and scoring',
    masters: [
      { doctype: 'Approval Chain Template', needs: ['Recruitment Tracks', 'Staff users with the approver roles'], usedBy: 'Pre- and post-interview green sheets (who approves, in what order).' },
      { doctype: 'Scoring Rubric Template', needs: ['Recruitment Tracks'], usedBy: 'Shortlisting scores and interview assessments.' },
    ],
  },
]

const byDoctype = computed(() => Object.fromEntries(categories.value.flatMap((c) => c.masters).map((m) => [m.doctype, m])))

const stages = computed(() => {
  const placed = new Set()
  const out = STAGES.map((st, i) => ({
    key: st.key,
    title: st.title,
    step: i + 1,
    masters: st.masters
      .filter((m) => byDoctype.value[m.doctype])
      .map((m) => {
        placed.add(m.doctype)
        return { ...byDoctype.value[m.doctype], needs: m.needs, usedBy: m.usedBy, step: i + 1, stageTitle: st.title }
      }),
  }))
  const rest = Object.values(byDoctype.value).filter((m) => !placed.has(m.doctype))
  if (rest.length) {
    const step = out.length + 1
    out.push({ key: 'other', title: 'Other', step, masters: rest.map((m) => ({ ...m, needs: [], usedBy: '—', step, stageTitle: 'Other' })) })
  }
  return out.filter((st) => st.masters.length)
})

const allMasters = computed(() => stages.value.flatMap((st) => st.masters))
const byLabel = computed(() => Object.fromEntries(allMasters.value.map((m) => [m.label, m])))

const query = ref('')
const visibleStages = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return stages.value
  return stages.value
    .map((st) => ({
      ...st,
      masters: st.masters.filter((m) =>
        [m.label, m.singular, m.description, m.doctype, ...(m.keywords || [])].join(' ').toLowerCase().includes(q),
      ),
    }))
    .filter((st) => st.masters.length)
})

// The selected master is kept in the URL (?master=Position), so a refresh or
// the back button returns to it.
const selected = computed(() => {
  const want = route.query.master
  return allMasters.value.find((m) => m.doctype === want) || allMasters.value[0] || null
})
function select(m) {
  router.replace({ query: { ...route.query, master: m.doctype } })
}

const facts = computed(() => {
  const m = selected.value
  if (!m) return []
  const inactive = m.inactive || 0
  return [
    { label: 'Records', value: m.total || 0, tone: m.total ? '' : 'text-orange-600' },
    { label: 'Active', value: m.inactive == null ? '—' : (m.total || 0) - inactive },
    { label: 'Inactive', value: m.inactive == null ? '—' : inactive },
    { label: 'Last updated', value: m.last_updated ? dayjs(m.last_updated).format('DD MMM YYYY') : '—' },
  ]
})

const records = reactive({ rows: [], loading: false, error: '' })
watch(
  () => selected.value?.doctype,
  async (doctype) => {
    if (!doctype) return
    records.loading = true
    records.error = ''
    try {
      records.rows = (await masterSetupService.getMasterRecords(doctype, 8)) || []
    } catch (e) {
      records.rows = []
      records.error = e?.messages?.[0] || 'Could not load the records.'
    } finally {
      records.loading = false
    }
  },
  { immediate: true },
)

function goTo(href) {
  window.location.href = href
}
</script>
