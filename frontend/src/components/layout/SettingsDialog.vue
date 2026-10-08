<template>
  <Dialog v-model="isOpen" :options="{ title: 'Pathways Settings', size: tab === 'access' ? '7xl' : '3xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <ErrorMessage :message="formError" />

        <nav v-if="tabs.length > 1" class="-mt-2 flex gap-1 border-b" role="tablist">
          <button
            v-for="t in tabs"
            :key="t.key"
            role="tab"
            :aria-selected="tab === t.key"
            class="relative flex items-center gap-1.5 px-3 py-2 text-sm"
            :class="tab === t.key ? 'font-semibold text-brand-700' : 'text-gray-600 hover:text-gray-900'"
            @click="tab = t.key"
          >
            <FeatherIcon :name="t.icon" class="h-4 w-4" />{{ t.label }}
            <span v-if="tab === t.key" class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-700" />
          </button>
        </nav>

        <div v-if="loading" v-show="tab !== 'access'" class="text-sm text-gray-500">Loading...</div>
        <template v-else-if="canEditSettings">
          <!-- Appearance -->
          <div v-show="tab === 'appearance'" class="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,1fr)_17rem]">
            <div class="flex flex-col gap-5">
              <div class="grid grid-cols-[auto_minmax(0,1fr)] items-end gap-4">
                <div>
                  <span class="mb-1.5 block text-sm text-gray-700">Logo</span>
                  <div class="flex h-14 w-14 items-center justify-center overflow-hidden rounded-lg border bg-gray-50">
                    <img v-if="form.app_logo" :src="form.app_logo" alt="" class="h-full w-full object-contain p-1" />
                    <FeatherIcon v-else name="image" class="h-5 w-5 text-gray-400" />
                  </div>
                </div>
                <div class="flex flex-col gap-2">
                  <FormControl label="App Name" v-model="form.app_name" placeholder="Pathways" />
                  <div class="flex flex-wrap gap-2">
                    <FileUploader
                      file-types="image/*"
                      :upload-args="{ doctype: 'Pathways Settings', docname: 'Pathways Settings', private: false }"
                      @success="(file) => (form.app_logo = file.file_url)"
                    >
                      <template #default="{ openFileSelector, uploading }">
                        <Button size="sm" icon-left="upload" :loading="uploading" @click="openFileSelector">
                          {{ form.app_logo ? 'Replace logo' : 'Upload logo' }}
                        </Button>
                      </template>
                    </FileUploader>
                    <Button v-if="form.app_logo" size="sm" variant="ghost" @click="form.app_logo = ''">Use default mark</Button>
                  </div>
                </div>
              </div>

              <div>
                <span class="mb-1.5 block text-sm text-gray-700">Brand Colour</span>
                <div class="flex flex-wrap items-center gap-2">
                  <button
                    v-for="p in COLOR_PRESETS"
                    :key="p.value"
                    class="h-8 w-8 rounded-full ring-offset-2 transition"
                    :class="sameColor(form.brand_color, p.value) ? 'ring-2 ring-gray-900' : 'hover:ring-2 hover:ring-gray-300'"
                    :style="{ backgroundColor: p.value }"
                    :title="p.name"
                    :aria-label="p.name"
                    @click="form.brand_color = p.value"
                  />
                  <label class="ml-2 flex items-center gap-2 rounded-md border px-2 py-1">
                    <input v-model="form.brand_color" type="color" class="h-6 w-8 cursor-pointer border-0 bg-transparent p-0" aria-label="Custom colour" />
                    <input
                      v-model.lazy="form.brand_color"
                      class="w-20 border-0 bg-transparent p-0 font-mono text-sm uppercase focus:ring-0"
                      maxlength="7"
                      aria-label="Hex colour"
                    />
                  </label>
                </div>
                <div class="mt-3 flex overflow-hidden rounded-md border">
                  <div
                    v-for="(rgb, shade) in shades"
                    :key="shade"
                    class="h-6 flex-1"
                    :style="{ backgroundColor: `rgb(${rgb.join(' ')})` }"
                    :title="`brand-${shade}`"
                  />
                </div>
                <p v-if="!isValidHex(form.brand_color)" class="mt-1.5 text-xs text-red-600">Enter a colour as #RRGGBB, e.g. #920C24.</p>
                <p v-else-if="lowContrast" class="mt-1.5 text-xs text-orange-700">
                  White text on this colour is hard to read (contrast {{ contrast.toFixed(1) }}:1). Pick a darker shade for buttons and
                  the top bar.
                </p>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <FormControl label="Body Font" type="select" v-model="form.body_font" :options="FONT_NAMES" />
                <FormControl label="Heading Font" type="select" v-model="form.heading_font" :options="FONT_NAMES" />
              </div>
              <p class="-mt-2 text-xs text-gray-500">
                Changes show immediately so you can preview them. Save to apply for everyone; close without saving to undo.
              </p>
            </div>

            <!-- Preview -->
            <div class="overflow-hidden rounded-xl border bg-gray-50 text-sm shadow-sm">
              <div class="flex items-center gap-2 bg-brand-700 px-3 py-2 text-white">
                <img v-if="form.app_logo" :src="form.app_logo" alt="" class="h-5 w-5 rounded bg-white object-contain" />
                <span v-else class="flex h-5 w-5 items-center justify-center rounded bg-white text-[11px] font-bold text-brand-700">
                  {{ (form.app_name || 'P')[0] }}
                </span>
                <span class="truncate font-heading font-bold">{{ form.app_name || 'Pathways' }}</span>
              </div>
              <div class="flex flex-col gap-3 p-3">
                <div class="rounded-lg border bg-white p-3">
                  <h3 class="text-base font-bold text-brand-700">Section heading</h3>
                  <p class="mt-1 text-xs text-gray-600">Body text in the chosen font. The quick brown fox jumps over the lazy dog.</p>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span class="rounded-md bg-brand-700 px-2.5 py-1 text-xs font-medium text-white">Primary</span>
                    <span class="rounded-md border border-brand-200 bg-white px-2.5 py-1 text-xs font-medium text-brand-700">Outline</span>
                    <span class="rounded-full bg-brand-50 px-2 py-1 text-xs font-semibold text-brand-700">63 / 100</span>
                  </div>
                </div>
                <div class="flex items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-700">
                  <FeatherIcon name="check-circle" class="h-4 w-4" /> Highlighted item
                </div>
              </div>
            </div>
          </div>

          <!-- General -->
          <div v-show="tab === 'general'" class="flex flex-col gap-6">
            <!-- Email settings live on their own page, with a test send. -->
            <div class="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-gray-50 px-4 py-3">
              <div class="min-w-0">
                <p class="text-sm font-medium text-gray-800">Email</p>
                <p class="mt-0.5 text-p-sm text-gray-600">The sending account, reply-to address and emails by stage are set in Email Setup.</p>
              </div>
              <Button icon-right="arrow-right" @click="openEmailSetup">Email Setup</Button>
            </div>

            <section class="flex flex-col gap-4">
              <h3 class="border-b pb-2 text-sm font-semibold uppercase tracking-wide text-gray-600">Offers</h3>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SettingsField label="Offer Acceptance Deadline (days)" :error="errors.acceptance_deadline_days" hint="Days a candidate has to accept an offer before it lapses.">
                  <TextInput v-model="form.acceptance_deadline_days" type="number" min="1" max="365" step="1" />
                </SettingsField>
              </div>
            </section>

            <section class="flex flex-col gap-4">
              <h3 class="border-b pb-2 text-sm font-semibold uppercase tracking-wide text-gray-600">Shortlisting & committees</h3>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SettingsField label="Default Shortlisting Ratio (1:N)" :error="errors.default_shortlisting_ratio" hint="Shortlist 1 candidate per N applications, where available. A job opening can set its own.">
                  <TextInput v-model="form.default_shortlisting_ratio" type="number" min="1" step="1" />
                </SettingsField>
              </div>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SettingsField label="Shortlisting committee — min members" :error="errors.min_shortlisting_committee_size">
                  <TextInput v-model="form.min_shortlisting_committee_size" type="number" min="1" step="1" />
                </SettingsField>
                <SettingsField label="Shortlisting committee — max members" :error="errors.max_shortlisting_committee_size">
                  <TextInput v-model="form.max_shortlisting_committee_size" type="number" min="1" step="1" />
                </SettingsField>
                <SettingsField label="Selection committee — min members" :error="errors.min_selection_committee_size">
                  <TextInput v-model="form.min_selection_committee_size" type="number" min="1" step="1" />
                </SettingsField>
                <SettingsField label="Selection committee — max members" :error="errors.max_selection_committee_size">
                  <TextInput v-model="form.max_selection_committee_size" type="number" min="1" step="1" />
                </SettingsField>
              </div>
            </section>

            <section class="flex flex-col gap-4">
              <div class="border-b pb-2">
                <h3 class="text-sm font-semibold uppercase tracking-wide text-gray-600">Approvals</h3>
                <p class="mt-1 text-p-sm text-gray-500">
                  Who approves each Green Sheet is set per track in
                  <button type="button" class="font-medium text-brand-700 hover:underline" @click="go('/master-setup/approval-chain-template')">Master Setup › Approval Chains</button>.
                </p>
              </div>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SettingsField label="Approval Override Role" hint="May record an approval on any step (e.g. a signed paper copy). Always flagged in the log.">
                  <FormControl v-model="form.approval_override_role" type="select" :options="roleSelectOptions" />
                </SettingsField>
                <SettingsField label="Job Status Override Role" hint="May set any job status without an approved Green Sheet.">
                  <FormControl v-model="form.status_override_role" type="select" :options="roleSelectOptions" />
                </SettingsField>
              </div>
              <label class="flex cursor-pointer items-start gap-2.5">
                <input
                  v-model="form.allow_same_approver_multiple_steps"
                  type="checkbox"
                  :true-value="1"
                  :false-value="0"
                  class="mt-px h-4 w-4 rounded border-gray-300 text-brand-700 focus:ring-brand-500"
                />
                <span>
                  <span class="block text-base text-gray-800">Allow one person to approve more than one step of the same Green Sheet</span>
                  <span class="mt-0.5 block text-p-sm text-gray-500">When off, someone who approved one step cannot approve a later step of that sheet.</span>
                </span>
              </label>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SettingsField
                  v-for="duty in DUTIES"
                  :key="duty.field"
                  :label="duty.label"
                  :hint="form[duty.field]?.length ? duty.hint : ''"
                  :warning="form[duty.field]?.length ? '' : duty.empty"
                  as="div"
                >
                  <div class="max-h-40 overflow-y-auto rounded border p-1.5">
                    <label
                      v-for="r in roleOptions"
                      :key="r"
                      class="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <input v-model="form[duty.field]" type="checkbox" :value="r" class="h-4 w-4 rounded border-gray-300 text-brand-700 focus:ring-brand-500" />
                      {{ r }}
                    </label>
                  </div>
                </SettingsField>
              </div>
            </section>

            <section class="flex flex-col gap-4">
              <h3 class="border-b pb-2 text-sm font-semibold uppercase tracking-wide text-gray-600">Candidate applications</h3>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SettingsField
                  label="Max Upload Size (MB)"
                  :error="errors.application_max_file_size_mb"
                  :hint="`Per file, up to ${maxUploadMb} MB (this site's limit). A Document Type can set its own.`"
                >
                  <TextInput v-model="form.application_max_file_size_mb" type="number" min="0.5" :max="maxUploadMb" step="0.5" />
                </SettingsField>
                <SettingsField label="Allowed Upload Formats" :error="errors.application_allowed_formats" hint="File extensions, comma-separated, e.g. PDF, JPG, PNG.">
                  <TextInput v-model="form.application_allowed_formats" type="text" />
                </SettingsField>
              </div>
              <SettingsField label="Application Declaration" hint="Shown on every application form; the candidate must accept it to submit.">
                <FormControl v-model="form.application_declaration" type="textarea" :rows="6" />
              </SettingsField>
              <SettingsField label="General Application Instructions" hint="Post-specific instructions are added on each Position and Job Opening." as="div">
                <TextEditor
                  :content="form.application_instructions"
                  placeholder="Shown on every application form under the Instructions button..."
                  :fixed-menu="true"
                  editor-class="prose-sm max-w-none min-h-[10rem] px-3 py-2"
                  class="rounded border border-gray-300 bg-white"
                  @change="(html) => (form.application_instructions = html)"
                />
              </SettingsField>
            </section>
          </div>
        </template>

        <!-- Roles & Permissions: changes save as they are made, so the tab has no Save button.
             Mounted on first visit and kept while the dialog is open so the selected role survives tab switches. -->
        <div
          v-if="canManageAccess && accessVisited"
          v-show="tab === 'access'"
          class="flex h-[70vh] min-h-[26rem] flex-col overflow-hidden rounded-lg border"
        >
          <RolesPermissionsPanel embedded />
        </div>
      </div>
    </template>
    <template v-if="tab !== 'access'" #actions>
      <Button variant="solid" :class="BTN_BRAND" :loading="saving" :disabled="loading || loadFailed || !isValidHex(form.brand_color)" @click="submit">Save</Button>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Dialog, Button, FeatherIcon, FileUploader, FormControl, ErrorMessage, TextEditor, TextInput } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import {
  COLOR_PRESETS,
  DEFAULT_APPEARANCE,
  FONTS,
  appearance,
  applyAppearance,
  brandScale,
  isValidHex,
  whiteTextContrast,
} from '@/utils/theme'
import { toast } from '@/utils/notify'
import { useSettings } from '@/composables/useSettings'
import { useSessionStore } from '@/stores/session'
import RolesPermissionsPanel from '@/components/settings/RolesPermissionsPanel.vue'
import SettingsField from '@/components/settings/SettingsField.vue'

