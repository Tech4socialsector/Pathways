<template>
  <!-- Frappe's Google Settings, edited here instead of the desk. Saved on its
       own (System Manager only), separately from Pathways Settings. -->
  <div>
    <div v-if="loading" class="h-40 animate-pulse rounded-xl bg-gray-50" aria-busy="true" />

    <p v-else-if="loadError" class="flex items-start gap-2 rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600">
      <FeatherIcon name="lock" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
      {{ loadError }}
    </p>

    <form v-else class="overflow-hidden rounded-xl border" novalidate @submit.prevent="save">
      <!-- On/off -->
      <div class="flex items-center justify-between gap-4 border-b bg-gray-50/70 px-4 py-3.5">
        <div class="min-w-0">
          <p class="text-sm font-semibold text-gray-900">Google integration</p>
          <p class="mt-0.5 text-p-sm text-gray-500">
            {{ form.enable ? 'On. Pathways uses the credentials below.' : 'Off. Enter the credentials, then turn this on.' }}
          </p>
        </div>
        <ToggleSwitch v-model="form.enable" label="Enable Google integration" :disabled="!canEdit" />
      </div>

      <div class="flex flex-col gap-4 p-4">
        <p v-if="!canEdit" class="flex items-start gap-2 rounded-lg bg-gray-50 px-3 py-2.5 text-sm text-gray-600">
          <FeatherIcon name="lock" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
          Only a System Manager can change these.
        </p>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <SettingsField label="Client ID" :error="errors.client_id" hint="From the OAuth client you created.">
            <TextInput v-model="form.client_id" type="text" :disabled="!canEdit" autocomplete="off" placeholder="1234…apps.googleusercontent.com" />
          </SettingsField>
          <SettingsField
            label="Client Secret"
            :error="errors.client_secret"
            :hint="hasSecret ? 'Saved. Leave blank to keep it.' : 'Shown when you create the OAuth client.'"
          >
            <div class="relative">
              <TextInput
                v-model="form.client_secret"
                :type="showSecret ? 'text' : 'password'"
                :disabled="!canEdit"
                autocomplete="new-password"
                :placeholder="hasSecret ? '•••••••••• saved' : 'Paste the secret'"
                class="[&_input]:pr-9"
              />
              <button
                v-if="form.client_secret"
                type="button"
                class="absolute inset-y-0 right-0 flex w-9 items-center justify-center text-gray-400 hover:text-gray-700"
                :aria-label="showSecret ? 'Hide secret' : 'Show secret'"
                @click="showSecret = !showSecret"
              >
                <FeatherIcon :name="showSecret ? 'eye-off' : 'eye'" class="h-4 w-4" />
              </button>
            </div>
          </SettingsField>
        </div>

        <!-- Optional extra; collapsed unless already in use. -->
        <details class="group rounded-lg border" :open="pickerOpen" @toggle="pickerOpen = $event.target.open">
          <summary class="flex cursor-pointer list-none items-center justify-between gap-2 px-3.5 py-2.5 text-sm">
            <span class="font-medium text-gray-800">
              Google Drive Picker
              <span class="ml-1 font-normal text-gray-500">{{ form.google_drive_picker_enabled ? '· On' : '· Optional, not needed for Meet' }}</span>
            </span>
            <FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-400 transition group-open:rotate-180" />
          </summary>
          <div class="flex flex-col gap-4 border-t px-3.5 py-3.5">
            <div class="flex items-center justify-between gap-4">
              <p class="text-sm text-gray-700">Let users attach files from Google Drive</p>
              <ToggleSwitch v-model="form.google_drive_picker_enabled" label="Enable Google Drive Picker" :disabled="!canEdit" />
            </div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <SettingsField label="App ID" :error="errors.app_id" hint="The Google Cloud project number.">
                <TextInput v-model="form.app_id" type="text" :disabled="!canEdit" autocomplete="off" />
              </SettingsField>
              <SettingsField label="API Key" hint="A browser API key.">
                <TextInput v-model="form.api_key" type="text" :disabled="!canEdit" autocomplete="off" />
              </SettingsField>
            </div>
          </div>
        </details>

        <ErrorMessage :message="saveError" />
      </div>

      <!-- Only when there is something to save. -->
      <div v-if="canEdit && dirty" class="flex items-center justify-between gap-3 border-t bg-brand-50/40 px-4 py-3">
        <span class="text-sm text-gray-600">Unsaved Google settings</span>
        <div class="flex gap-2">
          <Button :disabled="saving" @click="discard">Discard</Button>
          <Button type="submit" variant="solid" :class="BTN_BRAND" :loading="saving">Save</Button>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Button, ErrorMessage, FeatherIcon, TextInput } from 'frappe-ui'
