<template>
  <StaffLayout>
    <PageHeader :title="form?.label || 'Master Setup'" :subtitle="form?.description || ''" back-to="/master-setup">
      <template v-if="form?.can_create" #actions>
        <Button variant="solid" icon-left="plus" :class="BTN_BRAND" @click="router.push(newRoute(form.doctype))">New {{ form.singular }}</Button>
      </template>
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto bg-gray-50/60">
      <div v-if="pageError" class="p-6">
        <EmptyState :title="pageError.title" :description="pageError.message">
          <template #action>
            <div class="flex gap-2">
              <Button v-if="pageError.retry" @click="init">Try again</Button>
              <Button variant="solid" :class="BTN_BRAND" @click="router.push('/master-setup')">Back to Master Setup</Button>
            </div>
          </template>
        </EmptyState>
      </div>

      <div v-else class="mx-auto flex max-w-6xl flex-col gap-4 p-4 md:p-6">
        <!-- Toolbar -->
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="w-full sm:w-80">
            <TextInput v-model="searchText" type="text" :placeholder="`Search ${form?.label?.toLowerCase() || 'records'}`" :aria-label="`Search ${form?.label || 'records'}`">
              <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
            </TextInput>
          </div>
          <div v-if="form?.active_field" class="flex items-center gap-1 rounded-lg border bg-white p-1 text-sm" role="tablist" aria-label="Filter by status">
            <button
              v-for="s in STATUSES"
              :key="s.value"
              type="button"
              role="tab"
              :aria-selected="status === s.value"
              class="rounded-md px-3 py-1 font-medium transition"
              :class="status === s.value ? 'bg-brand-700 text-white' : 'text-gray-600 hover:bg-gray-100'"
              @click="setQuery({ status: s.value || undefined, page: undefined })"
            >
              {{ s.label }}
            </button>
          </div>
        </div>

        <!-- Records -->
        <section class="overflow-hidden rounded-xl border bg-white shadow-sm">
          <div v-if="listError" class="flex items-center justify-between gap-3 p-5 text-sm text-red-700" role="alert">
            {{ listError }}
            <Button size="sm" @click="fetchList">Retry</Button>
          </div>

          <div v-else-if="loading && !rows.length" class="divide-y" aria-busy="true">
            <div v-for="i in 6" :key="i" class="flex items-center justify-between gap-6 px-5 py-4">
              <div class="h-4 w-56 animate-pulse rounded bg-gray-100" />
              <div class="h-4 w-24 animate-pulse rounded bg-gray-100" />
            </div>
          </div>

          <div v-else-if="!rows.length" class="flex flex-col items-center gap-3 px-6 py-14 text-center">
            <span class="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-700">
              <FeatherIcon :name="form?.icon || 'database'" class="h-5 w-5" />
            </span>
            <p class="text-base font-medium text-gray-900">
              {{ isFiltered ? 'No records match' : `No ${form?.label?.toLowerCase() || 'records'} yet` }}
            </p>
            <p class="text-p-sm text-gray-500">
              {{ isFiltered ? 'Try another search or status.' : `Add the first ${form?.singular?.toLowerCase() || 'record'} to get started.` }}
            </p>
            <Button v-if="isFiltered" @click="clearFilters">Clear filters</Button>
            <Button v-else-if="form?.can_create" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="router.push(newRoute(form.doctype))">
              New {{ form.singular }}
            </Button>
          </div>

          <div v-else class="overflow-x-auto" :class="loading && 'opacity-60 transition-opacity'">
            <table class="w-full min-w-[640px] text-sm">
              <thead class="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                <tr>
                  <th class="px-5 py-3 font-medium">Name</th>
                  <th v-for="c in columns" :key="c.fieldname" class="px-5 py-3 font-medium">{{ c.label }}</th>
                  <th v-if="form?.active_field" class="px-5 py-3 font-medium">Status</th>
                  <th class="px-5 py-3 text-right font-medium">Last updated</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                <tr
                  v-for="r in rows"
                  :key="r.name"
                  class="cursor-pointer transition hover:bg-gray-50"
                  @click="router.push(editRoute(form.doctype, r.name))"
                >
                  <td class="px-5 py-3">
                    <RouterLink :to="editRoute(form.doctype, r.name)" class="text-base font-medium text-gray-900 hover:text-brand-700" @click.stop>
                      {{ r.title }}
                    </RouterLink>
                    <div v-if="r.title !== r.name" class="mt-0.5 text-xs text-gray-500">{{ r.name }}</div>
                  </td>
                  <td v-for="c in columns" :key="c.fieldname" class="px-5 py-3 text-gray-700">{{ display(c, r[c.fieldname]) }}</td>
                  <td v-if="form?.active_field" class="px-5 py-3">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
                      :class="r.active ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'"
                    >
                      <span class="h-1.5 w-1.5 rounded-full" :class="r.active ? 'bg-brand-600' : 'bg-gray-400'" />
                      {{ r.active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-5 py-3 text-right text-gray-500">{{ dayjs(r.modified).format('DD MMM YYYY') }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <footer v-if="total > PAGE_SIZE && !listError" class="flex flex-wrap items-center justify-between gap-3 border-t px-5 py-3 text-sm text-gray-600">
            <span class="tabular-nums">{{ rangeStart }}–{{ rangeEnd }} of {{ total }}</span>
            <div class="flex gap-2">
              <Button :disabled="page <= 1 || loading" icon-left="chevron-left" @click="setQuery({ page: page - 1 > 1 ? String(page - 1) : undefined })">Previous</Button>
              <Button :disabled="page >= pageCount || loading" icon-right="chevron-right" @click="setQuery({ page: String(page + 1) })">Next</Button>
            </div>
          </footer>
          <footer v-else-if="rows.length && !listError" class="border-t px-5 py-3 text-sm text-gray-500">
            {{ total }} {{ total === 1 ? 'record' : 'records' }}
          </footer>
        </section>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Button, FeatherIcon, TextInput } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { masterSetupService } from '@/services/masterSetup'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { editRoute, errorText, newRoute, resolveMaster } from '@/utils/masterForm'

const props = defineProps({
  slug: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 20
const STATUSES = [
  { value: '', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

const form = ref(null)
const pageError = ref(null)

// Search, status and page live in the URL, so Back from a record returns to
// the same view.
const q = computed(() => String(route.query.q || ''))
const status = computed(() => (['active', 'inactive'].includes(route.query.status) ? route.query.status : ''))
const page = computed(() => Math.max(parseInt(route.query.page, 10) || 1, 1))
const isFiltered = computed(() => Boolean(q.value || status.value))

function setQuery(patch) {
  const query = { ...route.query, ...patch }
  for (const k of Object.keys(query)) if (query[k] === undefined || query[k] === '') delete query[k]
  router.replace({ query })
}
function clearFilters() {
  searchText.value = ''
  setQuery({ q: undefined, status: undefined, page: undefined })
}

const searchText = ref(q.value)
let searchTimer = null
watch(searchText, (text) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    if (text.trim() !== q.value) setQuery({ q: text.trim() || undefined, page: undefined })
  }, 300)
})
watch(q, (value) => {
  if (value !== searchText.value.trim()) searchText.value = value
})
onBeforeUnmount(() => clearTimeout(searchTimer))

async function init() {
  pageError.value = null
  form.value = null
  try {
    const master = await resolveMaster(props.slug)
    if (!master) {
      pageError.value = { title: 'Master not found', message: 'This master does not exist, or you cannot manage it.' }
      return
    }
    form.value = await masterSetupService.getForm(master.doctype)
  } catch (e) {
    const denied = e?.exc_type === 'PermissionError' || e?.status === 403
    pageError.value = { title: denied ? 'No access' : 'Could not load', message: errorText(e), retry: !denied }
  }
}

const rows = ref([])
const columns = ref([])
const total = ref(0)
const loading = ref(false)
const listError = ref('')
const pageCount = computed(() => Math.max(Math.ceil(total.value / PAGE_SIZE), 1))
const rangeStart = computed(() => (page.value - 1) * PAGE_SIZE + 1)
const rangeEnd = computed(() => Math.min(page.value * PAGE_SIZE, total.value))

let listRequest = 0
async function fetchList() {
  if (!form.value) return
  const request = ++listRequest
  loading.value = true
  listError.value = ''
  try {
    const res = await masterSetupService.getList(form.value.doctype, {
      txt: q.value,
      status: status.value,
      start: (page.value - 1) * PAGE_SIZE,
      pageLength: PAGE_SIZE,
    })
    if (request !== listRequest) return
    rows.value = res?.rows || []
    columns.value = res?.columns || []
    total.value = res?.total || 0
    // A page past the end (records deleted meanwhile) falls back to the last one.
    if (!rows.value.length && total.value && page.value > 1) setQuery({ page: pageCount.value > 1 ? String(pageCount.value) : undefined })
  } catch (e) {
    if (request === listRequest) listError.value = errorText(e, 'Could not load the records.')
  } finally {
    if (request === listRequest) loading.value = false
  }
}

watch(() => props.slug, async () => {
  rows.value = []
  await init()
  fetchList()
}, { immediate: true })
watch([q, status, page], fetchList)

function display(column, value) {
  if (value === null || value === undefined || value === '') return '—'
  if (column.fieldtype === 'Check') return Number(value) ? 'Yes' : 'No'
  if (column.fieldtype === 'Percent') return `${value}%`
  return String(value)
}
</script>
