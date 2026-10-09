<template>
  <StaffLayout>
    <PageHeader :title="data?.candidate.full_name || 'Candidate'" back-to="/candidates">
      <template v-if="data" #meta>
        <span class="flex flex-wrap items-center gap-2 text-sm text-gray-500">
          <span class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs text-gray-700">{{ data.candidate.name }}</span>
          {{ data.applications.length }} application{{ data.applications.length === 1 ? '' : 's' }}
          · first applied {{ dayjs(data.candidate.creation).format('DD MMM YYYY') }}
        </span>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div v-if="loading && !data" class="h-64 animate-pulse rounded-xl border bg-white" />
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <div v-else-if="data" class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <!-- Applications -->
        <section class="min-w-0 overflow-hidden rounded-xl border bg-white shadow-sm">
          <header class="flex items-center justify-between border-b px-5 py-3">
            <h2 class="text-sm font-semibold text-gray-900">Applications</h2>
            <span class="text-xs text-gray-500">Newest first · click to open</span>
          </header>
          <div v-if="!data.applications.length" class="px-5 py-8 text-center text-sm text-gray-500">No applications.</div>
          <ul v-else class="divide-y">
            <li v-for="a in data.applications" :key="a.name">
              <router-link :to="`/applications/${a.name}`" class="flex flex-wrap items-start gap-x-5 gap-y-2 px-5 py-4 hover:bg-gray-50">
                <div class="min-w-0 flex-1">
                  <div class="font-medium text-gray-900">{{ a.job_title || a.job_opening }}</div>
                  <div class="mt-0.5 flex flex-wrap gap-x-2 text-xs text-gray-500">
                    <span class="font-mono">{{ a.application_id }}</span>
                    <span v-if="a.position">· {{ a.position }}</span>
                    <span v-if="a.track">· {{ a.track }}</span>
                    <span v-if="a.application_date">· applied {{ dayjs(a.application_date).format('DD MMM YYYY') }}</span>
                    <span v-if="a.source">· {{ a.source }}</span>
                  </div>
                  <div v-if="a.interviews.length" class="mt-1.5 flex flex-wrap gap-1.5">
                    <span v-for="(iv, i) in a.interviews" :key="i" class="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-700">
                      {{ iv.round }} · {{ iv.status }} · {{ dayjs(iv.date).format('DD MMM') }}
                    </span>
                  </div>
                </div>
                <div class="flex shrink-0 flex-col items-end gap-1">
                  <StatusBadge :status="a.status" />
                  <span v-if="a.selection_outcome" class="text-xs font-medium text-gray-600">Outcome: {{ a.selection_outcome }}</span>
                  <span v-else-if="a.eligibility_status && a.eligibility_status !== 'Pending'" class="text-xs text-gray-500">{{ a.eligibility_status }}</span>
                </div>
                <FeatherIcon name="chevron-right" class="mt-1 h-4 w-4 shrink-0 text-gray-300" />
              </router-link>
            </li>
          </ul>
        </section>

        <!-- Profile -->
        <div class="flex flex-col gap-4">
          <section class="rounded-xl border bg-white p-5 shadow-sm">
            <h2 class="mb-3 text-sm font-semibold text-gray-900">Profile</h2>
            <dl class="grid grid-cols-1 gap-3 text-sm">
              <div v-for="f in profileFields" :key="f.label">
                <dt class="text-xs text-gray-500">{{ f.label }}</dt>
                <dd class="whitespace-pre-line break-words text-gray-900">{{ f.value || '—' }}</dd>
              </div>
            </dl>
          </section>
          <section class="rounded-xl border bg-white p-5 text-sm shadow-sm">
            <h2 class="mb-2 text-sm font-semibold text-gray-900">Candidate portal</h2>
            <p v-if="!data.portal.exists" class="text-gray-600">No portal account yet.</p>
            <template v-else>
              <p class="text-gray-700">
                Login: <span class="font-medium">{{ data.candidate.email }}</span>
                <span class="ml-1 rounded-full px-2 py-0.5 text-[11px] font-medium" :class="data.portal.enabled ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'">{{ data.portal.enabled ? 'Active' : 'Disabled' }}</span>
              </p>
              <p class="mt-1 text-xs text-gray-500">Last signed in: {{ data.portal.last_login ? dayjs(data.portal.last_login).format('DD MMM YYYY, h:mm A') : 'never' }}</p>
            </template>
          </section>
          <section v-if="data.same_mobile.length" class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <div class="mb-1 flex items-center gap-1.5 font-medium"><FeatherIcon name="alert-triangle" class="h-4 w-4" />Same mobile number</div>
            <p class="mb-2 text-xs">These candidates applied with another email but the same mobile number. They may be the same person.</p>
            <ul class="flex flex-col gap-1">
              <li v-for="s in data.same_mobile" :key="s.name">
                <router-link :to="`/candidates/${s.name}`" class="hover:underline">{{ s.full_name }} <span class="text-xs">({{ s.email }})</span></router-link>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { candidateService } from '@/services/candidates'

const props = defineProps({ id: { type: String, required: true } })
const data = ref(null)
const loading = ref(false)
const error = ref('')

const profileFields = computed(() => {
  const c = data.value?.candidate || {}
  return [
    { label: 'Email', value: c.email },
    { label: 'Mobile', value: c.mobile_number },
    { label: 'Date of birth', value: c.date_of_birth ? dayjs(c.date_of_birth).format('DD MMM YYYY') : '' },
    { label: 'Gender', value: c.gender },
    { label: 'Category', value: c.category },
    { label: 'Address', value: c.address },
  ]
})

watch(
  () => props.id,
  async (id) => {
    loading.value = true
    error.value = ''
    try {
      data.value = await candidateService.get(id)
    } catch (e) {
      data.value = null
      error.value = e?.messages?.[0] || 'Could not load the candidate.'
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)
</script>
