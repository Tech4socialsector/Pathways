<template>
  <!-- Signed-in candidates: a left menu (a drawer on phones) and a slim top
       bar with the notification bell. Everyone else: the top bar below.
       The page itself scrolls (no inner scroll area), so the browser has one
       scrollbar and scrollIntoView / window.scrollTo behave. -->
  <div v-if="sidebar" class="flex min-h-full bg-gray-50">
    <aside class="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-t-4 border-t-brand-700 bg-white md:flex" aria-label="Portal menu">
      <PortalMenu />
    </aside>

    <!-- Phones: the same menu as a drawer -->
    <Transition enter-from-class="opacity-0" enter-active-class="transition-opacity duration-200" leave-to-class="opacity-0" leave-active-class="transition-opacity duration-150">
      <div v-if="drawerOpen" class="fixed inset-0 z-40 bg-gray-900/40 md:hidden" aria-hidden="true" @click="drawerOpen = false" />
    </Transition>
    <Transition enter-from-class="-translate-x-full" enter-active-class="transition-transform duration-200" leave-to-class="-translate-x-full" leave-active-class="transition-transform duration-150">
      <aside
        v-if="drawerOpen"
        id="portal-drawer"
        class="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-t-4 border-t-brand-700 bg-white shadow-xl md:hidden"
        aria-label="Portal menu"
      >
        <button type="button" class="absolute right-3 top-4 rounded-md p-1.5 text-gray-500 hover:bg-gray-100" aria-label="Close menu" @click="drawerOpen = false">
          <FeatherIcon name="x" class="h-5 w-5" />
        </button>
        <PortalMenu />
      </aside>
    </Transition>

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b bg-white/95 px-4 backdrop-blur md:px-6">
        <div class="flex min-w-0 items-center gap-2">
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md text-gray-700 hover:bg-gray-100 md:hidden"
            aria-controls="portal-drawer"
            :aria-expanded="drawerOpen"
            aria-label="Open menu"
            @click="drawerOpen = true"
          >
            <FeatherIcon name="menu" class="h-5 w-5" />
          </button>
          <router-link to="/portal/applications" class="flex items-center gap-2 md:hidden">
            <span class="flex h-8 w-8 items-center justify-center rounded-md bg-brand-700 font-heading font-bold text-white">N</span>
            <span class="font-heading font-bold text-gray-900">NLSIU Careers</span>
          </router-link>
          <span class="hidden truncate font-heading text-base font-semibold text-gray-900 md:block">{{ pageTitle }}</span>
        </div>
        <NotificationBell />
      </header>
      <main class="flex-1">
        <slot />
      </main>
      <footer class="border-t bg-white">
        <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-5 text-xs text-gray-500">
          <span>© {{ year }} National Law School of India University, Bengaluru</span>
          <span>Powered by Azim Premji Foundation - TFSS</span>
          <a href="https://www.nls.ac.in" target="_blank" rel="noopener" class="hover:text-brand-700">www.nls.ac.in</a>
        </div>
      </footer>
    </div>
  </div>

  <div v-else class="flex min-h-full flex-col bg-gray-50">
    <header class="sticky top-0 z-20 border-t-4 border-brand-700 bg-white/95 shadow-sm backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
        <router-link to="/portal/jobs" class="flex min-w-0 items-center gap-3">
          <img v-if="appearance.app_logo" :src="appearance.app_logo" alt="" class="h-9 w-9 shrink-0 rounded-md object-contain" />
          <span v-else class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-brand-700 font-heading text-lg font-bold text-white">
            N
          </span>
          <span class="min-w-0">
            <span class="block truncate font-heading text-lg font-bold leading-tight text-gray-900">NLSIU Careers</span>
            <span class="hidden truncate text-xs text-gray-500 sm:block">National Law School of India University</span>
          </span>
        </router-link>
        <!-- Desktop navigation -->
        <nav class="hidden items-center gap-1 text-sm md:flex">
          <router-link
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="relative whitespace-nowrap rounded-md px-3 py-2 font-medium transition-colors"
            :class="isActive(link.to) ? 'text-brand-700' : 'text-gray-600 hover:text-gray-900'"
          >
            {{ link.label }}
            <span v-if="isActive(link.to)" class="absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full bg-brand-700" />
          </router-link>
          <template v-if="session.isLoggedIn">
            <NotificationBell v-if="session.isCandidate && isDesktop" class="ml-2" />
            <!-- The signed-in person: Change password and Log out -->
            <div ref="userRoot" class="relative ml-1">
              <button
                type="button"
                class="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 text-gray-700 transition hover:bg-gray-100"
                :class="userOpen && 'bg-gray-100'"
                :aria-expanded="userOpen"
                aria-haspopup="menu"
                @click="userOpen = !userOpen"
              >
                <span class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-700 text-xs font-bold text-white">{{ initials }}</span>
                <span class="max-w-[10rem] truncate font-medium">{{ firstName }}</span>
                <FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-400 transition" :class="userOpen && 'rotate-180'" />
              </button>
              <div v-if="userOpen" class="absolute right-0 top-11 z-50 w-64 overflow-hidden rounded-xl border bg-white py-1 shadow-xl" role="menu">
                <div class="border-b px-4 py-3">
                  <div class="truncate text-sm font-semibold text-gray-900">{{ session.fullName }}</div>
                  <div class="truncate text-xs text-gray-500">{{ maskedEmail }}</div>
                </div>
                <router-link
                  v-if="session.isCandidate"
                  to="/portal/change-password"
                  class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
                  :class="route.path === '/portal/change-password' && 'font-medium text-brand-700'"
                  role="menuitem"
                  @click="userOpen = false"
                >
                  <FeatherIcon name="lock" class="h-4 w-4 text-gray-400" />Change password
                </router-link>
                <button
                  type="button"
                  class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50"
                  role="menuitem"
                  @click="(userOpen = false), (confirmLogout = true)"
                >
                  <FeatherIcon name="log-out" class="h-4 w-4 text-gray-400" />Log out
                </button>
              </div>
            </div>
          </template>
          <a
            v-else
            :href="loginUrl"
            class="ml-1 whitespace-nowrap rounded-md border border-brand-200 px-3 py-1.5 font-semibold text-brand-700 hover:bg-brand-50"
          >
            Log in
          </a>
        </nav>

        <!-- Phones: Log in stays visible; everything else is in a menu. -->
        <div class="flex shrink-0 items-center gap-2 md:hidden">
          <NotificationBell v-if="session.isLoggedIn && session.isCandidate && !isDesktop" />
          <a
            v-if="!session.isLoggedIn"
            :href="loginUrl"
            class="whitespace-nowrap rounded-md border border-brand-200 px-3 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
          >
            Log in
          </a>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md text-gray-700 hover:bg-gray-100"
            :aria-expanded="menuOpen"
            aria-controls="portal-menu"
            :aria-label="menuOpen ? 'Close menu' : 'Open menu'"
            @click="menuOpen = !menuOpen"
          >
            <FeatherIcon :name="menuOpen ? 'x' : 'menu'" class="h-5 w-5" />
          </button>
        </div>
      </div>

      <nav v-if="menuOpen" id="portal-menu" class="border-t bg-white px-4 py-2 md:hidden">
        <div v-if="session.isLoggedIn" class="flex items-center gap-3 border-b px-3 pb-3 pt-1">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-700 text-sm font-bold text-white">{{ initials }}</span>
          <span class="min-w-0">
            <span class="block truncate text-sm font-semibold text-gray-900">{{ session.fullName }}</span>
            <span class="block truncate text-xs text-gray-500">{{ maskedEmail }}</span>
          </span>
        </div>
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="flex items-center justify-between rounded-md px-3 py-2.5 text-base font-medium"
          :class="isActive(link.to) ? 'bg-brand-50 text-brand-700' : 'text-gray-700 hover:bg-gray-50'"
        >
          {{ link.label }}
          <FeatherIcon name="chevron-right" class="h-4 w-4 opacity-50" />
        </router-link>
        <router-link
          v-if="session.isCandidate"
          to="/portal/change-password"
          class="flex items-center justify-between rounded-md px-3 py-2.5 text-base font-medium"
          :class="route.path === '/portal/change-password' ? 'bg-brand-50 text-brand-700' : 'text-gray-700 hover:bg-gray-50'"
        >
          Change password
          <FeatherIcon name="chevron-right" class="h-4 w-4 opacity-50" />
        </router-link>
        <button
          v-if="session.isLoggedIn"
          type="button"
          class="flex w-full items-center rounded-md px-3 py-2.5 text-left text-base font-medium text-gray-700 hover:bg-gray-50"
          @click="(menuOpen = false), (confirmLogout = true)"
        >
          Log out
        </button>
      </nav>
    </header>

    <main class="flex-1">
      <slot />
    </main>
    <footer class="border-t bg-white">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-5 text-xs text-gray-500">
        <span>© {{ year }} National Law School of India University, Bengaluru</span>
        <span>Powered by Azim Premji Foundation - TFSS</span>
        <a href="https://www.nls.ac.in" target="_blank" rel="noopener" class="hover:text-brand-700">www.nls.ac.in</a>
      </div>
    </footer>
  </div>

  <Dialog v-model="confirmLogout" :options="{ title: 'Log out?', size: 'sm' }">
    <template #body-content>
      <p class="text-sm text-gray-600">You'll need your username and password to log in again.</p>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="confirmLogout = false">Cancel</Button>
        <Button variant="solid" :class="BTN_BRAND" :loading="session.logout.loading" @click="session.logout.submit()">Log out</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, defineComponent, h, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import NotificationBell from '@/components/candidate/NotificationBell.vue'
