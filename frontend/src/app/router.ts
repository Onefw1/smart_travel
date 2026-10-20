import { createRouter, createWebHashHistory, type RouteLocationNormalized } from 'vue-router'
import { useSessionStore } from '../features/auth/session-store'
import AuthPage from '../features/auth/pages/AuthPage.vue'
import AccountPage from '../features/auth/pages/AccountPage.vue'
import ForbiddenPage from '../features/auth/pages/ForbiddenPage.vue'
import type { Role } from '../features/auth/types'

export function homeForRole(role?: Role) { return role === 'admin' ? '/admin' : '/account' }

export function safeDestination(value: unknown, role: Role): string {
  const expected = homeForRole(role)
  return typeof value === 'string' && value === expected ? value : expected
}

export async function authGuard(to: RouteLocationNormalized) {
  const session = useSessionStore()
  try { await session.ensureInitialized() } catch {
    if (to.meta.role) return { path: '/login' }
    return true
  }
  if (to.meta.role && !session.user) return { path: '/login', query: { redirect: to.path } }
  if (to.meta.role && session.user?.role !== to.meta.role) return { path: '/forbidden' }
  if (to.meta.guest && session.user) return homeForRole(session.user.role)
  return true
}

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: AuthPage, meta: { guest: true }, props: { mode: 'login' } },
    { path: '/register', component: AuthPage, meta: { guest: true }, props: { mode: 'register' } },
    { path: '/account', component: AccountPage, meta: { role: 'user' } },
    { path: '/admin', component: AccountPage, meta: { role: 'admin' } },
    { path: '/forbidden', component: ForbiddenPage },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})
router.beforeEach(authGuard)
