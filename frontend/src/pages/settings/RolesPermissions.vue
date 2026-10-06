<template>
  <StaffLayout>
    <PageHeader
      title="Roles & Permissions"
      subtitle="Choose what each Pathways role can see and do, and who holds each role."
    >
      <template #actions>
        <Button @click="openNewUser">
          <template #prefix><FeatherIcon name="user-plus" class="h-4 w-4" /></template>
          New Staff User
        </Button>
        <Button variant="solid" @click="openNewRole">
          <template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
          New Role
        </Button>
      </template>
    </PageHeader>

    <div class="flex min-h-0 flex-1">
      <!-- Roles -->
      <aside class="w-72 shrink-0 overflow-y-auto border-r bg-white p-3">
        <div v-if="loading && !matrix" class="p-2 text-sm text-gray-500">Loading...</div>
        <div v-else-if="loadError" class="p-2 text-sm text-red-600">{{ loadError }}</div>
        <button
          v-for="r in roles"
          :key="r.role"
          class="mb-0.5 flex w-full items-center justify-between gap-2 rounded px-2.5 py-2 text-left text-sm"
          :class="r.role === selectedRole ? 'bg-gray-100 font-medium text-gray-900' : 'text-gray-700 hover:bg-gray-50'"
          @click="selectRole(r.role)"
        >
          <span class="truncate">{{ displayRole(r.role) }}</span>
          <span class="flex shrink-0 items-center gap-1.5">
            <FeatherIcon v-if="!r.editable" name="lock" class="h-3.5 w-3.5 text-gray-400" />
            <span class="rounded bg-gray-100 px-1.5 text-xs text-gray-600">{{ r.users }}</span>
          </span>
        </button>
      </aside>

      <!-- Selected role -->
      <section v-if="selected" class="flex min-h-0 min-w-0 flex-1 flex-col">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b px-6 py-3">
          <div class="min-w-0">
            <div class="truncate text-base font-semibold text-gray-900">{{ selected.role }}</div>
            <div class="text-xs text-gray-500">
              <template v-if="!selected.editable">
                Candidate access is fixed: candidates only reach their own records through the portal.
              </template>
              <template v-else-if="selected.row_scoped">
                Built-in committee role: members only ever see the Job Openings whose committee they sit on.
              </template>
              <template v-else>Users with this role see every record of the document types they can read.</template>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <TabButtons v-model="tab" :buttons="[{ label: 'Permissions', value: 'permissions' }, { label: `Users (${selected.users})`, value: 'users' }]" />
            <Button
              v-if="selected.editable && !selected.row_scoped"
              variant="ghost"
              theme="red"
              @click="confirmRemoveRole = true"
            >
              Remove
            </Button>
          </div>
        </div>

        <!-- Permissions tab -->
        <!-- Only the table scrolls, so its header can stay pinned (sticky
             sticks to the nearest scrolling box, which is the table's). -->
        <div v-if="tab === 'permissions'" class="flex min-h-0 flex-1 flex-col p-6">
          <div class="mb-3 flex shrink-0 flex-wrap items-center justify-between gap-3">
            <div class="w-72">
              <TextInput v-model="doctypeQuery" placeholder="Search document types...">
                <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
              </TextInput>
            </div>
            <label class="flex items-center gap-2 text-sm text-gray-600">
              <input v-model="onlyGranted" type="checkbox" class="rounded border-gray-300" />
              Only show granted
            </label>
          </div>

          <div class="mb-3 shrink-0 rounded border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-800">
            <b>Read</b> on a document type also shows its menu in the sidebar. Turning a permission on adds what
            it depends on (e.g. Amend → Cancel → Submit → Write → Read); turning one off removes what depends on it.
            Who approves Green Sheets is set in Master Setup &rsaquo; Approval Chains, not here.
          </div>

          <div class="min-h-0 flex-1 overflow-auto rounded-lg border bg-white">
            <table class="w-full text-sm">
              <thead class="sticky top-0 z-10 bg-gray-50 text-left text-xs uppercase text-gray-500 shadow-[inset_0_-1px_0_theme(colors.gray.200)]">
                <tr>
                  <th class="bg-gray-50 px-4 py-2.5">Document Type</th>
                  <th v-for="p in ptypes" :key="p" class="bg-gray-50 px-2 py-2.5 text-center">{{ ptypeLabel(p) }}</th>
                  <th class="bg-gray-50 px-2 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="dt in visibleDoctypes" :key="dt.name" class="border-b last:border-0">
                  <td class="px-4 py-2">
                    <div class="font-medium text-gray-900">{{ dt.name }}</div>
                    <div class="mt-0.5 flex flex-wrap gap-1">
                      <span
                        v-for="menu in dt.menus"
                        :key="menu"
                        class="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600"
                      >
                        Menu: {{ menu }}
                      </span>
                      <span v-if="dt.customised" class="rounded bg-amber-50 px-1.5 py-0.5 text-[11px] text-amber-700">
                        Customised
                      </span>
                    </div>
                  </td>
                  <td v-for="p in ptypes" :key="p" class="px-2 py-2 text-center">
                    <input
                      v-if="applies(dt, p)"
                      type="checkbox"
                      class="h-4 w-4 rounded border-gray-300 disabled:opacity-40"
                      :checked="isGranted(dt.name, p)"
                      :disabled="!selected.editable || isBusy(dt.name)"
                      :aria-label="`${ptypeLabel(p)} ${dt.name}`"
                      @change="toggle(dt.name, p, $event.target.checked)"
                    />
                    <span v-else class="text-gray-300">—</span>
                  </td>
                  <td class="px-2 py-2 text-right">
                    <Button
                      v-if="dt.customised"
                      size="sm"
                      variant="ghost"
                      :disabled="isBusy(dt.name)"
                      @click="askReset(dt)"
                    >
                      Reset
                    </Button>
                  </td>
                </tr>
                <tr v-if="!visibleDoctypes.length">
                  <td :colspan="ptypes.length + 2" class="px-4 py-6 text-center text-sm text-gray-500">
                    No document types match.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Users tab -->
        <div v-else class="flex-1 overflow-y-auto p-6">
          <div class="mb-4 flex flex-wrap items-end gap-2">
            <div class="w-80">
              <span class="mb-1.5 block text-sm text-gray-700">Give this role to</span>
              <Autocomplete
                placeholder="Search users by name or email"
                :options="userOptions"
                :model-value="userToAdd"
                @update:query="searchUsers"
                @update:model-value="(opt) => (userToAdd = opt)"
              />
            </div>
            <Button variant="solid" :disabled="!userToAdd" :loading="assigning" @click="assign">Add</Button>
          </div>

          <div v-if="usersLoading" class="text-sm text-gray-500">Loading...</div>
          <EmptyState v-else-if="!roleUsers.length" title="Nobody has this role yet" />
          <div v-else class="overflow-hidden rounded-lg border bg-white">
            <table class="w-full text-sm">
              <thead class="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
                <tr>
                  <th class="px-4 py-2">Name</th>
                  <th class="px-4 py-2">Email</th>
                  <th class="px-4 py-2">Type</th>
                  <th class="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in roleUsers" :key="u.name" class="border-b last:border-0">
                  <td class="px-4 py-2.5 font-medium text-gray-900">
                    {{ u.full_name || u.name }}
                    <span v-if="!u.enabled" class="ml-1 text-xs text-gray-500">(disabled)</span>
                  </td>
                  <td class="px-4 py-2.5 text-gray-600">{{ u.name }}</td>
                  <td class="px-4 py-2.5 text-gray-600">{{ u.user_type === 'System User' ? 'Staff' : 'Portal' }}</td>
                  <td class="px-4 py-2.5 text-right">
                    <Button size="sm" variant="ghost" theme="red" @click="unassign(u)">Remove</Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>

    <!-- New role -->
    <Dialog v-model="showNewRole" :options="{ title: 'New Role', size: 'sm' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <ErrorMessage :message="dialogError" />
          <FormControl v-model="newRoleName" label="Role name" placeholder="e.g. Pathways Finance Officer" />
          <p class="text-xs text-gray-500">
            A new role starts with no permissions. Grant it access on the Permissions tab, add it to an Approval Chain to
            make it an approver, then give it to users.
          </p>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :loading="saving" :disabled="!newRoleName.trim()" @click="createRole">Create</Button>
      </template>
    </Dialog>

    <!-- New staff user -->
    <Dialog v-model="showNewUser" :options="{ title: 'New Staff User', size: 'md' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <ErrorMessage :message="dialogError" />
          <FormControl v-model="newUser.email" label="Email" type="email" />
          <div class="grid grid-cols-2 gap-3">
            <FormControl v-model="newUser.first_name" label="First name" />
            <FormControl v-model="newUser.last_name" label="Last name" />
          </div>
          <div>
            <span class="mb-1.5 block text-sm text-gray-700">Roles</span>
            <div class="grid max-h-48 grid-cols-1 gap-1 overflow-y-auto rounded border p-2 sm:grid-cols-2">
              <label v-for="r in staffRoles" :key="r.role" class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="newUser.roles" type="checkbox" :value="r.role" class="rounded border-gray-300" />
                {{ displayRole(r.role) }}
              </label>
            </div>
          </div>
          <p class="text-xs text-gray-500">They'll get an email with a link to set their password.</p>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :loading="saving" @click="createUser">Create User</Button>
      </template>
    </Dialog>

    <Dialog
      v-model="confirmRemoveRole"
      :options="{
        title: 'Remove role from Pathways',
        message: `Remove '${selectedRole}' from Pathways? The role and its permissions are kept in the system and can be added back with New Role.`,
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" theme="red" :loading="saving" @click="removeRole">Remove</Button>
      </template>
    </Dialog>

    <Dialog
      v-model="showResetConfirm"
      :options="{
        title: 'Reset permissions',
        message: `Reset ${resetTarget?.name} to the permissions shipped with Pathways? This affects every role, not just ${selectedRole}.`,
        size: 'sm',
      }"
    >
      <template #actions>
        <Button variant="solid" theme="red" :loading="saving" @click="doReset">Reset</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Autocomplete, Button, Dialog, ErrorMessage, FeatherIcon, FormControl, TabButtons, TextInput } from 'frappe-ui'
