<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

import Sidebar from '../components/Sidebar.vue'
import Topbar from '../components/Topbar.vue'
import { useAuthStore } from '../stores/auth'
import { useNewsStore } from '../stores/news'
import { useSiteStore } from '../stores/site'

const authStore = useAuthStore()
const newsStore = useNewsStore()
const siteStore = useSiteStore()

const sidebarOpen = ref(false)

function closeSidebar() {
  sidebarOpen.value = false
}

onMounted(async () => {
  if (!authStore.user) {
    try {
      await authStore.getCurrentUser()
    } catch {
      return
    }
  }

  newsStore.startPolling()

  if (!siteStore.loaded && !siteStore.loading) {
    try {
      await siteStore.fetchSites()
    } catch {
      // optional
    }
  }
})

onBeforeUnmount(() => newsStore.stopPolling())
</script>

<template>
  <div class="app-viewport bg-[#FAFBFF]">
    <div class="app-viewport flex">
      <Sidebar :open="sidebarOpen" @close="closeSidebar" />

      <div class="app-viewport flex min-w-0 w-full flex-1 flex-col lg:pl-64">
        <Topbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />

        <main class="dashboard-main min-w-0 flex-1">
          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>
