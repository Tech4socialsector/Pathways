<template>
  <div class="flex items-center gap-1">
    <div class="min-w-0 flex-1">
      <Autocomplete
        :placeholder="placeholder"
        :options="options"
        :model-value="modelValue || ''"
        :loading="loading"
        :disabled="disabled"
        @update:query="onQuery"
        @update:model-value="(opt) => emit('update:modelValue', opt?.value ?? null)"
      >
        <template v-if="createTarget" #footer="{ togglePopover }">
          <button
            type="button"
            class="flex w-full items-center gap-2 rounded px-2.5 py-1.5 text-left text-base font-medium text-brand-700 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
            @click.stop="createNew(togglePopover)"
          >
            <FeatherIcon name="plus" class="h-4 w-4 shrink-0" />
            <span class="truncate">Create new {{ createTarget.singular }}</span>
            <FeatherIcon name="external-link" class="ml-auto h-3.5 w-3.5 shrink-0 text-gray-400" />
          </button>
        </template>
      </Autocomplete>
    </div>
    <Button
      v-if="modelValue && !disabled"
      variant="ghost"
      icon="x"
      :aria-label="`Clear ${label}`"
      :title="`Clear ${label}`"
      @click="emit('update:modelValue', null)"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Autocomplete, Button, FeatherIcon } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'
import { clearLinkCache, newRoute, resolveMaster, searchLink as search, slugOf } from '@/utils/masterForm'

const props = defineProps({
  doctype: { type: String, required: true },
  modelValue: { type: String, default: null },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const placeholder = computed(() => `Select ${props.label || props.doctype}`)

const results = ref([])
const loading = ref(false)
let request = 0
let timer = null

async function load(txt) {
  const mine = ++request
  loading.value = true
  try {
    const rows = (await search(props.doctype, txt)) || []
    if (mine === request) results.value = rows
  } catch {
    if (mine === request) results.value = []
  } finally {
    if (mine === request) loading.value = false
  }
}

function onQuery(txt) {
  clearTimeout(timer)
  timer = setTimeout(() => load((txt || '').trim()), 250)
}

// "Create new" at the end of the dropdown, for System Managers, when the
// linked DocType is itself a master they can create. It opens the full form
// in a new tab so this form's unsaved changes stay put; coming back to this
// tab refreshes the options, so the new record can be picked straight away.
const router = useRouter()
const session = useSessionStore()
const target = ref(null)
const createTarget = computed(() => (session.hasRole('System Manager') && target.value?.can_create ? target.value : null))
let awaitingCreate = false

function createNew(togglePopover) {
  togglePopover()
  awaitingCreate = true
  window.open(router.resolve(newRoute(props.doctype)).href, '_blank', 'noopener')
}

function onReturn() {
  if (!awaitingCreate || document.visibilityState !== 'visible') return
  awaitingCreate = false
  clearLinkCache()
  load('')
}

onMounted(() => {
  load('')
  resolveMaster(slugOf(props.doctype))
    .then((m) => (target.value = m))
    .catch(() => {
      // No "Create new" without the registry; picking still works.
    })
  window.addEventListener('focus', onReturn)
  document.addEventListener('visibilitychange', onReturn)
})
onBeforeUnmount(() => {
  clearTimeout(timer)
  window.removeEventListener('focus', onReturn)
  document.removeEventListener('visibilitychange', onReturn)
})

// The dropdown filters on label and value only, so the server's description
// (e.g. a user's full name) goes into the label to stay searchable. The
// current value is always listed, so it shows even if it isn't in the results.
const options = computed(() => {
  const opts = results.value.map((r) => {
    const main = r.label && r.label !== r.value ? `${r.label} (${r.value})` : r.value
    return { value: r.value, label: r.description ? `${main} · ${r.description}` : main }
  })
  if (props.modelValue && !opts.some((o) => o.value === props.modelValue)) {
    opts.unshift({ value: props.modelValue, label: props.modelValue })
  }
  return opts
})
</script>
