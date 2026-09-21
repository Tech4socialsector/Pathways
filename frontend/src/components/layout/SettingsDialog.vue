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
      </div>
    </template>
    <template #actions>
      <Button variant="solid" :loading="saving" @click="submit">Save</Button>
    </template>
  </Dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { Dialog, Button, FormControl, ErrorMessage, toast } from 'frappe-ui'
import { useSettings } from '@/composables/useSettings'

const isOpen = defineModel({ type: Boolean, default: false })

const { settings, loading, saving, fetchSettings, saveSettings } = useSettings()

const form = reactive({})
const formError = ref('')

watch(isOpen, async (open) => {
  if (!open) return
  formError.value = ''
  await fetchSettings()
  Object.assign(form, settings.value)
})

async function submit() {
  formError.value = ''
  const ok = await saveSettings({ ...form })
  if (ok) {
    toast({ title: 'Settings saved.', icon: 'check', iconClasses: 'text-green-500' })
    isOpen.value = false
  } else {
    formError.value = 'Could not save settings.'
  }
}
</script>
