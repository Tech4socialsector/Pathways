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

      <!-- Shortlisting sheet: the committee's sheet for this track -->
      <div v-if="s.can_shortlist && s.applications">
        <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Shortlisting sheet</div>
        <div class="grid grid-cols-2 gap-2">
          <Button size="sm" variant="outline" icon-left="eye" @click="openReport">View</Button>
          <a :href="scoringService.shortlistingReportUrl(job.name)" class="inline-flex">
            <Button size="sm" variant="solid" icon-left="download" class="w-full" :class="BTN_BRAND">Excel</Button>
          </a>
        </div>
        <p class="mt-1.5 text-xs text-gray-500">{{ reportHint }}</p>
      </div>

      <!-- Regret emails, sent together once screening is done -->
      <div v-if="s.can_shortlist && s.regret">
        <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Regret emails</div>
        <div class="rounded-lg border px-3 py-2.5">
          <div class="flex justify-between text-gray-700"><span>Not eligible, not yet sent</span><span class="font-semibold">{{ s.regret.not_eligible }}</span></div>
          <div class="mt-1 flex justify-between text-gray-700"><span>Not shortlisted, not yet sent</span><span class="font-semibold">{{ s.regret.not_shortlisted }}</span></div>
          <div class="mt-1 flex justify-between text-xs text-gray-500"><span>Already sent</span><span>{{ s.regret.sent }}</span></div>
          <Button
            class="mt-3 w-full"
            size="sm"
            variant="outline"
            icon-left="send"
            :disabled="!regretTotal || !s.regret.enabled"
            @click="regretOpen = true"
          >
            Send regret emails ({{ regretTotal }})
          </Button>
          <p v-if="!s.regret.enabled" class="mt-1.5 text-xs text-orange-700">Switched off in Email Setup ("Regret after screening").</p>
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

    <Dialog v-model="regretOpen" :options="{ title: 'Send regret emails', size: 'lg' }">
      <template #body-content>
        <div class="flex flex-col gap-3 text-sm">
          <p class="text-gray-600">Each candidate gets the "Regret Mail" template once. Candidates who already had a regret are skipped.</p>
          <label class="flex items-center gap-2.5">
            <input v-model="regretGroups" type="checkbox" value="not_eligible" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            Not eligible ({{ s.regret?.not_eligible || 0 }})
          </label>
          <label class="flex items-center gap-2.5">
            <input v-model="regretGroups" type="checkbox" value="not_shortlisted" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            Not shortlisted ({{ s.regret?.not_shortlisted || 0 }})
          </label>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="regretOpen = false">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="sendingRegret" :disabled="!regretSelected" @click="sendRegrets">
            Send {{ regretSelected }} email{{ regretSelected === 1 ? '' : 's' }}
          </Button>
        </div>
      </template>
    </Dialog>

    <ShortlistingSheetDialog v-model:open="reportOpen" :job-opening="job.name" :job-title="job.job_title" :track="job.track" />

    <CommitteeSetupDialog v-model:open="committeeOpen" :job-opening="job.name" @created="emit('changed')" />
  </SectionCard>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import SectionCard from '@/components/common/SectionCard.vue'
import CommitteeSetupDialog from '@/components/common/CommitteeSetupDialog.vue'
import ShortlistingSheetDialog from '@/components/common/ShortlistingSheetDialog.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { applicationService } from '@/services/applications'
import { jobOpeningService } from '@/services/jobOpenings'
import { scoringService } from '@/services/scoring'

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

// ----- regret emails
const regretOpen = ref(false)
const regretGroups = ref(['not_eligible', 'not_shortlisted'])
const sendingRegret = ref(false)
const regretTotal = computed(() => (s.value.regret?.not_eligible || 0) + (s.value.regret?.not_shortlisted || 0))
const regretSelected = computed(() => regretGroups.value.reduce((n, g) => n + (s.value.regret?.[g] || 0), 0))

async function sendRegrets() {
  sendingRegret.value = true
  try {
    const r = await scoringService.sendRegretEmails(props.job.name, regretGroups.value)
    regretOpen.value = false
    toast({ title: `${r.sent} regret email${r.sent === 1 ? '' : 's'} queued.`, icon: 'check', iconClasses: 'text-green-500' })
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not send the regrets.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    sendingRegret.value = false
  }
}

// ----- shortlisting sheet
const reportOpen = ref(false)
const reportHint = computed(
  () =>
    ({
      Faculty: 'Eligibility Check and Consolidated scores, as in the Faculty sheets.',
      Research: 'Candidate details, rubric scores (best 12), remarks and status.',
    })[props.job.track] || 'Candidate details, screening answers, ineligibility reason, decision and remarks.',
)
function openReport() {
  reportOpen.value = true
}
</script>
