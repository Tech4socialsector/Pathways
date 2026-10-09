<template>
  <!-- Who an interview email goes to (To / CC from Email Setup), with extra
       CC addresses for this send. -->
  <div class="rounded-lg border bg-white text-sm">
    <div v-if="loading" class="px-3 py-2 text-xs text-gray-500">Loading recipients…</div>
    <template v-else>
      <p v-if="info && !info.enabled" class="flex items-center gap-1.5 border-b bg-orange-50 px-3 py-2 text-xs text-orange-800">
        <FeatherIcon name="alert-triangle" class="h-3.5 w-3.5 shrink-0" />
        "{{ info.label }}" is turned off in Email Setup, so no email will be sent.
      </p>
      <div class="flex items-start gap-3 border-b px-3 py-2">
        <span class="w-7 shrink-0 pt-0.5 text-xs font-semibold uppercase text-gray-500">To</span>
        <div class="flex min-w-0 flex-1 flex-wrap gap-1.5">
          <template v-if="info?.to_candidate">
            <span v-for="n in candidateChips" :key="n" class="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-800">{{ n }}</span>
          </template>
          <span v-for="r in info?.to || []" :key="r.email" class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700" :title="r.email">{{ r.name || r.email }}</span>
          <span v-if="!info?.to_candidate && !(info?.to || []).length" class="text-xs text-gray-500">Nobody (check Email Setup)</span>
        </div>
      </div>
      <div class="flex items-start gap-3 px-3 py-2">
        <span class="w-7 shrink-0 pt-1 text-xs font-semibold uppercase text-gray-500">CC</span>
        <div class="flex min-w-0 flex-1 flex-col gap-2">
          <div class="flex flex-wrap items-center gap-1.5">
            <span v-for="e in info?.cc || []" :key="e" class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700" title="Always copied (Email Setup)">{{ e }}</span>
            <span v-for="e in modelValue" :key="e" class="flex items-center gap-1 rounded-full bg-blue-50 py-0.5 pl-2 pr-1 text-xs text-blue-800">
              {{ e }}
              <button type="button" class="rounded-full p-0.5 hover:bg-blue-100" :aria-label="`Remove ${e}`" @click="remove(e)">
                <FeatherIcon name="x" class="h-3 w-3" />
              </button>
            </span>
            <input
              v-model="draft"
              type="email"
              class="min-w-[12rem] flex-1 border-0 p-0.5 text-sm focus:ring-0"
              placeholder="Add email, press Enter"
              aria-label="Add CC email"
              @keydown.enter.prevent="addDraft"
              @keydown="(e) => [',', ';'].includes(e.key) && (e.preventDefault(), addDraft())"
              @blur="addDraft"
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
              @click="add(s.email)"
            >
              <FeatherIcon name="plus" class="h-3 w-3" />{{ s.name }}
            </button>
          </div>
          <p v-if="draftError" class="text-xs text-red-600">{{ draftError }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { interviewService } from '@/services/interviews'

const props = defineProps({
  // extra CC addresses (v-model)
  modelValue: { type: Array, default: () => [] },
  roundType: { type: String, default: 'HR Interaction' },
  jobOpenings: { type: Array, default: () => [] },
  cancelled: { type: Boolean, default: false },
  candidateNames: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const info = ref(null)
const loading = ref(false)
const draft = ref('')
const draftError = ref('')
const EMAIL = /^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$/

const candidateChips = computed(() => {
  const n = props.candidateNames
  if (n.length > 3) return [`Each of the ${n.length} candidates`]
  return n.length ? n : ['Candidate']
})
const taken = computed(() => new Set([...(info.value?.cc || []), ...props.modelValue].map((e) => e.toLowerCase())))
const openSuggestions = computed(() => (info.value?.suggestions || []).filter((s) => !taken.value.has(s.email.toLowerCase())))

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

function add(email) {
  if (!taken.value.has(email.toLowerCase())) emit('update:modelValue', [...props.modelValue, email])
}
function remove(email) {
  emit('update:modelValue', props.modelValue.filter((e) => e !== email))
}
function addDraft() {
  const parts = draft.value.split(/[\s,;]+/).filter(Boolean)
  const bad = parts.filter((p) => !EMAIL.test(p))
  // One emit for all of them: the prop only updates after the parent re-renders.
  const seen = new Set(taken.value)
  const fresh = parts.filter((p) => EMAIL.test(p) && !seen.has(p.toLowerCase()) && seen.add(p.toLowerCase()))
  if (fresh.length) emit('update:modelValue', [...props.modelValue, ...fresh])
  draft.value = bad.join(', ')
  draftError.value = bad.length ? `Not a valid email: ${bad.join(', ')}` : ''
}
</script>
