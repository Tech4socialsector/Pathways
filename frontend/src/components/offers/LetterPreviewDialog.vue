<template>
  <Dialog v-model="open" :options="{ title: 'Appointment Order', size: '4xl' }">
    <template #body-content>
      <div v-if="loading" class="py-10 text-center text-sm text-gray-500">Preparing the letter...</div>
      <ErrorMessage v-else-if="error" :message="error" />
      <!-- Rendered server-side from the template; sandboxed, no scripts. -->
      <iframe v-else :srcdoc="html" sandbox="" title="Appointment order preview" class="h-[70vh] w-full rounded border border-gray-200 bg-white" />
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button @click="open = false">Close</Button>
        <Button variant="solid" icon-left="download" :class="BTN_BRAND" :loading="downloading" @click="download">Download PDF</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage } from 'frappe-ui'
import { offerService } from '@/services/offers'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  offer: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])
const open = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

const html = ref('')
const loading = ref(false)
const error = ref('')
const downloading = ref(false)

watch(open, async (isOpen) => {
  if (!isOpen) return
  loading.value = true
  error.value = ''
  try {
    html.value = await offerService.previewLetter(props.offer)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not prepare the letter.'
  } finally {
    loading.value = false
  }
})

async function download() {
  downloading.value = true
  try {
    await offerService.downloadLetter(props.offer)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the letter.', icon: 'alert-triangle' })
  } finally {
    downloading.value = false
  }
}
</script>
