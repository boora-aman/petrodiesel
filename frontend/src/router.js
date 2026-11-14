import { createRouter, createWebHistory } from 'vue-router'
import { session, loadBoot } from './session'

const routes = [
  { path: '/login', name: 'Login', component: () => import('./pages/Login.vue'), meta: { public: true } },
  { path: '/', name: 'Home', component: () => import('./pages/Home.vue') },
  { path: '/shifts', name: 'Shifts', component: () => import('./pages/ShiftList.vue') },
  { path: '/shifts/new', name: 'ShiftNew', component: () => import('./pages/ShiftForm.vue') },
  { path: '/shifts/:name', name: 'Shift', component: () => import('./pages/ShiftForm.vue'), props: true },
  { path: '/tankers', name: 'Tankers', component: () => import('./pages/TankerList.vue') },
  { path: '/tankers/new', name: 'TankerNew', component: () => import('./pages/TankerForm.vue') },
  { path: '/tankers/:name', name: 'Tanker', component: () => import('./pages/TankerForm.vue'), props: true },
  { path: '/dips', name: 'Dips', component: () => import('./pages/DipList.vue') },
  { path: '/dips/new', name: 'DipNew', component: () => import('./pages/DipForm.vue') },
  { path: '/dips/:name', name: 'Dip', component: () => import('./pages/DipForm.vue'), props: true },
  { path: '/dsr', name: 'DsrList', component: () => import('./pages/DsrList.vue') },
  { path: '/dsr/new', name: 'DsrNew', component: () => import('./pages/DsrForm.vue') },
  { path: '/dsr/:name', name: 'Dsr', component: () => import('./pages/DsrForm.vue'), props: true },
  { path: '/pump-tests', name: 'PumpTests', component: () => import('./pages/PumpTestList.vue') },
  { path: '/pump-tests/new', name: 'PumpTestNew', component: () => import('./pages/PumpTestForm.vue') },
  { path: '/pump-tests/:name', name: 'PumpTest', component: () => import('./pages/PumpTestForm.vue'), props: true },
  { path: '/prices', name: 'Prices', component: () => import('./pages/Prices.vue') },
  { path: '/credit', name: 'Credit', component: () => import('./pages/CreditList.vue') },
  { path: '/credit/:customer', name: 'Customer', component: () => import('./pages/CustomerDetail.vue'), props: true },
  { path: '/advances', name: 'Advances', component: () => import('./pages/Advances.vue') },
  { path: '/credit-bills', name: 'CreditBills', component: () => import('./pages/CreditBillList.vue') },
  { path: '/credit-bills/new', name: 'CreditBillNew', component: () => import('./pages/CreditBillForm.vue') },
  { path: '/credit-bills/:name', name: 'CreditBill', component: () => import('./pages/CreditBillForm.vue'), props: true },
  { path: '/purchases', name: 'Purchases', component: () => import('./pages/ShopPurchaseList.vue') },
  { path: '/purchases/new', name: 'PurchaseNew', component: () => import('./pages/ShopPurchaseForm.vue') },
  { path: '/purchases/:name', name: 'Purchase', component: () => import('./pages/ShopPurchaseForm.vue'), props: true },
  { path: '/transfers', name: 'Transfers', component: () => import('./pages/TransferList.vue') },
  { path: '/transfers/new', name: 'TransferNew', component: () => import('./pages/TransferForm.vue') },
  { path: '/transfers/:name', name: 'Transfer', component: () => import('./pages/TransferForm.vue'), props: true },
  { path: '/approvals', name: 'Approvals', component: () => import('./pages/Approvals.vue') },
  { path: '/reports', name: 'Reports', component: () => import('./pages/Reports.vue') },
  { path: '/reports/:report', name: 'Report', component: () => import('./pages/ReportView.vue'), props: true },
  { path: '/alerts', name: 'Alerts', component: () => import('./pages/Alerts.vue') },
  { path: '/setup', name: 'Setup', component: () => import('./pages/Setup.vue') },
  { path: '/more', name: 'More', component: () => import('./pages/More.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory('/petrodiesel'), routes, scrollBehavior: () => ({ top: 0 }) })

router.beforeEach(async (to) => {
  if (!session.ready) await loadBoot()
  if (!to.meta.public && !session.loggedIn) return { name: 'Login', query: { redirect: to.fullPath } }
  if (to.name === 'Login' && session.loggedIn) return { name: 'Home' }
})

export default router
