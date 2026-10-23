<template>
  <Dialog v-model="open" :options="{ title: 'Create Offer', size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-4 text-sm">
        <p class="text-gray-600">
          Starts a draft appointment order. Candidates appear here once they are recommended or waitlisted on an approved
          Post-Interview Green Sheet and have no offer yet.
        </p>
        <div v-if="loading" class="text-gray-500">Loading...</div>
        <template v-else>
          <FormControl
            v-if="!application"
            type="select"
            label="Candidate"
            :options="candidateOptions"
            v-model="form.application"
          />
          <div v-else class="rounded border border-gray-200 bg-gray-50 px-3 py-2">
            Application <b>{{ application }}</b>
          </div>
          <p v-if="!application && !candidates.length" class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800">
            No candidate is ready for an offer. Approve the Post-Interview Green Sheet for the job first.
          </p>
          <FormControl type="select" label="Appointment Order Template" :options="templateOptions" v-model="form.template" />
          <p class="-mt-2 text-xs text-gray-500">Leave on "Suggest" to pick the best match for the job's track, employment type and designation.</p>
          <ErrorMessage :message="error" />
        </template>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button @click="open = false">Cancel</Button>
        <Button variant="solid" :class="BTN_BRAND" :loading="saving" :disabled="!(application || form.application)" @click="create">
          Create Draft
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { offerService } from '@/services/offers'
import { BTN_BRAND } from '@/utils/buttonStyles'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // Preset from ApplicationDetail; otherwise the user picks a candidate.
  application: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'created'])
const open = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

const SUGGEST = '__suggest__'
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const candidates = ref([])
const templates = ref([])
const form = reactive({ application: '', template: SUGGEST })

const candidateOptions = computed(() => [
  { label: 'Select a candidate', value: '' },
  ...candidates.value.map((c) => ({ label: `${c.candidate_name} · ${c.job_title} (${c.application_id || c.name})`, value: c.name })),
])
const templateOptions = computed(() => [
  { label: 'Suggest', value: SUGGEST },
  ...templates.value.map((t) => ({ label: t.name, value: t.name })),
])

watch(open, async (isOpen) => {
  if (!isOpen) return
  error.value = ''
  form.application = ''
  form.template = SUGGEST
  loading.value = true
  try {
    const [cands, tpls] = await Promise.all([
      props.application ? Promise.resolve([]) : offerService.getOfferCandidates(),
      offerService.getTemplates(),
    ])
    candidates.value = cands || []
    templates.value = tpls || []
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load candidates.'
  } finally {
    loading.value = false
  }
})

async function create() {
  saving.value = true
  error.value = ''
  try {
    const data = form.template && form.template !== SUGGEST ? { appointment_order_template: form.template } : {}
    const name = await offerService.createOffer(props.application || form.application, data)
    open.value = false
    emit('created', name)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not create the offer.'
  } finally {
    saving.value = false
  }
}
</script>
