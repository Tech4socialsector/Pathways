// Offer lifecycle, in workflow order (steps 26-28 then the response).
export const OFFER_STAGES = [
  'Draft',
  'Under Review',
  'Approved for Signature',
  'Signed by Registrar',
  'Sent',
  'Accepted',
  'Declined',
  'Expired',
]

export const STAGE_DOTS = {
  Draft: 'bg-orange-400',
  'Under Review': 'bg-yellow-400',
  'Approved for Signature': 'bg-blue-500',
  'Signed by Registrar': 'bg-indigo-500',
  Sent: 'bg-teal-500',
  Accepted: 'bg-green-500',
  Declined: 'bg-red-500',
  Expired: 'bg-gray-400',
}

// Old records ("Verbal Offer", "Drafted") read as Draft.
export const stageOf = (status) => (['Verbal Offer', 'Drafted'].includes(status) ? 'Draft' : status)