import { toast } from '@/utils/notify'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { accessService } from '@/services/access'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()

const matrix = ref(null)
const loading = ref(false)
const loadError = ref('')
const selectedRole = ref('')
const tab = ref('permissions')
const doctypeQuery = ref('')
const onlyGranted = ref(false)
const busy = reactive(new Set())

const roles = computed(() => matrix.value?.roles || [])
const ptypes = computed(() => matrix.value?.ptypes || [])
const selected = computed(() => roles.value.find((r) => r.role === selectedRole.value) || null)
const staffRoles = computed(() => roles.value.filter((r) => r.editable))

function errorText(e, fallback) {
  return e?.messages?.[0] || fallback
}

function displayRole(role) {
  return role.replace(/^Pathways /, '')
}

function ptypeLabel(p) {
  return p.charAt(0).toUpperCase() + p.slice(1)
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    matrix.value = await accessService.getMatrix()
    if (!selected.value && roles.value.length) {
      selectedRole.value = (roles.value.find((r) => r.editable) || roles.value[0]).role
    }
  } catch (e) {
    loadError.value = errorText(e, 'Could not load roles and permissions.')
  } finally {
    loading.value = false
  }
}

onMounted(load)

function selectRole(role) {
  selectedRole.value = role
}

// ----- permissions
function applies(dt, p) {
  if (['submit', 'cancel', 'amend'].includes(p)) return !!dt.is_submittable
  if (['create', 'delete'].includes(p)) return !dt.is_single
  return true
}

