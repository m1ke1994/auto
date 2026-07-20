<template>
  <footer class="footer-root w-full pb-8 pt-2 sm:pb-10">
    <div class="w-full px-5 sm:px-8 lg:px-12">
      <hr class="border-0 border-t border-[#5b6169]/45" />

      <div class="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 py-5 text-center text-[0.875rem] text-[#4b5563]">
        <p>© 2025 АРТ СТРОЙ</p>

        <RouterLink to="/privacy-policy" class="transition duration-200 hover:text-[#111827]">
          Политика конфиденциальности
        </RouterLink>

        <RouterLink to="/data-consent" class="transition duration-200 hover:text-[#111827]">
          Согласие на обработку данных
        </RouterLink>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer-root {
  font-family: "Manrope", "Segoe UI", sans-serif;
}
</style>
