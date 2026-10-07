<template>
  <header class="flex h-12 shrink-0 items-center gap-4 bg-brand-700 px-4 text-white shadow-sm">
    <RouterLink to="/" class="flex min-w-0 items-center gap-2.5">
      <img
        v-if="appearance.app_logo"
        :src="appearance.app_logo"
        alt=""
        class="h-7 w-7 shrink-0 rounded-md bg-white object-contain p-0.5"
      />
      <svg v-else viewBox="0 0 64 64" class="h-7 w-7 shrink-0" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill="#FFFFFF" />
        <path d="M18 46V18h13a10 10 0 0 1 0 20h-7v8h-6zm6-14h6a4 4 0 0 0 0-8h-6v8z" fill="rgb(var(--brand-700))" />
      </svg>
      <span class="truncate font-heading text-lg font-bold tracking-tight">{{ appearance.app_name }}</span>
    </RouterLink>

    <div class="flex-1" />

    <!-- Job opening search: title or job code. -->
    <div v-if="session.hasMenu('jobs')" class="relative hidden w-64 sm:block">
      <FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/70" />
      <input
        v-model="query"
        type="search"
        placeholder="Search job openings..."
        class="h-8 w-full rounded-md border border-white/25 bg-white/10 pl-8 pr-2 text-sm text-white placeholder-white/70 focus:border-white/60 focus:bg-white/15 focus:outline-none focus:ring-0"
        @focus="open = true"
        @blur="closeSoon"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="go(results[active])"
        @keydown.esc="open = false"
      />
      <div
        v-if="open && query.trim()"
        class="absolute right-0 top-10 z-20 w-80 overflow-hidden rounded-lg border bg-white py-1 text-gray-900 shadow-lg"
      >
        <div v-if="searching && !results.length" class="px-3 py-2 text-sm text-gray-500">Searching...</div>
        <div v-else-if="!results.length" class="px-3 py-2 text-sm text-gray-500">No job openings found.</div>
        <button
          v-for="(job, idx) in results"
          :key="job.name"
          class="flex w-full items-center gap-3 px-3 py-2 text-left text-sm"
          :class="idx === active ? 'bg-brand-50' : 'hover:bg-gray-50'"
          @mousedown.prevent="go(job)"
          @mouseenter="active = idx"
        >
          <FeatherIcon name="briefcase" class="h-4 w-4 shrink-0 text-brand-700" />
          <div class="min-w-0 flex-1">
            <div class="truncate font-medium">{{ job.job_title }}</div>
            <div class="truncate text-xs text-gray-500">{{ [job.position, job.department].filter(Boolean).join(' · ') }}</div>
          </div>
          <StatusBadge :status="job.status" />
        </button>
      </div>
    </div>

    <!-- Bell: what's waiting for me; click one to review it. -->
    <div v-if="session.hasMenu('approvals')" ref="bellRoot" class="relative">
      <button
        type="button"
        class="relative flex h-8 w-8 items-center justify-center rounded-md hover:bg-white/10"
        :class="bellOpen && 'bg-white/10'"
        :title="pendingCount ? `${pendingCount} pending approval${pendingCount === 1 ? '' : 's'}` : 'Notifications'"
        @click="toggleBell"
      >
        <FeatherIcon name="bell" class="h-4 w-4" />
        <span
          v-if="pendingCount"
          class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-white px-1 text-[10px] font-bold text-brand-700"
        >{{ pendingCount > 9 ? '9+' : pendingCount }}</span>
      </button>

      <div v-if="bellOpen" class="absolute right-0 top-10 z-40 w-96 overflow-hidden rounded-lg border bg-white text-gray-900 shadow-xl">
        <div class="flex items-center justify-between border-b px-4 py-2.5">
          <span class="font-semibold">Pending approvals</span>
          <span v-if="pendingCount" class="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">{{ pendingCount }}</span>
        </div>
        <div class="max-h-96 overflow-y-auto">
          <div v-if="!pending.length" class="flex flex-col items-center gap-2 px-4 py-8 text-sm text-gray-500">
            <FeatherIcon name="check-circle" class="h-6 w-6 text-green-500" />
            You're all caught up.
          </div>
          <button
            v-for="item in pending"
            :key="`${item.doctype}::${item.name}`"
            type="button"
            class="flex w-full items-start gap-3 border-b px-4 py-3 text-left last:border-0 hover:bg-brand-50"
            @click="openPending(item)"
          >
            <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700">
              <FeatherIcon name="file-text" class="h-4 w-4" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-medium">{{ item.job_title || item.job_opening }}</span>
              <span class="block truncate text-xs text-gray-500">{{ item.doctype }} · {{ item.name }}</span>
              <span class="mt-0.5 block truncate text-xs text-brand-700">
                Awaiting {{ item.approver_label }}<template v-if="item.is_override"> (on behalf)</template>
              </span>
            </span>
            <span class="shrink-0 text-xs text-gray-400">{{ timeAgo(item.submitted_on) }}</span>
          </button>
        </div>
        <RouterLink to="/approvals" class="block border-t bg-gray-50 px-4 py-2 text-center text-sm font-medium text-brand-700 hover:bg-gray-100" @click="bellOpen = false">
          View all in My Approvals
        </RouterLink>
      </div>
    </div>

    <Dropdown :options="appMenuOptions" placement="right">
      <template #default="{ open: menuOpen }">
        <button class="flex items-center gap-2 rounded-md px-1.5 py-1 hover:bg-white/10" :class="{ 'bg-white/10': menuOpen }">
          <Avatar :label="session.fullName" :image="session.userImage" size="md" />
          <span class="hidden max-w-[10rem] truncate text-sm font-medium sm:block">{{ session.fullName }}</span>
          <FeatherIcon name="chevron-down" class="h-4 w-4 text-white/80" />
        </button>
      </template>
    </Dropdown>

    <Dialog v-model="confirmLogout" :options="{ title: 'Log out?', size: 'sm' }">
      <template #body-content>
        <p class="text-sm text-gray-600">You'll be signed out of Pathways and the Desk.</p>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="confirmLogout = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="session.logout.loading" @click="session.logout.submit()">Log out</Button>
        </div>
      </template>
    </Dialog>

    <SettingsDialog v-if="session.canManageSettings || session.canManageAccess" v-model="showSettingsDialog" />
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Avatar, Button, Dialog, Dropdown, FeatherIcon } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { useSessionStore } from '@/stores/session'
import { jobOpeningService } from '@/services/jobOpenings'
import { approvalService } from '@/services/approvals'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SettingsDialog from './SettingsDialog.vue'
import { appearance } from '@/utils/theme'