import SettingsField from '@/components/settings/SettingsField.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { settingsService } from '@/services/settings'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const emit = defineEmits(['saved'])

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const saveError = ref('')
const canEdit = ref(false)
const hasSecret = ref(false)
const showSecret = ref(false)
const showErrors = ref(false)
const pickerOpen = ref(false)

const form = reactive({ enable: false, client_id: '', client_secret: '', api_key: '', google_drive_picker_enabled: false, app_id: '' })
const snapshot = ref('')
const serialize = () => JSON.stringify({ ...form, client_id: form.client_id.trim(), app_id: form.app_id.trim(), api_key: form.api_key.trim() })
const dirty = computed(() => serialize() !== snapshot.value)

let lastLoaded = {}
function fill(data) {
  lastLoaded = data
  form.enable = Boolean(data.enable)
  form.client_id = data.client_id || ''
  form.client_secret = ''
  form.api_key = data.api_key || ''
  form.google_drive_picker_enabled = Boolean(data.google_drive_picker_enabled)
  form.app_id = data.app_id || ''
  hasSecret.value = Boolean(data.has_client_secret)
  canEdit.value = Boolean(data.can_edit)
  showSecret.value = false
  pickerOpen.value = form.google_drive_picker_enabled
  snapshot.value = serialize()
}

function discard() {
  fill(lastLoaded)
  showErrors.value = false
  saveError.value = ''
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    fill(await settingsService.getGoogleSettings())
  } catch (e) {
    loadError.value =
      e?.exc_type === 'PermissionError' || e?.status === 403
        ? 'Only a System Manager can view or change Google settings.'
        : e?.messages?.[0] || 'Could not load Google settings.'
  } finally {
    loading.value = false
  }
}

// Same rules as the server, shown before saving.
const errors = computed(() => {
  if (!showErrors.value) return {}
  const e = {}
  if (form.enable && !form.client_id.trim()) e.client_id = 'Required to enable Google.'
  if (form.enable && !hasSecret.value && !form.client_secret.trim()) e.client_secret = 'Required to enable Google.'
  if (form.google_drive_picker_enabled && !form.client_id.trim()) e.client_id = e.client_id || 'Required for the Drive Picker.'
  if (form.google_drive_picker_enabled && !form.app_id.trim()) e.app_id = 'Required for the Drive Picker.'
  return e
})

async function save() {
  if (saving.value || !canEdit.value || !dirty.value) return
  showErrors.value = true
  saveError.value = ''
  if (Object.keys(errors.value).length) return
  saving.value = true
  try {
    const result = await settingsService.saveGoogleSettings({
      enable: form.enable ? 1 : 0,
      client_id: form.client_id.trim(),
      client_secret: form.client_secret.trim(),
      api_key: form.api_key.trim(),
      google_drive_picker_enabled: form.google_drive_picker_enabled ? 1 : 0,
      app_id: form.app_id.trim(),
    })
    fill(result)
    showErrors.value = false
    toast({ title: 'Google settings saved.' })
    emit('saved')
  } catch (e) {
    saveError.value = e?.messages?.[0] || 'Could not save Google settings.'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
