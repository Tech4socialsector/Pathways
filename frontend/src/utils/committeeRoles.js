// Roles offered on the Shortlisting and Selection Committee dialogs
// (Committee Member Row.designation_label). "External expert" also sets the
// member's External flag; there is no separate External switch.
export const EXTERNAL = 'External expert'
export const COMMITTEE_ROLES = ['Member', 'Chairperson', 'Subject expert', EXTERNAL, 'Member secretary']

// A custom role already saved stays selectable.
export function roleOptions(current) {
  const list = current && !COMMITTEE_ROLES.includes(current) ? [current, ...COMMITTEE_ROLES] : COMMITTEE_ROLES
  return list.map((r) => ({ label: r, value: r }))
}
