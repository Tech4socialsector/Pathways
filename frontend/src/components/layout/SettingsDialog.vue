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
          <div v-show="tab === 'general'" class="flex flex-col gap-4">
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
            <div>
              <span class="mb-1.5 block text-sm text-gray-700">General Application Instructions</span>
              <TextEditor
                :content="form.application_instructions"
                placeholder="Shown on every application form under the Instructions button..."
                :fixed-menu="true"
                editor-class="prose-sm max-w-none min-h-[10rem] px-3 py-2"
                class="rounded border border-gray-300 bg-white"
                @change="(html) => (form.application_instructions = html)"
              />
              <p class="mt-1 text-xs text-gray-500">Post-specific instructions are added on each Position and Job Opening.</p>
            </div>
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
      <Button variant="solid" :class="BTN_BRAND" :loading="saving" :disabled="!isValidHex(form.brand_color)" @click="submit">Save</Button>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Dialog, Button, FeatherIcon, FileUploader, FormControl, ErrorMessage, TextEditor } from 'frappe-ui'
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
  if (!open) {
    if (!saved && savedAppearance) applyAppearance(savedAppearance)
    savedAppearance = null
    accessVisited.value = false
    return
  }
  saved = false
  savedAppearance = null
  formError.value = ''
  tab.value = tabs.value[0]?.key || 'appearance'
  accessVisited.value = tab.value === 'access'
  if (!canEditSettings.value) return
  await fetchSettings()
  const { role_options, ...values } = settings.value || {}
  roleOptions.value = role_options || []
  Object.assign(form, values)
  for (const key of APPEARANCE_KEYS) form[key] = values[key] || DEFAULT_APPEARANCE[key]
  if (form.app_logo === DEFAULT_APPEARANCE.app_logo) form.app_logo = ''
  savedAppearance = { ...appearance }
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
    saved = true
    applyAppearance(currentAppearance())
    toast({ title: 'Settings saved.', icon: 'check', iconClasses: 'text-green-500' })
    isOpen.value = false
  } else {
    formError.value = error.value?.messages?.[0] || 'Could not save settings.'
  }
}
</script>
