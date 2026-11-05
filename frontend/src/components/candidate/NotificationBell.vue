<template>
  <!-- Candidate portal: the notification bell. Every email Pathways sends
       the candidate is listed here too (newest first). -->
  <div ref="root" class="relative">
    <button
      type="button"
      class="relative flex h-9 w-9 items-center justify-center rounded-full text-gray-600 transition hover:bg-gray-100 hover:text-gray-900"
      :class="open && 'bg-gray-100 text-gray-900'"
      :aria-label="unread ? `Notifications, ${unread} unread` : 'Notifications'"
      :aria-expanded="open"
      aria-haspopup="dialog"
      @click="toggle"
    >
      <FeatherIcon name="bell" class="h-5 w-5" />
      <span
        v-if="unread"
        class="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-brand-700 px-1 text-[10px] font-bold leading-none text-white ring-2 ring-white"
        aria-hidden="true"
      >
        {{ unread > 9 ? '9+' : unread }}
      </span>
    </button>

    <div
      v-if="open"
      class="fixed inset-x-3 top-16 z-50 overflow-hidden rounded-xl border bg-white shadow-xl sm:absolute sm:inset-x-auto sm:right-0 sm:top-11 sm:w-96"
      role="dialog"
      aria-label="Notifications"
    >
      <div class="flex items-center justify-between border-b px-4 py-3">
        <span class="text-sm font-semibold text-gray-900">Notifications</span>
        <button
          v-if="unread"
          type="button"
          class="text-xs font-medium text-brand-700 hover:underline disabled:opacity-50"
          :disabled="marking"
          @click="markAll"
        >
          Mark all as read
        </button>
      </div>

      <div class="max-h-[70vh] overflow-y-auto sm:max-h-96">
        <div v-if="loading && !items.length" class="flex flex-col gap-3 p-4">
          <div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded bg-gray-100" />
        </div>
        <div v-else-if="error" class="p-6 text-center text-sm text-gray-600">
          <p>{{ error }}</p>
          <button type="button" class="mt-2 font-medium text-brand-700 hover:underline" @click="load">Try again</button>
        </div>
        <div v-else-if="!items.length" class="flex flex-col items-center px-6 py-10 text-center">
          <span class="flex h-11 w-11 items-center justify-center rounded-full bg-gray-100 text-gray-500">
            <FeatherIcon name="bell-off" class="h-5 w-5" />
          </span>
          <p class="mt-3 text-sm font-medium text-gray-900">No notifications yet</p>
          <p class="mt-1 text-xs text-gray-500">Interview invites and other updates about your applications appear here.</p>
        </div>
        <ul v-else class="divide-y">
          <li v-for="n in items" :key="n.name">
            <button
              type="button"
              class="flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-gray-50"
              :class="!n.read && 'bg-brand-50/50'"
              @click="openItem(n)"
            >
              <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :class="n.read ? 'bg-transparent' : 'bg-brand-700'" :aria-label="n.read ? undefined : 'Unread'" />
              <span class="min-w-0 flex-1">
                <span class="line-clamp-2 text-sm" :class="n.read ? 'text-gray-700' : 'font-medium text-gray-900'">{{ n.subject }}</span>
                <span class="mt-0.5 block text-xs text-gray-500" :title="dayjs(n.creation).format('DD MMM YYYY, h:mm A')">{{ ago(n.creation) }}</span>
              </span>
              <FeatherIcon name="chevron-right" class="mt-1 h-4 w-4 shrink-0 text-gray-300" />
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { callMethod } from '@/services/api'

const M = 'pathways.utils.candidate_notifications.'
// The router serves the portal under /pathways.
const BASE = '/pathways'
// Unread count refresh while the tab is visible.
const POLL_MS = 60_000

const router = useRouter()
const route = useRoute()
const root = ref(null)
const open = ref(false)
const items = ref([])
const unread = ref(0)
const loading = ref(false)
const marking = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const r = await callMethod(M + 'get_my_notifications', { limit: 20 })
    items.value = r?.notifications || []
    unread.value = r?.unread || 0
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load notifications.'
  } finally {
    loading.value = false
  }
}

function toggle() {
  open.value = !open.value
  if (open.value) load()
}

async function markRead(names) {
  marking.value = true
  try {
    const r = await callMethod(M + 'mark_my_notifications_read', names ? { names: JSON.stringify(names) } : {})
    unread.value = r?.unread ?? unread.value
    items.value = items.value.map((n) => (!names || names.includes(n.name) ? { ...n, read: 1 } : n))
  } catch {
    // stays unread; the next load shows the true state
  } finally {
    marking.value = false
  }
}
const markAll = () => markRead(null)

async function openItem(n) {
  open.value = false
  if (!n.read) markRead([n.name])
  const link = n.link || '/pathways/portal/applications'
  const path = link.startsWith(BASE) ? link.slice(BASE.length) || '/' : link
  if (router.resolve(path).fullPath !== route.fullPath) router.push(path)
}

// "5 min ago", "Yesterday", "3 Nov".
function ago(value) {
  const t = dayjs(value)
  const mins = dayjs().diff(t, 'minute')
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`
  if (hours < 48) return 'Yesterday'
  return t.format(t.year() === dayjs().year() ? 'D MMM' : 'D MMM YYYY')
}

// Close on a click elsewhere, Escape, or moving to another page.
function onDocClick(e) {
  if (open.value && root.value && !root.value.contains(e.target)) open.value = false
}
function onKey(e) {
  if (e.key === 'Escape') open.value = false
}
watch(() => route.fullPath, () => (open.value = false))

let timer = null
function poll() {
  if (document.visibilityState === 'visible' && !open.value) load()
}
onMounted(() => {
  load()
  timer = setInterval(poll, POLL_MS)
  document.addEventListener('visibilitychange', poll)
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', poll)
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})
</script>
