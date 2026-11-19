<template>
  <!-- Tablet / desktop (md+): a rail beside the page — icons only when
       collapsed (labels as tooltips), icons + labels when expanded. -->
  <nav
    class="hidden h-full shrink-0 flex-col border-r bg-white py-3 transition-[width] duration-200 ease-in-out md:flex"
    :class="isExpanded ? 'w-60 px-3' : 'w-16 px-2.5'"
    aria-label="Main menu"
  >
    <div class="flex flex-1 flex-col gap-1 overflow-y-auto overflow-x-hidden">
      <SidebarNavLink
        v-for="item in visibleItems"
        :key="item.to"
        :to="item.to"
        :icon="item.icon"
        :label="item.label"
        :is-expanded="isExpanded"
        :force-active="item.to === sectionTo"
      />
    </div>

    <div class="mt-2 border-t pt-2">
      <SidebarNavLink
        :icon="isExpanded ? 'chevrons-left' : 'chevrons-right'"
        :label="isExpanded ? 'Collapse menu' : 'Expand menu'"
        :is-expanded="isExpanded"
        :aria-expanded="isExpanded"
        as="button"
        @click="isExpanded = !isExpanded"
      />
    </div>
  </nav>

  <!-- Phones (below md): the same menu as a drawer from the left, opened by
       the top bar's menu button. Above page content (z-40 at most), below
       dialogs (z-50). -->
  <Transition
    enter-from-class="opacity-0"
    enter-active-class="transition-opacity duration-200"
    leave-to-class="opacity-0"
    leave-active-class="transition-opacity duration-150"
  >
    <div v-if="mobileOpen" class="fixed inset-0 z-[44] bg-gray-900/40 md:hidden" aria-hidden="true" @click="closeMobile" />
  </Transition>
  <Transition
    enter-from-class="-translate-x-full"
    enter-active-class="transition-transform duration-200 ease-out"
    leave-to-class="-translate-x-full"
    leave-active-class="transition-transform duration-150 ease-in"
  >
    <nav
      v-if="mobileOpen"
      id="pathways-drawer"
      class="fixed inset-y-0 left-0 z-[45] flex w-72 max-w-[85vw] flex-col bg-white shadow-2xl md:hidden"
      style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom)"
      aria-label="Main menu"
    >
      <div class="flex h-14 shrink-0 items-center gap-2.5 border-b px-4">
        <img v-if="appearance.app_logo" :src="appearance.app_logo" alt="" class="h-8 w-8 shrink-0 rounded-md object-contain" />
        <img v-else :src="APP_ICON" alt="" class="h-8 w-8 shrink-0 rounded-md" />
        <span class="min-w-0 flex-1 truncate font-heading text-lg font-bold text-gray-900">{{ appearance.app_name }}</span>
        <button
          ref="closeButton"
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100"
          aria-label="Close menu"
          @click="closeMobile"
        >
          <FeatherIcon name="x" class="h-5 w-5" />
        </button>
      </div>
      <div class="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
        <SidebarNavLink
          v-for="item in visibleItems"
          :key="item.to"
          :to="item.to"
          :icon="item.icon"
          :label="item.label"
          :is-expanded="true"
          :force-active="item.to === sectionTo"
        />
      </div>
    </nav>
  </Transition>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import { useSidebar } from '@/composables/useSidebar'
import { appearance } from '@/utils/theme'
import SidebarNavLink from './SidebarNavLink.vue'
import { APP_ICON } from '@/utils/pwa'

const session = useSessionStore()
const { mobileOpen, closeMobile } = useSidebar()

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
  { key: 'candidates', to: '/candidates', label: 'Candidate Master', icon: 'users' },
  { key: 'applications', to: '/applications', label: 'Applications', icon: 'file-text' },
  { key: 'interviews', to: '/interviews', label: 'Interviews', icon: 'calendar' },
  { key: 'panel', to: '/panel', label: 'Interview Panel', icon: 'clipboard' },
  { key: 'selection', to: '/selection', label: 'Selection', icon: 'check-circle' },
  { key: 'approvals', to: '/approvals', label: 'My Approvals', icon: 'check-square' },
  { key: 'offers', to: '/offers', label: 'Offers', icon: 'award' },
  { key: 'documents', to: '/documents', label: 'Documents', icon: 'folder' },
  // One module for three lists: shown to whoever has any of them (its tabs).
  { key: 'onboarding', to: '/onboarding', label: 'Onboarding', icon: 'user-check', anyOf: ['documents', 'joinings', 'it_requests'] },
  { key: 'honorarium', to: '/honorarium', label: 'Panel Honorarium', icon: 'gift' },
  { key: 'communications', to: '/communications', label: 'Communications', icon: 'mail' },
  { key: 'reports', to: '/reports', label: 'Reports', icon: 'bar-chart-2' },
]

const visibleItems = computed(() =>
  ALL_ITEMS.filter((item) => item.key === 'dashboard' || (item.anyOf || [item.key]).some((key) => session.hasMenu(key))),
)

// A page outside its module's path (route meta.sections, e.g. a selection
// green sheet) lights up the first of its modules this user has.
const route = useRoute()
const sectionTo = computed(() => {
  const sections = route.meta?.sections || []
  return sections.find((to) => visibleItems.value.some((item) => item.to === to)) || null
})

// ----- phone drawer: closes on navigation, Escape, or growing to md+.
const closeButton = ref(null)

watch(() => route.fullPath, closeMobile)
watch(mobileOpen, async (open) => {
  if (open) {
    await nextTick()
    closeButton.value?.focus()
  }
})

function onKeydown(e) {
  if (e.key === 'Escape' && mobileOpen.value) closeMobile()
}

const desktop = window.matchMedia('(min-width: 768px)')
function onBreakpoint(e) {
  if (e.matches) closeMobile()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  desktop.addEventListener?.('change', onBreakpoint)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  desktop.removeEventListener?.('change', onBreakpoint)
  closeMobile()
})
</script>
