<template>
  <nav class="flex h-full w-56 flex-col border-r bg-gray-50 p-3">
    <div class="mb-4 px-2 text-lg font-semibold text-gray-900">Pathways</div>
    <div class="flex flex-1 flex-col gap-0.5">
      <router-link
        v-for="item in visibleItems"
        :key="item.to"
        :to="item.to"
        class="rounded px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
        active-class="bg-gray-200 font-medium text-gray-900"
      >
        {{ item.label }}
      </router-link>
    </div>
    <div class="border-t pt-3">
      <div class="px-2 text-xs text-gray-500">{{ session.user }}</div>
      <button
        class="w-full rounded px-2 py-1.5 text-left text-sm text-gray-700 hover:bg-gray-100"
        @click="session.logout.submit()"
      >
        Log out
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()

const ALL_ITEMS = [
  { to: '/', label: 'Dashboard', roles: null },
  { to: '/jobs', label: 'Job Openings', roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'] },
  { to: '/applications', label: 'Applications', roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'] },
  {
    to: '/interviews',
    label: 'Interviews',
    roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin', 'Pathways Selection Committee Member'],
  },
  {
    to: '/approvals',
    label: 'My Approvals',
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
  { to: '/offers', label: 'Offers', roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Registrar', 'Pathways Admin'] },
  { to: '/documents', label: 'Documents', roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'] },
  { to: '/reports', label: 'Reports', roles: ['Pathways Recruiter', 'Pathways PNCO', 'Pathways Admin'] },
]

const visibleItems = computed(() =>
  ALL_ITEMS.filter((item) => !item.roles || session.hasAnyRole(item.roles) || session.hasRole('Pathways Admin')),
)
</script>