const session = useSessionStore()
const router = useRouter()

// ----- search
const query = ref('')
const results = ref([])
const active = ref(0)
const open = ref(false)
const searching = ref(false)
let timer = null
let requestId = 0

watch(query, (value) => {
  clearTimeout(timer)
  const text = value.trim()
  if (!text) {
    results.value = []
    return
  }
  timer = setTimeout(() => search(text), 250)
})

async function search(text) {
  const id = ++requestId
  searching.value = true
  try {
    const like = ['like', `%${text}%`]
    // Two calls: get_all filters are AND-ed, and a match on either the
    // title or the job code should count.
    const [byTitle, byCode] = await Promise.all([
      jobOpeningService.listStaffJobs({ job_title: like }, { limit_page_length: 8 }),
      jobOpeningService.listStaffJobs({ position: like }, { limit_page_length: 8 }),
    ])
    if (id !== requestId) return
    const seen = new Set()
    results.value = [...byTitle, ...byCode].filter((j) => !seen.has(j.name) && seen.add(j.name)).slice(0, 8)
    active.value = 0
  } catch {
    if (id === requestId) results.value = []
  } finally {
    if (id === requestId) searching.value = false
  }
}

function move(step) {
  if (!results.value.length) return
  active.value = (active.value + step + results.value.length) % results.value.length
}

function go(job) {
  if (!job) return
  open.value = false
  query.value = ''
  router.push(`/jobs/${job.name}`)
}

function closeSoon() {
  setTimeout(() => (open.value = false), 100)
}

// ----- pending approvals
const pending = ref([])
const pendingCount = computed(() => pending.value.length)
const bellOpen = ref(false)
const bellRoot = ref(null)

async function loadPending() {
  if (!session.hasMenu('approvals')) return
  try {
    const rows = await approvalService.getMyPendingApprovals()
    pending.value = Array.isArray(rows) ? rows : []
  } catch {
    pending.value = []
  }
}

function toggleBell() {
  bellOpen.value = !bellOpen.value
  if (bellOpen.value) loadPending()
}

function openPending(item) {
  bellOpen.value = false
  router.push({ path: '/approvals', query: { open: `${item.doctype}::${item.name}` } })
}

function timeAgo(value) {
  if (!value) return ''
  const mins = Math.round((Date.now() - new Date(String(value).replace(' ', 'T'))) / 60000)
  if (mins < 60) return `${Math.max(mins, 1)}m`
  if (mins < 1440) return `${Math.round(mins / 60)}h`
  return `${Math.round(mins / 1440)}d`
}

function onOutsideBell(e) {
  if (bellOpen.value && bellRoot.value && !bellRoot.value.contains(e.target)) bellOpen.value = false
}
onMounted(() => document.addEventListener('mousedown', onOutsideBell))
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutsideBell))

onMounted(async () => {
  await session.fetchRoles()
  loadPending()
})
watch(() => router.currentRoute.value.path, loadPending)

// ----- user menu (moved here from the sidebar)
const showSettingsDialog = ref(false)
const confirmLogout = ref(false)

const appMenuOptions = computed(() => {
  const items = []
  // Settings holds the Roles & Permissions tab too, so access managers see it as well.
  if (session.canManageSettings || session.canManageAccess) {
    items.push({ label: 'Settings', icon: 'settings', onClick: () => (showSettingsDialog.value = true) })
  }
  if (session.canManageSettings) {
    items.push({ label: 'Email Setup', icon: 'mail', onClick: () => router.push('/settings/email') })
  }
  items.push(
    { label: 'Desk', icon: 'grid', onClick: () => (window.location.href = '/app') },
    { label: 'Log out', icon: 'log-out', onClick: () => (confirmLogout.value = true) },
  )
  return [{ group: 'Pathways', hideLabel: true, items }]
})
</script>
