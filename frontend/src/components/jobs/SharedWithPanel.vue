<template>
  <!-- Workflow step 7: the job's department folder, and colleagues tagged on the job.
       Tagged colleagues can read this job's applications and documents. -->
  <SectionCard title="Folder & Sharing" icon="share-2">
    <div v-if="loading && !data" class="text-sm text-gray-500">Loading...</div>
    <div v-else-if="data" class="flex flex-col gap-5 text-sm">
      <div>
        <div class="mb-1.5 text-xs font-bold uppercase tracking-wide text-brand-700">Department folder</div>
        <div v-if="data.files_folder" class="flex items-start gap-2">
          <FeatherIcon name="folder" class="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />
          <a :href="data.folder_link" target="_blank" rel="noopener" class="break-all text-gray-800 hover:text-brand-700 hover:underline">
            {{ data.files_folder }}
          </a>
        </div>
        <div v-else class="flex items-center justify-between gap-2 text-gray-500">
          No folder yet.
          <Button v-if="data.can_edit" size="sm" variant="outline" icon-left="folder-plus" :loading="creatingFolder" @click="createFolder">
            Create folder
          </Button>
        </div>
      </div>

      <div>
        <div class="mb-1.5 flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wide text-brand-700">Shared with · {{ data.shared_with.length }}</span>
        </div>
        <p v-if="!data.shared_with.length" class="text-gray-500">Nobody tagged. Tagged colleagues can read this job's applications and documents.</p>
        <ul v-else class="flex flex-col gap-2">
          <li v-for="c in data.shared_with" :key="c.user" class="flex items-start gap-2.5 rounded-lg border border-gray-200 px-3 py-2">
            <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[11px] font-bold text-brand-700">
              {{ (c.full_name || c.user)[0] }}
            </span>
            <div class="min-w-0 flex-1">
              <div class="truncate font-medium text-gray-900">{{ c.full_name || c.user }}</div>
              <div v-if="c.access_note" class="text-xs text-gray-600">{{ c.access_note }}</div>
              <div v-if="c.tagged_by" class="text-xs text-gray-400">Tagged by {{ c.tagged_by }}<template v-if="c.tagged_on"> · {{ formatDate(c.tagged_on) }}</template></div>
            </div>
            <Button
              v-if="data.can_edit"
              size="sm"
              variant="ghost"
              icon="x"
              :aria-label="`Remove ${c.full_name || c.user}`"
              :loading="saving === c.user"
              @click="remove(c.user)"
            />
          </li>
        </ul>

        <div v-if="data.can_edit" class="mt-3 flex flex-col gap-2 rounded-lg bg-gray-50 p-3">
          <div class="text-xs font-medium text-gray-700">Tag a colleague</div>
          <div v-if="picked" class="flex items-center justify-between rounded-md border bg-white px-2.5 py-1.5">
            <span class="truncate font-medium text-gray-900">{{ picked.full_name || picked.name }}</span>
            <Button size="sm" variant="ghost" icon="x" aria-label="Clear" @click="picked = null" />
          </div>
          <UserPicker v-else :users="data.users" :exclude="data.shared_with.map((c) => c.user)" placeholder="Search staff..." @select="(u) => (picked = u)" />
          <FormControl v-model="note" placeholder="Access note (optional), e.g. Head of department: review CVs" />
          <ErrorMessage :message="error" />
          <Button variant="solid" size="sm" :class="BTN_BRAND" :disabled="!picked" :loading="saving === 'add'" @click="add">
            Tag and notify
          </Button>
        </div>
      </div>
    </div>
  </SectionCard>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { Button, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import UserPicker from '@/components/common/UserPicker.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { jobOpeningService } from '@/services/jobOpenings'

const props = defineProps({ job: { type: Object, required: true } })

const data = ref(null)
const loading = ref(false)
const saving = ref('')
const error = ref('')
const picked = ref(null)
const note = ref('')
const creatingFolder = ref(false)

async function load() {
  loading.value = true
  try {
    data.value = await jobOpeningService.getSharing(props.job.name)
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.job.name, load)

const current = () => data.value.shared_with.map((c) => ({ user: c.user, access_note: c.access_note || '' }))

async function save(colleagues, key) {
  saving.value = key
  error.value = ''
  try {
    data.value = await jobOpeningService.setColleagues(props.job.name, colleagues)
    return true
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not update who this job is shared with.'
    return false
  } finally {
    saving.value = ''
  }
}

async function add() {
  const user = picked.value
  if (!user) return
  if (await save([...current(), { user: user.name, access_note: note.value }], 'add')) {
    toast({ title: `${user.full_name || user.name} tagged and notified.`, icon: 'check', iconClasses: 'text-green-500' })
    picked.value = null
    note.value = ''
  }
}

async function remove(user) {
  if (await save(current().filter((c) => c.user !== user), user)) {
    toast({ title: 'Access removed.', icon: 'check', iconClasses: 'text-green-500' })
  }
}

async function createFolder() {
  creatingFolder.value = true
  try {
    data.value = await jobOpeningService.ensureFolder(props.job.name)
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not create the folder.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    creatingFolder.value = false
  }
}

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}
</script>
