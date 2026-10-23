<template>
  <!-- Workflow step 3: where the advertisement went live (filled in by Communications),
       the LinkedIn share button and the public job feeds. -->
  <SectionCard title="Publishing" icon="globe" subtitle="NLSIU website, LinkedIn and Indeed">
    <template #actions>
      <a v-if="linkedinShareUrl" :href="linkedinShareUrl" target="_blank" rel="noopener">
        <Button size="sm" variant="outline" icon-left="linkedin">Share on LinkedIn</Button>
      </a>
      <Button v-if="data?.can_edit_publishing && !editing" size="sm" variant="ghost" icon-left="edit-2" @click="startEdit">Edit</Button>
    </template>

    <div v-if="loading && !data" class="text-sm text-gray-500">Loading...</div>
    <div v-else-if="data" class="flex flex-col gap-5 text-sm">
      <template v-if="!editing">
        <ul class="flex flex-col divide-y divide-gray-100">
          <li v-for="c in CHANNELS" :key="c.key" class="flex flex-wrap items-center justify-between gap-2 py-2.5 first:pt-0">
            <div class="flex min-w-0 items-center gap-2.5">
              <span
                class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
                :class="p[`${c.key}_url`] ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-400'"
              >
                <FeatherIcon :name="p[`${c.key}_url`] ? 'check' : c.icon" class="h-3.5 w-3.5" />
              </span>
              <div class="min-w-0">
                <div class="font-medium text-gray-900">{{ c.label }}</div>
                <a
                  v-if="p[`${c.key}_url`]"
                  :href="p[`${c.key}_url`]"
                  target="_blank"
                  rel="noopener"
                  class="block truncate text-xs text-brand-700 hover:underline"
                >
                  {{ p[`${c.key}_url`] }}
                </a>
                <div v-else class="text-xs text-gray-500">Not published yet</div>
              </div>
            </div>
            <span v-if="p[`${c.key}_published_on`]" class="text-xs text-gray-500">{{ formatDate(p[`${c.key}_published_on`]) }}</span>
          </li>
        </ul>
        <p v-if="p.published_by" class="text-xs text-gray-500">Recorded by {{ p.published_by_name || p.published_by }}</p>
      </template>

      <div v-else class="flex flex-col gap-3">
        <div v-for="c in CHANNELS" :key="c.key" class="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_11rem]">
          <FormControl :label="`${c.label} link`" v-model="form[`${c.key}_url`]" :placeholder="c.placeholder" />
          <FormControl label="Published on" type="date" v-model="form[`${c.key}_published_on`]" />
        </div>
        <ErrorMessage :message="error" />
        <div class="flex gap-2">
          <Button variant="solid" :class="BTN_BRAND" :loading="saving" @click="save">Save</Button>
          <Button variant="ghost" @click="editing = false">Cancel</Button>
        </div>
      </div>

      <!-- Feeds: Indeed and the website read the open jobs from these. -->
      <div class="rounded-lg bg-gray-50 px-3 py-2.5">
        <div class="mb-1 text-xs font-bold uppercase tracking-wide text-brand-700">Job feeds</div>
        <p class="mb-2 text-xs text-gray-600">Open (Advertised) jobs only, public fields only. Give these links to Indeed and the website team once.</p>
        <div v-for="f in feeds" :key="f.label" class="flex items-center justify-between gap-2 py-1">
          <span class="min-w-0">
            <span class="text-xs font-medium text-gray-700">{{ f.label }}</span>
            <a :href="f.url" target="_blank" rel="noopener" class="block truncate text-xs text-brand-700 hover:underline">{{ f.url }}</a>
          </span>
          <Button size="sm" variant="ghost" icon="copy" :aria-label="`Copy ${f.label} link`" @click="copy(f.url)" />
        </div>
      </div>
    </div>
  </SectionCard>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Button, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import dayjs from 'dayjs'
import SectionCard from '@/components/common/SectionCard.vue'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { jobNoticeService } from '@/services/jobNotice'

const props = defineProps({ job: { type: Object, required: true } })

const CHANNELS = [
  { key: 'website', label: 'NLSIU website', icon: 'globe', placeholder: 'https://www.nls.ac.in/...' },
  { key: 'linkedin', label: 'LinkedIn', icon: 'linkedin', placeholder: 'https://www.linkedin.com/posts/...' },
  { key: 'indeed', label: 'Indeed', icon: 'briefcase', placeholder: 'https://in.indeed.com/viewjob?jk=...' },
]
const FIELDS = CHANNELS.flatMap((c) => [`${c.key}_url`, `${c.key}_published_on`])

const data = ref(null)
const loading = ref(false)
const p = computed(() => data.value?.publishing || {})

async function load() {
  loading.value = true
  try {
    data.value = await jobNoticeService.getNotice(props.job.name)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.job.name, load)

// LinkedIn's share-offsite dialog for the public posting (only while Advertised).
const linkedinShareUrl = computed(() =>
  props.job.advertisement_url
    ? `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(props.job.advertisement_url)}`
    : '',
)
const feeds = [
  { label: 'Indeed XML feed', url: `${window.location.origin}/jobs-feed.xml` },
  { label: 'Website JSON feed', url: `${window.location.origin}/jobs-feed.json` },
]

const editing = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive(Object.fromEntries(FIELDS.map((f) => [f, ''])))

function startEdit() {
  for (const f of FIELDS) form[f] = p.value[f] || ''
  error.value = ''
  editing.value = true
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    data.value = await jobNoticeService.savePublishing(props.job.name, { ...form })
    editing.value = false
    toast({ title: 'Publishing details saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not save the publishing details.'
  } finally {
    saving.value = false
  }
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast({ title: 'Link copied.', icon: 'check', iconClasses: 'text-green-500' })
  } catch {
    toast({ title: 'Could not copy. Select the link and copy it.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

function formatDate(value) {
  return value ? dayjs(value).format('DD MMM YYYY') : ''
}
</script>
