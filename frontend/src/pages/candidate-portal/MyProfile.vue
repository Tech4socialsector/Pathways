<template>
  <CandidatePortalLayout>
    <div class="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8 sm:px-6">
      <div v-if="loading" class="h-60 animate-pulse rounded-xl border bg-white" />
      <div v-else-if="error" class="rounded-xl border bg-white p-8 text-center text-sm text-gray-600">{{ error }}</div>
      <template v-else-if="profile">
        <!-- Who they are -->
        <section class="flex flex-wrap items-center gap-4 rounded-xl border bg-white p-5 shadow-sm">
          <span class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-brand-700 text-xl font-bold text-white">
            {{ initials }}
          </span>
          <div class="min-w-0 flex-1">
            <h1 class="font-heading text-xl font-bold text-gray-900">{{ profile.full_name }}</h1>
            <p class="truncate text-sm text-gray-600">{{ profile.email }}</p>
            <p class="mt-0.5 text-xs text-gray-500">
              Candidate ID <span class="font-mono font-medium text-gray-700">{{ profile.name }}</span> ·
              {{ profile.applications }} application{{ profile.applications === 1 ? '' : 's' }}
            </p>
          </div>
          <Button variant="outline" icon-left="file-text" @click="$router.push('/portal/applications')">My applications</Button>
        </section>

        <!-- Contact details -->
        <section class="rounded-xl border bg-white shadow-sm">
          <header class="flex items-center justify-between border-b px-5 py-3">
            <h2 class="text-sm font-semibold text-gray-900">Contact details</h2>
            <span class="text-xs text-gray-500">Used for interview and offer communication</span>
          </header>
          <form class="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2" @submit.prevent="save">
            <FormControl label="Full name" :model-value="profile.full_name" disabled />
            <FormControl label="Email (login)" :model-value="profile.email" disabled />
            <FormControl label="Mobile number" v-model="form.mobile_number" required />
            <FormControl label="Date of birth" type="date" v-model="form.date_of_birth" />
            <FormControl label="Gender" type="select" v-model="form.gender" :options="['', ...(profile.gender_options || [])]" />
            <div class="sm:col-span-2">
              <FormControl label="Address for correspondence" type="textarea" v-model="form.address" :rows="3" />
            </div>
            <p class="text-xs text-gray-500 sm:col-span-2">
              Your name and email identify your applications and cannot be changed here. Write to the Recruitment Team if they need correcting.
            </p>
            <div class="flex items-center gap-3 sm:col-span-2">
              <Button type="submit" variant="solid" :class="BTN_BRAND" :loading="saving" :disabled="!dirty">Save changes</Button>
              <span v-if="saved && !dirty" class="flex items-center gap-1 text-sm text-green-700"><FeatherIcon name="check" class="h-4 w-4" />Saved</span>
            </div>
          </form>
        </section>

        <!-- Security -->
        <section class="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-5 shadow-sm">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">Password</h2>
            <p class="mt-0.5 text-sm text-gray-600">Sign in with your Candidate ID or email and your password.</p>
          </div>
          <Button variant="outline" icon-left="lock" @click="$router.push('/portal/change-password')">Change password</Button>
        </section>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Button, FeatherIcon, FormControl } from 'frappe-ui'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import { callMethod } from '@/services/api'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const profile = ref(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const saved = ref(false)
const form = reactive({ mobile_number: '', date_of_birth: '', gender: '', address: '' })
const KEYS = Object.keys(form)

const initials = computed(() =>
  (profile.value?.full_name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join(''),
)
const dirty = computed(() => !!profile.value && KEYS.some((k) => (form[k] || '') !== (profile.value[k] || '')))

function fill(p) {
  profile.value = p
  for (const k of KEYS) form[k] = p[k] || ''
}

onMounted(async () => {
  try {
    fill(await callMethod('pathways.utils.candidate_account.get_my_profile'))
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not load your profile.'
  } finally {
    loading.value = false
  }
})

async function save() {
  saving.value = true
  try {
    fill(await callMethod('pathways.utils.candidate_account.update_my_profile', { data: { ...form } }))
    saved.value = true
    toast({ title: 'Profile saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save your profile.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    saving.value = false
  }
}
</script>
