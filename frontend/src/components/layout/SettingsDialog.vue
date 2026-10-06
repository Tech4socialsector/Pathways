<template>
  <Dialog v-model="isOpen" :options="{ title: 'Pathways Settings', size: '2xl' }">
    <template #body-content>
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <div v-else class="flex flex-col gap-4">
        <ErrorMessage :message="formError" />

        <div class="text-xs font-semibold uppercase text-gray-500">Email</div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl label="Default Sender Email" v-model="form.default_sender_email" />
          <FormControl label="Recruitment Contact Email" v-model="form.recruitment_contact_email" />
        </div>

        <div class="mt-2 text-xs font-semibold uppercase text-gray-500">Offers & Interviews</div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            label="Acceptance Deadline (days)"
            type="number"
            v-model="form.acceptance_deadline_days"
          />
          <FormControl
            label="Interview Login Buffer (minutes)"
            type="number"
            v-model="form.interview_login_buffer_minutes"
          />
        </div>

        <div class="mt-2 text-xs font-semibold uppercase text-gray-500">Committees</div>
        <FormControl label="Default Shortlisting Ratio" type="number" v-model="form.default_shortlisting_ratio" />
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            label="Min Shortlisting Committee Size"
            type="number"
            v-model="form.min_shortlisting_committee_size"
          />
          <FormControl
            label="Max Shortlisting Committee Size"
            type="number"
            v-model="form.max_shortlisting_committee_size"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            label="Min Selection Committee Size"
            type="number"
            v-model="form.min_selection_committee_size"
          />
          <FormControl
            label="Max Selection Committee Size"
            type="number"
            v-model="form.max_selection_committee_size"
          />
        </div>

        <div class="mt-2 text-xs font-semibold uppercase text-gray-500">Offer Letter</div>
        <FormControl
          label="Default General Conditions"
          type="textarea"
          v-model="form.default_general_conditions"
        />

        <div class="mt-2 text-xs font-semibold uppercase text-gray-500">Approvals</div>
        <p class="-mt-2 text-xs text-gray-500">
          Who approves each Green Sheet is set per track in Master Setup &rsaquo; Approval Chains.
        </p>
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            label="Approval Override Role"
            type="select"
            v-model="form.approval_override_role"
            :options="roleSelectOptions"
            description="May record an approval on any step (e.g. a signed paper copy). Always flagged in the log."
          />
          <FormControl
            label="Job Status Override Role"
            type="select"
            v-model="form.status_override_role"
            :options="roleSelectOptions"
            description="May set any job status without an approved Green Sheet."
          />
        </div>
        <label class="flex items-center gap-2 text-sm text-gray-700">
          <input v-model="form.allow_same_approver_multiple_steps" type="checkbox" :true-value="1" :false-value="0" class="rounded border-gray-300" />
          Allow one person to approve more than one step of the same Green Sheet
        </label>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <span class="mb-1.5 block text-sm text-gray-700">Document Verifier Roles</span>
            <div class="max-h-36 overflow-y-auto rounded border p-2">
              <label v-for="r in roleOptions" :key="r" class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="form.document_verifier_roles" type="checkbox" :value="r" class="rounded border-gray-300" />
                {{ r }}
              </label>
            </div>
          </div>
          <div>
            <span class="mb-1.5 block text-sm text-gray-700">Corrigendum Signer Roles</span>
            <div class="max-h-36 overflow-y-auto rounded border p-2">
              <label v-for="r in roleOptions" :key="r" class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="form.corrigendum_signer_roles" type="checkbox" :value="r" class="rounded border-gray-300" />
                {{ r }}
              </label>
            </div>
          </div>
        </div>

        <div class="mt-2 text-xs font-semibold uppercase text-gray-500">Candidate Applications</div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl label="Max Upload Size (MB)" type="number" v-model="form.application_max_file_size_mb" />
          <FormControl label="Allowed Upload Formats" v-model="form.application_allowed_formats" />
        </div>
        <FormControl label="Application Declaration" type="textarea" :rows="6" v-model="form.application_declaration" />
      </div>
    </template>
    <template #actions>
      <Button variant="solid" :loading="saving" @click="submit">Save</Button>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Dialog, Button, FormControl, ErrorMessage } from 'frappe-ui'
import { toast } from '@/utils/notify'
import { useSettings } from '@/composables/useSettings'

const isOpen = defineModel({ type: Boolean, default: false })

const { settings, loading, saving, error, fetchSettings, saveSettings } = useSettings()

const form = reactive({})
const formError = ref('')
const roleOptions = ref([])
// frappe-ui's Select drops options whose value is '', so "nobody" needs a
// sentinel that is mapped back to blank on save.
const NONE = '__none__'
const ROLE_FIELDS = ['approval_override_role', 'status_override_role']
const roleSelectOptions = computed(() => [
  { label: '(Disabled)', value: NONE },
  ...roleOptions.value.map((r) => ({ label: r, value: r })),
])

watch(isOpen, async (open) => {
  if (!open) return
  formError.value = ''
  await fetchSettings()
  const { role_options, ...values } = settings.value || {}
  roleOptions.value = role_options || []
  Object.assign(form, values)
  for (const field of ROLE_FIELDS) form[field] = values[field] || NONE
  form.document_verifier_roles = [...(values.document_verifier_roles || [])]
  form.corrigendum_signer_roles = [...(values.corrigendum_signer_roles || [])]
})

async function submit() {
  formError.value = ''
  const payload = { ...form }
  for (const field of ROLE_FIELDS) if (payload[field] === NONE) payload[field] = ''
  const ok = await saveSettings(payload)
  if (ok) {
    toast({ title: 'Settings saved.', icon: 'check', iconClasses: 'text-green-500' })
    isOpen.value = false
  } else {
    formError.value = error.value?.messages?.[0] || 'Could not save settings.'
  }
}
</script>
