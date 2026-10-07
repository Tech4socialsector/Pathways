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
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import { useSessionStore } from '@/stores/session'
import { applicationService } from '@/services/applications'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

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
