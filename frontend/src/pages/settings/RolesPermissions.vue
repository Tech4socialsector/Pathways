<template>
  <StaffLayout>
    <PageHeader
      title="Roles & Permissions"
      subtitle="Choose what each Pathways role can see and do, and who holds each role."
    >
      <template #actions>
        <Button @click="panel?.openNewUser()">
          <template #prefix><FeatherIcon name="user-plus" class="h-4 w-4" /></template>
          New Staff User
        </Button>
        <Button variant="solid" @click="panel?.openNewRole()">
          <template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
          New Role
        </Button>
      </template>
    </PageHeader>

    <RolesPermissionsPanel ref="panel" />
  </StaffLayout>
</template>

<script setup>
// The main entry point is the Roles & Permissions tab in Settings; this page
// keeps old links to /settings/access working.
import { ref } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import RolesPermissionsPanel from '@/components/settings/RolesPermissionsPanel.vue'

const panel = ref(null)
</script>
