<template>
  <SectionCard
    v-if="data?.can_view"
    title="References"
    icon="phone-call"
    subtitle="Reference checks · confidential, never shown to the candidate"
  >
    <template v-if="data.can_create" #actions>
      <Button size="sm" icon-left="user-plus" @click="openReferee()">Add referee</Button>
      <Button
        v-if="pendingReferees.length && data.template"
        size="sm"
        variant="solid"
        icon-left="plus"
        :class="BTN_BRAND"
        :loading="creating"
        @click="createFromApplication"
      >
        Start checks ({{ pendingReferees.length }})
      </Button>
    </template>

    <ErrorMessage v-if="error" class="mb-3" :message="error" />

    <div
      v-if="data.can_create && !data.template"
      class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
    >
      There is no active reference check template for the {{ data.track || '' }} track. Add one in Master Setup &gt;
      Reference Check Templates.
    </div>

    <div v-if="!data.checks.length" class="text-sm text-gray-500">
      No reference checks yet.
      <template v-if="data.can_create && pendingReferees.length && data.template">
        Use <b>Start checks</b> to create one for each referee the candidate gave.
      </template>
    </div>

    <ul v-else class="flex flex-col divide-y divide-gray-100">
      <li v-for="check in data.checks" :key="check.name" class="py-3 first:pt-0 last:pb-0">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-semibold text-gray-900">{{ check.referee_name }}</span>
              <StatusBadge :status="check.status" />
              <span v-if="check.mode" class="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">{{ check.mode }}</span>
            </div>
            <div class="mt-0.5 text-sm text-gray-600">
              {{ [check.referee_designation_org, check.relationship_to_candidate].filter(Boolean).join(' · ') }}
            </div>
            <div class="mt-0.5 flex flex-wrap gap-x-3 text-xs text-gray-500">
              <span v-if="check.referee_email">{{ check.referee_email }}</span>
              <span v-if="check.referee_mobile">{{ check.referee_mobile }}</span>
            </div>
            <div class="mt-1 text-xs text-gray-500">{{ timeline(check) }}</div>
          </div>
          <div class="flex flex-wrap items-center gap-1.5">
            <template v-if="data.can_manage && check.status !== 'Completed'">
              <Button
                size="sm"
                icon-left="send"
                :disabled="!check.referee_email"
                :loading="busy === `send:${check.name}`"
                :title="check.referee_email ? '' : 'Add the referee\'s email address first'"
                @click="sendLink(check)"
              >
                {{ check.requested_on ? 'Resend link' : 'Email form link' }}
              </Button>
              <Button size="sm" icon-left="edit-3" @click="openRecord(check)">Record answers</Button>
              <Button size="sm" variant="ghost" icon="edit-2" title="Edit referee" @click="openReferee(check)" />
            </template>
            <Button
              v-else-if="data.can_manage && check.mode === 'Recorded by recruiter'"
              size="sm"
              icon-left="edit-3"
              @click="openRecord(check)"
            >
              Edit answers
            </Button>
            <Button
              v-if="answeredCount(check)"
              size="sm"
              variant="ghost"
              :icon-right="expanded[check.name] ? 'chevron-up' : 'chevron-down'"
              @click="expanded[check.name] = !expanded[check.name]"
            >
              Responses
            </Button>
            <a
              :href="referenceCheckService.printUrl(check.name)"
              target="_blank"
              rel="noopener"
              class="inline-flex h-7 items-center gap-1 rounded px-2 text-sm text-gray-700 hover:bg-gray-100"
              title="Printable view"
            >
              <FeatherIcon name="printer" class="h-3.5 w-3.5" />Print
            </a>
          </div>
        </div>

        <div v-if="links[check.name]" class="mt-2 flex items-center gap-2 rounded-md bg-brand-50/70 px-2.5 py-1.5 text-xs">
          <FeatherIcon name="link" class="h-3.5 w-3.5 shrink-0 text-brand-700" />
          <span class="min-w-0 flex-1 truncate font-mono text-gray-700">{{ links[check.name] }}</span>
          <Button size="sm" variant="ghost" @click="copy(links[check.name])">Copy</Button>
        </div>

        <!-- Responses + overall assessment -->
        <div v-if="expanded[check.name]" class="mt-3 rounded-lg border border-gray-100 bg-gray-50 p-3">
          <ReferenceResponses :responses="check.responses" />
          <div class="mt-4 border-t border-gray-200 pt-3">
            <div class="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Overall assessment summary</div>
            <template v-if="data.can_manage">
              <FormControl
                type="textarea"
                :rows="3"
                v-model="summaries[check.name]"
                placeholder="The recruitment team's summary of this reference."
              />
              <div class="mt-2 flex justify-end">
                <Button
                  size="sm"
                  variant="solid"
                  :class="BTN_BRAND"
                  :loading="busy === `summary:${check.name}`"
                  :disabled="(summaries[check.name] || '') === (check.overall_assessment_summary || '')"
                  @click="saveSummary(check)"
                >
                  Save summary
                </Button>
              </div>
            </template>
            <p v-else class="whitespace-pre-wrap text-sm text-gray-800">{{ check.overall_assessment_summary || '—' }}</p>
          </div>
        </div>
      </li>
    </ul>

    <div v-if="pendingReferees.length" class="mt-4 border-t border-gray-100 pt-3">
      <div class="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">Referees given in the application, not yet checked</div>
      <ul class="flex flex-col gap-1 text-sm">
        <li v-for="ref in pendingReferees" :key="ref.idx" class="text-gray-700">
          <span class="font-medium text-gray-900">{{ ref.referee_name }}</span>
          <span v-if="ref.referee_designation_org" class="text-gray-500"> · {{ ref.referee_designation_org }}</span>
          <span v-if="ref.referee_email" class="text-gray-500"> · {{ ref.referee_email }}</span>
        </li>
      </ul>
    </div>
  </SectionCard>

  <!-- Add / edit referee -->
  <Dialog v-model="refereeDialog.open" :options="{ title: refereeDialog.check ? 'Edit referee' : 'Add referee', size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="refereeDialog.error" />
        <FormControl label="Name" v-model="refereeDialog.form.referee_name" :required="true" />
        <FormControl label="Current designation and organisation" v-model="refereeDialog.form.referee_designation_org" />
        <FormControl label="Relationship with the candidate" v-model="refereeDialog.form.relationship_to_candidate" />
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <FormControl label="Email" type="email" v-model="refereeDialog.form.referee_email" />
          <FormControl label="Mobile" v-model="refereeDialog.form.referee_mobile" />
        </div>
        <p v-if="refereeDialog.check?.requested_on" class="text-xs text-gray-500">
          Changing the email address cancels the link already sent; send a new one afterwards.
        </p>
      </div>
    </template>
    <template #actions>
      <Button variant="solid" :class="BTN_BRAND" :loading="refereeDialog.saving" @click="saveReferee">
        {{ refereeDialog.check ? 'Save' : 'Add referee' }}
      </Button>
    </template>
  </Dialog>

  <!-- Record answers (phone check) -->
  <Dialog v-model="recordDialog.open" :options="{ title: `Record reference: ${recordDialog.check?.referee_name || ''}`, size: '3xl' }">
    <template #body-content>
      <div v-if="recordDialog.check" class="flex flex-col gap-4">
        <ErrorMessage :message="recordDialog.error" />
        <p class="text-sm text-gray-600">
          Record what the referee said, for example on a phone call. <b>Save draft</b> keeps partial answers;
          <b>Mark complete</b> needs every required answer.
        </p>
        <ReferenceQuestionsForm :questions="recordQuestions" v-model="recordDialog.answers" />
        <FormControl
          label="Overall assessment summary"
          type="textarea"
          :rows="3"
          v-model="recordDialog.summary"
          placeholder="Your summary of this reference."
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :loading="recordDialog.saving === 'draft'" @click="saveRecord(false)">Save draft</Button>
        <Button variant="solid" :class="BTN_BRAND" :loading="recordDialog.saving === 'complete'" @click="saveRecord(true)">
          Mark complete
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ReferenceResponses from '@/components/references/ReferenceResponses.vue'
import ReferenceQuestionsForm from '@/components/references/ReferenceQuestionsForm.vue'
import { referenceCheckService } from '@/services/referenceChecks'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({ applicationId: { type: String, required: true } })

