<template>
  <Badge :theme="theme" :label="status" />
</template>

<script setup>
import { computed } from 'vue'
import { Badge } from 'frappe-ui'

const props = defineProps({
  status: { type: String, required: true },
})

const POSITIVE = [
  'Approved', 'Shortlisted', 'Selected', 'Offer Accepted', 'Verified', 'Joined', 'Completed', 'Advertised',
  'Accepted', 'Complete', 'Paid', 'Signed by Registrar', 'Published',
]
const NEGATIVE = [
  'Not Selected', 'Withdrawn', 'Declined', 'Returned for Revision', 'Expired', 'Rejected', 'Cancelled', 'No-show',
]
const WARNING = [
  'Under Review', 'Pending', 'Under Approval', 'Under Verification', 'Resubmission Requested', 'Draft',
  'Approved for Signature', 'Partially Submitted', 'In Progress', 'Requested',
]
// In flight but on track: sent out, confirmed, awaiting the other side.
const INFO = ['Sent', 'Confirmed', 'Scheduled', 'Rescheduled', 'Submitted']

const theme = computed(() => {
  if (POSITIVE.includes(props.status)) return 'green'
  if (NEGATIVE.includes(props.status)) return 'red'
  if (WARNING.includes(props.status)) return 'orange'
  if (INFO.includes(props.status)) return 'blue'
  return 'gray'
})
</script>
