<template>
  <!-- Public page: the referee is not a Pathways user. The token in the URL
       is the only credential; the server validates it on every call. -->
  <div class="flex min-h-full flex-col bg-gray-50">
    <header class="border-t-4 border-brand-700 bg-white shadow-sm">
      <div class="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-brand-700 font-heading text-lg font-bold text-white">N</span>
        <span class="min-w-0">
          <span class="block truncate font-heading text-lg font-bold leading-tight text-gray-900">NLSIU Reference Check</span>
          <span class="block truncate text-xs text-gray-500">National Law School of India University, Bengaluru</span>
        </span>
      </div>
    </header>

    <main class="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6">
      <div v-if="loading" class="rounded-2xl border bg-white p-8 text-sm text-gray-500" aria-busy="true">Loading…</div>

      <div v-else-if="state !== 'open'" class="rounded-2xl border bg-white p-8 text-center shadow-sm">
        <div
          class="mx-auto flex h-12 w-12 items-center justify-center rounded-full"
          :class="state === 'submitted' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'"
        >
          <FeatherIcon :name="state === 'submitted' ? 'check' : 'alert-circle'" class="h-6 w-6" />
        </div>
        <h1 class="mt-4 font-heading text-xl font-bold text-gray-900">{{ MESSAGES[state]?.title || MESSAGES.invalid.title }}</h1>
        <p class="mt-2 text-sm text-gray-600">{{ MESSAGES[state]?.text || MESSAGES.invalid.text }}</p>
        <p v-if="contactEmail && state !== 'submitted'" class="mt-3 text-sm text-gray-600">
          Contact: <a :href="`mailto:${contactEmail}`" class="text-brand-700 underline">{{ contactEmail }}</a>
        </p>
      </div>

      <form v-else class="flex flex-col gap-6" novalidate @submit.prevent="submit">
        <section class="rounded-2xl border bg-white p-6 shadow-sm sm:p-8">
          <p class="text-sm text-gray-600">Dear {{ form.referee_name }},</p>
          <h1 class="mt-3 font-heading text-2xl font-bold text-gray-900">Reference for {{ form.candidate_name }}</h1>
          <p class="mt-1 text-sm text-gray-600">
            Post applied for: <b class="text-gray-900">{{ form.position }}</b>
          </p>
          <p v-if="form.intro" class="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-gray-700">{{ form.intro }}</p>
          <p class="mt-4 rounded-md bg-brand-50/70 px-3 py-2 text-xs text-gray-600">
            Your responses are confidential and are not shared with the candidate. You can submit this form once
            <template v-if="form.expires_on">, until {{ formatDate(form.expires_on) }}</template>.
            Questions marked <span class="text-red-600">*</span> are required.
          </p>
        </section>

        <section class="rounded-2xl border bg-white p-6 shadow-sm sm:p-8">
          <ReferenceQuestionsForm v-model="answers" :questions="form.questions" :disabled="submitting" />
        </section>

        <ErrorMessage :message="error" />
        <div class="flex justify-end">
          <Button type="submit" variant="solid" size="lg" :class="BTN_BRAND" :loading="submitting">Submit reference</Button>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Button, ErrorMessage, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import ReferenceQuestionsForm from '@/components/references/ReferenceQuestionsForm.vue'
import { referenceCheckService } from '@/services/referenceChecks'
import { BTN_BRAND } from '@/utils/buttonStyles'

const route = useRoute()

const MESSAGES = {
  submitted: { title: 'Thank you', text: 'Your reference has been received. We greatly appreciate your support in our hiring process.' },
  expired: { title: 'This link has expired', text: 'Please contact the recruitment team for a new link.' },
  invalid: { title: 'This link is not valid', text: 'It may have been replaced by a newer link. Please use the link in the most recent email from NLSIU.' },
}

const loading = ref(true)
const state = ref('invalid')
const contactEmail = ref('')
const form = ref({})
const answers = ref({})
const error = ref('')
const submitting = ref(false)

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}

async function load() {
  loading.value = true
  try {
    const out = await referenceCheckService.getRefereeForm(route.params.token)
    state.value = out.state
    contactEmail.value = out.contact_email || ''
    if (out.state === 'open') {
      form.value = out
      answers.value = Object.fromEntries(out.questions.map((q) => [q.name, { answer_text: '', rating_value: null }]))
    }
  } catch {
    state.value = 'invalid'
  } finally {
    loading.value = false
  }
}

function missingRequired() {
  return form.value.questions.filter((q) => {
    if (!q.required) return false
    const a = answers.value[q.name] || {}
    return q.answer_type === 'Rating 1-5' ? !a.rating_value : !(a.answer_text || '').trim()
  })
}

async function submit() {
  error.value = ''
  const missing = missingRequired()
  if (missing.length) {
    error.value = `Please answer all required questions (${missing.length} left).`
    return
  }
  submitting.value = true
  try {
    await referenceCheckService.submitRefereeForm(route.params.token, answers.value)
    state.value = 'submitted'
    window.scrollTo({ top: 0 })
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not submit your reference. Please try again.'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
