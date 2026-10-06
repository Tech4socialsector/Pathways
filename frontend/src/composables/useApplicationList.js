import { createListResource } from 'frappe-ui'

export function useApplicationList() {
  return createListResource({
    doctype: 'Application',
    fields: ['name', 'application_id', 'candidate', 'job_opening', 'status', 'application_date'],
    orderBy: 'creation desc',
    // DataTable searches, filters and paginates client-side, so load all rows.
    pageLength: 1000,
    auto: true,
  })
}
