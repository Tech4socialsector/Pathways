<template>
  <StaffLayout>
    <PageHeader :title="form ? form.interview.candidate_name : 'Interview Assessment'" back-to="/panel">
      <template v-if="form" #meta>
        <span class="text-sm text-gray-500">
          {{ form.interview.job_title }} · Final interview · {{ dayjs(form.interview.scheduled_datetime).format('ddd, DD MMM YYYY, h:mm A') }}
        </span>
      </template>
      <template v-if="form" #actions>
        <a v-if="form.interview.meeting_link && form.interview.status !== 'Completed'" :href="form.interview.meeting_link" target="_blank" rel="noopener">
          <Button variant="outline" icon-left="video">Join {{ form.interview.meeting_platform || 'meeting' }}</Button>
        </a>
        <Button v-if="prev" variant="ghost" icon-left="chevron-left" @click="go(prev)">Previous</Button>
        <Button v-if="next" variant="ghost" icon-right="chevron-right" @click="go(next)">Next candidate</Button>
      </template>
    </PageHeader>

    <div class="flex-1 overflow-y-auto bg-gray-50/60 p-6">
      <div v-if="loading && !form" class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_26rem]">
        <div class="h-96 animate-pulse rounded-xl border bg-white" />
        <div class="h-96 animate-pulse rounded-xl border bg-white" />
      </div>
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>

      <div v-else-if="form" class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_26rem]">
        <!-- The candidate's application and documents -->
        <div class="flex min-w-0 flex-col gap-4">
          <div class="flex flex-wrap items-center gap-x-6 gap-y-1 rounded-xl border bg-white px-5 py-3 text-sm shadow-sm">
            <span><span class="text-gray-500">Candidate ID</span> <span class="font-mono font-medium text-gray-900">{{ form.application.application_id }}</span></span>
            <span v-if="form.interview.position"><span class="text-gray-500">Position</span> <span class="font-medium text-gray-900">{{ form.interview.position }}</span></span>
            <span><span class="text-gray-500">Mode</span> <span class="font-medium text-gray-900">{{ form.interview.mode === 'In-Person' ? form.interview.location || 'In person' : form.interview.meeting_platform || 'Online' }}</span></span>
          </div>
          <!-- Only what the panel needs (workflow step 16), not the whole application -->
          <section class="rounded-xl border bg-white shadow-sm">
            <header class="flex items-center justify-between border-b px-5 py-3">
              <h2 class="text-sm font-semibold text-gray-900">Documents</h2>
              <span class="text-xs text-gray-500">{{ brief.documents.length }} file{{ brief.documents.length === 1 ? '' : 's' }}</span>
            </header>
            <div v-if="!brief.documents.length" class="px-5 py-4 text-sm text-gray-500">No documents uploaded.</div>
            <ul v-else class="grid gap-2 p-4 sm:grid-cols-2">
              <li v-for="(d, i) in brief.documents" :key="d.file_url">
                <button
                  type="button"
                  class="flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left text-sm hover:border-brand-300 hover:bg-brand-50"
                  @click="openDoc(i)"
                >
                  <FeatherIcon :name="d.kind === 'image' ? 'image' : 'file-text'" class="h-5 w-5 shrink-0 text-brand-700" />
                  <span class="min-w-0">
                    <span class="block truncate font-medium text-gray-900">{{ d.label }}</span>
                    <span class="block truncate text-xs text-gray-500">{{ d.file_name }}</span>
                  </span>
                  <FeatherIcon name="eye" class="ml-auto h-4 w-4 shrink-0 text-gray-400" />
                </button>
              </li>
            </ul>
          </section>

          <section class="grid gap-4 md:grid-cols-2">
            <div class="rounded-xl border bg-white p-5 shadow-sm">
              <h2 class="mb-3 text-sm font-semibold text-gray-900">Qualifications</h2>
              <p v-if="!brief.qualifications.length" class="text-sm text-gray-500">None listed.</p>
              <ul v-else class="flex flex-col gap-2.5 text-sm">
                <li v-for="(q, i) in brief.qualifications" :key="i">
                  <div class="font-medium text-gray-900">{{ q.degree || q.level }}<template v-if="q.specialization"> · {{ q.specialization }}</template></div>
                  <div class="text-xs text-gray-500">{{ [q.institution, q.year, q.score].filter(Boolean).join(' · ') }}</div>
                </li>
              </ul>
            </div>
            <div class="rounded-xl border bg-white p-5 shadow-sm">
              <h2 class="mb-1 text-sm font-semibold text-gray-900">Experience</h2>
              <p class="mb-3 text-xs text-gray-500">
                {{ fmt(brief.overall_experience_years) || 0 }} years overall<template v-if="brief.relevant_experience_years != null"> · {{ fmt(brief.relevant_experience_years) }} relevant</template>
              </p>
              <p v-if="!brief.employment.length" class="text-sm text-gray-500">No employment listed.</p>
              <ul v-else class="flex flex-col gap-2.5 text-sm">
                <li v-for="(e, i) in brief.employment" :key="i">
                  <div class="font-medium text-gray-900">{{ e.designation }}</div>
                  <div class="text-xs text-gray-500">
                    {{ e.employer }}<template v-if="e.from_date"> · {{ dayjs(e.from_date).format('MMM YYYY') }} – {{ e.is_current ? 'present' : e.to_date ? dayjs(e.to_date).format('MMM YYYY') : '' }}</template>
                  </div>
                </li>
              </ul>
            </div>
          </section>

          <section class="rounded-xl border bg-white p-5 shadow-sm">
            <h2 class="mb-3 text-sm font-semibold text-gray-900">Notes for the panel</h2>
            <dl class="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt class="text-xs text-gray-500">Shortlisting note</dt>
                <dd class="whitespace-pre-line text-gray-800">{{ brief.shortlisting_note || '—' }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500">Round 1 (HR interaction)</dt>
                <dd class="text-gray-800">{{ brief.round1 ? `${brief.round1.status} · ${dayjs(brief.round1.date).format('DD MMM YYYY')}` : 'No Round 1 interview' }}</dd>
              </div>
            </dl>
            <router-link v-if="session.hasMenu('applications')" :to="`/applications/${form.application.name}`" class="mt-3 inline-block text-xs text-brand-700 hover:underline">
              Open the full application
            </router-link>
          </section>
          <DocumentViewer v-model:open="viewer.open" :title="`${brief.full_name} · documents`" :documents="brief.documents" :start-index="viewer.index" />
        </div>

        <!-- Interview Assessment Form -->
        <section class="overflow-hidden rounded-xl border bg-white shadow-sm lg:sticky lg:top-0">
          <header class="border-b bg-brand-700 px-5 py-3 text-white">
            <div class="text-sm font-semibold">Interview Assessment Form</div>
            <div class="text-xs text-white/80">
              Panellist: {{ form.panellist_name }} · out of {{ fmt(form.rubric.max_score) }} · {{ fmt(form.rubric.pass_percent) }}% needed for an offer
            </div>
          </header>

          <!-- Recruitment team: whose form is being typed in -->
          <div v-if="form.panel.length" class="border-b bg-gray-50 px-5 py-3">
            <div class="mb-1.5 text-xs font-medium text-gray-700">{{ form.is_panellist ? 'Scoring for' : 'Enter the scores of' }}</div>
            <div class="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Panellist">
              <button
                v-for="p in form.panel"
                :key="p.user"
                type="button"
                role="radio"
                :aria-checked="form.panelist === p.user"
                class="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition"
                :class="form.panelist === p.user ? 'border-brand-700 bg-brand-50 font-semibold text-brand-800' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-100'"
                @click="pickPanellist(p.user)"
              >
                <FeatherIcon :name="p.total_score != null ? 'check-circle' : 'circle'" class="h-3 w-3" :class="p.total_score != null ? 'text-green-600' : 'text-gray-400'" />
                {{ p.full_name }}<template v-if="p.total_score != null"> · {{ fmt(p.total_score) }}/{{ fmt(p.max_score) }}</template>
              </button>
            </div>
            <p v-if="form.on_behalf" class="mt-1.5 text-xs text-gray-500">Typing in {{ form.panellist_name }}'s signed form. It is saved as their score, noting that you entered it.</p>
          </div>

          <p v-if="form.locked_reason" class="flex items-start gap-2 border-b bg-orange-50 px-5 py-2.5 text-sm text-orange-800">
            <FeatherIcon name="lock" class="mt-0.5 h-4 w-4 shrink-0" />{{ form.locked_reason }}
          </p>

          <div class="flex flex-col gap-4 p-5 text-sm">
            <div v-for="(c, i) in form.rubric.criteria" :key="c.label" class="rounded-lg border p-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="font-semibold text-gray-900">{{ i + 1 }}. {{ c.label }}</div>
                  <p v-if="c.guidance" class="mt-0.5 text-xs leading-relaxed text-gray-500">{{ c.guidance }}</p>
                </div>
                <div class="flex shrink-0 items-center gap-1.5">
                  <input
                    v-model="scores[c.label]"
                    type="number"
                    inputmode="decimal"
                    :min="0"
                    :max="c.max_score"
                    step="0.5"
                    :disabled="!form.can_score"
                    class="w-20 rounded-md text-right text-base font-semibold tabular-nums focus:border-brand-700 focus:ring-brand-700 disabled:bg-gray-50"
                    :class="invalid(c) ? 'border-red-400' : 'border-gray-300'"
                    :aria-label="`${c.label} score out of ${c.max_score}`"
                  />
                  <span class="text-gray-500">/ {{ fmt(c.max_score) }}</span>
                </div>
              </div>
              <p v-if="invalid(c)" class="mt-1 text-xs text-red-600">Enter a score from 0 to {{ fmt(c.max_score) }}.</p>
            </div>

            <!-- Total, against the 50% bar -->
            <div class="rounded-lg bg-gray-50 px-4 py-3">
              <div class="flex items-baseline justify-between">
                <span class="font-semibold text-gray-900">Total score</span>
                <span class="text-2xl font-bold tabular-nums text-gray-900">{{ fmt(total) }} <span class="text-base font-medium text-gray-500">/ {{ fmt(form.rubric.max_score) }}</span></span>
              </div>
              <div class="relative mt-2 h-2 overflow-hidden rounded-full bg-gray-200">
                <div class="h-full rounded-full transition-all" :class="meetsBar ? 'bg-green-600' : 'bg-orange-500'" :style="{ width: `${Math.min(100, percent)}%` }" />
                <div class="absolute inset-y-0 w-0.5 bg-gray-500" :style="{ left: `${form.rubric.pass_percent}%` }" title="Needed for an offer" />
              </div>
              <div class="mt-1 text-xs" :class="!complete ? 'text-gray-500' : meetsBar ? 'text-green-700' : 'text-orange-700'">
                {{ fmt(percent) }}% · {{ !complete ? 'Score every criterion' : meetsBar ? 'Meets the bar for an offer' : `Below the ${fmt(form.rubric.pass_percent)}% needed for an offer` }}
              </div>
            </div>

            <FormControl
              v-if="form.ask_specialization"
              label="Area of specialization"
              v-model="extra.area"
              :disabled="!form.can_score"
              placeholder="e.g. Constitutional law, Financial reporting"
            />

            <div>
              <div class="mb-1.5 text-xs font-medium text-gray-700">Your recommendation</div>
              <div class="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Recommendation">
                <button
                  v-for="v in VERDICTS"
                  :key="v.value"
                  type="button"
                  role="radio"
                  :aria-checked="extra.verdict === v.value"
                  :disabled="!form.can_score"
                  class="rounded-lg border px-2 py-2 text-xs font-medium transition disabled:cursor-not-allowed"
                  :class="extra.verdict === v.value ? v.on : 'border-gray-200 text-gray-700 hover:bg-gray-50'"
                  @click="extra.verdict = extra.verdict === v.value ? '' : v.value"
                >
                  {{ v.label }}
                </button>
              </div>
            </div>

            <FormControl label="Additional comments" type="textarea" v-model="extra.comments" :rows="3" :disabled="!form.can_score" />

            <template v-if="form.can_score">
              <label class="flex items-start gap-2.5 text-gray-700">
                <input v-model="extra.confirm" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
                <span v-if="form.on_behalf">I have entered these scores exactly as given on {{ form.panellist_name }}'s signed assessment form.</span>
                <span v-else>I confirm this is my assessment of the candidate as a member of the Selection Committee. <span class="text-xs text-gray-500">(In place of the panellist's signature.)</span></span>
              </label>
              <p v-if="saveError" class="rounded-md bg-red-50 px-3 py-2 text-red-700">{{ saveError }}</p>
              <div class="flex items-center gap-3">
                <Button variant="solid" :class="BTN_BRAND" :loading="saving" :disabled="!!blocker" :title="blocker" @click="save">
                  {{ form.mine ? 'Update scores' : 'Submit scores' }}
                </Button>
                <span v-if="form.mine" class="text-xs text-gray-500">Saved {{ dayjs(form.mine.modified).format('DD MMM, h:mm A') }}<template v-if="form.entered_by"> · entered by {{ form.entered_by }}</template></span>
              </div>
              <p v-if="blocker" class="text-xs text-gray-500">{{ blocker }}</p>
            </template>
          </div>
        </section>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import DocumentViewer from '@/components/common/DocumentViewer.vue'
import { useSessionStore } from '@/stores/session'
import { panelService } from '@/services/panel'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({ interview: { type: String, required: true } })
const router = useRouter()

const VERDICTS = [
  { value: 'Recommended', label: 'Recommend', on: 'border-green-600 bg-green-50 text-green-800' },
  { value: 'Waitlist', label: 'Waitlist', on: 'border-amber-500 bg-amber-50 text-amber-800' },
  { value: 'Not Recommended', label: 'Not recommended', on: 'border-red-500 bg-red-50 text-red-700' },
]

const form = ref(null)
const loading = ref(false)
const error = ref('')
const scores = reactive({})
const extra = reactive({ verdict: '', comments: '', area: '', confirm: false })
const saving = ref(false)
const saveError = ref('')

const session = useSessionStore()
const brief = computed(() => form.value?.brief || { documents: [], qualifications: [], employment: [] })
const viewer = reactive({ open: false, index: 0 })
const openDoc = (i) => Object.assign(viewer, { open: true, index: i })

// Previous / next candidate of the same job, from the panel list.
const siblings = ref([])
const index = computed(() => siblings.value.indexOf(props.interview))
const prev = computed(() => (index.value > 0 ? siblings.value[index.value - 1] : null))
const next = computed(() => (index.value >= 0 && index.value < siblings.value.length - 1 ? siblings.value[index.value + 1] : null))
const go = (name) => router.push(`/panel/${name}`)

const fmt = (n) => Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })
const num = (v) => (v === '' || v === null || v === undefined ? null : Number(v))
const invalid = (c) => {
  const v = num(scores[c.label])
  return v !== null && (Number.isNaN(v) || v < 0 || v > c.max_score)
}
const complete = computed(() => !!form.value && form.value.rubric.criteria.every((c) => num(scores[c.label]) !== null && !invalid(c)))
const total = computed(() => (form.value?.rubric.criteria || []).reduce((s, c) => s + (invalid(c) ? 0 : num(scores[c.label]) || 0), 0))
const percent = computed(() => (form.value?.rubric.max_score ? (total.value * 100) / form.value.rubric.max_score : 0))
const meetsBar = computed(() => complete.value && percent.value >= (form.value?.rubric.pass_percent || 50))
const blocker = computed(() => {
  if (!complete.value) return 'Score every criterion.'
  if (!extra.verdict) return 'Choose your recommendation.'
  if (!extra.confirm) return 'Tick the confirmation to submit.'
  return ''
})