function isGranted(doctype, p) {
  return !!matrix.value?.matrix?.[selectedRole.value]?.[doctype]?.[p]
}

function isBusy(doctype) {
  return busy.has(doctype)
}

const visibleDoctypes = computed(() => {
  const q = doctypeQuery.value.trim().toLowerCase()
  return (matrix.value?.doctypes || []).filter((dt) => {
    if (q && !`${dt.name} ${dt.menus.join(' ')}`.toLowerCase().includes(q)) return false
    if (onlyGranted.value && !ptypes.value.some((p) => isGranted(dt.name, p))) return false
    return true
  })
})

async function toggle(doctype, ptype, value) {
  const role = selectedRole.value
  busy.add(doctype)
  try {
    const res = await accessService.setPermission(doctype, role, ptype, value)
    const byRole = matrix.value.matrix[role] || (matrix.value.matrix[role] = {})
    byRole[doctype] = res.perms
    const dt = matrix.value.doctypes.find((d) => d.name === doctype)
    if (dt) dt.customised = true
    // The current user's own menu may have changed.
    session.fetchRoles(true)
  } catch (e) {
    toast({ title: errorText(e, 'Could not update the permission.'), icon: 'alert-triangle', iconClasses: 'text-red-500' })
    await load()
  } finally {
    busy.delete(doctype)
  }
}

