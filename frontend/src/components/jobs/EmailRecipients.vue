<template>
  <!-- Who an interview email goes to (To / CC from Email Setup), with extra
       CC and BCC addresses for this send. -->
  <div class="rounded-lg border bg-white text-sm">
    <div v-if="loading" class="px-3 py-2 text-xs text-gray-500">Loading recipients…</div>
    <template v-else>
      <p v-if="info && !info.enabled" class="flex items-center gap-1.5 border-b bg-orange-50 px-3 py-2 text-xs text-orange-800">
        <FeatherIcon name="alert-triangle" class="h-3.5 w-3.5 shrink-0" />
        "{{ info.label }}" is turned off in Email Setup, so no email will be sent.
      </p>
      <div class="flex items-start gap-3 border-b px-3 py-2">
        <span class="w-8 shrink-0 pt-0.5 text-xs font-semibold uppercase text-gray-500">To</span>
        <div class="flex min-w-0 flex-1 flex-wrap gap-1.5">
          <template v-if="info?.to_candidate">
            <span v-for="n in candidateChips" :key="n" class="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-800">{{ n }}</span>
          </template>
          <span v-for="r in info?.to || []" :key="r.email" class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700" :title="r.email">{{ r.name || r.email }}</span>
          <span v-if="!info?.to_candidate && !(info?.to || []).length" class="text-xs text-gray-500">Nobody (check Email Setup)</span>
        </div>
      </div>
      <div class="flex items-start gap-3 border-b px-3 py-2">
        <span class="w-8 shrink-0 pt-1 text-xs font-semibold uppercase text-gray-500">CC</span>
        <div class="flex min-w-0 flex-1 flex-col gap-2">
          <div class="flex flex-wrap items-center gap-1.5">
            <span v-for="e in info?.cc || []" :key="e" class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700" title="Always copied (Email Setup)">{{ e }}</span>
            <span v-for="e in modelValue" :key="e" class="flex items-center gap-1 rounded-full bg-blue-50 py-0.5 pl-2 pr-1 text-xs text-blue-800">
              {{ e }}
              <button type="button" class="rounded-full p-0.5 hover:bg-blue-100" :aria-label="`Remove ${e}`" @click="remove('cc', e)">
                <FeatherIcon name="x" class="h-3 w-3" />
              </button>
            </span>
            <input
              v-model="drafts.cc"
              type="email"
              class="min-w-[12rem] flex-1 border-0 p-0.5 text-sm focus:ring-0"
              placeholder="Add email, press Enter"
              aria-label="Add CC email"
              @keydown.enter.prevent="addDraft('cc')"
              @keydown="(e) => [',', ';'].includes(e.key) && (e.preventDefault(), addDraft('cc'))"
              @blur="addDraft('cc')"
            />
          </div>
          <div v-if="openSuggestions.length" class="flex flex-wrap items-center gap-1.5">
            <span class="text-xs text-gray-500">Add:</span>
            <button
              v-for="s in openSuggestions"
              :key="s.email"
              type="button"
              class="flex items-center gap-1 rounded-full border border-dashed px-2 py-0.5 text-xs text-gray-700 hover:border-brand-300 hover:bg-brand-50"
              :title="`${s.email} · ${s.tag}`"
              @click="add('cc', s.email)"
            >
              <FeatherIcon name="plus" class="h-3 w-3" />{{ s.name }}
            </button>
          </div>
          <p v-if="errors.cc" class="text-xs text-red-600">{{ errors.cc }}</p>
        </div>
      </div>
      <div class="flex items-start gap-3 px-3 py-2">
        <span class="w-8 shrink-0 pt-1 text-xs font-semibold uppercase text-gray-500">BCC</span>
        <div class="flex min-w-0 flex-1 flex-col gap-1.5">
          <div class="flex flex-wrap items-center gap-1.5">
            <span v-for="e in bcc" :key="e" class="flex items-center gap-1 rounded-full bg-violet-50 py-0.5 pl-2 pr-1 text-xs text-violet-800">
              {{ e }}
              <button type="button" class="rounded-full p-0.5 hover:bg-violet-100" :aria-label="`Remove ${e}`" @click="remove('bcc', e)">
                <FeatherIcon name="x" class="h-3 w-3" />
              </button>
            </span>
            <input
              v-model="drafts.bcc"
              type="email"
              class="min-w-[12rem] flex-1 border-0 p-0.5 text-sm focus:ring-0"
              placeholder="Add email, press Enter"
              aria-label="Add BCC email"
              @keydown.enter.prevent="addDraft('bcc')"
              @keydown="(e) => [',', ';'].includes(e.key) && (e.preventDefault(), addDraft('bcc'))"
              @blur="addDraft('bcc')"
            />
          </div>
          <p v-if="errors.bcc" class="text-xs text-red-600">{{ errors.bcc }}</p>
          <p v-else class="text-xs text-gray-500">Hidden from the candidate and everyone else on the email.</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { interviewService } from '@/services/interviews'

