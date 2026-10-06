<template>
  <nav
    class="flex h-full flex-col border-r bg-gray-50 p-2 transition-all duration-200 ease-in-out"
    :class="isExpanded ? 'w-56' : 'w-14'"
  >
    <Dropdown :options="appMenuOptions" placement="left">
      <template #default="{ open }">
        <button
          class="mb-3 flex w-full items-center gap-2 rounded px-2 py-1.5 text-left hover:bg-gray-100"
          :class="{ 'bg-gray-100': open }"
        >
          <Avatar :label="session.fullName" :image="session.userImage" size="lg" />
          <template v-if="isExpanded">
            <div class="flex-1 overflow-hidden">
              <div class="truncate text-sm font-semibold text-gray-900">Pathways</div>
              <div class="truncate text-xs text-gray-500">{{ session.fullName }}</div>
            </div>
            <FeatherIcon name="chevron-down" class="h-4 w-4 shrink-0 text-gray-500" />
          </template>
        </button>
      </template>
    </Dropdown>

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

    <SettingsDialog v-if="session.canManageSettings" v-model="showSettingsDialog" />
  </nav>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Dropdown, Avatar, FeatherIcon } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import SidebarNavLink from './SidebarNavLink.vue'
import SettingsDialog from './SettingsDialog.vue'

const session = useSessionStore()
const router = useRouter()

const isExpanded = ref(localStorage.getItem('pathways-sidebar-expanded') !== 'false')

watch(isExpanded, (value) => {
  try {
    localStorage.setItem('pathways-sidebar-expanded', String(value))
  } catch {
    // ignore storage errors (private browsing, quota, etc.)
  }
})

onMounted(() => session.fetchRoles())

const showSettingsDialog = ref(false)

const appMenuOptions = computed(() => {
  const items = []

  if (session.canManageSettings) {
    items.push({
      label: 'Settings',
      icon: 'settings',
      onClick: () => {
        showSettingsDialog.value = true
      },
    })
  }

  if (session.canManageAccess) {
    items.push({
      label: 'Roles & Permissions',
      icon: 'shield',
      onClick: () => router.push('/settings/access'),
    })
  }

  items.push(
    {
      label: 'Desk',
      icon: 'grid',
      onClick: () => {
        window.location.href = '/app'
      },
    },
    {
      label: 'Log out',
      icon: 'log-out',
      onClick: () => session.logout.submit(),
    },
  )

  return [{ group: 'Pathways', hideLabel: true, items }]
})

// Which entries a user sees is decided server-side from Role Permissions
// (pathways.api.access.get_my_access / MENU_ITEMS): granting a role read
// on a DocType in Roles & Permissions is what reveals its menu.
const ALL_ITEMS = [
  { key: 'dashboard', to: '/', label: 'Dashboard', icon: 'home' },
  { key: 'master_setup', to: '/master-setup', label: 'Master Setup', icon: 'sliders' },
  { key: 'jobs', to: '/jobs', label: 'Job Openings', icon: 'briefcase' },
  { key: 'applications', to: '/applications', label: 'Applications', icon: 'file-text' },
  { key: 'interviews', to: '/interviews', label: 'Interviews', icon: 'calendar' },
  { key: 'approvals', to: '/approvals', label: 'My Approvals', icon: 'check-square' },
  { key: 'offers', to: '/offers', label: 'Offers', icon: 'award' },
  { key: 'documents', to: '/documents', label: 'Documents', icon: 'folder' },
  { key: 'reports', to: '/reports', label: 'Reports', icon: 'bar-chart-2' },
]

const visibleItems = computed(() =>
  ALL_ITEMS.filter((item) => item.key === 'dashboard' || session.hasMenu(item.key)),
)
</script>
