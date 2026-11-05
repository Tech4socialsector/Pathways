// A candidate's reply to an interview (Interview.rsvp_status), for staff
// lists. Older replies say Declined; it now reads as Withdrawn.
export const RSVP_TONE = {
  Pending: 'bg-orange-50 text-orange-700',
  Confirmed: 'bg-green-50 text-green-700',
  'Reschedule Requested': 'bg-amber-50 text-amber-800',
  Withdrawn: 'bg-red-50 text-red-700',
}

export function rsvpLabel(status) {
  const s = status || 'Pending'
  return s === 'Declined' ? 'Withdrawn' : s
}

// The candidate's preferred times, one per line ("YYYY-MM-DD HH:mm").
export function preferredTimes(row) {
  return (row?.reschedule_preferences || '').split('\n').filter(Boolean)
}
