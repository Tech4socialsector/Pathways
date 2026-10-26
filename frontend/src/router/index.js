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
    path: '/candidates',
    name: 'Candidates',
    component: () => import('@/pages/Candidates.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/candidates/:id',
    name: 'CandidateDetail',
    component: () => import('@/pages/CandidateDetail.vue'),
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
    path: '/selection-green-sheets/:id',
    name: 'PostGreenSheetDetail',
    component: () => import('@/pages/PostGreenSheetDetail.vue'),
    props: true,
    // Part of Selection (step 3); approvers without Selection reach it from My Approvals.
    meta: { requiresStaff: true, sections: ['/selection', '/approvals'] },
  },
  {
    path: '/interviews',
    name: 'Interviews',
    component: () => import('@/pages/Interviews.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/panel',
    name: 'InterviewPanel',
    component: () => import('@/pages/InterviewPanel.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/panel/documents',
    name: 'SharedDocuments',
    component: () => import('@/pages/SharedDocuments.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/honorarium',
    name: 'Honorarium',
    component: () => import('@/pages/Honorarium.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/selection',
    name: 'Selection',
    component: () => import('@/pages/Selection.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/selection/:job',
    name: 'SelectionJob',
    component: () => import('@/pages/SelectionJob.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    // Panellists' read-only score sheet. The recruitment team decides in
    // Selection, so their old links land there.
    beforeEnter(to) {
      if (useSessionStore().hasMenu('selection')) return { path: `/selection/${to.params.job}` }
      return true
    },
    path: '/panel/sheet/:job',
    name: 'ConsolidatedScores',
    component: () => import('@/pages/ConsolidatedScores.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    path: '/panel/:interview',
    name: 'InterviewAssessment',
    component: () => import('@/pages/InterviewAssessment.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    path: '/offers',
    name: 'Offers',
    component: () => import('@/pages/Offers.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/offers/:id',
    name: 'OfferDetail',
    component: () => import('@/pages/OfferDetail.vue'),
    props: true,
    meta: { requiresStaff: true },
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/pages/Documents.vue'),
    meta: { requiresStaff: true },
    // Onboarding verification moved to the Onboarding module.
    beforeEnter: (to) => (to.query.tab === 'onboarding' ? '/onboarding/verification' : true),
  },
  // Onboarding: verification, joinings and IT requests as tabs of one module.
  {
    path: '/onboarding/:tab?',
    name: 'Onboarding',
    component: () => import('@/pages/Onboarding.vue'),
    meta: { requiresStaff: true },
  },
  // The lists' old addresses (also in emails already sent).
  { path: '/joinings', redirect: '/onboarding/joinings' },
  { path: '/it-requests', redirect: '/onboarding/it-requests' },
  {
    path: '/joinings/:id',
    name: 'JoiningDetail',
    component: () => import('@/pages/JoiningDetail.vue'),
    props: true,
    meta: { requiresStaff: true, sections: ['/onboarding'] },
  },
  {
    path: '/master-setup',
    name: 'MasterSetup',
    component: () => import('@/pages/MasterSetup.vue'),
    meta: { requiresStaff: true },
  },
  // Department and Designation were renamed to "Pathways …" (ERPNext owns the
  // bare names); keep old bookmarks working.
  ...['department', 'designation'].flatMap((old) => [
    { path: `/master-setup/${old}`, redirect: `/master-setup/pathways-${old}` },
    {
      path: `/master-setup/${old}/:mode(new|edit)/:name?`,
      redirect: (to) => ({ name: 'MasterForm', params: { ...to.params, slug: `pathways-${old}` } }),
    },
  ]),
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
    path: '/communications',
    name: 'CommunicationLog',
    component: () => import('@/pages/CommunicationLog.vue'),
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
    // Public: the referee is not a user; the token is checked server-side.
    path: '/referee/:token',
    name: 'RefereeForm',
    component: () => import('@/pages/RefereeForm.vue'),
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
    window.location.href = `/login?redirect-to=${encodeURIComponent('/pathways' + to.fullPath)}`
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
