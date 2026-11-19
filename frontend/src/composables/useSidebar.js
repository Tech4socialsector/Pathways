import { ref } from 'vue'

// Phone menu drawer: opened by the top bar's menu button, rendered by
// RoleAwareSidebar. Module-level so both share it without prop drilling.
const mobileOpen = ref(false)

export function useSidebar() {
  return {
    mobileOpen,
    openMobile: () => (mobileOpen.value = true),
    closeMobile: () => (mobileOpen.value = false),
  }
}