const data = ref(null)
const error = ref('')
const creating = ref(false)
const busy = ref('')
const expanded = reactive({})
const summaries = reactive({})
const links = reactive({})

const pendingReferees = computed(() => (data.value?.referees || []).filter((r) => !r.added))

function messageOf(e, fallback) {
  return e?.messages?.[0] || fallback
}

async function load() {
  error.value = ''
  try {
    data.value = await referenceCheckService.getApplicationChecks(props.applicationId)
    for (const c of data.value.checks || []) summaries[c.name] = c.overall_assessment_summary || ''
  } catch (e) {
    data.value = null
  }
}

function fmt(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

function timeline(check) {
  const parts = []
  if (check.status === 'Completed') {
    parts.push(`Completed ${fmt(check.completed_on)}`)
    if (check.mode === 'Referee form') parts.push('answered by the referee')
  } else if (check.mode === 'Referee form' && check.requested_on) {
    parts.push(`Link sent ${fmt(check.requested_on)}`)
    if (check.reminder_sent_on) parts.push(`reminded ${fmt(check.reminder_sent_on)}`)
    parts.push(check.link_active ? `expires ${fmt(check.token_expires_on)}` : 'link expired')
  } else if (check.mode === 'Recorded by recruiter') {
    parts.push('Answers being recorded')
  } else {
    parts.push('Not started')
  }
  return parts.join(' · ')
}

function answeredCount(check) {
  return (check.responses || []).filter((r) => r.answer_text || r.rating_value).length
}

async function createFromApplication() {
  creating.value = true
  error.value = ''
  try {
    const out = await referenceCheckService.createChecks(props.applicationId)
    toast({ title: `${out.created.length} reference check${out.created.length === 1 ? '' : 's'} created.` })
    await load()
  } catch (e) {
    error.value = messageOf(e, 'Could not create the reference checks.')
  } finally {
    creating.value = false
  }
}

async function sendLink(check) {
  busy.value = `send:${check.name}`
  error.value = ''
  try {
    const out = await referenceCheckService.sendRequest(check.name)
    links[check.name] = out.form_link
    toast({
      title: data.value.email_enabled
        ? `Form link emailed to ${check.referee_email}.`
        : 'Link created. The referee email is turned off in Email Setup, so share the link yourself.',
    })
    await load()
  } catch (e) {
    error.value = messageOf(e, 'Could not send the link.')
  } finally {
    busy.value = ''
  }
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast({ title: 'Link copied.' })
  } catch {
    toast({ title: 'Could not copy the link.', icon: 'alert-triangle' })
  }
}

