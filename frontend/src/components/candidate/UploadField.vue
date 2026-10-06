<template>
  <div>
    <div class="mb-1.5 text-sm text-gray-700">
      {{ label }}<span v-if="required" class="text-red-500">*</span>
    </div>
    <p v-if="hint" class="mb-1.5 text-xs text-gray-500">{{ hint }}</p>
    <FileUploader
      :file-types="accept"
      :upload-args="{ private: true }"
      :validate-file="validate"
      @success="(file) => emit('update:modelValue', file.file_url)"
    >
      <template #default="{ uploading, progress, error, openFileSelector }">
        <div class="flex flex-wrap items-center gap-2">
          <template v-if="modelValue">
            <span class="flex items-center gap-1.5 rounded bg-green-50 px-2 py-1 text-sm text-green-800">
              <FeatherIcon name="check" class="h-3.5 w-3.5" />
              {{ fileName }}
            </span>
            <Button size="sm" variant="ghost" :loading="uploading" @click="openFileSelector">Replace</Button>
            <Button size="sm" variant="ghost" @click="emit('update:modelValue', '')">Remove</Button>
          </template>
          <Button v-else size="sm" :loading="uploading" @click="openFileSelector">
            <template #prefix><FeatherIcon name="upload" class="h-3.5 w-3.5" /></template>
            {{ uploading ? `Uploading ${progress}%` : 'Upload file' }}
          </Button>
          <span class="text-xs text-gray-500">{{ ruleText }}</span>
        </div>
        <div v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</div>
      </template>
    </FileUploader>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button, FeatherIcon, FileUploader } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, required: true },
  required: { type: Boolean, default: false },
  hint: { type: String, default: '' },
  rule: { type: Object, default: () => ({ formats: ['pdf', 'jpg', 'jpeg', 'png'], max_size_mb: 5 }) },
})
const emit = defineEmits(['update:modelValue'])

const accept = computed(() => (props.rule.formats || []).map((f) => `.${f}`).join(','))
const ruleText = computed(
  () => `${(props.rule.formats || []).map((f) => f.toUpperCase()).join(', ')} · max ${props.rule.max_size_mb} MB`,
)
const fileName = computed(() => decodeURIComponent((props.modelValue || '').split('/').pop()))

// UX only — the server re-checks owner, format and size on submit.
function validate(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (props.rule.formats?.length && !props.rule.formats.includes(ext)) {
    return `Allowed formats: ${props.rule.formats.map((f) => f.toUpperCase()).join(', ')}`
  }
  if (props.rule.max_size_mb && file.size > props.rule.max_size_mb * 1024 * 1024) {
    return `File is larger than ${props.rule.max_size_mb} MB`
  }
  return null
}
</script>
