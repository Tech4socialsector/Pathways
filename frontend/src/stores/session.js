import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { ref, computed } from 'vue'
import { accessService } from '@/services/access'

export const useSessionStore = defineStore('pathways-session', () => {
  function sessionUser() {
    const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser === 'Guest' || !_sessionUser) {
      _sessionUser = null
    }
    return _sessionUser ? decodeURIComponent(_sessionUser) : null
  }

  const user = ref(sessionUser())
  const isLoggedIn = computed(() => !!user.value)

  // Everything below comes from pathways.api.access.get_my_access, which
  // derives it from Role Permissions — the UI never decides access from
  // hardcoded role names.
  const access = ref({})
  const rolesLoaded = ref(false)
  const roles = computed(() => access.value.roles || [])

  let accessPromise = null

  function fetchRoles(force = false) {
    if (!isLoggedIn.value || (rolesLoaded.value && !force)) {
      return Promise.resolve()
    }
    if (!accessPromise) {
      accessPromise = accessService
        .getMyAccess()
        .then((data) => {
          access.value = data || {}
          rolesLoaded.value = true
        })
        .catch(() => {
          access.value = {}
          rolesLoaded.value = true
        })
        .finally(() => {
          accessPromise = null
        })
    }
    return accessPromise
  }

  function hasRole(roleName) {
    return roles.value.includes(roleName)
  }

  function hasAnyRole(roleNames) {
    return roleNames.some((r) => roles.value.includes(r))
  }

  // can('Job Opening', 'create')
  function can(doctype, ptype = 'read') {
    return !!access.value.doctypes?.[doctype]?.[ptype]
  }

  function hasMenu(key) {
    return (access.value.menu || []).includes(key)
  }

  const isStaff = computed(() => !!access.value.is_staff)
  const isCandidate = computed(() => !!access.value.is_candidate)
  const canManageAccess = computed(() => !!access.value.can_manage_access)
  const canManageSettings = computed(() => !!access.value.can_manage_settings)
  const canViewPipeline = computed(() => !!access.value.can_view_pipeline)
  const fullName = computed(() => access.value.full_name || user.value)
  const userImage = computed(() => access.value.user_image || null)

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      user.value = null
      access.value = {}
      rolesLoaded.value = false
      window.location.href = '/login?redirect-to=/pathways'
    },
  })

  return {
    user,
    isLoggedIn,
    access,
    roles,
    rolesLoaded,
    fetchRoles,
    hasRole,
    hasAnyRole,
    can,
    hasMenu,
    isStaff,
    isCandidate,
    canManageAccess,
    canManageSettings,
    canViewPipeline,
    fullName,
    userImage,
    logout,
  }
})
