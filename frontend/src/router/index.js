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

  if (to.meta.requiresStaff && !session.isStaff) {
    return { path: '/portal/applications' }
  }

  return true
})

export default router
