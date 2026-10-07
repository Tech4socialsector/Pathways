<template>
  <!-- Workflow steps 7-12 for one job: committee, eligibility, 1:N ratio, documents. -->
  <SectionCard title="Shortlisting" icon="check-circle">
    <div class="flex flex-col gap-5 text-sm">
      <!-- 1:N target -->
      <div>
        <div class="flex items-baseline justify-between gap-2">
          <span class="text-xs font-bold uppercase tracking-wide text-brand-700">Target · 1 : {{ s.ratio }}</span>
          <button v-if="canEdit && !editingRatio" class="text-xs font-medium text-gray-500 hover:text-brand-700" @click="startRatio">
            Change ratio
          </button>
        </div>
        <div v-if="editingRatio" class="mt-2 flex items-end gap-2">
          <FormControl class="w-24" label="1 :" type="number" v-model="ratioInput" :min="1" />
          <Button size="sm" variant="solid" :class="BTN_BRAND" :loading="savingRatio" @click="saveRatio">Save</Button>
          <Button size="sm" variant="ghost" @click="editingRatio = false">Cancel</Button>
        </div>
        <div class="mt-2 flex items-baseline gap-1.5">
          <span class="text-2xl font-bold text-gray-900">{{ s.shortlisted }}</span>
          <span class="text-gray-500">of {{ s.target }} shortlisted</span>
        </div>
        <div class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
          <div class="h-full rounded-full transition-all" :class="barClass" :style="{ width: `${Math.min(100, (s.shortlisted / (s.target || 1)) * 100)}%` }" />
        </div>
        <p class="mt-1.5 text-xs" :class="s.shortlisted > s.target ? 'text-orange-700' : 'text-gray-500'">{{ targetHint }}</p>
      </div>

      <!-- Funnel -->
      <dl class="grid grid-cols-2 gap-2">
        <div v-for="c in counts" :key="c.label" class="rounded-lg px-3 py-2" :class="c.tone">
          <dt class="text-xs">{{ c.label }}</dt>
          <dd class="text-lg font-bold">{{ c.value }}</dd>
        </div>
      </dl>

      <!-- Committee -->
      <div>
        <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Committee</div>
        <template v-if="s.committee">
          <ul class="flex flex-col gap-1.5">
            <li v-for="m in s.committee.members" :key="m.user" class="flex items-center gap-2">
              <span class="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-[11px] font-bold text-brand-700">
                {{ (m.full_name || m.user)[0] }}
              </span>
              <span class="text-gray-800">{{ m.full_name || m.user }}</span>
            </li>
          </ul>
          <p v-if="s.committee.office_order_reference" class="mt-2 text-xs text-gray-500">Office order: {{ s.committee.office_order_reference }}</p>
        </template>
        <div v-else class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-orange-800">
          No committee yet.
          <Button v-if="s.can_create_committee" class="mt-2 w-full" size="sm" variant="solid" icon-left="users" :class="BTN_BRAND" @click="committeeOpen = true">
            Set up committee
          </Button>
        </div>
      </div>

      <!-- Documents by type -->
      <div v-if="s.can_shortlist && s.applications">
        <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Applicant documents</div>
        <div class="grid grid-cols-1 gap-2">
          <a
            v-for="d in downloads"
            :key="d.scope"
            :href="applicationService.documentsZipUrl({ jobOpening: job.name, scope: d.scope })"
            class="flex items-center justify-between rounded-md border px-3 py-2 hover:border-brand-200 hover:bg-brand-50"
            :class="!d.count && 'pointer-events-none opacity-50'"
          >
            <span class="flex items-center gap-2 text-gray-800"><FeatherIcon name="download" class="h-4 w-4 text-brand-700" />{{ d.label }}</span>
            <span class="text-xs text-gray-500">{{ d.count }}</span>
          </a>
        </div>
        <p class="mt-1.5 text-xs text-gray-500">ZIP with a folder per document type: CV, SOP, Writing Sample, Transcripts…</p>
      </div>
    </div>

    <CommitteeSetupDialog v-model:open="committeeOpen" :job-opening="job.name" @created="emit('changed')" />
  </SectionCard>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import SectionCard from '@/components/common/SectionCard.vue'
import CommitteeSetupDialog from '@/components/common/CommitteeSetupDialog.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { applicationService } from '@/services/applications'
import { jobOpeningService } from '@/services/jobOpenings'

const props = defineProps({
  job: { type: Object, required: true },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['changed'])

const s = computed(() => props.job.shortlisting || { ratio: 5, target: 0, shortlisted: 0 })

const counts = computed(() => [
  { label: 'Applications', value: s.value.applications, tone: 'bg-gray-50 text-gray-900' },
  { label: 'To check', value: s.value.pending, tone: 'bg-orange-50 text-orange-900' },
  { label: 'Eligible', value: s.value.eligible, tone: 'bg-green-50 text-green-900' },
  { label: 'Not eligible', value: s.value.not_eligible, tone: 'bg-red-50 text-red-900' },
])

const targetHint = computed(() => {
  const gap = s.value.target - s.value.shortlisted
  if (gap > 0) return `${gap} more to reach 1:${s.value.ratio} (${props.job.vacancies} vacanc${props.job.vacancies == 1 ? 'y' : 'ies'} × ${s.value.ratio}).`
  if (gap === 0) return `Target reached: 1:${s.value.ratio}.`
  return `${-gap} over the 1:${s.value.ratio} target.`
})
const barClass = computed(() => (s.value.shortlisted > s.value.target ? 'bg-orange-500' : 'bg-brand-700'))

const downloads = computed(() => [
  { scope: 'all', label: 'All applicants', count: s.value.applications },
  { scope: 'eligible', label: 'Eligible only', count: s.value.eligible },
  { scope: 'shortlisted', label: 'Shortlisted', count: s.value.shortlisted },
])

// ----- ratio
const editingRatio = ref(false)
const ratioInput = ref(5)
const savingRatio = ref(false)
const committeeOpen = ref(false)

function startRatio() {
  ratioInput.value = s.value.ratio
  editingRatio.value = true
}

async function saveRatio() {
  savingRatio.value = true
  try {
    await jobOpeningService.updateJob(props.job.name, { shortlisting_ratio: Number(ratioInput.value) || 0 })
    editingRatio.value = false
    toast({ title: `Shortlisting ratio set to 1:${ratioInput.value}.`, icon: 'check', iconClasses: 'text-green-500' })
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save the ratio.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    savingRatio.value = false
  }
}
</script>