import { Button, Dialog, FeatherIcon } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { RouterLink, useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { appearance } from '@/utils/theme'

const session = useSessionStore()
// The left menu is for signed-in candidates; guests applying keep the top bar.
const sidebar = computed(() => session.isLoggedIn && session.isCandidate)
const drawerOpen = ref(false)
watch(drawerOpen, (open) => (document.body.style.overflow = open ? 'hidden' : ''))
const confirmLogout = ref(false)
const route = useRoute()
const loginUrl = computed(() => `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`)
const year = new Date().getFullYear()

// Phone menu and the user menu; both close on navigation.
const menuOpen = ref(false)
const userOpen = ref(false)
const userRoot = ref(null)
watch(() => route.fullPath, () => ((menuOpen.value = false), (userOpen.value = false), (drawerOpen.value = false)))
function onDocClick(e) {
  if (userOpen.value && userRoot.value && !userRoot.value.contains(e.target)) userOpen.value = false
}
function onKey(e) {
  if (e.key !== 'Escape') return
  userOpen.value = false
  drawerOpen.value = false
}
// One bell at a time (it polls): in the desktop bar or beside the phone menu.
const desktopQuery = window.matchMedia('(min-width: 768px)')
const isDesktop = ref(desktopQuery.matches)
const onWidth = (e) => (isDesktop.value = e.matches)
onMounted(() => {
  desktopQuery.addEventListener('change', onWidth)
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  desktopQuery.removeEventListener('change', onWidth)
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})

const initials = computed(() => {
  const parts = String(session.fullName || session.user || '?').trim().split(/\s+/)
  return ((parts[0]?.[0] || '') + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase() || '?'
})
const firstName = computed(() => String(session.fullName || '').trim().split(/\s+/)[0] || 'Account')
// n*******a@gmail.com: the menu is often seen on a shared screen.
const maskedEmail = computed(() => {
  const [local = '', domain = ''] = String(session.user || '').split('@')
  if (!domain) return local
  return local.length > 2 ? `${local[0]}${'*'.repeat(Math.min(local.length - 2, 8))}${local.slice(-1)}@${domain}` : `${local[0] || ''}*@${domain}`
})

// Signed-in candidates see their own pages first; Openings comes last.
const links = computed(() => [
  ...(session.isLoggedIn ? [{ to: '/portal/applications', label: 'My Applications' }] : []),
  { to: '/portal/jobs', label: 'Openings' },
])

function isActive(to) {
  return route.path === to || route.path.startsWith(`${to}/`)
}

// ----- left menu (signed-in candidates)
const MENU = [
  { to: '/portal/applications', label: 'My Applications', icon: 'file-text' },
  { to: '/portal/jobs', label: 'Openings', icon: 'briefcase' },
  { to: '/portal/change-password', label: 'Change password', icon: 'lock' },
]
const pageTitle = computed(() => MENU.find((m) => isActive(m.to))?.label || 'NLSIU Careers')

// The menu's content, shared by the sidebar and the phone drawer.
const PortalMenu = defineComponent({
  setup() {
    return () =>
      h('div', { class: 'flex h-full flex-col' }, [
        h(RouterLink, { to: '/portal/applications', class: 'flex items-center gap-3 px-5 py-4' }, () => [
          appearance.app_logo
            ? h('img', { src: appearance.app_logo, alt: '', class: 'h-9 w-9 shrink-0 rounded-md object-contain' })
            : h('span', { class: 'flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-brand-700 font-heading text-lg font-bold text-white' }, 'N'),
          h('span', { class: 'min-w-0' }, [
            h('span', { class: 'block truncate font-heading text-base font-bold leading-tight text-gray-900' }, 'NLSIU Careers'),
            h('span', { class: 'block truncate text-[11px] text-gray-500' }, 'Candidate portal'),
          ]),
        ]),
        h(
          'nav',
          { class: 'flex flex-1 flex-col gap-1 px-3 py-2' },
          MENU.map((m) =>
            h(
              RouterLink,
              {
                to: m.to,
                class: [
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition',
                  isActive(m.to) ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                ],
                'aria-current': isActive(m.to) ? 'page' : undefined,
              },
              () => [h(FeatherIcon, { name: m.icon, class: 'h-4 w-4 shrink-0' }), m.label],
            ),
          ),
        ),
        h('div', { class: 'border-t p-3' }, [
          h('div', { class: 'flex items-center gap-3 px-2 py-2' }, [
            h('span', { class: 'flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-700 text-xs font-bold text-white' }, initials.value),
            h('span', { class: 'min-w-0' }, [
              h('span', { class: 'block truncate text-sm font-semibold text-gray-900' }, session.fullName),
              h('span', { class: 'block truncate text-xs text-gray-500' }, maskedEmail.value),
            ]),
          ]),
          h(
            'button',
            {
              type: 'button',
              class: 'mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-gray-600 transition hover:bg-red-50 hover:text-red-700',
              onClick: () => ((drawerOpen.value = false), (confirmLogout.value = true)),
            },
            [h(FeatherIcon, { name: 'log-out', class: 'h-4 w-4 shrink-0' }), 'Log out'],
          ),
        ]),
      ])
  },
})
</script>
