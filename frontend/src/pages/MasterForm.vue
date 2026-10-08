<template>
  <StaffLayout>
    <PageHeader :title="pageTitle" :subtitle="pageSubtitle" :back-to="backPath">
      <template v-if="form && doc && !isNew && statusLabel" #meta>
        <span
          class="mt-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-medium"
          :class="isActive ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'"
        >
          <span class="h-1.5 w-1.5 rounded-full" :class="isActive ? 'bg-brand-600' : 'bg-gray-400'" />
          {{ statusLabel }}
        </span>
      </template>
      <template v-if="form && doc" #actions>
        <Button v-if="!isNew && form.can_delete" variant="ghost" theme="red" icon-left="trash-2" @click="openDelete">Delete</Button>
        <Button
          v-if="canEdit"
          variant="solid"
          :class="BTN_BRAND"
          :loading="saving"
          :disabled="!isNew && !dirty"
          @click="save"
        >
          {{ isNew ? `Create ${form.singular}` : 'Save' }}
        </Button>
      </template>
    </PageHeader>

    <div ref="scroller" class="min-h-0 flex-1 overflow-y-auto bg-gray-50/60">
      <div v-if="loading" class="mx-auto flex max-w-5xl flex-col gap-5 p-4 md:p-6">
        <div v-for="i in 2" :key="i" class="h-56 animate-pulse rounded-xl border bg-white" />
      </div>

      <div v-else-if="loadError" class="p-6">
        <EmptyState :title="loadError.title" :description="loadError.message">
          <template #action>
            <div class="flex gap-2">
              <Button v-if="loadError.retry" @click="load">Try again</Button>
              <Button variant="solid" :class="BTN_BRAND" @click="router.push(backPath)">Back to list</Button>
            </div>
          </template>
        </EmptyState>
      </div>

      <form v-else-if="form && doc" class="mx-auto flex max-w-5xl flex-col gap-5 p-4 md:p-6" novalidate @submit.prevent="save">
        <div v-if="saveError" class="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3" role="alert">
          <FeatherIcon name="alert-octagon" class="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-red-800">Not saved</p>
            <p class="mt-0.5 text-p-sm text-red-700">{{ saveError }}</p>
          </div>
          <Button v-if="saveErrorType === 'TimestampMismatchError'" size="sm" @click="reloadDiscarding">Reload latest</Button>
        </div>

        <div v-else-if="errorCount" class="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" role="alert">
          <FeatherIcon name="alert-triangle" class="h-4 w-4 shrink-0 text-amber-600" />
          {{ errorCount === 1 ? '1 field needs' : `${errorCount} fields need` }} attention before saving.
        </div>

        <div v-if="!canEdit" class="flex items-center gap-3 rounded-xl border bg-white px-4 py-3 text-sm text-gray-600">
          <FeatherIcon name="lock" class="h-4 w-4 shrink-0 text-gray-400" />
          You can view this {{ form.singular.toLowerCase() }} but not change it.
        </div>

        <section v-for="s in visibleSections" :key="s.key" class="rounded-xl border bg-white shadow-sm">
          <header v-if="s.label" class="border-b px-5 py-3.5">
            <h2 class="text-base font-semibold text-gray-900">{{ s.label }}</h2>
          </header>
          <div class="grid grid-cols-1 gap-x-8 gap-y-5 p-5" :class="COLUMN_CLASSES[Math.min(s.columns.length, 4)]">
            <div
              v-for="(column, ci) in s.columns"
              :key="ci"
              class="flex min-w-0 flex-col gap-5"
              :class="s.columns.length === 1 && !hasWideField(column) && 'max-w-2xl'"
            >
              <template v-for="f in column" :key="f.fieldname">
                <template v-if="isVisible(f, doc)">
                  <ChildTable
                    v-if="f.fieldtype === 'Table'"
                    :field="f"
                    :child-fields="form.child_tables[f.options]?.fields || []"
                    :rows="doc[f.fieldname] || []"
                    :parent-doc="doc"
                    :required="isRequired(f, doc)"
                    :read-only="!canEdit || isReadOnly(f, doc)"
                    :error="errors[f.fieldname] || ''"
                    :errors="errors"
                    @add-row="addRow(f)"
                    @remove-row="(i) => removeRow(f, i)"
                    @move-row="(i, d) => moveRow(f, i, d)"
                    @set-row-value="(i, k, v) => (doc[f.fieldname][i][k] = v)"
                  />
                  <MasterField
                    v-else
                    :field="f"
                    :path="f.fieldname"
                    :model-value="doc[f.fieldname]"
                    :required="isRequired(f, doc)"
                    :read-only="!canEdit || isReadOnly(f, doc) || isLockedName(f)"
                    :note="isLockedName(f) ? 'This is the record ID, so it can’t be changed after saving.' : ''"
                    :error="errors[f.fieldname] || ''"
                    @update:model-value="(v) => setValue(f, v)"
                  />
                </template>
              </template>
            </div>
          </div>
        </section>

        <!-- Keeps Save in reach on long forms such as Position. -->
        <div
          v-if="canEdit && (dirty || isNew)"
          class="sticky bottom-0 z-10 -mx-4 flex items-center justify-between gap-3 border-t bg-white/95 px-4 py-3 backdrop-blur md:-mx-6 md:px-6"
        >
          <span class="text-sm text-gray-600">{{ isNew ? `New ${form.singular.toLowerCase()} — not saved yet` : 'You have unsaved changes' }}</span>
          <div class="flex gap-2">
            <Button @click="discard">{{ isNew ? 'Cancel' : 'Discard' }}</Button>
            <Button type="submit" variant="solid" :class="BTN_BRAND" :loading="saving" :disabled="!isNew && !dirty">
              {{ isNew ? `Create ${form.singular}` : 'Save' }}
            </Button>
          </div>
        </div>
      </form>
    </div>

    <Dialog v-model="confirmDelete" :options="{ title: `Delete ${form?.singular || 'record'}?`, size: 'sm' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <ErrorMessage :message="deleteError" />
          <p class="text-p-base text-gray-700">
            <strong>{{ pageTitle }}</strong> will be deleted permanently. A record still used by recruitment records can’t be
            deleted; deactivate it instead.
          </p>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button @click="confirmDelete = false">Cancel</Button>
          <Button variant="solid" :class="BTN_DANGER" :loading="deleting" @click="remove">Delete</Button>
        </div>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRouter } from 'vue-router'