async function load(name, panelist = null) {
  loading.value = true
  error.value = ''
  saveError.value = ''
  try {
    const f = await panelService.getAssessmentForm(name, panelist)
    form.value = f
    for (const k of Object.keys(scores)) delete scores[k]
    for (const c of f.rubric.criteria) scores[c.label] = c.score ?? ''
    Object.assign(extra, {
      verdict: f.mine?.verdict || '',
      comments: f.mine?.additional_comments || '',
      area: f.mine?.area_of_specialization || '',
      confirm: !!f.mine,
    })
  } catch (e) {
    form.value = null
    error.value = e?.messages?.[0] || 'Could not load the assessment form.'
  } finally {
    loading.value = false
  }
}

function pickPanellist(user) {
  if (user !== form.value?.panelist) load(props.interview, user)
}

async function loadSiblings() {
  try {
    const d = await panelService.getMyPanel()
    const me = d.interviews.find((iv) => iv.name === props.interview)
    siblings.value = me ? d.interviews.filter((iv) => iv.job_opening === me.job_opening).map((iv) => iv.name) : []
  } catch {
    siblings.value = []
  }
}

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    const r = await panelService.submitAssessment({
      interview: props.interview,
      panelist: form.value.panelist,
      scores: Object.fromEntries(form.value.rubric.criteria.map((c) => [c.label, num(scores[c.label])])),
      verdict: extra.verdict,
      additionalComments: extra.comments,
      areaOfSpecialization: extra.area,
    })
    toast({ title: `Scores saved: ${fmt(r.total_score)} / ${fmt(r.max_score)}.`, icon: 'check', iconClasses: 'text-green-500' })
    await load(props.interview, form.value.panelist)
  } catch (e) {
    saveError.value = e?.messages?.[0] || 'Could not save your scores.'
  } finally {
    saving.value = false
  }
}

watch(
  () => props.interview,
  (name) => {
    load(name)
    if (!siblings.value.includes(name)) loadSiblings()
  },
  { immediate: true },
)
</script>
