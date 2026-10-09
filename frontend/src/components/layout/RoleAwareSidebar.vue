<template>
  <nav
    class="flex h-full flex-col border-r bg-white px-2 py-3 transition-all duration-200 ease-in-out"
    :class="isExpanded ? 'w-56' : 'w-14'"
  >
    <div class="flex flex-1 flex-col gap-0.5 overflow-y-auto overflow-x-hidden">
      <SidebarNavLink
        v-for="item in visibleItems"
        :key="item.to"
        :to="item.to"
        :icon="item.icon"
        :label="item.label"
        :is-expanded="isExpanded"
      />
    </div>

    <div class="border-t pt-2">
      <SidebarNavLink
        :icon="isExpanded ? 'chevron-left' : 'chevron-right'"
        :label="isExpanded ? 'Collapse' : 'Expand'"
        :is-expanded="isExpanded"
        as="button"
        @click="isExpanded = !isExpanded"
      />
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useSessionStore } from '@/stores/session'
import SidebarNavLink from './SidebarNavLink.vue'

const session = useSessionStore()

// Collapsed by default; once the user expands or collapses it, that choice
// is remembered. (New key: the old 'pathways-sidebar-expanded' defaulted to
// expanded, so existing browsers would never have picked up the new default.)
const SIDEBAR_KEY = 'pathways-sidebar'

function readExpanded() {
  try {
    return localStorage.getItem(SIDEBAR_KEY) === 'expanded'
  } catch {
    return false
  }
}

const isExpanded = ref(readExpanded())

watch(isExpanded, (value) => {
  try {
    localStorage.setItem(SIDEBAR_KEY, value ? 'expanded' : 'collapsed')
  } catch {
    // ignore storage errors (private browsing, quota, etc.)
  }
})

onMounted(() => session.fetchRoles())

// Which entries a user sees is decided server-side from Role Permissions
// (pathways.api.access.get_my_access / MENU_ITEMS): granting a role read
// on a DocType in Roles & Permissions is what reveals its menu.
const ALL_ITEMS = [
  { key: 'dashboard', to: '/', label: 'Dashboard', icon: 'home' },
  { key: 'master_setup', to: '/master-setup', label: 'Master Setup', icon: 'sliders' },
  { key: 'jobs', to: '/jobs', label: 'Job Openings', icon: 'briefcase' },
  { key: 'applications', to: '/applications', label: 'Applications', icon: 'file-text' },
  { key: 'interviews', to: '/interviews', label: 'Interviews', icon: 'calendar' },
  { key: 'panel', to: '/panel', label: 'Interview Panel', icon: 'clipboard' },
  { key: 'approvals', to: '/approvals', label: 'My Approvals', icon: 'check-square' },
  { key: 'offers', to: '/offers', label: 'Offers', icon: 'award' },
  { key: 'documents', to: '/documents', label: 'Documents', icon: 'folder' },
  { key: 'reports', to: '/reports', label: 'Reports', icon: 'bar-chart-2' },
]

const visibleItems = computed(() =>
  ALL_ITEMS.filter((item) => item.key === 'dashboard' || session.hasMenu(item.key)),
)
</script>
