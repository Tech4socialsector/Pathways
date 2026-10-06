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
        class="flex h-full max-h-[92vh] w-full max-w-7xl flex-col overflow-hidden rounded-xl bg-[#1c1a33] text-white shadow-2xl outline-none"
      >
        <!-- Header -->
        <div class="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-3.5">
          <h2 class="truncate text-base font-bold">{{ title }}</h2>
          <div class="flex shrink-0 items-center gap-2">
            <a
              v-if="downloadAllUrl && documents.length"
              :href="downloadAllUrl"
              class="flex items-center gap-1.5 rounded-md bg-indigo-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-400"
            >
              <FeatherIcon name="download" class="h-4 w-4" />
              <span class="hidden sm:inline">Download All (PDF)</span>
            </a>
            <button class="rounded-md p-1.5 text-white/70 hover:bg-white/10 hover:text-white" aria-label="Close" @click="close">
              <FeatherIcon name="x" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <div class="flex min-h-0 flex-1 flex-col md:flex-row">
          <!-- Document list -->
          <aside class="flex max-h-56 shrink-0 flex-col border-b border-white/10 md:max-h-none md:w-80 md:border-b-0 md:border-r">
            <div class="flex items-center justify-between px-4 py-3">
              <div>
                <div class="text-sm font-bold">Documents</div>
                <div class="text-xs text-white/60">{{ documents.length }} document{{ documents.length === 1 ? '' : 's' }}</div>
              </div>
              <span class="rounded-full bg-indigo-500/30 px-2 py-0.5 text-xs font-bold text-indigo-200">{{ documents.length }}</span>
            </div>
            <div v-if="loading" class="px-4 py-3 text-sm text-white/60">Loading...</div>
            <div v-else-if="!documents.length" class="px-4 py-3 text-sm text-white/60">No documents uploaded.</div>
            <ul v-else class="flex-1 overflow-y-auto px-2 pb-3">
              <li v-for="(doc, idx) in documents" :key="doc.file_url + idx" class="mb-1.5">
                <div
                  class="group flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition"
                  :class="
                    idx === selected
                      ? 'border-indigo-400 bg-indigo-500/25'
                      : 'border-transparent hover:border-white/10 hover:bg-white/5'
                  "
                  @click="selected = idx"
                >
                  <span
                    class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md"
                    :class="idx === selected ? 'bg-indigo-500' : 'bg-red-500/20 text-red-300'"
                  >
                    <FeatherIcon :name="doc.kind === 'image' ? 'image' : 'file-text'" class="h-4 w-4" />
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-sm font-bold" :title="doc.label">{{ doc.label }}</div>
                    <div class="text-xs text-white/50">Document {{ idx + 1 }}</div>
                  </div>
                  <a
                    :href="doc.file_url"
                    :download="doc.file_name"
                    class="rounded-md border border-white/15 bg-white/10 p-1.5 text-white/80 hover:bg-white/20"
                    :aria-label="`Download ${doc.label}`"
                    @click.stop
                  >
                    <FeatherIcon name="download" class="h-3.5 w-3.5" />
                  </a>
                  <FeatherIcon name="chevron-right" class="h-4 w-4 text-white/40" />
                </div>
              </li>
            </ul>
          </aside>

          <!-- Preview -->
          <section class="flex min-h-0 flex-1 flex-col bg-[#2a2840]">
            <div v-if="current" class="flex items-center gap-3 border-b border-white/10 px-4 py-2.5 text-sm">
              <span class="text-[11px] font-bold uppercase tracking-wider text-white/50">Document preview</span>
              <span class="truncate font-medium">{{ current.label }}</span>
              <span class="ml-auto hidden truncate text-xs text-white/40 lg:inline">{{ current.file_name }}</span>
              <a :href="current.file_url" target="_blank" rel="noopener" class="text-white/60 hover:text-white" aria-label="Open in new tab">
                <FeatherIcon name="external-link" class="h-4 w-4" />
              </a>
            </div>
            <div class="flex min-h-0 flex-1 items-center justify-center overflow-auto">
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
                class="max-h-full max-w-full bg-white object-contain p-2"
              />
              <div v-else-if="current" class="p-8 text-center text-sm text-white/70">
                <FeatherIcon name="file" class="mx-auto mb-3 h-10 w-10 text-white/40" />
                This file type cannot be previewed.
                <a :href="current.file_url" :download="current.file_name" class="mt-3 block font-medium text-indigo-300 hover:underline">
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
})
const emit = defineEmits(['update:open'])

const selected = ref(0)
const panel = ref(null)
const current = computed(() => props.documents[selected.value])

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    selected.value = 0
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
