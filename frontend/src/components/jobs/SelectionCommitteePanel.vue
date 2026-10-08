<template>
  <!-- Workflow step 15: the job's Selection Committee (the interview panel). -->
  <SectionCard title="Selection Committee" icon="users">
    <template v-if="data?.can_manage" #actions>
      <Button size="sm" variant="ghost" :icon-left="committee ? 'edit-2' : 'plus'" @click="openEditor">
        {{ committee ? 'Edit' : 'Set up' }}
      </Button>
    </template>

    <div v-if="!data" class="text-sm text-gray-500">Loading…</div>
    <div v-else-if="!committee" class="rounded-lg border border-dashed px-4 py-5 text-center text-sm text-gray-500">
      No selection committee yet.
      <span class="block text-xs">Needed before final interviews can be scheduled ({{ data.committee_size.min }}–{{ data.committee_size.max }} panellists).</span>
    </div>
    <div v-else class="flex flex-col gap-3 text-sm">
      <div v-if="committee.scheduled_date" class="flex items-center gap-2 text-gray-700">
        <FeatherIcon name="calendar" class="h-4 w-4 text-gray-400" />
        {{ dayjs(committee.scheduled_date).format('ddd, DD MMM YYYY') }}<template v-if="committee.scheduled_time"> · {{ timeLabel(committee.scheduled_time) }}</template>
      </div>
      <ul class="divide-y rounded-lg border">
        <li v-for="m in committee.members" :key="m.member" class="flex items-center gap-3 px-3 py-2">
          <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-700">
            {{ (m.full_name || m.member)[0] }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="truncate font-medium text-gray-900">{{ m.full_name || m.member }}</div>
            <div v-if="m.designation_label" class="truncate text-xs text-gray-500">{{ m.designation_label }}</div>
          </div>
          <span v-if="m.is_external_expert" class="shrink-0 rounded bg-blue-50 px-1.5 py-0.5 text-[11px] font-medium text-blue-700">External</span>
        </li>
      </ul>
    </div>

    <SelectionCommitteeDialog v-model:open="editorOpen" :job-opening="jobOpening" @saved="emit('changed')" />
  </SectionCard>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import SelectionCommitteeDialog from '@/components/jobs/SelectionCommitteeDialog.vue'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'

const props = defineProps({
  jobOpening: { type: String, required: true },
  // pathways.api.interviews.get_job_interviews, loaded by the parent
  data: { type: Object, default: null },
})
const emit = defineEmits(['changed'])

const committee = computed(() => props.data?.committee)
const editorOpen = ref(false)

function timeLabel(t) {
  return dayjs(`2000-01-01 ${t}`).format('h:mm A')
}

function openEditor() {
  editorOpen.value = true
}
</script>
