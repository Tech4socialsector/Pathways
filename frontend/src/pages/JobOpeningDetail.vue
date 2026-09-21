<template>
  <StaffLayout>
    <PageHeader :title="job?.job_title || 'Job Opening'" :subtitle="job?.track" />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <div v-else-if="job" class="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div class="rounded-lg border bg-white p-4 md:col-span-2">
          <div class="mb-3 text-sm font-semibold text-gray-900">Job Description</div>
          <div v-if="job.jd_text" class="prose prose-sm max-w-none" v-html="job.jd_text" />
          <div v-else class="text-sm text-gray-500">No description provided.</div>
        </div>
        <div class="rounded-lg border bg-white p-4">
          <dl class="flex flex-col gap-3 text-sm">
            <div>
              <dt class="text-gray-500">Department</dt>
              <dd class="font-medium text-gray-900">{{ job.department }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">Employment Type</dt>
              <dd class="font-medium text-gray-900">{{ job.employment_type }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">Vacancies</dt>
              <dd class="font-medium text-gray-900">{{ job.vacancies }}</dd>
            </div>
            <div v-if="job.pay_level">
              <dt class="text-gray-500">Pay Level</dt>
              <dd class="font-medium text-gray-900">{{ job.pay_level }}</dd>
            </div>
            <div v-if="job.tenure_description">
              <dt class="text-gray-500">Tenure</dt>
              <dd class="font-medium text-gray-900">{{ job.tenure_description }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </StaffLayout>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'

const props = defineProps({ id: { type: String, required: true } })

const { job, loading, fetchJob } = useJobOpeningDetail()

onMounted(() => fetchJob(props.id))
watch(() => props.id, (id) => fetchJob(id))
</script>