const showResetConfirm = ref(false)
const resetTarget = ref(null)

function askReset(dt) {
  resetTarget.value = dt
  showResetConfirm.value = true
}

async function doReset() {
  saving.value = true
  try {
    await accessService.resetDoctype(resetTarget.value.name)
    showResetConfirm.value = false
    toast({ title: `${resetTarget.value.name} reset to default.`, icon: 'check', iconClasses: 'text-green-500' })
    await load()
    session.fetchRoles(true)
  } catch (e) {
    toast({ title: errorText(e, 'Could not reset permissions.'), icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    saving.value = false
  }
}

// ----- users
const roleUsers = ref([])
const usersLoading = ref(false)
const userOptions = ref([])
const userToAdd = ref(null)
const assigning = ref(false)

async function loadUsers() {
  if (!selectedRole.value) return
  usersLoading.value = true
  try {
    roleUsers.value = await accessService.getRoleUsers(selectedRole.value)
  } catch (e) {
    roleUsers.value = []
    toast({ title: errorText(e, 'Could not load users.'), icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    usersLoading.value = false
  }
}

let searchTimer = null
function searchUsers(txt) {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const rows = await accessService.searchUsers(txt || '')
      userOptions.value = rows.map((u) => ({
        label: u.full_name ? `${u.full_name} (${u.name})` : u.name,
        value: u.name,
      }))
    } catch {
      userOptions.value = []
    }
  }, 250)
}

watch([selectedRole, tab], ([, t]) => {
  if (t === 'users') {
    userToAdd.value = null
    loadUsers()
    searchUsers('')
  }
})

function setUserCount(role, count) {
  const r = roles.value.find((x) => x.role === role)
  if (r) r.users = count
}

async function assign() {
  if (!userToAdd.value) return
  assigning.value = true
  try {
    await accessService.assignRole(userToAdd.value.value, selectedRole.value)
    userToAdd.value = null
    await loadUsers()
    setUserCount(selectedRole.value, roleUsers.value.length)
  } catch (e) {
    toast({ title: errorText(e, 'Could not assign the role.'), icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    assigning.value = false
  }
}

async function unassign(u) {
  try {
    await accessService.unassignRole(u.name, selectedRole.value)
    await loadUsers()
    setUserCount(selectedRole.value, roleUsers.value.length)
    if (u.name === session.user) session.fetchRoles(true)
  } catch (e) {
    toast({ title: errorText(e, 'Could not remove the role.'), icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

// ----- roles / users dialogs
const saving = ref(false)
const dialogError = ref('')
const showNewRole = ref(false)
const newRoleName = ref('')
const confirmRemoveRole = ref(false)

function openNewRole() {
  newRoleName.value = ''
  dialogError.value = ''
  showNewRole.value = true
}

async function createRole() {
  saving.value = true
  dialogError.value = ''
  try {
    const role = await accessService.createRole(newRoleName.value.trim())
    showNewRole.value = false
    await load()
    selectedRole.value = role
    tab.value = 'permissions'
  } catch (e) {
    dialogError.value = errorText(e, 'Could not create the role.')
  } finally {
    saving.value = false
  }
}

async function removeRole() {
  saving.value = true
  try {
    await accessService.removeRole(selectedRole.value)
    confirmRemoveRole.value = false
    selectedRole.value = ''
    await load()
    session.fetchRoles(true)
  } catch (e) {
    toast({ title: errorText(e, 'Could not remove the role.'), icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    saving.value = false
  }
}

const showNewUser = ref(false)
const newUser = reactive({ email: '', first_name: '', last_name: '', roles: [] })

function openNewUser() {
  Object.assign(newUser, { email: '', first_name: '', last_name: '', roles: selected.value?.editable ? [selectedRole.value] : [] })
  dialogError.value = ''
  showNewUser.value = true
}

async function createUser() {
  saving.value = true
  dialogError.value = ''
  try {
    await accessService.createStaffUser({ ...newUser, roles: [...newUser.roles] })
    showNewUser.value = false
    toast({ title: 'User created and invited.', icon: 'check', iconClasses: 'text-green-500' })
    await load()
    if (tab.value === 'users') loadUsers()
  } catch (e) {
    dialogError.value = errorText(e, 'Could not create the user.')
  } finally {
    saving.value = false
  }
}
</script>
