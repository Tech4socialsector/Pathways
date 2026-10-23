<template>
  <!-- Approval log of a green sheet, newest first: collapsed to its latest
       entry, so the steps above stay the focus of the card. -->
  <div v-if="rows.length" class="text-sm">
    <button
      type="button"
      class="flex w-full items-center justify-between gap-2 rounded-md py-1 text-left text-gray-600 hover:text-gray-900"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="font-medium">Approval log <span class="font-normal text-gray-500">· {{ rows.length }} {{ rows.length === 1 ? 'entry' : 'entries' }}</span></span>
      <span class="flex items-center gap-1 text-xs text-brand-700">
        {{ open ? 'Hide' : 'Show all' }}
        <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4 w-4" />
      </span>
    </button>

    <p v-if="!open" class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-gray-500">
      <span>Latest:</span>
      <StatusBadge :status="rows[0].action" />
      <span class="text-gray-800">{{ rows[0].approver_role || rows[0].approver }}</span>
      <span>· {{ when(rows[0].acted_on) }}</span>
    </p>

    <ul v-else class="mt-2 flex flex-col gap-2">
      <li v-for="(row, idx) in rows" :key="idx" class="rounded border px-3 py-2">
        <div class="flex flex-wrap items-center gap-2">
          <StatusBadge :status="row.action" />
          <span class="text-gray-900">{{ row.approver_role || row.approver }}</span>
          <span v-if="row.is_override" class="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">recorded on behalf</span>
        </div>
        <div class="mt-0.5 text-xs text-gray-500">{{ row.approver_name || row.approver }} · {{ row.channel }} · {{ when(row.acted_on) }}</div>
        <div v-if="row.remarks" class="mt-1 text-gray-600">{{ row.remarks }}</div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import StatusBadge from '@/components/common/StatusBadge.vue'

defineProps({
  // Newest first.
  rows: { type: Array, default: () => [] },
})

const open = ref(false)
const when = (value) => (value ? dayjs(value).format('DD MMM YYYY, h:mm A') : '')
</script>