import { Button, Dialog, ErrorMessage, FeatherIcon } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import MasterField from '@/components/master/MasterField.vue'
import ChildTable from '@/components/master/ChildTable.vue'
import { masterSetupService } from '@/services/masterSetup'
import { toast } from '@/utils/notify'
import { BTN_BRAND, BTN_DANGER } from '@/utils/buttonStyles'
import {
  TEXT_TYPES,
  buildSections,
  clearLinkCache,
  editRoute,
  errorText,
  isEmpty,
  isReadOnly,
  isRequired,
  isVisible,
  listRoute,
  newRecord,
  newRow,
  resolveMaster,
  toPayload,
  validateRecord,
  withRowKeys,
} from '@/utils/masterForm'

const props = defineProps({
  slug: { type: String, required: true },
  mode: { type: String, default: 'new' },
  name: { type: String, default: '' },
})

const router = useRouter()

const COLUMN_CLASSES = { 1: '', 2: 'md:grid-cols-2', 3: 'md:grid-cols-2 xl:grid-cols-3', 4: 'md:grid-cols-2 xl:grid-cols-4' }

const form = ref(null)
const doc = ref(null)
const loading = ref(true)
const loadError = ref(null)
const snapshot = ref('')
// Declared up here because load() (run immediately below) resets them.
const showErrors = ref(false)
const saving = ref(false)
const saveError = ref('')
const saveErrorType = ref('')

const isNew = computed(() => props.mode !== 'edit')
const backPath = computed(() => router.resolve(listRoute(form.value?.doctype || props.slug)).fullPath)

