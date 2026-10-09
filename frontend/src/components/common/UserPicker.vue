<template>
  <!-- Search people and add one at a time. Results open inline under the
       input (not in a portal): inside a modal dialog a portal would be clipped
       or unclickable. Already-chosen people are not offered. -->
  <div class="w-full">
    <label
      class="flex h-10 w-full items-center gap-2 rounded-lg border bg-white px-3 transition focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-100"
      :class="disabled ? 'cursor-not-allowed border-gray-200 bg-gray-50 opacity-70' : 'border-gray-300'"
    >
      <FeatherIcon name="search" class="h-4 w-4 shrink-0 text-gray-400" />
      <input
        ref="input"
        v-model="query"
        type="text"
        role="combobox"
        :aria-expanded="open"
        :aria-controls="listId"
        aria-autocomplete="list"
        :aria-label="placeholder"
        :placeholder="placeholder"
        :disabled="disabled"
        autocomplete="off"
        class="min-w-0 flex-1 border-0 bg-transparent p-0 text-sm text-gray-900 placeholder-gray-400 focus:ring-0"
        @focus="show"
        @click="show"
        @blur="hideSoon"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="pick(results[active])"
        @keydown.esc="onEscape"
      />
    </label>

    <div v-if="open" :id="listId" class="mt-1.5 overflow-hidden rounded-xl border bg-white shadow-sm" @mousedown.prevent>
        <ul v-if="results.length" class="max-h-60 overflow-y-auto py-1" role="listbox">
          <li v-for="(u, i) in results" :key="u.name" role="option" :aria-selected="i === active">
            <button
              type="button"
              tabindex="-1"
              class="flex w-full items-center gap-3 px-3 py-2 text-left"
              :class="i === active ? 'bg-brand-50' : 'hover:bg-gray-50'"
              @mouseenter="active = i"
              @click="pick(u)"
            >
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                {{ initials(u) }}
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium text-gray-900">{{ displayName(u) }}</span>
                <span v-if="secondary(u)" class="block truncate text-xs text-gray-500">{{ secondary(u) }}</span>
              </span>
              <FeatherIcon name="plus" class="h-4 w-4 shrink-0 text-gray-400" />
            </button>
          </li>
        </ul>
        <p v-else class="px-4 py-6 text-center text-sm text-gray-500">
          {{ query.trim() ? `No one matches “${query.trim()}”.` : 'Everyone available is already on the panel.' }}
        </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  // [{ name, full_name, email }]
  users: { type: Array, default: () => [] },
  // user names already chosen; they are not offered
  exclude: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Search people by name or email' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['select'])

const open = ref(false)
const query = ref('')
const active = ref(0)
const input = ref(null)

const displayName = (u) => u.full_name || u.name
const secondary = (u) => {
  const email = u.email || u.name
  return email !== displayName(u) ? email : ''
}
function initials(u) {
  const words = displayName(u).replace(/@.*/, '').split(/[\s._-]+/).filter(Boolean)
  return words.slice(0, 2).map((w) => w[0].toUpperCase()).join('') || '?'
}

const results = computed(() => {
  const taken = new Set(props.exclude)
  const q = query.value.trim().toLowerCase()
  return props.users
    .filter((u) => !taken.has(u.name))
    .filter((u) => !q || [u.full_name, u.email, u.name].some((v) => String(v || '').toLowerCase().includes(q)))
    .slice(0, 50)
})
watch(results, () => (active.value = 0))
watch(
  () => props.disabled,
  (d) => d && (open.value = false),
)

const listId = `user-picker-${Math.random().toString(36).slice(2, 8)}`

function show() {
  if (!props.disabled) open.value = true
}
let blurTimer = null
function hideSoon() {
  clearTimeout(blurTimer)
  blurTimer = setTimeout(() => (open.value = false), 120)
}
onBeforeUnmount(() => clearTimeout(blurTimer))

// Escape closes the list first; with the list closed it reaches the dialog.
function onEscape(event) {
  if (!open.value) return
  event.stopPropagation()
  open.value = false
}

function move(step) {
  if (!open.value) return show()
  const n = results.value.length
  if (n) active.value = (active.value + step + n) % n
}

function pick(u) {
  if (!u || props.disabled) return
  emit('select', u)
  query.value = ''
  // Stay open for adding the next person.
  input.value?.focus()
}
</script>
