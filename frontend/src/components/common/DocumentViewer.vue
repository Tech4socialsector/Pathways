<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-2 sm:p-6"
      @click.self="close"
      @keydown="onKey"
    >
      <div
        ref="panel"
        tabindex="-1"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        class="flex h-full max-h-[92vh] w-full max-w-7xl flex-col overflow-hidden rounded-xl bg-white text-gray-900 shadow-2xl outline-none"
      >
        <!-- Header -->
        <div class="flex items-center justify-between gap-3 bg-brand-700 px-5 py-3.5 text-white">
          <h2 class="flex min-w-0 items-center gap-2 text-base font-bold">
            <FeatherIcon name="folder" class="h-4 w-4 shrink-0" /><span class="truncate">{{ title }}</span>
          </h2>
          <div class="flex shrink-0 items-center gap-2">
            <a
              v-if="downloadAllUrl && documents.length"
              :href="downloadAllUrl"
              class="flex items-center gap-1.5 rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              <FeatherIcon name="download" class="h-4 w-4" />
              <span class="hidden sm:inline">Download All (PDF)</span>
            </a>
            <button class="rounded-md p-1.5 text-white/80 hover:bg-white/15 hover:text-white" aria-label="Close" @click="close">
              <FeatherIcon name="x" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <div class="flex min-h-0 flex-1 flex-col md:flex-row">
          <!-- Document list -->
          <aside class="flex max-h-56 shrink-0 flex-col border-b border-gray-200 bg-white md:max-h-none md:w-80 md:border-b-0 md:border-r">
            <div class="flex items-center justify-between px-4 py-3">
              <div>
                <div class="text-sm font-bold text-gray-900">Documents</div>
                <div class="text-xs text-gray-500">{{ documents.length }} document{{ documents.length === 1 ? '' : 's' }}</div>
              </div>
              <span class="rounded-full bg-brand-700 px-2 py-0.5 text-xs font-bold text-white">{{ documents.length }}</span>
            </div>
            <div v-if="loading" class="px-4 py-3 text-sm text-gray-500">Loading...</div>
            <div v-else-if="!documents.length" class="px-4 py-3 text-sm text-gray-500">No documents uploaded.</div>
            <ul v-else class="flex-1 overflow-y-auto px-2 pb-3">
              <li v-for="(doc, idx) in documents" :key="doc.file_url + idx" class="mb-1.5">
                <div
                  class="group flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition"
                  :class="
                    idx === selected
                      ? 'border-brand-200 bg-brand-50'
                      : 'border-transparent hover:border-gray-200 hover:bg-gray-50'
                  "
                  @click="selected = idx"
                >
                  <span
                    class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md"
                    :class="idx === selected ? 'bg-brand-700 text-white' : 'bg-gray-100 text-gray-600'"
                  >
                    <FeatherIcon :name="doc.kind === 'image' ? 'image' : 'file-text'" class="h-4 w-4" />
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-sm font-bold" :class="idx === selected ? 'text-brand-700' : 'text-gray-900'" :title="doc.label">{{ doc.label }}</div>
                    <div class="text-xs text-gray-500">Document {{ idx + 1 }}</div>
                  </div>
                  <a
                    :href="doc.file_url"
                    :download="doc.file_name"
                    class="rounded-md border border-gray-200 bg-white p-1.5 text-gray-600 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"
                    :aria-label="`Download ${doc.label}`"
                    @click.stop
                  >
                    <FeatherIcon name="download" class="h-3.5 w-3.5" />
                  </a>
                  <FeatherIcon name="chevron-right" class="h-4 w-4 text-gray-400" />
                </div>
              </li>
            </ul>
          </aside>

          <!-- Preview -->
          <section class="flex min-h-0 flex-1 flex-col bg-gray-50">
            <div v-if="current" class="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-2.5 text-sm">
              <span class="text-[11px] font-bold uppercase tracking-wider text-gray-500">Document preview</span>
              <span class="truncate font-semibold text-gray-900">{{ current.label }}</span>
              <span class="ml-auto hidden truncate text-xs text-gray-500 lg:inline">{{ current.file_name }}</span>
              <a :href="current.file_url" target="_blank" rel="noopener" class="text-gray-500 hover:text-brand-700" aria-label="Open in new tab">
                <FeatherIcon name="external-link" class="h-4 w-4" />
              </a>
            </div>
            <div class="flex min-h-0 flex-1 items-center justify-center overflow-auto p-4">
              <iframe
                v-if="current?.kind === 'pdf'"
                :key="current.file_url"
                :src="`${current.file_url}#view=FitH`"
                :title="current.label"
                class="h-full w-full bg-white"
              />
              <img
                v-else-if="current?.kind === 'image'"
                :key="current.file_url"
                :src="current.file_url"
                :alt="current.label"
                class="max-h-full max-w-full rounded-lg border border-gray-200 bg-white object-contain p-2 shadow-sm"
              />
              <div v-else-if="current" class="p-8 text-center text-sm text-gray-600">
                <FeatherIcon name="file" class="mx-auto mb-3 h-10 w-10 text-gray-400" />
                This file type cannot be previewed.
                <a :href="current.file_url" :download="current.file_name" class="mt-3 block font-medium text-brand-700 hover:underline">
                  Download {{ current.file_name }}
                </a>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Documents' },
  // [{ label, file_url, file_name, kind: 'pdf' | 'image' | 'other' }]
  documents: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  downloadAllUrl: { type: String, default: '' },
  // Which document to show first.
  startIndex: { type: Number, default: 0 },
})
const emit = defineEmits(['update:open'])

const selected = ref(0)
const panel = ref(null)
const current = computed(() => props.documents[selected.value])

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    selected.value = Math.min(Math.max(props.startIndex, 0), Math.max(props.documents.length - 1, 0))
    await nextTick()
    panel.value?.focus()
  },
)

function close() {
  emit('update:open', false)
}

function onKey(e) {
  if (e.key === 'Escape') close()
  else if (e.key === 'ArrowDown' && selected.value < props.documents.length - 1) selected.value++
  else if (e.key === 'ArrowUp' && selected.value > 0) selected.value--
  else return
  e.preventDefault()
}
</script>
