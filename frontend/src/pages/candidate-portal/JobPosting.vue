<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-3xl px-6 py-10">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>
      <EmptyState
        v-else-if="!job"
        title="This position is not currently open for applications"
        description="It may have closed or been filled."
      >
        <template #action>
          <Button @click="$router.push('/portal/jobs')">View current openings</Button>
        </template>
      </EmptyState>
      <template v-else>
        <BackButton fallback="/portal/jobs" label="All openings" />
        <div class="mt-3 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">{{ job.job_title }}</h1>
            <p class="mt-1 text-sm text-gray-500">National Law School of India University</p>
          </div>
          <Button variant="solid" size="md" @click="$router.push(`/portal/jobs/${job.name}/apply`)">Apply Now</Button>
        </div>

        <dl class="mt-6 grid grid-cols-2 gap-4 rounded-lg border bg-white p-4 text-sm sm:grid-cols-3">
          <div v-for="item in details" :key="item.label">
            <dt class="text-gray-500">{{ item.label }}</dt>
            <dd class="font-medium text-gray-900">{{ item.value }}</dd>
          </div>
        </dl>

        <div class="mt-6 rounded-lg border bg-white p-6">
          <div class="mb-3 text-base font-semibold text-gray-900">Job Description</div>
          <div v-if="job.jd_text" class="prose prose-sm max-w-none" v-html="job.jd_text" />
          <p v-else class="text-sm text-gray-500">A detailed description will be shared with shortlisted candidates.</p>
          <a
            v-if="job.jd_attachment"
            :href="job.jd_attachment"
            target="_blank"
            rel="noopener"
            class="mt-4 inline-block text-sm font-medium text-blue-600 hover:underline"
          >Download full job description</a>
        </div>

        <div class="mt-6 flex justify-end">
          <Button variant="solid" size="md" @click="$router.push(`/portal/jobs/${job.name}/apply`)">Apply Now</Button>
        </div>
      </template>
    </div>
  </CandidatePortalLayout>
</template>

<script setup>
import BackButton from '@/components/common/BackButton.vue'
import { computed, onMounted } from 'vue'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'

const props = defineProps({ id: { type: String, required: true } })

// Public: the endpoint only returns Advertised jobs, otherwise job stays null.
const { job, loading, fetchJob } = useJobOpeningDetail()

const details = computed(() =>
  [
    { label: 'Department', value: job.value?.department },
    { label: 'Recruitment Track', value: job.value?.track },
    { label: 'Designation', value: job.value?.designation },
    { label: 'Employment Type', value: job.value?.employment_type },
    { label: 'Vacancies', value: job.value?.vacancies },
    { label: 'Pay Level', value: job.value?.pay_level },
    { label: 'Tenure', value: job.value?.tenure_description },
  ].filter((d) => d.value),
)

onMounted(() => fetchJob(props.id))
</script>
