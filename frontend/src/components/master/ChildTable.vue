<template>
  <div :data-field="field.fieldname">
    <div class="mb-2 flex items-center justify-between gap-3">
      <span class="text-sm font-medium text-gray-700">
        {{ field.label }}<span v-if="required" class="text-red-600" aria-hidden="true"> *</span>
        <span class="ml-1 font-normal tabular-nums text-gray-500">({{ rows.length }})</span>
      </span>
    </div>

    <p v-if="error" class="mb-2 text-sm text-red-600" role="alert">{{ error }}</p>

    <div v-if="!rows.length" class="rounded-lg border border-dashed px-4 py-6 text-center text-p-sm text-gray-500">
      No {{ field.label.toLowerCase() }} yet.
    </div>

    <ol v-else class="flex flex-col gap-3">
      <li v-for="(row, i) in rows" :key="row.__key || row.name" class="rounded-lg border bg-gray-50/70">
        <div class="flex items-center justify-between gap-2 border-b bg-white/60 px-4 py-2">
          <span class="text-sm font-semibold text-gray-700">{{ rowTitle(row, i) }}</span>
          <div v-if="!readOnly" class="flex items-center gap-0.5">
            <Button variant="ghost" icon="arrow-up" :disabled="i === 0" :aria-label="`Move row ${i + 1} up`" title="Move up" @click="move(i, -1)" />
            <Button variant="ghost" icon="arrow-down" :disabled="i === rows.length - 1" :aria-label="`Move row ${i + 1} down`" title="Move down" @click="move(i, 1)" />
            <Button variant="ghost" theme="red" icon="trash-2" :aria-label="`Remove row ${i + 1}`" title="Remove" @click="remove(i)" />
          </div>
        </div>
        <div class="grid grid-cols-1 gap-x-5 gap-y-4 p-4 md:grid-cols-2 xl:grid-cols-3">
          <MasterField
            v-for="cf in visibleFields(row)"
            :key="cf.fieldname"
            :class="isWide(cf) && 'md:col-span-2 xl:col-span-3'"
            :field="cf"
            :path="`${field.fieldname}.${i}.${cf.fieldname}`"
            :model-value="row[cf.fieldname]"
            :required="isRequired(cf, row, parentDoc)"
            :read-only="readOnly || isReadOnly(cf, row, parentDoc)"
            :error="errors[`${field.fieldname}.${i}.${cf.fieldname}`] || ''"
            @update:model-value="(v) => emit('set-row-value', i, cf.fieldname, v)"
          />
        </div>
      </li>
    </ol>

    <Button v-if="!readOnly" class="mt-3" icon-left="plus" @click="add">Add {{ rowNoun }}</Button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'
import MasterField from './MasterField.vue'
import { TEXT_TYPES, hasValue, isReadOnly, isRequired, isVisible } from '@/utils/masterForm'

const props = defineProps({
  field: { type: Object, required: true },
  childFields: { type: Array, required: true },
  rows: { type: Array, required: true },
  parentDoc: { type: Object, required: true },
  required: { type: Boolean, default: false },
  readOnly: { type: Boolean, default: false },
  error: { type: String, default: '' },
  errors: { type: Object, default: () => ({}) },
})
// The form owns the record; the table only asks for changes.
const emit = defineEmits(['add-row', 'remove-row', 'move-row', 'set-row-value'])

const valueFields = computed(() => props.childFields.filter(hasValue))
const visibleFields = (row) => valueFields.value.filter((cf) => isVisible(cf, row, props.parentDoc))
const isWide = (cf) => TEXT_TYPES.includes(cf.fieldtype) || cf.fieldtype === 'Text Editor'

// "Screening Questions" -> "question", "Steps" -> "step".
const rowNoun = computed(() => {
  const words = props.field.label.toLowerCase().split(' ')
  const last = words.pop() || 'row'
  return [...words, last.endsWith('s') ? last.slice(0, -1) : last].join(' ')
})

// "Row 2 · Registrar" — the first filled text value helps tell rows apart.
function rowTitle(row, i) {
  const first = valueFields.value.find((cf) => ['Data', 'Link', 'Small Text'].includes(cf.fieldtype) && row[cf.fieldname])
  const text = first ? String(row[first.fieldname]).replace(/\s+/g, ' ').trim() : ''
  return text ? `${i + 1}. ${text.length > 60 ? `${text.slice(0, 60)}…` : text}` : `Row ${i + 1}`
}

const add = () => emit('add-row')
const remove = (i) => emit('remove-row', i)
const move = (i, delta) => emit('move-row', i, delta)
</script>
