<template>
  <!-- "Emails" on the application page: every recruitment email about this
       application and its interviews, offer and joining. -->
  <SectionCard v-if="data?.can_view" title="Emails" icon="mail" :subtitle="subtitle">
    <template v-if="rows.length > LIMIT" #actions>
      <Button size="sm" variant="ghost" :icon-right="expanded ? 'chevron-up' : 'chevron-down'" @click="expanded = !expanded">
        {{ expanded ? 'Show fewer' : `Show all (${rows.length})` }}
      </Button>
    </template>
    <div v-if="loading && !data" class="text-sm text-gray-500">Loading...</div>
    <div v-else-if="!rows.length" class="text-sm text-gray-500">No emails sent about this application yet.</div>
    <ul v-else class="-mx-2 flex flex-col">
      <li v-for="row in shown" :key="row.name">
        <button type="button" class="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left hover:bg-brand-50" @click="openEmail(row.name)">
          <FeatherIcon name="mail" class="h-4 w-4 shrink-0" :class="row.status === 'Failed' ? 'text-red-500' : 'text-brand-700'" />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium text-gray-900">{{ row.event_label }}</span>
            <span class="block truncate text-xs text-gray-500">To {{ row.recipient }} · {{ formatDateTime(row.sent_on) }}</span>
          </span>
          <StatusBadge v-if="row.status === 'Failed'" :status="row.status" />
          <FeatherIcon name="chevron-right" class="h-4 w-4 shrink-0 text-gray-400" />
        </button>
      </li>
    </ul>
    <EmailDrawer v-model:open="drawer.open" :name="drawer.name" />
  </SectionCard>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmailDrawer from '@/components/common/EmailDrawer.vue'
import { communicationService } from '@/services/communications'

const props = defineProps({ application: { type: String, required: true } })

const LIMIT = 5
const data = ref(null)
const loading = ref(false)
const expanded = ref(false)
const drawer = reactive({ open: false, name: '' })

const rows = computed(() => data.value?.rows || [])
const shown = computed(() => (expanded.value ? rows.value : rows.value.slice(0, LIMIT)))
const subtitle = computed(() => `${rows.value.length} email${rows.value.length === 1 ? '' : 's'}, newest first`)

async function load() {
  loading.value = true
  try {
    data.value = await communicationService.listForApplication(props.application)
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.application, load)

function openEmail(name) {
  Object.assign(drawer, { open: true, name })
}
function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A') : ''
}
</script>
