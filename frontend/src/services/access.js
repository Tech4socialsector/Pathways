import { callMethod } from './api'

export const accessService = {
  getMyAccess() {
    return callMethod('pathways.api.access.get_my_access')
  },
  // System Manager — Roles & Permissions
  getMatrix() {
    return callMethod('pathways.api.access.get_access_matrix')
  },
  setPermission(doctype, role, ptype, value) {
    return callMethod('pathways.api.access.set_role_permission', { doctype, role, ptype, value: value ? 1 : 0 })
  },
  resetDoctype(doctype) {
    return callMethod('pathways.api.access.reset_doctype_permissions', { doctype })
  },
  createRole(roleName) {
    return callMethod('pathways.api.access.create_role', { role_name: roleName })
  },
  removeRole(role) {
    return callMethod('pathways.api.access.remove_role', { role })
  },
  getRoleUsers(role) {
    return callMethod('pathways.api.access.get_role_users', { role })
  },
  searchUsers(txt) {
    return callMethod('pathways.api.access.search_users', { txt })
  },
  assignRole(user, role) {
    return callMethod('pathways.api.access.assign_role', { user, role })
  },
  unassignRole(user, role) {
    return callMethod('pathways.api.access.unassign_role', { user, role })
  },
  createStaffUser(data) {
    return callMethod('pathways.api.access.create_staff_user', data)
  },
}
