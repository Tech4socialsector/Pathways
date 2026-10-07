import { createListResource } from 'frappe-ui'

export function useApplicationList() {
  return createListResource({
    doctype: 'Application',
    // Names, not IDs: the linked candidate's name and the job's title.
    fields: [
      'name',
      'application_id',
      'candidate',
      'candidate.full_name as candidate_name',
      'job_opening',
      'job_opening.job_title as job_title',
      'status',
      'eligibility_status',
      'application_date',
      // Optional columns (Columns menu)
      'candidate.email as candidate_email',
      'candidate.mobile_number as candidate_mobile',
      'track',
      'job_opening.department as department',
      'source',
      'overall_experience_years',
      'relevant_experience_years',
      'notice_period',
      'eligibility_reason',
      'regret_sent_on',
      'modified',
    ],
    orderBy: 'creation desc',
    // DataTable searches, filters and paginates client-side, so load all rows.
    pageLength: 1000,
    auto: true,
  })
}
