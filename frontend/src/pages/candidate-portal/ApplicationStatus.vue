<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-2xl px-6 py-10">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <template v-else-if="status">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">{{ status.job_title }}</h1>
            <p class="text-sm text-gray-500">{{ status.application_id }}</p>
          </div>
          <StatusBadge :status="status.status" />
        </div>

        <div class="mb-6 rounded-lg border bg-white p-4">
          <div class="mb-4 text-sm font-semibold text-gray-900">Your Progress</div>
          <RecruitmentTimeline :steps="timelineSteps" />
        </div>

        <div v-if="status.interviews?.length" class="mb-6 rounded-lg border bg-white p-4">
          <div class="mb-3 text-sm font-semibold text-gray-900">Interviews</div>
          <div v-for="(iv, idx) in status.interviews" :key="idx" class="mb-2 text-sm">
            <div class="font-medium text-gray-900">{{ iv.round_type }}</div>
            <div class="text-gray-600">{{ formatDate(iv.scheduled_datetime) }} &middot; {{ iv.mode }}</div>
            <a v-if="iv.meeting_link" :href="iv.meeting_link" class="text-blue-600 hover:underline">
              Join meeting
            </a>
          </div>
        </div>

        <div v-if="offer.offer.value" class="mb-6 rounded-lg border bg-white p-4">
          <div class="mb-3 text-sm font-semibold text-gray-900">Offer</div>
          <StatusBadge :status="offer.offer.value.status" />
          <p v-if="offer.offer.value.acceptance_deadline" class="mt-1 text-xs text-gray-500">
            Please respond by {{ offer.offer.value.acceptance_deadline }}
          </p>

          <div v-if="offer.offer.value.status === 'Sent'" class="mt-4 flex flex-col gap-3">
            <FormControl label="Confirmed Date of Joining" type="date" v-model="confirmedDoj" />
            <div class="flex gap-2">
              <Button variant="solid" theme="green" @click="respondAccept">Accept Offer</Button>
              <Button variant="outline" theme="red" @click="respondDecline">Decline</Button>
            </div>
          </div>
        </div>

        <div v-if="status.document_status" class="rounded-lg border bg-white p-4">
          <div class="mb-3 text-sm font-semibold text-gray-900">Documents</div>
          <StatusBadge :status="status.document_status" />
        </div>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Button, FormControl, toast } from 'frappe-ui'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RecruitmentTimeline from '@/components/common/RecruitmentTimeline.vue'
import { useApplicationStatus } from '@/composables/useApplications'
import { useMyOffer } from '@/composables/useOffers'

const props = defineProps({ id: { type: String, required: true } })

const { status, loading, fetchStatus } = useApplicationStatus()
const offer = useMyOffer()
const confirmedDoj = ref('')

const PIPELINE = [
  { key: 'Submitted', label: 'Application Received' },
  { key: 'Under Review', label: 'Under Review' },
  { key: 'Shortlisted', label: 'Shortlisted' },
  { key: 'Interview Scheduled', label: 'Interview Scheduled' },
  { key: 'Interview Completed', label: 'Interview Completed' },
  { key: 'Selected', label: 'Selected' },
  { key: 'Offer Extended', label: 'Offer Extended' },
  { key: 'Offer Accepted', label: 'Offer Accepted' },
  { key: 'Documents Verified', label: 'Documents Verified' },
  { key: 'Joined', label: 'Joined' },
]

const timelineSteps = computed(() => {
  if (!status.value) return []
  const currentStatus = status.value.status
  if (currentStatus === 'Not Selected' || currentStatus === 'Withdrawn') {
    return [
      ...PIPELINE.slice(0, 2).map((s) => ({ ...s, state: 'completed' })),
      { key: currentStatus, label: currentStatus === 'Not Selected' ? 'Application Not Successful' : 'Withdrawn', state: 'rejected' },
    ]
  }
  const currentIdx = PIPELINE.findIndex((s) => s.key === currentStatus)
  return PIPELINE.map((step, idx) => ({
    ...step,
    state: idx < currentIdx ? 'completed' : idx === currentIdx ? 'current' : 'pending',
  }))
})

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function respondAccept() {
  if (!confirmedDoj.value) {
    toast({ title: 'Please select your confirmed date of joining before accepting.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    return
  }
  try {
    await offer.respond(offer.offer.value.name, 'Accepted', confirmedDoj.value)
    toast({ title: 'Offer accepted. Congratulations!', icon: 'check', iconClasses: 'text-green-500' })
    await offer.fetchOffer(props.id)
    await fetchStatus(props.id)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not accept the offer.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

async function respondDecline() {
  try {
    await offer.respond(offer.offer.value.name, 'Declined')
    toast({ title: 'Offer declined.', icon: 'info', iconClasses: 'text-gray-500' })
    await offer.fetchOffer(props.id)
    await fetchStatus(props.id)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not decline the offer.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

onMounted(() => {
  fetchStatus(props.id)
  offer.fetchOffer(props.id)
})
watch(() => props.id, (id) => {
  fetchStatus(id)
  offer.fetchOffer(id)
})
</script>
