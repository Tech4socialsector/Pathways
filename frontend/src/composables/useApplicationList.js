import { createListResource } from 'frappe-ui'

export function useApplicationList() {
  return createListResource({
    doctype: 'Application',
    fields: ['name', 'application_id', 'candidate', 'job_opening', 'status', 'application_date'],
    orderBy: 'creation desc',
    pageLength: 20,
    auto: true,
  })
}
