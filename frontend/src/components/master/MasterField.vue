<template>
  <div :class="error && 'field-invalid'" :data-field="path">
    <!-- Checkboxes carry their label beside the box, like the desk form. -->
    <label v-if="field.fieldtype === 'Check'" class="flex cursor-pointer items-start gap-2.5 py-1" :class="readOnly && 'cursor-not-allowed opacity-70'">
      <input
        type="checkbox"
        class="mt-px h-4 w-4 shrink-0 rounded border-gray-300 text-brand-700 focus:ring-brand-500"
        :checked="Boolean(modelValue)"
        :disabled="readOnly"
        @change="emit('update:modelValue', $event.target.checked ? 1 : 0)"
      />
      <span class="text-base text-gray-800">{{ field.label }}</span>
    </label>

    <template v-else>
      <component :is="wrapsInLabel ? 'label' : 'div'" class="block">
        <span class="mb-1.5 block text-sm font-medium text-gray-700">
          {{ field.label }}<span v-if="required" class="text-red-600" aria-hidden="true"> *</span>
        </span>

        <LinkField
          v-if="field.fieldtype === 'Link'"
          :doctype="field.options"
          :label="field.label"
          :model-value="modelValue || null"
          :disabled="readOnly"
          @update:model-value="(v) => emit('update:modelValue', v)"
        />

        <FormControl
          v-else-if="field.fieldtype === 'Select'"
          type="select"
          :options="selectOptions"
          :model-value="modelValue ?? ''"
          :disabled="readOnly"
          :required="required"
          @update:model-value="(v) => emit('update:modelValue', v === '' ? null : v)"
        />

        <FormControl
          v-else-if="TEXT_TYPES.includes(field.fieldtype)"
          type="textarea"
          :rows="field.fieldtype === 'Small Text' ? 3 : 5"
          :model-value="modelValue ?? ''"
          :disabled="readOnly"
          :required="required"
          @update:model-value="(v) => emit('update:modelValue', v)"
        />

        <TextEditor
          v-else-if="field.fieldtype === 'Text Editor'"
          :content="modelValue || ''"
          :editable="!readOnly"
          :fixed-menu="true"
          editor-class="prose-sm max-w-none min-h-[10rem] px-3 py-2"
          class="rounded border border-gray-300 bg-white"
          @change="(html) => emit('update:modelValue', html)"
        />

        <TextInput
          v-else-if="NUMBER_TYPES.includes(field.fieldtype)"
          type="number"
          :step="field.fieldtype === 'Int' ? 1 : 'any'"
          :min="field.fieldtype === 'Percent' ? 0 : undefined"
          :max="field.fieldtype === 'Percent' ? 100 : undefined"
          :model-value="modelValue ?? ''"
          :disabled="readOnly"
          :required="required"
          @update:model-value="(v) => emit('update:modelValue', v)"
        />

        <TextInput
          v-else-if="field.fieldtype === 'Date'"
          type="date"
          :model-value="modelValue ?? ''"
          :disabled="readOnly"
          :required="required"
          @update:model-value="(v) => emit('update:modelValue', v || null)"
        />

        <TextInput
          v-else
          type="text"
          :maxlength="field.length || 140"
          :model-value="modelValue ?? ''"
          :disabled="readOnly"
          :required="required"
          @update:model-value="(v) => emit('update:modelValue', v)"
        />
      </component>
    </template>

    <p v-if="error" class="mt-1 text-sm text-red-600" role="alert">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-p-sm text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FormControl, TextEditor, TextInput } from 'frappe-ui'
import LinkField from './LinkField.vue'
import { NUMBER_TYPES, TEXT_TYPES } from '@/utils/masterForm'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Boolean], default: null },
  required: { type: Boolean, default: false },
  readOnly: { type: Boolean, default: false },
  error: { type: String, default: '' },
  // Extra help shown under the field (e.g. why it is locked).
  note: { type: String, default: '' },
  // "fieldname" or "table.row.fieldname": lets the form scroll to an error.
  path: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

// A <label> wrapper focuses the input when its caption is clicked. Link and
// Text Editor render their own popover / toolbar, so they get a plain div.
const wrapsInLabel = computed(() => !['Link', 'Text Editor'].includes(props.field.fieldtype))

const hint = computed(() => props.note || props.field.description || '')

// A blank first choice unless the DocType already has one, so a required
// Select is never silently set to its first option.
const selectOptions = computed(() => {
  const values = (props.field.options || []).map((o) => (o == null ? '' : String(o)))
  const opts = values.filter((v) => v !== '').map((v) => ({ label: v, value: v }))
  const blank = { label: props.required ? `Select ${props.field.label}` : '—', value: '' }
  // Keep an unknown saved value visible rather than showing a different one.
  const current = props.modelValue == null ? '' : String(props.modelValue)
  if (current && !values.includes(current)) opts.unshift({ label: current, value: current })
  return [blank, ...opts]
})
</script>
