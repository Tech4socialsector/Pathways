<template>
  <StaffLayout>
    <PageHeader title="Onboarding" subtitle="From the accepted offer to the first day: documents, joining date and IT & Facilities" />
    <div class="flex-1 overflow-y-auto p-6">
      <div class="mb-5 flex gap-1 border-b" role="tablist">
        <RouterLink
          v-for="t in tabs"
          :key="t.slug"
          :to="`/onboarding/${t.slug}`"
          role="tab"
          :aria-selected="current?.slug === t.slug"
          class="-mb-px flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm font-medium"
          :class="current?.slug === t.slug ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          <FeatherIcon :name="t.icon" class="h-4 w-4" />{{ t.label }}
        </RouterLink>
      </div>
      <!-- Kept alive: switching tabs does not reload the lists. -->
      <KeepAlive>
        <component :is="current.component" v-if="current" :key="current.slug" />
      </KeepAlive>
      <p v-if="!tabs.length" class="text-sm text-gray-500">You do not have access to any onboarding lists.</p>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import VerificationTab from '@/components/onboarding/VerificationTab.vue'
import JoiningsTab from '@/components/onboarding/JoiningsTab.vue'
import ITRequestsTab from '@/components/onboarding/ITRequestsTab.vue'
import { useSessionStore } from '@/stores/session'

// Each tab shows for whoever has its menu (Role Permissions, as before the
// three lists moved here): Document Collection, Joining, IT request.
const ONBOARDING_TABS = [
  { slug: 'verification', menu: 'documents', label: 'Onboarding Verification', icon: 'check-square', component: VerificationTab },
  { slug: 'joinings', menu: 'joinings', label: 'Joinings', icon: 'user-check', component: JoiningsTab },
  { slug: 'it-requests', menu: 'it_requests', label: 'IT Requests', icon: 'monitor', component: ITRequestsTab },
]

const session = useSessionStore()
const route = useRoute()
const router = useRouter()

const tabs = computed(() => ONBOARDING_TABS.filter((t) => session.hasMenu(t.menu)))
const current = computed(() => tabs.value.find((t) => t.slug === route.params.tab) || null)

// /onboarding (or a tab this user cannot see) opens their first tab.
watch(
  [tabs, () => route.params.tab],
  () => {
    if (!current.value && tabs.value.length) router.replace(`/onboarding/${tabs.value[0].slug}`)
  },
  { immediate: true },
)
</script>
