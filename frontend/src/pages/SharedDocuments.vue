<template>
  <StaffLayout>
    <PageHeader
      title="Shared documents"
      :subtitle="data?.can_manage
        ? 'Candidate documents the recruitment team has shared with each panellist.'
        : 'Candidate documents the recruitment team has shared with you for your interviews.'"
      back-to="/panel"
    />
    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div v-if="loading && !data" class="grid gap-3">
        <div v-for="i in 3" :key="i" class="h-24 animate-pulse rounded-xl border bg-white" />
      </div>
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <template v-else-if="data">
        <div class="mb-4 flex flex-wrap items-center gap-2">
          <label v-if="jobOptions.length > 1" class="flex items-center gap-2 text-sm text-gray-700">
            <span class="font-medium">Position</span>
            <select
              v-model="job"
              class="min-w-[16rem] rounded-md border-gray-300 py-1 text-sm focus:border-brand-700 focus:ring-brand-700"
              aria-label="Position"
            >
              <option value="">All positions ({{ data.rows.length }})</option>
              <option v-for="j in jobOptions" :key="j.value" :value="j.value">{{ j.label }} ({{ j.count }})</option>
            </select>
          </label>
          <select
            v-if="data.can_manage && panellistOptions.length > 1"
            v-model="panellist"
            class="rounded-md border-gray-300 py-1 text-sm focus:border-brand-700 focus:ring-brand-700"
            aria-label="Panellist"
          >
            <option value="">All panellists</option>
            <option v-for="p in panellistOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
          <input
            v-model="search"
            type="search"
            class="ml-auto w-64 rounded-md border-gray-300 text-sm focus:border-brand-700 focus:ring-brand-700"
            placeholder="Search candidate or document…"
            aria-label="Search"
          />
        </div>

        <div v-if="!groups.length" class="rounded-xl border border-dashed bg-white px-6 py-12 text-center text-sm text-gray-500">
          <FeatherIcon name="folder" class="mx-auto mb-2 h-6 w-6 text-gray-300" />
          {{ data.rows.length ? 'Nothing matches your search.' : 'No documents have been shared yet.' }}
        </div>

        <section v-for="g in groups" :key="g.job_opening" class="mb-5 overflow-hidden rounded-xl border bg-white shadow-sm">
          <header class="flex flex-wrap items-center justify-between gap-2 border-b bg-gray-50/60 px-5 py-3">
            <div>
              <h2 class="font-semibold text-gray-900">{{ g.job_title }}</h2>
              <p class="text-xs text-gray-500">{{ g.rows.length }} {{ data.can_manage ? 'share' : 'candidate' }}{{ g.rows.length === 1 ? '' : 's' }}</p>
            </div>
          </header>
          <ul class="divide-y">
            <li v-for="r in g.rows" :key="r.name" class="px-5 py-3">
              <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <div>
                  <span class="font-medium text-gray-900">{{ r.candidate_name }}</span>
                  <span class="ml-2 font-mono text-xs text-gray-500">{{ r.application_id }}</span>
                  <span v-if="data.can_manage" class="ml-2 text-xs text-gray-600">→ {{ r.panelist_name }}</span>
                </div>
                <span class="text-xs text-gray-500">
                  Shared {{ r.shared_on ? dayjs(r.shared_on).format('DD MMM YYYY, h:mm A') : '' }}<template v-if="r.shared_by"> by {{ r.shared_by }}</template>
                </span>
              </div>
              <p v-if="r.note" class="mt-1 whitespace-pre-line rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-900">{{ r.note }}</p>
              <div v-if="!r.documents.length" class="mt-2 text-xs text-gray-500">The shared documents are no longer on the application.</div>
              <div v-else class="mt-2 flex flex-wrap gap-2">
                <button
                  v-for="(d, i) in r.documents"
                  :key="d.file_url + i"
                  type="button"
                  class="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs text-gray-800 hover:border-brand-300 hover:bg-brand-50"
                  @click="openViewer(r, i)"
                >
                  <FeatherIcon :name="d.kind === 'image' ? 'image' : 'file-text'" class="h-3.5 w-3.5 text-brand-700" />{{ d.label }}
                </button>
              </div>
            </li>
          </ul>
        </section>
      </template>
    </div>

    <DocumentViewer
      v-model:open="viewer.open"
      :title="`${viewer.row?.candidate_name || ''} · ${viewer.row?.application_id || ''}`"
      :documents="viewer.row?.documents || []"
      :start-index="viewer.index"
    />
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import { panelService } from '@/services/panel'

const route = useRoute()
const router = useRouter()
const data = ref(null)
const loading = ref(false)
const error = ref('')
const search = ref('')
const panellist = ref('')
// From the email link: ?job=<Job Opening>
const job = ref(typeof route.query.job === 'string' ? route.query.job : '')
watch(job, (value) => router.replace({ query: value ? { job: value } : {} }))

const jobOptions = computed(() => {
  const map = new Map()
  for (const r of data.value?.rows || []) {
    if (!map.has(r.job_opening)) map.set(r.job_opening, { value: r.job_opening, label: r.position && r.position !== r.job_title ? `${r.job_title} · ${r.position}` : r.job_title, count: 0 })
    map.get(r.job_opening).count++
  }
  return [...map.values()]
})
const panellistOptions = computed(() => {
  const map = new Map()
  for (const r of data.value?.rows || []) map.set(r.panelist, { value: r.panelist, label: r.panelist_name })
  return [...map.values()].sort((a, b) => a.label.localeCompare(b.label))
})
const groups = computed(() => {
  const q = search.value.trim().toLowerCase()
  const out = new Map()
  for (const r of data.value?.rows || []) {
    // A job that is no longer listed (e.g. from an old link) shows everything.
    if (job.value && jobOptions.value.some((j) => j.value === job.value) && r.job_opening !== job.value) continue
    if (panellist.value && r.panelist !== panellist.value) continue
    if (q && ![r.candidate_name, r.application_id, r.panelist_name, ...r.documents.map((d) => d.label)].some((v) => (v || '').toLowerCase().includes(q))) continue
    if (!out.has(r.job_opening)) out.set(r.job_opening, { job_opening: r.job_opening, job_title: r.job_title, rows: [] })
    out.get(r.job_opening).rows.push(r)
  }
  return [...out.values()]
})

const viewer = reactive({ open: false, row: null, index: 0 })
function openViewer(row, index) {
  Object.assign(viewer, { open: true, row, index })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await panelService.getSharedDocuments()
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load the shared documents.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>