const isOpen = defineModel({ type: Boolean, default: false })

const { settings, loading, saving, error, fetchSettings, saveSettings } = useSettings()

const form = reactive({})

const session = useSessionStore()
const canEditSettings = computed(() => session.canManageSettings)
const canManageAccess = computed(() => session.canManageAccess)

const tabs = computed(() => [
  ...(canEditSettings.value
    ? [
        { key: 'appearance', label: 'Appearance', icon: 'droplet' },
        { key: 'general', label: 'General', icon: 'settings' },
      ]
    : []),
  ...(canManageAccess.value ? [{ key: 'access', label: 'Roles & Permissions', icon: 'shield' }] : []),
])
const tab = ref('appearance')
const accessVisited = ref(false)
watch(tab, (key) => {
  if (key === 'access') accessVisited.value = true
})
// If a permission change removes the open tab, fall back to one still available.
watch(tabs, (list) => {
  if (list.length && !list.some((t) => t.key === tab.value)) tab.value = list[0].key
})

// ----- appearance: previewed live, reverted if the dialog closes unsaved
const APPEARANCE_KEYS = Object.keys(DEFAULT_APPEARANCE)
const FONT_NAMES = Object.keys(FONTS)
let savedAppearance = null
let saved = false

const shades = computed(() => brandScale(form.brand_color))
const contrast = computed(() => whiteTextContrast(form.brand_color))
const lowContrast = computed(() => contrast.value < 4.5)

