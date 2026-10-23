<template>
  <!-- After the interviews: regrets (workflow step 32) and panel thanks (step 33) -->
  <section class="rounded-xl border bg-white shadow-sm" aria-label="Regrets and panel thanks">
    <div v-if="loading && !summary" class="h-40 animate-pulse" />
    <div v-else-if="!summary" class="p-5 text-sm text-gray-500">Could not load the regrets and thanks for this job.</div>
    <div v-else class="grid gap-0 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
      <div class="flex flex-col gap-2 p-5">
        <div class="flex items-center gap-2 text-sm font-semibold text-gray-900"><FeatherIcon name="mail" class="h-4 w-4 text-brand-700" />Regret emails</div>
        <p class="text-sm text-gray-600">
          {{ summary.regret.not_selected }} not selected waiting for a regret<template v-if="summary.regret.waitlisted">
            · {{ summary.regret.waitlisted }} waitlisted {{ summary.regret.waitlist_released ? '(waitlist released)' : '(held until the waitlist is released)' }}</template>
          <template v-if="summary.regret.sent"> · {{ summary.regret.sent }} already sent</template>
        </p>
        <p class="text-xs text-gray-500">
          Goes to interviewed candidates marked <b>Not selected</b> on the Scores &amp; decision step, once each.
        </p>
        <p v-if="!summary.regret.enabled" class="text-xs text-orange-700">The “Regret after interview” email is switched off in Email Setup.</p>
        <div>
          <Button
            variant="solid"
            icon-left="send"
            :class="BTN_BRAND"
            :disabled="!summary.regret.enabled || !(summary.regret.not_selected + summary.regret.waitlisted)"
            @click="openRegret"
          >
            Send regrets
          </Button>
        </div>
      </div>
      <div class="flex flex-col gap-2 p-5">
        <div class="flex items-center gap-2 text-sm font-semibold text-gray-900"><FeatherIcon name="gift" class="h-4 w-4 text-brand-700" />Panel thank-you &amp; honorarium</div>
        <p class="text-sm text-gray-600">
          <template v-if="summary.thanks.committee">
            {{ summary.thanks.pending }} of {{ summary.thanks.panel_size }} panellists not thanked yet<template v-if="summary.thanks.sent"> · {{ summary.thanks.sent }} thanked</template>
          </template>
          <template v-else>No Selection Committee for this job.</template>
        </p>
        <p class="text-xs text-gray-500">Each panellist is thanked once and an honorarium record is opened for them.</p>
        <p v-if="!summary.thanks.enabled" class="text-xs text-orange-700">The “Thank you to panellists” email is switched off in Email Setup.</p>
        <div class="flex flex-wrap items-center gap-3">
          <Button
            v-if="summary.thanks.can_send"
            variant="solid"
            icon-left="heart"
            :class="BTN_BRAND"
            :disabled="!summary.thanks.enabled || !summary.thanks.pending"
            @click="askThanks"
          >
            Send thank-you to panel
          </Button>
          <router-link v-if="session.hasMenu('honorarium')" to="/honorarium" class="text-sm text-brand-700 hover:underline">Open Panel Honorarium</router-link>
        </div>
      </div>
    </div>

    <ConfirmActionDialog v-model:open="confirmBox.open" v-bind="confirmBox" />

    <Dialog v-model="regretBox.open" :options="{ title: 'Send regret emails?', size: 'md' }">
      <template #body-content>
        <div v-if="summary" class="flex flex-col gap-3 text-sm text-gray-700">
          <p>
            The “Regret after interview” email goes to <b>{{ regretCount }}</b> candidate{{ regretCount === 1 ? '' : 's' }} of {{ jobTitle }}
            who {{ regretCount === 1 ? 'was' : 'were' }} interviewed and not selected. Each candidate gets it once.
          </p>
          <label v-if="summary.regret.waitlisted && !summary.regret.waitlist_released" class="flex items-start gap-2">
            <input v-model="regretBox.includeWaitlisted" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            <span>
              Also send to the {{ summary.regret.waitlisted }} waitlisted candidate{{ summary.regret.waitlisted === 1 ? '' : 's' }} (release the waitlist).
              <span class="block text-xs text-gray-500">They are recorded as Not selected. Leave unticked while the waitlist may still be used.</span>
            </span>
          </label>
          <p v-else-if="summary.regret.waitlisted" class="text-xs text-gray-600">
            The waitlist is released (the job is Filled or Cancelled), so the {{ summary.regret.waitlisted }} waitlisted candidate(s) are included and recorded as Not selected.
          </p>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="regretBox.open = false">Cancel</Button>
          <Button variant="solid" theme="red" :loading="regretBox.busy" :disabled="!regretCount" @click="sendRegrets">Send {{ regretCount }} regret{{ regretCount === 1 ? '' : 's' }}</Button>
        </div>
      </template>
    </Dialog>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'
import ConfirmActionDialog from '@/components/common/ConfirmActionDialog.vue'
import { selectionService } from '@/services/selection'
import { honorariumService } from '@/services/honorarium'
import { useSessionStore } from '@/stores/session'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  job: { type: String, required: true },
  jobTitle: { type: String, default: '' },
})
const emit = defineEmits(['changed'])
const session = useSessionStore()

const summary = ref(null)
const loading = ref(false)
async function load() {
  loading.value = true
  try {
    summary.value = await selectionService.getPostInterviewSummary(props.job)
  } catch {
    summary.value = null
  } finally {
    loading.value = false
  }
}
watch(() => props.job, load, { immediate: true })

const confirmBox = reactive({ open: false, title: '', message: '', label: '', theme: 'gray', run: null })
const regretBox = reactive({ open: false, includeWaitlisted: false, busy: false })
const regretCount = computed(() => {
  const r = summary.value?.regret
  if (!r) return 0
  return r.not_selected + (r.waitlist_released || regretBox.includeWaitlisted ? r.waitlisted : 0)
})

function openRegret() {
  Object.assign(regretBox, { open: true, includeWaitlisted: false, busy: false })
}
async function sendRegrets() {
  regretBox.busy = true
  try {
    const r = await selectionService.sendRegrets(props.job, regretBox.includeWaitlisted)
    toast({ title: `${r.sent} regret email${r.sent === 1 ? '' : 's'} queued.`, icon: 'check', iconClasses: 'text-green-500' })
    regretBox.open = false
    await load()
    emit('changed')
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not send the regrets.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    regretBox.busy = false
  }
}

function askThanks() {
  const t = summary.value.thanks
  Object.assign(confirmBox, {
    open: true,
    title: 'Send thank-you to panel?',
    message:
      `The “Thank you to panellists” email goes to ${t.pending} panellist${t.pending === 1 ? '' : 's'} not thanked yet, and an honorarium record ` +
      `is opened for each on the Panel Honorarium page${t.external_only ? ' (internal panellists: Not applicable)' : ''}.`,
    label: 'Send thank-you',
    theme: 'gray',
    run: async () => {
      try {
        const r = await honorariumService.sendPanelThanks(props.job)
        toast({ title: `Thank-you sent to ${r.sent} panellist${r.sent === 1 ? '' : 's'}.`, icon: 'check', iconClasses: 'text-green-500' })
        await load()
        emit('changed')
      } catch (e) {
        toast({ title: e?.messages?.[0] || 'Could not send the thank-you.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
      }
    },
  })
}

defineExpose({ load })
</script>
