<template>
  <StaffLayout>
    <PageHeader title="Master Setup" subtitle="Manage the master records used across the recruitment platform." />
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-sm text-gray-500">Loading...</div>

      <EmptyState
        v-else-if="isPermissionError"
        title="You don't have access to Master Setup"
        description="Ask a Pathways administrator if you need to manage master records."
      />

      <EmptyState v-else-if="error" title="Could not load Master Setup" :description="errorMessage">
        <template #action>
          <Button @click="fetchMasterSetup">Try again</Button>
        </template>
      </EmptyState>

      <template v-else>
        <div class="mb-6 max-w-md">
          <TextInput v-model="query" type="text" placeholder="Search master setup...">
            <template #prefix>
              <FeatherIcon name="search" class="h-4 w-4 text-gray-500" />
            </template>
          </TextInput>
        </div>

        <EmptyState
          v-if="!filteredCategories.length"
          title="No masters match your search"
          :description="`Nothing found for “${query}”.`"
        />

        <section v-for="category in filteredCategories" :key="category.key" class="mb-8">
          <div class="mb-3 text-xs font-semibold uppercase text-gray-500">{{ category.label }}</div>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
            <div
              v-for="master in category.masters"
              :key="master.doctype"
              class="flex flex-col rounded-lg border bg-white transition-colors hover:border-gray-400"
            >
              <a :href="master.route" class="flex flex-1 flex-col p-4">
                <div class="mb-3 flex h-8 w-8 items-center justify-center rounded bg-gray-100">
                  <FeatherIcon :name="master.icon" class="h-4 w-4 text-gray-700" />
                </div>
                <div class="text-sm font-semibold text-gray-900">{{ master.label }}</div>
                <div class="mt-0.5 text-sm text-gray-500">{{ master.description }}</div>
              </a>

              <div v-if="master.total" class="flex items-center justify-between border-t px-4 py-2.5 text-xs">
                <a :href="master.route" class="flex flex-1 items-center justify-between text-gray-600">
                  <span>
                    {{ pluralise(master.total, 'record') }}
                    <span v-if="master.inactive" class="text-gray-500">&middot; {{ master.inactive }} inactive</span>
                  </span>
                  <FeatherIcon name="arrow-right" class="h-4 w-4 text-gray-500" />
                </a>
              </div>
              <div v-else class="flex flex-wrap items-center justify-between gap-2 border-t px-4 py-2.5 text-xs text-gray-500">
                <span>No {{ master.label }} found.</span>
                <Button v-if="master.can_create" size="sm" @click="goTo(master.new_route)">
                  <template #prefix><FeatherIcon name="plus" class="h-3.5 w-3.5" /></template>
                  Add {{ master.singular }}
                </Button>
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, FeatherIcon, TextInput } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useMasterSetup } from '@/composables/useMasterSetup'

const { categories, loading, error, fetchMasterSetup } = useMasterSetup()

onMounted(fetchMasterSetup)

const isPermissionError = computed(() => error.value?.exc_type === 'PermissionError' || error.value?.status === 403)

// Server messages are user-facing frappe.throw text; anything else
// (network failure, 500) gets a generic line instead of raw details.
const errorMessage = computed(() =>
  error.value?.status && error.value.status < 500 && error.value.messages?.[0]
    ? error.value.messages[0]
    : 'Something went wrong while loading master records. Please try again.',
)

const query = ref('')

function matches(master, category, q) {
  return [master.label, master.singular, master.description, master.doctype, category.label, ...master.keywords]
    .join(' ')
    .toLowerCase()
    .includes(q)
}

const filteredCategories = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return categories.value
  return categories.value
    .map((category) => ({ ...category, masters: category.masters.filter((m) => matches(m, category, q)) }))
    .filter((category) => category.masters.length)
})

function pluralise(count, word) {
  return `${count} ${word}${count === 1 ? '' : 's'}`
}

function goTo(href) {
  window.location.href = href
}
</script>
