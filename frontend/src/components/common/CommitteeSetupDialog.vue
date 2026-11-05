<template>
  <!-- Set up or edit a job's Shortlisting Committee (workflow steps 7-8): members
       with their roles, office order and the shortlisting deadline. Laid out
       like the Selection Committee dialog. -->
  <Dialog :model-value="open" :options="{ title: dialogTitle, size: '2xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div class="flex flex-col gap-5 text-sm">
        <div v-if="state.loading" class="flex flex-col gap-3" aria-busy="true">
          <div v-for="i in 3" :key="i" class="h-14 animate-pulse rounded-xl bg-gray-50" />
        </div>

        <template v-else>
          <p class="text-p-sm text-gray-600">
            The committee shortlists for this job. They get the Shortlisting Committee Member role and
            see only this job's applications.
            <template v-if="state.existing">Members you add are emailed the committee invitation; the others are not emailed again.</template>
            <template v-else>Every member is emailed the committee invitation.</template>
          </p>

          <!-- How many members. The range comes from Settings › General
               (shortlisting committee min/max), like the Selection Committee's panel size. -->
          <div class="grid grid-cols-1 items-end gap-4 rounded-xl border bg-gray-50/60 p-4 sm:grid-cols-[12rem_minmax(0,1fr)]">
            <FormControl
              label="Number of members"
              type="number"
              :min="1"
              :model-value="sizeInput"
              placeholder="e.g. 3"
              @update:model-value="setCommitteeSize"
            />
            <p class="pb-1.5 text-xs" :class="sizeProblem ? 'text-red-600' : 'text-gray-500'">
              {{ sizeProblem || `${state.min}–${state.max} members allowed (Settings › General).` }}
            </p>
          </div>

          <!-- Members: nobody until people are added -->
          <div>
            <div class="mb-2 flex items-center justify-between gap-3">
              <h3 class="text-sm font-semibold text-gray-900">Members</h3>
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium tabular-nums" :class="enough ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'">
                {{ state.members.length }} of {{ committeeSize }}
              </span>
            </div>

            <UserPicker
              :users="state.users"
              :exclude="state.members.map((m) => m.member)"
              :disabled="state.members.length >= committeeSize"
              :placeholder="state.members.length >= committeeSize ? 'Committee is full: choose a larger committee size to add more' : 'Search staff by name or email to add a member'"
              @select="addMember"
            />

            <div v-if="!state.members.length" class="mt-3 flex flex-col items-center gap-1 rounded-xl border border-dashed px-4 py-7 text-center">
              <FeatherIcon name="users" class="h-5 w-5 text-gray-400" />
              <p class="text-sm font-medium text-gray-700">No members yet</p>
              <p class="text-xs text-gray-500">Search above to add {{ committeeSize }} people to the committee.</p>
            </div>

            <ul v-else class="mt-3 divide-y overflow-hidden rounded-xl border">
              <li v-for="(row, i) in state.members" :key="row.member" class="flex flex-wrap items-center gap-3 px-3 py-2.5 sm:flex-nowrap">
                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                  {{ initialsOf(row.member) }}
                </span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-gray-900">
                    {{ nameOf(row.member) }}
                    <span v-if="state.existing && !state.originalMembers.includes(row.member)" class="ml-1 text-xs font-medium text-green-700">· New</span>
                  </p>
                  <p v-if="emailOf(row.member)" class="truncate text-xs text-gray-500">{{ emailOf(row.member) }}</p>
                </div>
                <select
                  v-model="row.designation_label"
                  @change="row.is_external_expert = row.designation_label === EXTERNAL"
                  class="h-8 w-40 shrink-0 rounded-lg border-gray-200 bg-gray-50 py-0 pl-2.5 pr-8 text-sm text-gray-800 focus:border-brand-500 focus:ring-brand-500"
                  :aria-label="`Role of ${nameOf(row.member)}`"
                >
                  <option v-for="r in roleOptions(row.designation_label)" :key="r.value" :value="r.value">{{ r.label }}</option>
                </select>
                <Button variant="ghost" icon="x" :aria-label="`Remove ${nameOf(row.member)}`" title="Remove" @click="state.members.splice(i, 1)" />
              </li>
            </ul>
          </div>

          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <FormControl label="Office Order Reference (optional)" v-model="state.officeOrder" placeholder="e.g. NLSIU/OO/2026/45" />
            <FormControl label="Shortlisting deadline (optional)" type="date" v-model="state.deadline" :min="today" />
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <a v-if="state.attachment" :href="state.attachment" target="_blank" rel="noopener" class="text-xs text-brand-700 hover:underline">
              {{ state.attachment.split('/').pop() }}
            </a>
            <FileUploader
              file-types=".pdf,.jpg,.jpeg,.png"
              :upload-args="uploadArgs"
              @success="(f) => (state.attachment = f.file_url)"
            >
              <template #default="{ openFileSelector, uploading }">
                <Button size="sm" icon-left="paperclip" :loading="uploading" @click="openFileSelector">
                  {{ state.attachment ? 'Replace office order' : 'Upload office order' }}
                </Button>
              </template>
            </FileUploader>
            <Button v-if="state.attachment" size="sm" variant="ghost" @click="state.attachment = ''">Remove</Button>
          </div>
        </template>

        <p v-if="state.error" class="rounded-lg bg-red-50 px-3 py-2 text-red-700" role="alert">{{ state.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="flex items-center gap-1.5 text-sm text-amber-700">
          <template v-if="!state.loading && !enough && !sizeProblem">
            <FeatherIcon name="info" class="h-4 w-4 shrink-0" />
            <template v-if="remaining > 0">Add {{ remaining }} more {{ remaining === 1 ? 'member' : 'members' }} to save.</template>
            <!-- An older committee can be larger than the size now allowed. -->
            <template v-else>Remove {{ -remaining }} {{ remaining === -1 ? 'member' : 'members' }}: at most {{ state.max }} allowed.</template>
          </template>
        </p>
        <div class="flex gap-2">
          <Button variant="ghost" @click="emit('update:open', false)">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="state.saving" :disabled="state.loading || !enough" @click="save">
            {{ state.existing ? 'Save changes' : 'Create committee' }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FileUploader, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import UserPicker from './UserPicker.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { EXTERNAL, roleOptions } from '@/utils/committeeRoles'
import { toast } from '@/utils/notify'
import { scoringService } from '@/services/scoring'

const props = defineProps({
  open: { type: Boolean, default: false },
  jobOpening: { type: String, required: true },
})
const emit = defineEmits(['update:open', 'created', 'updated'])

const today = dayjs().format('YYYY-MM-DD')
const state = reactive({
  loading: false,
  saving: false,
  users: [],
  // [{ member, designation_label, is_external_expert }]
  members: [],
  originalMembers: [],
  min: 2,
  max: 3,
  officeOrder: '',
  deadline: '',
  attachment: '',
  existing: null,
  error: '',
})

const dialogTitle = computed(() => (state.existing ? 'Edit Shortlisting Committee' : 'Set up Shortlisting Committee'))
// Committee size is the target; members are only the people added so far.
const committeeSize = ref(2)
const remaining = computed(() => committeeSize.value - state.members.length)
const enough = computed(() => !sizeProblem.value && state.members.length === committeeSize.value)
// Typed as a number; Settings › General (shortlisting committee min/max)
// decides what can be saved, so a number outside it is explained, not changed.
const sizeInput = ref('2')
function setCommitteeSize(v) {
  sizeInput.value = v
  const n = parseInt(v, 10)
  if (n >= 1) committeeSize.value = n
}
const sizeProblem = computed(() => {
  const n = parseInt(sizeInput.value, 10)
  if (!(n >= 1)) return 'Enter how many members the committee has.'
  if (n < state.min || n > state.max) return `Settings allow ${state.min}–${state.max} members. Ask an administrator to change Settings › General for a ${n}-member committee.`
  if (n < state.members.length) return `${state.members.length} members are added: remove some, or enter a larger number.`
  return ''
})
// The office order is filed with the committee once it exists, with the job before that.
const uploadArgs = computed(() =>
  state.existing
    ? { doctype: 'Shortlisting Committee', docname: state.existing, private: true }
    : { doctype: 'Job Opening', docname: props.jobOpening, private: true },
)

function addMember(user) {
  if (state.members.length >= committeeSize.value || state.members.some((m) => m.member === user.name)) return
  state.members.push({ member: user.name, designation_label: 'Member', is_external_expert: false })
}

const userByName = computed(() => Object.fromEntries(state.users.map((u) => [u.name, u])))
const nameOf = (name) => userByName.value[name]?.full_name || name
function emailOf(name) {
  const email = userByName.value[name]?.email || name
  return email !== nameOf(name) ? email : ''
}
function initialsOf(name) {
  const words = nameOf(name).replace(/@.*/, '').split(/[\s._-]+/).filter(Boolean)
  return words.slice(0, 2).map((w) => w[0].toUpperCase()).join('') || '?'
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    Object.assign(state, { loading: true, members: [], originalMembers: [], officeOrder: '', deadline: '', attachment: '', existing: null, error: '' })
    try {
      const [options, committee] = await Promise.all([
        scoringService.getCommitteeOptions(),
        scoringService.getShortlistingCommittee(props.jobOpening),
      ])
      Object.assign(state, { users: options.users, min: options.min, max: options.max })
      if (committee) {
        Object.assign(state, {
          existing: committee.name,
          members: committee.member_rows.map((m) => ({
            member: m.member,
            // An external member saved without a role shows as External expert.
            designation_label: m.designation_label || (m.is_external_expert ? EXTERNAL : 'Member'),
            is_external_expert: !!m.is_external_expert,
          })),
          originalMembers: [...committee.members],
          officeOrder: committee.office_order_reference || '',
          deadline: committee.shortlisting_deadline || '',
          attachment: committee.office_order_attachment || '',
        })
      }
      // Editing keeps the committee's own size; a new one starts at the minimum.
      setCommitteeSize(String(state.members.length > state.max ? state.members.length : Math.max(state.members.length, state.min)))
    } catch (e) {
      state.error = e?.messages?.[0] || 'Could not load staff.'
    } finally {
      state.loading = false
    }
  },
)

async function save() {
  if (state.saving || !enough.value) return
  state.saving = true
  state.error = ''
  const members = state.members.map((m) => ({
    member: m.member,
    designation_label: (m.designation_label || '').trim(),
    is_external_expert: m.is_external_expert ? 1 : 0,
  }))
  const extra = {
    shortlisting_deadline: state.deadline || null,
    office_order_attachment: state.attachment || null,
  }
  try {
    if (state.existing) {
      const res = await scoringService.updateShortlistingCommittee(props.jobOpening, {
        members,
        office_order_reference: state.officeOrder,
        ...extra,
      })
      emit('update:open', false)
      const added = res?.added?.length || 0
      toast({
        title: added ? `Committee updated. ${added} new member${added === 1 ? '' : 's'} emailed.` : 'Committee updated.',
        icon: 'check',
        iconClasses: 'text-green-500',
      })
      emit('updated')
    } else {
      await scoringService.createShortlistingCommittee(props.jobOpening, members, state.officeOrder, extra)
      emit('update:open', false)
      toast({ title: 'Shortlisting Committee created.', icon: 'check', iconClasses: 'text-green-500' })
      emit('created')
    }
  } catch (e) {
    state.error = e?.messages?.[0] || 'Could not save the committee.'
  } finally {
    state.saving = false
  }
}
</script>
