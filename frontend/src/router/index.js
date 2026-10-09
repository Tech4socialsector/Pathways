import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/jobs',
    name: 'JobOpenings',
    component: () => import('@/pages/JobOpenings.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/jobs/:id',
    name: 'JobOpeningDetail',
    component: () => import('@/pages/JobOpeningDetail.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    path: '/applications',
    name: 'Applications',
    component: () => import('@/pages/Applications.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/applications/:id',
    name: 'ApplicationDetail',
    component: () => import('@/pages/ApplicationDetail.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    path: '/approvals',
    name: 'Approvals',
    component: () => import('@/pages/Approvals.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/interviews',
    name: 'Interviews',
    component: () => import('@/pages/Interviews.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/offers',
    name: 'Offers',
    component: () => import('@/pages/Offers.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/pages/Documents.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/master-setup',
    name: 'MasterSetup',
    component: () => import('@/pages/MasterSetup.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/master-setup/:slug',
    name: 'MasterList',
    component: () => import('@/pages/MasterList.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    // One record for /new and /edit/<name>: see newRoute() in utils/masterForm.js.
    path: '/master-setup/:slug/:mode(new|edit)/:name?',
    name: 'MasterForm',
    component: () => import('@/pages/MasterForm.vue'),
    props: (route) => ({ slug: route.params.slug, mode: route.params.mode, name: route.params.name || '' }),
    meta: { requiresStaff: true },
  },
  {
    path: '/settings/email',
    name: 'EmailSetup',
    component: () => import('@/pages/settings/EmailSetup.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/settings/access',
    name: 'RolesPermissions',
    component: () => import('@/pages/settings/RolesPermissions.vue'),
    meta: { requiresStaff: true, requiresAccessManager: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/pages/Reports.vue'),
    meta: { requiresStaff: true },
  },
  // Candidate portal
  {
    path: '/portal',
    name: 'CandidatePortal',
    redirect: '/portal/applications',
  },
  {
    path: '/portal/jobs',
    name: 'PublicJobBoard',
    component: () => import('@/pages/candidate-portal/JobBoard.vue'),
  },
  {
    path: '/portal/jobs/:id',
    name: 'JobPosting',
    component: () => import('@/pages/candidate-portal/JobPosting.vue'),
    props: true,
  },
  {
    path: '/portal/jobs/:id/apply',
    name: 'ApplyForm',
    component: () => import('@/pages/candidate-portal/ApplyForm.vue'),
    props: true,
  },
  {
    path: '/portal/applications',
    name: 'MyApplications',
    component: () => import('@/pages/candidate-portal/MyApplications.vue'),
    meta: { requiresCandidate: true },
  },
  {
    path: '/portal/applications/:id',
    name: 'MyApplicationStatus',
    component: () => import('@/pages/candidate-portal/ApplicationStatus.vue'),
    props: true,
    meta: { requiresCandidate: true },
  },
  {
    path: '/portal/profile',
    name: 'MyProfile',
    component: () => import('@/pages/candidate-portal/MyProfile.vue'),
    meta: { requiresCandidate: true },
  },
  {
    path: '/portal/change-password',
    name: 'ChangePassword',
    component: () => import('@/pages/candidate-portal/ChangePassword.vue'),
    meta: { requiresCandidate: true },
  },
  {
    path: '/login',
    name: 'Login',
    beforeEnter() {
      window.location.href = '/login?redirect-to=/pathways'
    },
  },
]

const router = createRouter({
  history: createWebHistory('/pathways'),
  routes,
})

router.beforeEach(async (to) => {
  const session = useSessionStore()

  if (!session.isLoggedIn && (to.meta.requiresStaff || to.meta.requiresCandidate)) {
    window.location.href = `/login?redirect-to=/pathways${to.fullPath}`
    return false
  }

  if (session.isLoggedIn && !session.rolesLoaded) {
    await session.fetchRoles()
  }

  if (session.mustChangePassword && to.name !== 'ChangePassword') {
    return { name: 'ChangePassword', query: { next: to.fullPath } }
  }

  if (to.meta.requiresStaff && !session.isStaff) {
    return { path: '/portal/applications' }
  }

  // UX only — every Roles & Permissions endpoint is System Manager-only server-side.
  if (to.meta.requiresAccessManager && !session.canManageAccess) {
    return { path: '/' }
  }

  return true
})

// After a new build, an open tab still points at the old page files, which
// no longer exist, so opening a page fails silently. Load the page fresh.
router.onError((error, to) => {
  const message = String(error?.message || error)
  if (/Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i.test(message)) {
    window.location.assign(`/pathways${to.fullPath}`)
  }
})

export default router
