<template>
  <section class="space-y-4">
    <div class="rounded-2xl border border-brand-100 bg-white/92 p-4 shadow-soft">
      <h1 class="text-xl font-semibold text-[#17223B]">Дополнительные инструменты</h1>
      <p class="mt-1 text-sm text-slate-500">Отчёты, настройки и дополнительные возможности сайта.</p>
    </div>

    <div class="rounded-2xl border border-brand-100 bg-white/92 p-2 shadow-soft">
      <nav class="flex flex-wrap gap-2">
        <RouterLink class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50" active-class="bg-brand-50 text-brand-700" to="/mini">Статистика</RouterLink>
        <RouterLink class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50" active-class="bg-brand-50 text-brand-700" to="/mini/leads">Заявки</RouterLink>
        <RouterLink class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50" active-class="bg-brand-50 text-brand-700" to="/mini/seo">Проверка сайта</RouterLink>
        <RouterLink class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50" active-class="bg-brand-50 text-brand-700" to="/mini/reports">Отчёты</RouterLink>
        <RouterLink class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50" active-class="bg-brand-50 text-brand-700" to="/mini/settings">Настройки</RouterLink>
        <RouterLink class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50" active-class="bg-brand-50 text-brand-700" to="/mini/integration">Telegram</RouterLink>
      </nav>
    </div>

    <RouterView />
  </section>
</template>