async function saveSummary(check) {
  busy.value = `summary:${check.name}`
  try {
    await referenceCheckService.saveSummary(check.name, summaries[check.name])
    toast({ title: 'Summary saved.' })
    await load()
  } catch (e) {
    error.value = messageOf(e, 'Could not save the summary.')
  } finally {
    busy.value = ''
  }
}

// ----- referee dialog
const EMPTY_REFEREE = {
  referee_name: '',
  referee_designation_org: '',
  relationship_to_candidate: '',
  referee_email: '',
  referee_mobile: '',
}
const refereeDialog = reactive({ open: false, check: null, form: { ...EMPTY_REFEREE }, error: '', saving: false })

function openReferee(check = null) {
  refereeDialog.check = check
  refereeDialog.form = check ? Object.fromEntries(Object.keys(EMPTY_REFEREE).map((k) => [k, check[k] || ''])) : { ...EMPTY_REFEREE }
  refereeDialog.error = ''
  refereeDialog.open = true
}

async function saveReferee() {
  if (!refereeDialog.form.referee_name.trim()) {
    refereeDialog.error = "Enter the referee's name."
    return
  }
  refereeDialog.saving = true
  refereeDialog.error = ''
  try {
    if (refereeDialog.check) {
      await referenceCheckService.updateReferee(refereeDialog.check.name, refereeDialog.form)
    } else {
      await referenceCheckService.createChecks(props.applicationId, [refereeDialog.form])
    }
    refereeDialog.open = false
    await load()
  } catch (e) {
    refereeDialog.error = messageOf(e, 'Could not save the referee.')
  } finally {
    refereeDialog.saving = false
  }
}

// ----- record answers dialog
const recordDialog = reactive({ open: false, check: null, answers: {}, summary: '', error: '', saving: '' })
const recordQuestions = computed(() =>
  (recordDialog.check?.responses || []).map((r) => ({
    name: r.name,
    section: r.section,
    question: r.question_text,
    answer_type: r.answer_type || 'Text',
    required: r.required,
  })),
)

function openRecord(check) {
  recordDialog.check = check
  recordDialog.answers = Object.fromEntries(
    (check.responses || []).map((r) => [r.name, { answer_text: r.answer_text || '', rating_value: r.rating_value || null }]),
  )
  recordDialog.summary = check.overall_assessment_summary || ''
  recordDialog.error = ''
  recordDialog.open = true
}

async function saveRecord(complete) {
  recordDialog.saving = complete ? 'complete' : 'draft'
  recordDialog.error = ''
  try {
    await referenceCheckService.recordResponses(recordDialog.check.name, recordDialog.answers, recordDialog.summary, complete)
    recordDialog.open = false
    toast({ title: complete ? 'Reference check completed.' : 'Draft saved.' })
    await load()
  } catch (e) {
    recordDialog.error = messageOf(e, 'Could not save the answers.')
  } finally {
    recordDialog.saving = ''
  }
}

onMounted(load)
watch(() => props.applicationId, load)
</script>
