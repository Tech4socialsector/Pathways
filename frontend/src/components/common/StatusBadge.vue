<template>
  <Badge :theme="theme" :label="status" />
</template>

<script setup>
import { computed } from 'vue'
import { Badge } from 'frappe-ui'

const props = defineProps({
  status: { type: String, required: true },
})

const POSITIVE = ['Approved', 'Shortlisted', 'Selected', 'Offer Accepted', 'Verified', 'Joined', 'Completed', 'Advertised']
const NEGATIVE = ['Not Selected', 'Withdrawn', 'Declined', 'Returned for Revision', 'Expired', 'Rejected', 'Cancelled']
const WARNING = ['Under Review', 'Pending', 'Under Approval', 'Under Verification', 'Resubmission Requested', 'Draft']

const theme = computed(() => {
  if (POSITIVE.includes(props.status)) return 'green'
  if (NEGATIVE.includes(props.status)) return 'red'
  if (WARNING.includes(props.status)) return 'orange'
  return 'gray'
})
</script>
