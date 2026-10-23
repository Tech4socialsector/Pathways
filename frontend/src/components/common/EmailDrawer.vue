<template>
  <!-- One logged email as it was sent, in a panel on the right. -->
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-40 flex justify-end" @keydown.esc="close">
        <div class="absolute inset-0 bg-black/30" aria-hidden="true" @click="close" />
        <aside
          class="relative flex h-full w-full max-w-2xl flex-col bg-white shadow-xl"
          role="dialog"
          aria-modal="true"
          aria-label="Email details"
        >
          <header class="flex items-start justify-between gap-3 border-b px-5 py-4">
            <div class="min-w-0">
              <div class="text-xs font-bold uppercase tracking-wide text-brand-700">{{ item?.event_label || 'Email' }}</div>
              <h2 class="mt-0.5 break-words text-lg font-bold text-gray-900">{{ subject }}</h2>
            </div>
            <Button variant="ghost" icon="x" aria-label="Close" @click="close" />
          </header>
          <div v-if="loading" class="p-5 text-sm text-gray-500">Loading...</div>
          <div v-else-if="error" class="p-5 text-sm text-red-600">{{ error }}</div>
          <div v-else-if="item" class="flex min-h-0 flex-1 flex-col">
            <dl class="grid grid-cols-[7rem_1fr] gap-x-3 gap-y-1.5 border-b px-5 py-3 text-sm">
              <dt class="text-gray-500">To</dt>
              <dd class="break-all text-gray-900">{{ item.recipient }}</dd>
              <dt class="text-gray-500">Sent</dt>
              <dd class="flex items-center gap-2 text-gray-900">{{ formatDateTime(item.sent_on) }} <StatusBadge :status="item.status" /></dd>
              <template v-if="item.job_opening">
                <dt class="text-gray-500">Job</dt>
                <dd><RouterLink :to="`/jobs/${item.job_opening}`" class="text-brand-700 hover:underline" @click="close">{{ item.job_title || item.job_opening }}</RouterLink></dd>
              </template>
              <template v-if="item.application">
                <dt class="text-gray-500">Application</dt>
                <dd>
                  <RouterLink :to="`/applications/${item.application}`" class="text-brand-700 hover:underline" @click="close">
                    {{ item.candidate_name || item.application_id || item.application }}
                  </RouterLink>
                </dd>
              </template>
              <dt class="text-gray-500">Record</dt>
              <dd class="text-gray-700">{{ item.reference_doctype }} {{ item.reference_name }}</dd>
              <dt class="text-gray-500">Template</dt>
              <dd class="text-gray-700">{{ item.email_template }}</dd>
            </dl>
            <div class="min-h-0 flex-1 overflow-y-auto px-5 py-4">
              <p v-if="item.email?.error && item.status === 'Failed'" class="mb-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">{{ item.email.error }}</p>
              <iframe
                v-if="html"
                :srcdoc="html"
                sandbox=""
                title="Email body"
                class="h-[60vh] w-full rounded-lg border bg-white"
              />
              <pre v-else-if="item.email?.text" class="whitespace-pre-wrap text-sm text-gray-800">{{ item.email.text }}</pre>
              <template v-else-if="item.template">
                <p class="mb-2 rounded-md bg-orange-50 px-3 py-2 text-xs text-orange-800">
                  The sent copy is no longer kept by the mail queue. This is the template as it reads now, without the details filled in.
                </p>
                <iframe :srcdoc="item.template.html" sandbox="" title="Email template" class="h-[55vh] w-full rounded-lg border bg-white" />
              </template>
              <p v-else class="text-sm text-gray-500">The email body is not available.</p>
            </div>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button } from 'frappe-ui'
import dayjs from 'dayjs'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { communicationService } from '@/services/communications'

const props = defineProps({
  open: { type: Boolean, default: false },
  name: { type: String, default: '' },
})
const emit = defineEmits(['update:open'])

const item = ref(null)
const loading = ref(false)
const error = ref('')

watch(
  () => [props.open, props.name],
  async ([open, name]) => {
    if (!open || !name) return
    loading.value = true
    error.value = ''
    item.value = null
    try {
      item.value = await communicationService.get(name)
    } catch (e) {
      error.value = e?.messages?.[0] || 'Could not load this email.'
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const subject = computed(() => item.value?.email?.subject || item.value?.template?.subject || item.value?.email_template || 'Email')
const html = computed(() => item.value?.email?.html || '')

function close() {
  emit('update:open', false)
}
function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A') : ''
}
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.15s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
</style>