function sameColor(a, b) {
  return String(a || '').toLowerCase() === String(b || '').toLowerCase()
}

function currentAppearance() {
  return Object.fromEntries(APPEARANCE_KEYS.map((key) => [key, form[key]]))
}

watch(
  () => APPEARANCE_KEYS.map((key) => form[key]),
  () => {
    if (isOpen.value && savedAppearance && isValidHex(form.brand_color)) applyAppearance(currentAppearance())
  },
)
const formError = ref('')
// Saving after a failed load would write blanks over the real settings.
const loadFailed = ref(false)
const roleOptions = ref([])
const maxUploadMb = ref(10)

const DUTIES = [
  {
    field: 'document_verifier_roles',
    label: 'Document Verifier Roles',
    hint: "May verify or reject candidates' onboarding documents.",
    empty: "No one can verify candidates' onboarding documents while this is empty.",
  },
  {
    field: 'corrigendum_signer_roles',
    label: 'Corrigendum Signer Roles',
    hint: 'May create and sign a Corrigendum.',
    empty: 'No one can issue a Corrigendum while this is empty.',
  },
]

// ----- general: checked here for instant feedback; the server checks again.
const showErrors = ref(false)
const num = (v) => (v === '' || v === null || v === undefined ? NaN : Number(v))
const isWhole = (v) => Number.isInteger(num(v))
const FORMAT = /^[a-z0-9]{1,10}$/
const errors = computed(() => {
  if (!showErrors.value) return {}
  const e = {}
  if (!isWhole(form.acceptance_deadline_days) || num(form.acceptance_deadline_days) < 1 || num(form.acceptance_deadline_days) > 365) {
    e.acceptance_deadline_days = 'Enter a whole number from 1 to 365.'
  }
  if (!isWhole(form.default_shortlisting_ratio) || num(form.default_shortlisting_ratio) < 1) {
    e.default_shortlisting_ratio = 'Enter a whole number, 1 or more.'
  }
  for (const c of ['shortlisting', 'selection']) {
    const min = `min_${c}_committee_size`
    const max = `max_${c}_committee_size`
    if (!isWhole(form[min]) || num(form[min]) < 1) e[min] = 'Enter a whole number, 1 or more.'
    if (!isWhole(form[max]) || num(form[max]) < 1) e[max] = 'Enter a whole number, 1 or more.'
    else if (!e[min] && num(form[max]) < num(form[min])) e[max] = 'Cannot be less than the minimum.'
  }
  const size = num(form.application_max_file_size_mb)
  if (!(size > 0)) e.application_max_file_size_mb = 'Enter a size above 0.'
  else if (size > maxUploadMb.value) e.application_max_file_size_mb = `This site allows up to ${maxUploadMb.value} MB.`
  const formats = String(form.application_allowed_formats || '')
    .split(',')
    .map((f) => f.trim().toLowerCase().replace(/^\./, ''))
    .filter(Boolean)
  if (!formats.length) e.application_allowed_formats = 'List at least one file extension.'
  else if (formats.some((f) => !FORMAT.test(f))) e.application_allowed_formats = 'Use extensions only, e.g. PDF, JPG, PNG.'
  return e
})

