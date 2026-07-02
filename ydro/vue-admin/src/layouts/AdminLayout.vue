<script setup>
import { onMounted, ref } from 'vue'

import Sidebar from '../components/Sidebar.vue'
import Topbar from '../components/Topbar.vue'
import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'

const authStore = useAuthStore()
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

  if (!siteStore.sites.length) {
    try {
      await siteStore.fetchSites()
    } catch {
      // optional
    }
  }
})
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
