import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { ref, computed } from 'vue'

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

  const roles = ref([])
  const rolesLoaded = ref(false)

  const rolesResource = createResource({
    url: 'pathways.api.auth.get_my_roles',
    auto: false,
    onSuccess(data) {
      roles.value = data || []
      rolesLoaded.value = true
    },
  })

  function fetchRoles() {
    if (isLoggedIn.value && !rolesLoaded.value) {
      rolesResource.fetch()
    }
  }

  function hasRole(roleName) {
    return roles.value.includes(roleName)
  }

  function hasAnyRole(roleNames) {
    return roleNames.some((r) => roles.value.includes(r))
  }

  const isStaff = computed(() => !hasRole('Pathways Candidate') && roles.value.length > 0)
  const isCandidate = computed(() => hasRole('Pathways Candidate'))
  const isAdmin = computed(() => hasRole('Pathways Admin'))

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      user.value = null
      roles.value = []
      rolesLoaded.value = false
      window.location.href = '/login?redirect-to=/pathways'
    },
  })

  return {
    user,
    isLoggedIn,
    roles,
    rolesLoaded,
    fetchRoles,
    hasRole,
    hasAnyRole,
    isStaff,
    isCandidate,
    isAdmin,
    logout,
  }
})