const pageTitle = computed(() => {
  if (!form.value) return 'Master Setup'
  if (isNew.value) return `New ${form.value.singular}`
  return (form.value.title_field && doc.value?.[form.value.title_field]) || props.name
})
const pageSubtitle = computed(() => {
  if (!form.value) return ''
  if (isNew.value) return form.value.description
  return pageTitle.value !== props.name ? `${form.value.singular} · ${props.name}` : form.value.singular
})

const canEdit = computed(() => Boolean(form.value && (isNew.value ? form.value.can_create : form.value.can_write)))

const isActive = computed(() => {
  const f = form.value?.active_field
  return f ? Number(doc.value?.[f] || 0) === form.value.active_value : null
})
const statusLabel = computed(() => (isActive.value === null ? '' : isActive.value ? 'Active' : 'Inactive'))

// The naming field is the record's ID: editing it later would not rename
// the record, so it is locked once saved.
const isLockedName = (f) => !isNew.value && f.fieldname === form.value?.name_field
const hasWideField = (column) => column.some((f) => f.fieldtype === 'Table' || f.fieldtype === 'Text Editor' || TEXT_TYPES.includes(f.fieldtype))

const sections = computed(() => (form.value ? buildSections(form.value.fields) : []))
const visibleSections = computed(() => sections.value.filter((s) => isVisible(s, doc.value)))

const serialized = computed(() => (form.value && doc.value ? JSON.stringify(toPayload(form.value, doc.value)) : ''))
const dirty = computed(() => Boolean(serialized.value) && serialized.value !== snapshot.value)
const markClean = () => (snapshot.value = serialized.value)

// --- Loading ---------------------------------------------------------------

let loadRequest = 0
async function load() {
  const request = ++loadRequest
  loading.value = true
  loadError.value = null
  saveError.value = ''
  saveErrorType.value = ''
  showErrors.value = false
  try {
    if (!isNew.value && !props.name) {
      if (request === loadRequest) loadError.value = { title: 'Record not found', message: 'No record was given in the link.' }
      return
    }
    const master = await resolveMaster(props.slug)
    if (!master) {
      if (request === loadRequest) loadError.value = { title: 'Master not found', message: 'This master does not exist, or you cannot manage it.' }
      return
    }
    const meta = await masterSetupService.getForm(master.doctype)
    const record = !isNew.value ? await masterSetupService.getDoc(master.doctype, props.name) : newRecord(meta.fields)
    if (request !== loadRequest) return
    form.value = meta
    doc.value = withRowKeys(meta, record)
    await nextTick()
    markClean()
  } catch (e) {
    if (request !== loadRequest) return
    if (e?.exc_type === 'DoesNotExistError' || e?.status === 404) {
      loadError.value = { title: 'Record not found', message: 'It may have been deleted or renamed.' }
    } else if (e?.exc_type === 'PermissionError' || e?.status === 403) {
      loadError.value = { title: 'No access', message: errorText(e, 'You do not have permission to open this record.') }
    } else {
      loadError.value = { title: 'Could not load', message: errorText(e), retry: true }
    }
  } finally {
    if (request === loadRequest) loading.value = false
  }
}
watch(() => [props.slug, props.mode, props.name], load, { immediate: true })

// --- Editing ---------------------------------------------------------------

// fetch_from: picking a Designation fills Employment Type and Pay Level,
// as on the desk. Only the latest pick per field is applied.
const fetchRequests = {}
function setValue(f, value) {
  doc.value[f.fieldname] = value
  if (f.fieldtype !== 'Link') return
  const targets = form.value.fields.filter((t) => t.fetch_from && t.fetch_from.split('.')[0] === f.fieldname)
  for (const t of targets) {
    if (t.fetch_if_empty && !isEmpty(t, doc.value[t.fieldname])) continue
    const source = t.fetch_from.split('.')[1]
    const request = (fetchRequests[t.fieldname] = (fetchRequests[t.fieldname] || 0) + 1)
    if (!value) {
      doc.value[t.fieldname] = null
      continue
    }
    masterSetupService
      .getValue(f.options, value, source)
      .then((r) => {
        if (request === fetchRequests[t.fieldname] && doc.value) doc.value[t.fieldname] = r?.[source] ?? null
      })
      .catch(() => {
        // Leave the field for the user to fill in.
      })
  }
}

