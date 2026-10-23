<template>
  <!-- Candidate portal: the appointment order once it has been sent. -->
  <div v-if="offer" class="rounded-xl border bg-white p-5 shadow-sm">
    <div class="mb-3 flex items-center justify-between gap-2">
      <div class="text-xs font-bold uppercase tracking-wide text-brand-700">Appointment order</div>
      <StatusBadge :status="offer.status" />
    </div>
    <dl class="flex flex-col gap-1.5 text-sm">
      <div v-if="offer.designation" class="flex justify-between gap-2"><dt class="text-gray-500">Position</dt><dd class="text-right font-medium">{{ offer.designation }}</dd></div>
      <div v-if="offer.proposed_doj" class="flex justify-between gap-2"><dt class="text-gray-500">Proposed joining</dt><dd>{{ fmt(offer.proposed_doj) }}</dd></div>
      <div v-if="offer.acceptance_deadline && offer.status === 'Sent'" class="flex justify-between gap-2">
        <dt class="text-gray-500">Respond by</dt><dd class="font-medium">{{ fmt(offer.acceptance_deadline) }}</dd>
      </div>
      <div v-if="offer.candidate_confirmed_doj" class="flex justify-between gap-2"><dt class="text-gray-500">Your joining date</dt><dd class="font-medium">{{ fmt(offer.candidate_confirmed_doj) }}</dd></div>
    </dl>

    <div v-if="offer.has_letter" class="mt-4 flex flex-wrap gap-2">
      <Button size="sm" variant="outline" icon-left="eye" @click="previewOpen = true">View letter</Button>
      <Button size="sm" icon-left="download" :loading="busy === 'download'" @click="download">Download PDF</Button>
    </div>

    <div v-if="offer.can_upload_signed_copy" class="mt-4 border-t pt-3 text-sm">
      <div class="text-xs text-gray-500">Signed copy of the letter</div>
      <a v-if="offer.signed_copy_attachment" :href="offer.signed_copy_attachment" target="_blank" class="text-brand-700 hover:underline">
        {{ decodeURIComponent(offer.signed_copy_attachment.split('/').pop()) }}
      </a>
      <FileUploader file-types=".pdf,.jpg,.jpeg,.png" :upload-args="{ private: true }" @success="onUploaded">
        <template #default="{ openFileSelector, uploading }">
          <Button class="mt-2" size="sm" icon-left="upload" :loading="uploading || busy === 'upload'" @click="openFileSelector">
            {{ offer.signed_copy_attachment ? 'Replace signed copy' : 'Upload signed copy' }}
          </Button>
        </template>
      </FileUploader>
      <p class="mt-1 text-xs text-gray-500">Print, sign and scan the letter, then upload it here.</p>
    </div>

    <div v-if="offer.can_respond" class="mt-4 flex flex-col gap-3 border-t pt-3">
      <FormControl label="Your date of joining" type="date" v-model="doj" />
      <div class="flex flex-wrap gap-2">
        <Button variant="solid" :class="BTN_SUCCESS" :loading="busy === 'accept'" @click="accept">Accept offer</Button>
        <Button variant="outline" theme="red" @click="declineOpen = true">Decline</Button>
      </div>
    </div>

    <LetterPreviewDialog v-model="previewOpen" :offer="offer.name" />
    <Dialog v-model="declineOpen" :options="{ title: 'Decline the offer?' }">
      <template #body-content>
        <p class="mb-3 text-sm text-gray-600">This cannot be undone. You may tell us why (optional).</p>
        <FormControl type="textarea" label="Reason" v-model="reason" />
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button @click="declineOpen = false">Cancel</Button>
          <Button variant="solid" :class="BTN_DANGER" :loading="busy === 'decline'" @click="decline">Decline offer</Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { Button, Dialog, FileUploader, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LetterPreviewDialog from '@/components/offers/LetterPreviewDialog.vue'
import { offerService } from '@/services/offers'
import { BTN_DANGER, BTN_SUCCESS } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({ application: { type: String, required: true } })
const emit = defineEmits(['changed'])

const offer = ref(null)
const busy = ref('')
const doj = ref('')
const reason = ref('')
const previewOpen = ref(false)
const declineOpen = ref(false)
const fmt = (d) => (d ? dayjs(d).format('DD MMM YYYY') : '')

async function load() {
  try {
    offer.value = await offerService.getMyOffer(props.application)
    if (offer.value && !doj.value) doj.value = offer.value.proposed_doj || ''
  } catch {
    offer.value = null
  }
}

async function act(key, fn, message) {
  busy.value = key
  try {
    await fn()
    if (message) toast({ title: message, icon: 'check' })
    await load()
    emit('changed')
    return true
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Something went wrong.', icon: 'alert-triangle' })
    return false
  } finally {
    busy.value = ''
  }
}

function accept() {
  if (!doj.value) {
    toast({ title: 'Please choose your date of joining before accepting.', icon: 'alert-triangle' })
    return
  }
  act('accept', () => offerService.respondToOffer(offer.value.name, 'Accepted', doj.value), 'Offer accepted. Congratulations!')
}

async function decline() {
  if (await act('decline', () => offerService.respondToOffer(offer.value.name, 'Declined', null, null, reason.value), 'Offer declined.')) {
    declineOpen.value = false
  }
}

function onUploaded(file) {
  act('upload', () => offerService.uploadSignedCopy(offer.value.name, file.file_url), 'Signed copy uploaded.')
}

async function download() {
  busy.value = 'download'
  try {
    await offerService.downloadLetter(offer.value.name)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not download the letter.', icon: 'alert-triangle' })
  } finally {
    busy.value = ''
  }
}

onMounted(load)
watch(() => props.application, load)
defineExpose({ reload: load })
</script>
