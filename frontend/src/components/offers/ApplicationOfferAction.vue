<template>
  <!-- ApplicationDetail's Offer card: open the offer, or start one for a
       candidate on an approved Post-Interview Green Sheet. -->
  <div v-if="info" class="mt-2">
    <RouterLink v-if="info.offer" :to="`/offers/${info.offer.name}`" class="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline">
      Open offer <FeatherIcon name="arrow-right" class="h-3 w-3" />
    </RouterLink>
    <Button v-else-if="info.can_create" size="sm" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="open = true">Create offer</Button>
    <p v-else-if="info.blocked_reason" class="text-xs text-gray-500">{{ info.blocked_reason }}</p>
    <CreateOfferDialog v-model="open" :application="application" @created="(name) => router.push(`/offers/${name}`)" />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import CreateOfferDialog from '@/components/offers/CreateOfferDialog.vue'
import { offerService } from '@/services/offers'
import { BTN_BRAND } from '@/utils/buttonStyles'

const props = defineProps({ application: { type: String, required: true } })
const router = useRouter()
const info = ref(null)
const open = ref(false)

async function load() {
  try {
    info.value = await offerService.getOfferForApplication(props.application)
  } catch {
    info.value = null
  }
}

onMounted(load)
watch(() => props.application, load)
</script>
