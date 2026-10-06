import { ref } from 'vue'
import { createResource } from 'frappe-ui'

function useActiveRecordOptions(doctype, labelField, extraFields = [], format = (row) => row[labelField]) {
  const options = ref([])

  const resource = createResource({
    url: 'frappe.client.get_list',
    params: {
      doctype,
      filters: { is_active: 1 },
      fields: ['name', labelField, ...extraFields],
      limit_page_length: 0,
      order_by: `${labelField} asc`,
    },
    auto: false,
    onSuccess(data) {
      options.value = data.map((row) => ({ label: format(row), value: row.name }))
    },
  })

  function fetch() {
    if (!resource.fetched) resource.fetch()
  }

  return { options, fetch }
}

export function useRecruitmentTrackOptions() {
  return useActiveRecordOptions('Recruitment Track', 'track_name')
}

export function useDepartmentOptions() {
  return useActiveRecordOptions('Department', 'department_name')
}

export function useDesignationOptions() {
  return useActiveRecordOptions('Designation', 'designation_name')
}

export function usePositionOptions() {
  return useActiveRecordOptions('Position', 'job_code', ['position_title'], (row) => `${row.job_code} · ${row.position_title}`)
}
