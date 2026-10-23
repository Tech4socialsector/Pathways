import dayjs from 'dayjs'

export function formatDateTime(value) {
  return value ? dayjs(value).format('DD MMM YYYY, h:mm A [IST]') : ''
}

/** The most recent "Returned for Revision" entry of a chain's log. */
export function lastReturn(chain) {
  return [...(chain?.log || [])].reverse().find((r) => r.action === 'Returned for Revision') || null
}

/**
 * RecruitmentTimeline steps from get_chain_status() output (same rules as
 * the Pre-Recruitment GreenSheetPanel).
 */
export function chainTimeline(chain) {
  if (!chain) return []
  const log = chain.log || []
  const returned = lastReturn(chain)
  return chain.steps.map((step) => {
    const entry = [...log].reverse().find((r) => r.sequence === step.sequence)
    let state = 'pending'
    if (step.completed) state = 'completed'
    else if (chain.status === 'Under Approval' && step.sequence === chain.current_level) state = 'current'
    else if (chain.status === 'Returned for Revision' && entry && entry === returned) state = 'rejected'
    const who = entry?.approver_name || entry?.approver
    let detail = step.approver_role
    if (state === 'completed' && entry) detail = `Approved by ${who} · ${formatDateTime(entry.acted_on)}`
    else if (state === 'rejected' && entry) detail = `Returned by ${who} · ${formatDateTime(entry.acted_on)}`
    else if (state === 'current') detail = `Awaiting ${step.approver_role}`
    return { key: step.sequence, label: step.approver_label || step.approver_role, detail, state }
  })
}
