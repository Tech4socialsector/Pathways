<template>
  <!-- An email exactly as it will be sent (pathways.utils.communication.preview_event). -->
  <Dialog v-model="open" :options="{ title: 'Email preview', size: '3xl' }">
    <template #body-content>
      <div v-if="loading && !preview" class="h-72 animate-pulse rounded-lg bg-gray-100" />
      <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>
      <div v-else-if="preview" class="flex flex-col gap-3 text-sm">
        <p v-if="!preview.enabled" class="rounded-md bg-orange-50 px-3 py-2 text-orange-800">
          This email (“{{ preview.label }}”) is switched off in Email Setup, so it will not be sent.
        </p>
        <dl class="grid grid-cols-[6rem_minmax(0,1fr)] gap-x-3 gap-y-1.5 rounded-lg border bg-gray-50 px-4 py-3">
          <dt class="text-gray-500">To</dt>
          <dd class="text-gray-900">
            <template v-if="preview.recipients.length">
              <span v-for="(r, i) in preview.recipients" :key="r.email">{{ i ? ', ' : '' }}{{ r.name ? `${r.name} <${r.email}>` : r.email }}</span>
            </template>
            <span v-else class="text-red-700">Nobody: check the recipients in Email Setup.</span>
          </dd>
          <template v-if="preview.cc?.length">
            <dt class="text-gray-500">CC</dt>
            <dd class="text-gray-900">{{ preview.cc.join(', ') }}</dd>
          </template>
          <template v-if="preview.reply_to">
            <dt class="text-gray-500">Reply-to</dt>
            <dd class="text-gray-900">{{ preview.reply_to }}</dd>
          </template>
          <dt class="text-gray-500">Subject</dt>
          <dd class="font-semibold text-gray-900">{{ preview.subject }}</dd>
          <dt class="text-gray-500">Attachments</dt>
          <dd class="flex flex-wrap gap-1.5">
            <span v-for="a in preview.attachments" :key="a" class="inline-flex items-center gap-1 rounded border bg-white px-2 py-0.5 text-xs text-gray-700">
              <FeatherIcon name="paperclip" class="h-3 w-3" />{{ a }}
            </span>
            <span v-if="!preview.attachments.length" class="text-gray-500">None</span>
          </dd>
        </dl>
        <!-- Sandboxed: the email's own styles stay inside, and nothing in it runs. -->
        <iframe :srcdoc="frameDoc" sandbox="" title="Email body" class="h-[28rem] w-full rounded-lg border bg-white" />
        <p class="text-xs text-gray-500">
          Template: {{ preview.email_template }}. The wording is edited in Email Setup; this shows it filled in for this candidate.
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <slot name="actions" />
        <Button @click="open = false">Close</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  preview: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])
const open = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

const frameDoc = computed(
  () =>
    '<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;line-height:1.5;margin:16px}a{color:#8a1538}</style></head><body>' +
    (props.preview?.body || '') +
    '</body></html>',
)
</script>
