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
          <Avatar :label="profile.full_name" :image="profile.user_image" size="lg" />
          <template v-if="isExpanded">
            <div class="flex-1 overflow-hidden">
              <div class="truncate text-sm font-semibold text-gray-900">Pathways</div>
              <div class="truncate text-xs text-gray-500">{{ profile.full_name }}</div>
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

    <SettingsDialog v-if="session.hasRole('Pathways Admin')" v-model="showSettingsDialog" />
  </nav>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Dropdown, Avatar, FeatherIcon } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import { callMethod } from '@/services/api'
import SidebarNavLink from './SidebarNavLink.vue'
import SettingsDialog from './SettingsDialog.vue'

const session = useSessionStore()

const isExpanded = ref(localStorage.getItem('pathways-sidebar-expanded') !== 'false')

watch(isExpanded, (value) => {
  try {
    localStorage.setItem('pathways-sidebar-expanded', String(value))
  } catch {
    // ignore storage errors (private browsing, quota, etc.)
  }
})

const profile = reactive({ full_name: session.user, user_image: null })

onMounted(async () => {
  const data = await callMethod('pathways.api.auth.get_my_profile')
  if (data) {
    profile.full_name = data.full_name
    profile.user_image = data.user_image
  }
})

const showSettingsDialog = ref(false)

const appMenuOptions = computed(() => {
  const items = []

  if (session.hasRole('Pathways Admin')) {
    items.push({
      label: 'Settings',
      icon: 'settings',
      onClick: () => {
        showSettingsDialog.value = true
      },
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

const ALL_ITEMS = [
  { to: '/', label: 'Dashboard', icon: 'home', roles: null },
  {
    to: '/jobs',
    label: 'Job Openings',
    icon: 'briefcase',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'],
  },
  {
    to: '/applications',
    label: 'Applications',
    icon: 'file-text',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'],
  },
  {
    to: '/interviews',
    label: 'Interviews',
    icon: 'calendar',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin', 'Pathways Selection Committee Member'],
  },
  {
    to: '/approvals',
    label: 'My Approvals',
    icon: 'check-square',
    roles: [
      'Pathways PNCO',
      'Pathways Registrar',
      'Pathways Vice Chancellor',
      'Pathways CFO',
      'Pathways Dean Academics',
      'Pathways Dean Research',
      'Pathways Senior Manager Research',
      'Pathways Director People Culture',
      'Pathways Admin',
    ],
  },
  {
    to: '/offers',
    label: 'Offers',
    icon: 'award',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Registrar', 'Pathways Admin'],
  },
  {
    to: '/documents',
    label: 'Documents',
    icon: 'folder',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'],
  },
  {
    to: '/reports',
    label: 'Reports',
    icon: 'bar-chart-2',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'],
  },
]

const visibleItems = computed(() =>
  ALL_ITEMS.filter((item) => !item.roles || session.hasAnyRole(item.roles) || session.hasRole('Pathways Admin')),
)
</script>
