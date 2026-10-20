import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import { onUnauthorized } from '../shared/api/client'
import { useSessionStore } from '../features/auth/session-store'
import '../shared/styles/main.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
watch(() => useSessionStore(pinia).user, (user) => {
  if (!user && router.currentRoute.value.meta.role) void router.replace('/login?expired=1')
})
onUnauthorized(() => {
  useSessionStore(pinia).clear()
  if (router.currentRoute.value.meta.role) void router.replace('/login?expired=1')
})
app.use(router)
app.mount('#app')
