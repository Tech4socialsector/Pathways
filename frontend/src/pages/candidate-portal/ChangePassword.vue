<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-md px-4 py-12 sm:px-6">
      <div class="overflow-hidden rounded-2xl border bg-white shadow-sm">
        <div class="border-b bg-brand-50 px-6 py-5">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-brand-700 text-white">
            <FeatherIcon name="lock" class="h-5 w-5" />
          </span>
          <h1 class="mt-3 font-heading text-xl font-bold text-gray-900">
            {{ session.mustChangePassword ? 'Set your own password' : 'Change password' }}
          </h1>
          <p class="mt-1 text-sm text-gray-600">
            <template v-if="session.mustChangePassword">
              You logged in with the temporary password we emailed you. Choose a new password to continue.
            </template>
            <template v-else>Enter your current password and a new one.</template>
          </p>
        </div>

        <form class="flex flex-col gap-4 px-6 py-6" autocomplete="off" @submit.prevent="save">
          <FormControl
            v-model="form.current"
            type="password"
            :label="session.mustChangePassword ? 'Temporary password (from the email)' : 'Current password'"
            autocomplete="current-password"
          />
          <button type="button" class="-mt-2 self-end text-xs font-medium text-brand-700 hover:underline" @click="openForgot">
            Forgot your {{ session.mustChangePassword ? 'temporary' : 'current' }} password?
          </button>
          <FormControl v-model="form.next" type="password" label="New password" autocomplete="new-password" />
          <FormControl v-model="form.confirm" type="password" label="Confirm new password" autocomplete="new-password" />
          <ul class="flex flex-col gap-1 text-xs">
            <li v-for="r in rules" :key="r.label" class="flex items-center gap-1.5" :class="r.ok ? 'text-green-700' : 'text-gray-500'">
              <FeatherIcon :name="r.ok ? 'check-circle' : 'circle'" class="h-3.5 w-3.5" />{{ r.label }}
            </li>
          </ul>
          <p v-if="error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
          <Button type="submit" variant="solid" size="md" :class="BTN_BRAND" :loading="saving" :disabled="!valid">
            Save password
          </Button>
        </form>
      </div>
    </div>

    <!-- Forgot password: a reset link to their own email -->
    <Dialog v-model="forgot.open" :options="{ size: 'sm' }">
      <template #body>
        <div class="px-6 pb-6 pt-7 text-center">
          <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full" :class="forgot.sentTo ? 'bg-green-50 text-green-700' : 'bg-brand-50 text-brand-700'">
            <FeatherIcon :name="forgot.sentTo ? 'mail' : 'key'" class="h-6 w-6" />
          </span>
          <template v-if="!forgot.sentTo">
            <h2 class="mt-4 font-heading text-lg font-bold text-gray-900">Reset your password</h2>
            <p class="mt-2 text-sm text-gray-600">
              We will email a secure link to <b class="text-gray-900">{{ maskedEmail }}</b>. Open it to choose a new password; you will be signed in again.
            </p>
          </template>
          <template v-else>
            <h2 class="mt-4 font-heading text-lg font-bold text-gray-900">Check your inbox</h2>
            <p class="mt-2 text-sm text-gray-600">
              We sent a reset link to <b class="text-gray-900">{{ forgot.sentTo }}</b>. It works once and expires soon. Not there? Check your spam folder.
            </p>
          </template>
          <p v-if="forgot.error" class="mt-4 flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2 text-left text-sm text-red-700" role="alert">
            <FeatherIcon name="alert-circle" class="mt-0.5 h-4 w-4 shrink-0" />{{ forgot.error }}
          </p>
          <div class="mt-6 flex flex-col gap-2">
            <Button v-if="!forgot.sentTo" variant="solid" size="lg" icon-left="send" :class="BTN_BRAND" :loading="forgot.sending" @click="sendReset">Email me a reset link</Button>
            <Button size="lg" :disabled="forgot.sending" @click="forgot.open = false">{{ forgot.sentTo ? 'Done' : 'Cancel' }}</Button>
          </div>
        </div>
      </template>
    </Dialog>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import { useSessionStore } from '@/stores/session'
import { applicationService } from '@/services/applications'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { callMethod } from '@/services/api'

const session = useSessionStore()
const route = useRoute()
const router = useRouter()

const form = reactive({ current: '', next: '', confirm: '' })
const saving = ref(false)
const error = ref('')

const rules = computed(() => [
  { label: 'At least 8 characters', ok: form.next.length >= 8 },
  { label: 'Different from the current password', ok: !!form.next && form.next !== form.current },
  { label: 'Both new passwords match', ok: !!form.next && form.next === form.confirm },
])
const valid = computed(() => !!form.current && rules.value.every((r) => r.ok))

// ----- forgot password
const forgot = reactive({ open: false, sending: false, sentTo: '', error: '' })
// Shown before sending; the server answers with the same form.
const maskedEmail = computed(() => {
  const [local = '', domain = ''] = String(session.user || '').split('@')
  return local.length > 2 ? `${local[0]}${'*'.repeat(local.length - 2)}${local.slice(-1)}@${domain}` : `${local[0] || ''}*@${domain}`
})
function openForgot() {
  Object.assign(forgot, { open: true, sending: false, sentTo: '', error: '' })
}
async function sendReset() {
  forgot.sending = true
  forgot.error = ''
  try {
    const result = await callMethod('pathways.utils.candidate_account.send_my_password_reset')
    forgot.sentTo = result?.email || maskedEmail.value
  } catch (e) {
    const message = e?.messages?.[0] || ''
    forgot.error = /rate limit|too many/i.test(message) || e?.exc_type === 'TooManyRequestsError'
      ? 'Too many reset emails were asked for. Please try again in an hour.'
      : message || 'Could not send the reset email. Please try again.'
  } finally {
    forgot.sending = false
  }
}

async function save() {
  if (!valid.value) return
  saving.value = true
  error.value = ''
  try {
    await applicationService.changePortalPassword(form.current, form.next)
    await session.fetchRoles(true)
    toast({ title: 'Password saved.', icon: 'check', iconClasses: 'text-green-500' })
    const next = String(route.query.next || '')
    router.replace(next.startsWith('/portal/') && !next.startsWith('/portal/change-password') ? next : '/portal/applications')
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not save the password.'
  } finally {
    saving.value = false
  }
}
</script>
