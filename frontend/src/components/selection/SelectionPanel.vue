<template>
  <SectionCard
    v-if="visible"
    title="Selection"
    icon="award"
    subtitle="Committee recommendation and the Post-Interview Green Sheet"
  >
    <template #actions>
      <StatusBadge v-if="current" :status="current.status" />
    </template>

    <div v-if="loading && !data" class="text-sm text-gray-500">Loading...</div>
    <div v-else-if="loadError" class="text-sm text-red-600">{{ loadError }}</div>
    <div v-else-if="data" class="flex flex-col gap-4 text-sm">
      <!-- Outcomes recorded on the consolidated score sheet -->
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div v-for="group in outcomeGroups" :key="group.label" class="rounded-lg border px-3 py-2.5">
          <div class="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">{{ group.label }}</div>
          <ul v-if="group.rows.length" class="flex flex-col gap-1">
            <li v-for="r in group.rows" :key="r.application" class="flex items-center justify-between gap-2">
              <router-link :to="`/applications/${r.application}`" class="truncate text-gray-900 hover:underline">
                {{ r.candidate_name || r.application_id }}
              </router-link>
              <span v-if="r.average != null" class="shrink-0 text-xs tabular-nums text-gray-500">
                {{ r.average }}<template v-if="data.outcomes.max_total"> / {{ data.outcomes.max_total }}</template>
              </span>
            </li>
          </ul>
          <div v-else class="text-gray-500">None</div>
        </div>
      </div>
      <router-link :to="`/panel/sheet/${job.name}`" class="self-start text-xs font-medium text-brand-700 hover:underline">
        Open the consolidated score sheet to record or change outcomes
      </router-link>

      <div
        v-if="!data.has_chain_template && (!current || current.docstatus === 0)"
        class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-orange-800"
      >
        No active Approval Chain for the Post-Interview Green Sheet matches the '{{ job.track }}' track
        ({{ job.employment_type || 'any type' }}). Configure one in Master Setup &gt; Approval Chains before submitting.
      </div>

      <!-- No sheet in progress -->
      <template v-if="!current || current.status === 'Cancelled'">
        <p class="text-gray-600">
          Once the committee's outcomes are recorded, raise the Post-Interview Green Sheet. It is drafted with the
          recommended and waitlisted candidates; complete it, attach the annexures and submit it for approval.
        </p>
        <div v-if="perms.can_create">
          <Button
            variant="solid"
            :class="BTN_BRAND"
            icon-left="file-plus"
            :disabled="!data.outcomes.selected.length || !job.track"
            :loading="raising"
            @click="raise"
          >
            Raise Selection Green Sheet
          </Button>
          <p v-if="!data.outcomes.selected.length" class="mt-1 text-xs text-gray-500">
            Mark at least one candidate as Selected first.
          </p>
        </div>
      </template>

      <!-- Current sheet -->
      <template v-else>
        <router-link
          :to="`/selection-green-sheets/${current.name}`"
          class="flex flex-col gap-1 rounded-lg border px-3 py-2.5 hover:border-brand-200 hover:bg-brand-50"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="font-medium text-gray-900">{{ current.subject || current.name }}</span>
            <FeatherIcon name="chevron-right" class="h-4 w-4 text-gray-400" />
          </div>
          <div class="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-gray-500">
            <span>{{ current.name }}</span>
            <span v-if="current.recommended_candidate_name">Recommended: <b class="text-gray-800">{{ current.recommended_candidate_name }}</b></span>
            <span v-if="current.waitlist_candidate_name">Waitlist: <b class="text-gray-800">{{ current.waitlist_candidate_name }}</b></span>
            <span v-if="current.signed_copy_attachment" class="text-green-700">Signed copy attached</span>
          </div>
        </router-link>

        <div v-if="current.status === 'Returned for Revision' && returned" class="rounded border border-red-200 bg-red-50 px-3 py-2 text-red-800">
          Returned by {{ returned.approver_role || returned.approver }}<span v-if="returned.remarks">: “{{ returned.remarks }}”</span>
        </div>
        <div v-if="current.status === 'Under Approval' && !perms.can_act && perms.act_blocked_reason" class="text-gray-500">
          {{ perms.act_blocked_reason }}
        </div>

        <div v-if="timeline.length">
          <div class="mb-2 text-gray-500">Approval chain</div>
          <RecruitmentTimeline :steps="timeline" />
        </div>

        <div class="flex flex-wrap gap-2">
          <Button variant="solid" :class="BTN_BRAND" @click="router.push(`/selection-green-sheets/${current.name}`)">
            {{ current.docstatus === 0 && perms.can_create ? 'Continue editing' : perms.can_act ? 'Review & approve' : 'Open sheet' }}
          </Button>
          <Button
            v-if="current.status === 'Approved' && perms.can_create && data.outcomes.selected.length"
            variant="outline"
            :loading="raising"
            @click="raise"
          >
            Raise another sheet
          </Button>
        </div>
      </template>

      <div v-if="history.length">
        <div class="mb-1.5 text-gray-500">Earlier sheets</div>
        <ul class="flex flex-col gap-1">
          <li v-for="sheet in history" :key="sheet.name" class="flex items-center justify-between gap-2">
            <router-link :to="`/selection-green-sheets/${sheet.name}`" class="text-gray-700 hover:underline">{{ sheet.name }}</router-link>
            <StatusBadge :status="sheet.status" />
          </li>
        </ul>
      </div>
    </div>
  </SectionCard>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
import { postGreenSheetService } from '@/services/postGreenSheets'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { chainTimeline, lastReturn } from './approvalTimeline'

const props = defineProps({
  job: { type: Object, required: true },
})

const router = useRouter()
const data = ref(null)
const loading = ref(false)
const loadError = ref('')
const raising = ref(false)

const current = computed(() => data.value?.current || null)
const perms = computed(() => data.value?.permissions || {})
const history = computed(() => (data.value?.sheets || []).filter((s) => !current.value || s.name !== current.value.name))
const timeline = computed(() => chainTimeline(data.value?.chain))
const returned = computed(() => lastReturn(data.value?.chain))

// Shown once the selection stage has started: an outcome or a sheet exists.
const visible = computed(() => {
  if (loadError.value) return true
  if (!data.value) return false
  const o = data.value.outcomes
  return o.selected.length > 0 || o.waitlisted.length > 0 || data.value.sheets.length > 0
})

const outcomeGroups = computed(() => [
  { label: 'Selected', rows: data.value?.outcomes.selected || [] },
  { label: 'Waitlisted', rows: data.value?.outcomes.waitlisted || [] },
])

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    data.value = await postGreenSheetService.getJobSelection(props.job.name)
  } catch {
    // Users who may not read the job's sheets simply do not see the card.
    data.value = null
  } finally {
    loading.value = false
  }
}

async function raise() {
  raising.value = true
  try {
    const name = await postGreenSheetService.createFromOutcomes(props.job.name)
    toast({ title: 'Selection Green Sheet drafted.', icon: 'check', iconClasses: 'text-green-500' })
    router.push(`/selection-green-sheets/${name}`)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not raise the Selection Green Sheet.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    raising.value = false
  }
}

onMounted(load)
watch(() => props.job.name, load)
defineExpose({ reload: load })
</script>