const router = useRouter()
function go(path) {
  isOpen.value = false
  router.push(path)
}
const openEmailSetup = () => go('/settings/email')
// frappe-ui's Select drops options whose value is '', so "nobody" needs a
// sentinel that is mapped back to blank on save.
const NONE = '__none__'
const ROLE_FIELDS = ['approval_override_role', 'status_override_role']
const roleSelectOptions = computed(() => [
  { label: '(Disabled)', value: NONE },
  ...roleOptions.value.map((r) => ({ label: r, value: r })),
])

watch(isOpen, async (open) => {
  if (!open) {
    if (!saved && savedAppearance) applyAppearance(savedAppearance)
    savedAppearance = null
    accessVisited.value = false
    return
  }
  saved = false
  savedAppearance = null
  formError.value = ''
  showErrors.value = false
  loadFailed.value = false
  tab.value = tabs.value[0]?.key || 'appearance'
  accessVisited.value = tab.value === 'access'
  if (!canEditSettings.value) return
  await fetchSettings()
  if (!settings.value) {
    loadFailed.value = true
    formError.value = error.value?.messages?.[0] || 'Could not load settings. Close this and try again.'
    return
  }
  const { role_options, max_upload_mb, ...values } = settings.value
  roleOptions.value = role_options || []
  maxUploadMb.value = Number(max_upload_mb) || 10
  Object.assign(form, values)
  for (const key of APPEARANCE_KEYS) form[key] = values[key] || DEFAULT_APPEARANCE[key]
  if (form.app_logo === DEFAULT_APPEARANCE.app_logo) form.app_logo = ''
  savedAppearance = { ...appearance }
  for (const field of ROLE_FIELDS) form[field] = values[field] || NONE
  form.document_verifier_roles = [...(values.document_verifier_roles || [])]
  form.corrigendum_signer_roles = [...(values.corrigendum_signer_roles || [])]
})

const NUMBER_FIELDS = [
  'acceptance_deadline_days',
  'default_shortlisting_ratio',
  'min_shortlisting_committee_size',
  'max_shortlisting_committee_size',
  'min_selection_committee_size',
  'max_selection_committee_size',
  'application_max_file_size_mb',
]

async function submit() {
  if (loadFailed.value || saving.value) return
  formError.value = ''
  showErrors.value = true
  if (Object.keys(errors.value).length) {
    tab.value = 'general'
    formError.value = 'Some General settings need fixing before saving.'
    return
  }
  const payload = { ...form }
  for (const field of ROLE_FIELDS) if (payload[field] === NONE) payload[field] = ''
  for (const field of NUMBER_FIELDS) payload[field] = num(payload[field])
  const ok = await saveSettings(payload)
  if (ok) {
    saved = true
    applyAppearance(currentAppearance())
    toast({ title: 'Settings saved.', icon: 'check', iconClasses: 'text-green-500' })
    isOpen.value = false
  } else {
    formError.value = error.value?.messages?.[0] || 'Could not save settings.'
  }
}
</script>
