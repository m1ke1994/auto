<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getPlatformClient } from '../../api/platform'
const route = useRoute(), client = ref(null), error = ref('')
onMounted(async () => { try { client.value = (await getPlatformClient(route.params.clientId)).data } catch (e) { error.value = e.response?.data?.detail || 'Клиент не найден.' } })
</script>
<template><section class="space-y-4"><div v-if="error" class="rounded-2xl bg-red-50 p-4 text-red-800">{{ error }}</div><template v-else-if="client"><div class="rounded-3xl bg-white p-6 shadow-soft"><p class="text-xs font-bold uppercase text-violet-600">Карточка клиента</p><h2 class="mt-2 text-2xl font-bold">{{ client.company || client.username }}</h2><p class="mt-1 text-slate-500">{{ client.email }} · зарегистрирован {{ new Date(client.date_joined).toLocaleDateString('ru-RU') }}</p></div><div class="rounded-3xl bg-white p-5 shadow-soft"><h3 class="font-semibold">Сайты клиента</h3><RouterLink v-for="site in client.sites" :key="site.id" :to="`/platform/sites/${site.id}`" class="mt-3 flex items-center justify-between rounded-2xl border border-violet-100 p-4 hover:bg-violet-50"><span><b>{{ site.name }}</b><small class="block text-slate-500">{{ site.domain }}</small></span><span>{{ site.is_active ? 'Активен' : 'Отключён' }}</span></RouterLink></div></template></section></template>

