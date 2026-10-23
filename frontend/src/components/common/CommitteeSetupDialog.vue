<template>
  <!-- Set up or edit a job's Shortlisting Committee (workflow steps 7-8): members,
       office order and the shortlisting deadline. -->
  <Dialog :model-value="open" :options="{ title: dialogTitle, size: 'lg' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-gray-600">
          Pick {{ state.min }}–{{ state.max }} members who will shortlist for this job. They get the Shortlisting Committee
          Member role and see only this job's applications.
          <template v-if="state.existing">Members you add are emailed the committee invitation; the others are not emailed again.</template>
        </p>
        <div v-if="state.loading" class="text-sm text-gray-500">Loading staff...</div>
        <div v-else class="max-h-64 overflow-y-auto rounded-lg border">
          <label
            v-for="u in state.users"
            :key="u.name"
            class="flex cursor-pointer items-center gap-3 border-b px-3 py-2 text-sm last:border-0 hover:bg-gray-50"
          >
            <input
              v-model="state.members"
              type="checkbox"
              :value="u.name"
              :disabled="!state.members.includes(u.name) && state.members.length >= state.max"
              class="rounded border-gray-300"
            />
            <span class="flex-1">
              <span class="font-medium text-gray-900">{{ u.full_name || u.name }}</span>
              <span class="block text-xs text-gray-500">{{ u.name }}</span>
            </span>
            <span v-if="state.existing && !state.originalMembers.includes(u.name) && state.members.includes(u.name)" class="text-xs font-medium text-green-700">
              New
            </span>
          </label>
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
        <ErrorMessage :message="state.error" />
      </div>
    </template>
    <template #actions>
      <Button variant="solid" :class="BTN_BRAND" :loading="state.saving" :disabled="state.members.length < state.min" @click="save">
        <template v-if="state.existing">Save changes ({{ state.members.length }} members)</template>
        <template v-else>Create committee ({{ state.members.length }} selected)</template>
      </Button>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FileUploader, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import { BTN_BRAND } from '@/utils/buttonStyles'
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
// The office order is filed with the committee once it exists, with the job before that.
const uploadArgs = computed(() =>
  state.existing
    ? { doctype: 'Shortlisting Committee', docname: state.existing, private: true }
    : { doctype: 'Job Opening', docname: props.jobOpening, private: true },
)

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
          members: [...committee.members],
          originalMembers: [...committee.members],
          officeOrder: committee.office_order_reference || '',
          deadline: committee.shortlisting_deadline || '',
          attachment: committee.office_order_attachment || '',
        })
        // Members who are no longer offered (e.g. disabled) stay visible.
        for (const m of committee.members) {
          if (!state.users.some((u) => u.name === m)) state.users.push({ name: m, full_name: m })
        }
      }
    } catch (e) {
      state.error = e?.messages?.[0] || 'Could not load staff.'
    } finally {
      state.loading = false
    }
  },
)

async function save() {
  state.saving = true
  state.error = ''
  const extra = {
    shortlisting_deadline: state.deadline || null,
    office_order_attachment: state.attachment || null,
  }
  try {
    if (state.existing) {
      const res = await scoringService.updateShortlistingCommittee(props.jobOpening, {
        members: state.members,
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
      await scoringService.createShortlistingCommittee(props.jobOpening, state.members, state.officeOrder, extra)
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
