import { ref } from 'vue'
import { createResource } from 'frappe-ui'

function useActiveRecordOptions(doctype, labelField) {
  const options = ref([])

  const resource = createResource({
    url: 'frappe.client.get_list',
    params: {
      doctype,
      filters: { is_active: 1 },
      fields: ['name', labelField],
      limit_page_length: 0,
      order_by: `${labelField} asc`,
    },
    auto: false,
    onSuccess(data) {
      options.value = data.map((row) => ({ label: row[labelField], value: row.name }))
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
