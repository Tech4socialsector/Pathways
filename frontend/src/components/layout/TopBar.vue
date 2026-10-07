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

    <RouterLink
      v-if="session.hasMenu('approvals')"
      to="/approvals"
      class="relative flex h-8 w-8 items-center justify-center rounded-md hover:bg-white/10"
      :title="pendingCount ? `${pendingCount} pending approval${pendingCount === 1 ? '' : 's'}` : 'My Approvals'"
    >
      <FeatherIcon name="bell" class="h-4 w-4" />
      <span
        v-if="pendingCount"
        class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-white px-1 text-[10px] font-bold text-brand-700"
      >{{ pendingCount > 9 ? '9+' : pendingCount }}</span>
    </RouterLink>

    <Dropdown :options="appMenuOptions" placement="right">
      <template #default="{ open: menuOpen }">
        <button class="flex items-center gap-2 rounded-md px-1.5 py-1 hover:bg-white/10" :class="{ 'bg-white/10': menuOpen }">
          <Avatar :label="session.fullName" :image="session.userImage" size="md" />
          <span class="hidden max-w-[10rem] truncate text-sm font-medium sm:block">{{ session.fullName }}</span>
          <FeatherIcon name="chevron-down" class="h-4 w-4 text-white/80" />
        </button>
      </template>
    </Dropdown>

    <SettingsDialog v-if="session.canManageSettings" v-model="showSettingsDialog" />
  </header>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Avatar, Dropdown, FeatherIcon } from 'frappe-ui'
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
const pendingCount = ref(0)

async function loadPending() {
  if (!session.hasMenu('approvals')) return
  try {
    const pending = await approvalService.getMyPendingApprovals()
    pendingCount.value = Array.isArray(pending) ? pending.length : 0
  } catch {
    pendingCount.value = 0
  }
}

onMounted(async () => {
  await session.fetchRoles()
  loadPending()
})
watch(() => router.currentRoute.value.path, loadPending)

// ----- user menu (moved here from the sidebar)
const showSettingsDialog = ref(false)

const appMenuOptions = computed(() => {
  const items = []
  if (session.canManageSettings) {
    items.push({ label: 'Settings', icon: 'settings', onClick: () => (showSettingsDialog.value = true) })
  }
  if (session.canManageAccess) {
    items.push({ label: 'Roles & Permissions', icon: 'shield', onClick: () => router.push('/settings/access') })
  }
  items.push(
    { label: 'Desk', icon: 'grid', onClick: () => (window.location.href = '/app') },
    { label: 'Log out', icon: 'log-out', onClick: () => session.logout.submit() },
  )
  return [{ group: 'Pathways', hideLabel: true, items }]
})
</script>