// Rows with a sequence number (approval steps) follow their on-screen
// order, since the server sorts them by it.
function renumber(f) {
  const fields = form.value.child_tables[f.options]?.fields || []
  if (!fields.some((cf) => cf.fieldname === 'sequence' && cf.fieldtype === 'Int')) return
  doc.value[f.fieldname].forEach((row, i) => (row.sequence = i + 1))
}
function addRow(f) {
  const rows = (doc.value[f.fieldname] ||= [])
  rows.push(newRow(form.value.child_tables[f.options]?.fields || [], rows.length))
  renumber(f)
}
function removeRow(f, i) {
  doc.value[f.fieldname].splice(i, 1)
  renumber(f)
}
function moveRow(f, i, delta) {
  const rows = doc.value[f.fieldname]
  const j = i + delta
  if (j < 0 || j >= rows.length) return
  ;[rows[i], rows[j]] = [rows[j], rows[i]]
  renumber(f)
}

// --- Validation and saving ------------------------------------------------

// Errors show once a save has been tried, then update as fields are fixed.
const errors = computed(() => (showErrors.value && form.value && doc.value ? validateRecord(form.value, doc.value, sections.value) : {}))
const errorCount = computed(() => Object.keys(errors.value).length)

const scroller = ref(null)
function scrollToFirstError() {
  const first = Object.keys(errors.value)[0]
  const el = first && scroller.value?.querySelector(`[data-field="${CSS.escape(first)}"]`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.querySelector('input, textarea, select, button')?.focus({ preventScroll: true })
  } else {
    scroller.value?.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

async function save() {
  if (saving.value || !canEdit.value || (!isNew.value && !dirty.value)) return
  showErrors.value = true
  saveError.value = ''
  if (errorCount.value) {
    await nextTick()
    scrollToFirstError()
    return
  }
  saving.value = true
  const wasNew = isNew.value
  try {
    const saved = await masterSetupService.save(form.value.doctype, toPayload(form.value, doc.value))
    clearLinkCache()
    showErrors.value = false
    toast({ title: `${form.value.singular} ${wasNew ? 'created' : 'saved'}` })
    if (wasNew) {
      markClean() // lets the route change through the unsaved-changes guard
      await router.replace(editRoute(form.value.doctype, saved.name))
    } else {
      doc.value = withRowKeys(form.value, saved)
      await nextTick()
      markClean()
    }
  } catch (e) {
    saveError.value = errorText(e, 'Could not save. Please try again.')
    saveErrorType.value = e?.exc_type || ''
    scroller.value?.scrollTo({ top: 0, behavior: 'smooth' })
  } finally {
    saving.value = false
  }
}

function discard() {
  if (isNew.value) {
    markClean()
    router.push(backPath.value)
    return
  }
  if (window.confirm('Discard your changes?')) load()
}

function reloadDiscarding() {
  if (window.confirm('Reload the latest version? Your unsaved changes will be lost.')) load()
}

// --- Deleting --------------------------------------------------------------

const confirmDelete = ref(false)
const deleting = ref(false)
const deleteError = ref('')
function openDelete() {
  deleteError.value = ''
  confirmDelete.value = true
}
async function remove() {
  if (deleting.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    await masterSetupService.remove(form.value.doctype, props.name)
    clearLinkCache()
    toast({ title: `${form.value.singular} deleted` })
    confirmDelete.value = false
    markClean()
    await router.replace(backPath.value)
  } catch (e) {
    deleteError.value = errorText(e, 'Could not delete. Please try again.')
  } finally {
    deleting.value = false
  }
}

// --- Unsaved changes ------------------------------------------------------

const confirmLeave = () => !dirty.value || window.confirm('You have unsaved changes. Leave without saving?')
onBeforeRouteLeave(confirmLeave)
onBeforeRouteUpdate(confirmLeave)

function onBeforeUnload(event) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}
function onKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
    event.preventDefault()
    if (!confirmDelete.value) save()
  }
}
onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  window.removeEventListener('keydown', onKeydown)
})
</script>