const props = defineProps({
  // extra CC addresses (v-model)
  modelValue: { type: Array, default: () => [] },
  // BCC addresses (v-model:bcc)
  bcc: { type: Array, default: () => [] },
  roundType: { type: String, default: 'HR Interaction' },
  jobOpenings: { type: Array, default: () => [] },
  cancelled: { type: Boolean, default: false },
  candidateNames: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'update:bcc'])

const info = ref(null)
const loading = ref(false)
const drafts = reactive({ cc: '', bcc: '' })
const errors = reactive({ cc: '', bcc: '' })
const EMAIL = /^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$/
// Same limit as the server (interviews._copies).
const MAX_COPIES = 20
const LABEL = { cc: 'CC', bcc: 'BCC' }

const candidateChips = computed(() => {
  const n = props.candidateNames
  if (n.length > 3) return [`Each of the ${n.length} candidates`]
  return n.length ? n : ['Candidate']
})
const lower = (list) => list.map((e) => e.toLowerCase())
const values = (field) => (field === 'cc' ? props.modelValue : props.bcc)
// Where an address already is: the rule's To / CC, or the other extra list.
function placeOf(email) {
  const e = email.toLowerCase()
  if (lower((info.value?.to || []).map((r) => r.email)).includes(e)) return 'To'
  if (lower([...(info.value?.cc || []), ...props.modelValue]).includes(e)) return 'CC'
  if (lower(props.bcc).includes(e)) return 'BCC'
  return ''
}
const openSuggestions = computed(() => (info.value?.suggestions || []).filter((s) => !placeOf(s.email)))

watch(
  () => [props.roundType, props.cancelled, props.jobOpenings.join(',')],
  async () => {
    loading.value = true
    try {
      info.value = await interviewService.getEmailRecipients({ roundType: props.roundType, jobOpenings: props.jobOpenings, cancelled: props.cancelled })
    } catch {
      info.value = null
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

function emitField(field, list) {
  emit(field === 'cc' ? 'update:modelValue' : 'update:bcc', list)
}
function add(field, email) {
  if (placeOf(email)) return
  if (values(field).length >= MAX_COPIES) {
    errors[field] = `At most ${MAX_COPIES} ${LABEL[field]} addresses per email.`
    return
  }
  emitField(field, [...values(field), email])
}
function remove(field, email) {
  emitField(field, values(field).filter((e) => e !== email))
  errors[field] = ''
}
// Adds what is typed in `field`; keeps the ones that cannot be added in the
// box with the reason. Returns the field's list after adding.
function addDraft(field) {
  const parts = drafts[field].split(/[\s,;]+/).filter(Boolean)
  const kept = []
  const problems = []
  // One emit for all of them: the prop only updates after the parent re-renders.
  const fresh = []
  const seen = new Set()
  for (const p of parts) {
    const where = placeOf(p) || (seen.has(p.toLowerCase()) ? LABEL[field] : '')
    if (!EMAIL.test(p)) {
      kept.push(p)
      problems.push(`Not a valid email: ${p}`)
    } else if (where) {
      problems.push(where === LABEL[field] ? `${p} is already added.` : `${p} is already in ${where}.`)
    } else if (values(field).length + fresh.length >= MAX_COPIES) {
      kept.push(p)
      problems.push(`At most ${MAX_COPIES} ${LABEL[field]} addresses per email.`)
    } else {
      seen.add(p.toLowerCase())
      fresh.push(p)
    }
  }
  const all = fresh.length ? [...values(field), ...fresh] : values(field)
  if (fresh.length) emitField(field, all)
  drafts[field] = kept.join(', ')
  errors[field] = [...new Set(problems)].join(' ')
  return { emails: all, valid: !kept.length }
}

// The parent calls this before it sends, so an address typed but not yet
// added counts. null when CC or BCC still holds an address that cannot go.
function commit() {
  const cc = addDraft('cc')
  const bcc = addDraft('bcc')
  return cc.valid && bcc.valid ? { cc: cc.emails, bcc: bcc.emails } : null
}

defineExpose({ commit })
</script>
