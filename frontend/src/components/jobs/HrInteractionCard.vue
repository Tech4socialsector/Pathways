<template>
  <!-- Application page: Round 1 (HR interaction) assessors, what each
       recorded, and whether the candidate is on the final shortlist
       (workflow steps 13-14). Hidden when there is nothing to show. -->
  <SectionCard v-if="data && (data.interviews.length || data.final_shortlisted)" title="HR Interaction" icon="user-check">
    <div class="flex flex-col gap-3 text-sm">
      <p v-if="data.final_shortlisted" class="flex items-start gap-1.5 rounded-lg bg-brand-50 px-3 py-2 text-brand-800">
        <FeatherIcon name="star" class="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>On the final shortlist<template v-if="data.final_shortlist_remarks">: {{ data.final_shortlist_remarks }}</template></span>
      </p>
      <div v-for="iv in data.interviews" :key="iv.name" class="flex flex-col gap-2">
        <div class="flex flex-wrap items-baseline justify-between gap-2 text-xs text-gray-500">
          <span>Round 1 · {{ dayjs(iv.scheduled_datetime).format('DD MMM YYYY, h:mm A [IST]') }}</span>
          <span>{{ iv.status }}</span>
        </div>
        <p v-if="iv.hr_assessors.length" class="text-xs text-gray-600">Assessors: {{ iv.hr_assessors.map((a) => a.assessor_name).join(', ') }}</p>
        <p v-if="!iv.assessments.length" class="text-xs text-gray-500">No HR assessment recorded yet.</p>
        <div v-for="a in iv.assessments" :key="a.assessor" class="rounded-lg border px-3 py-2">
          <div class="flex flex-wrap items-baseline justify-between gap-2">
            <span class="font-medium text-gray-900">{{ a.assessor_name }}</span>
            <span class="text-xs font-medium" :class="TONE[a.hr_outcome] || 'text-gray-600'">{{ a.hr_outcome || 'No outcome' }}</span>
          </div>
          <div class="text-xs text-gray-500">Score {{ fmt(a.total_score) }} / {{ fmt(a.max_score) }}</div>
          <p v-if="a.note" class="mt-1 whitespace-pre-line text-gray-700">{{ a.note }}</p>
          <p v-if="a.expected_salary || a.notice_period" class="mt-1 text-xs text-gray-500">
            <template v-if="a.expected_salary">Salary expectation: {{ a.expected_salary }}</template>
            <template v-if="a.expected_salary && a.notice_period"> · </template>
            <template v-if="a.notice_period">Notice period: {{ a.notice_period }}</template>
          </p>
        </div>
      </div>
    </div>
  </SectionCard>
</template>

<script setup>
import { ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import { interviewService } from '@/services/interviews'

const props = defineProps({ application: { type: String, required: true } })

const TONE = { 'Recommend for final': 'text-green-700', Hold: 'text-amber-700', 'Not recommended': 'text-red-700' }
const data = ref(null)
const fmt = (n) => Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })

watch(
  () => props.application,
  async (name) => {
    data.value = null
    try {
      data.value = await interviewService.getHrInteraction(name)
    } catch {
      // No access or no data: the card stays hidden.
    }
  },
  { immediate: true },
)
</script>
