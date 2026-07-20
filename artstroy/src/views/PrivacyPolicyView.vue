<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
    return
  }

  router.push('/')
}
</script>

<template>
  <main class="legal-page w-full bg-[#f2f4f7] pb-12 pt-8 sm:pb-14 sm:pt-10 lg:pb-16 lg:pt-12">
    <section class="mx-auto w-full max-w-[1440px] px-5 sm:px-8 lg:px-12">
      <article class="rounded-[1.5rem] border border-white/75 bg-white/70 p-6 shadow-[0_14px_34px_rgba(15,23,42,0.08)] backdrop-blur-[8px] sm:p-8 lg:p-10">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-full border border-[#c8d0dc] bg-white/80 px-4 py-2 text-[0.875rem] font-medium text-[#374151] transition duration-200 hover:border-[#9aa6b7] hover:text-[#111827]"
          @click="goBack"
        >
          <span aria-hidden="true">←</span>
          Назад
        </button>

        <h1 class="mt-5 text-[2rem] font-semibold leading-[1.05] tracking-[-0.03em] text-[#111827] sm:text-[2.6rem]">
          Политика конфиденциальности
        </h1>

        <div class="mt-6 space-y-5 text-[0.975rem] leading-[1.72] text-[#4b5563]">
          <p>
            Настоящая Политика конфиденциальности определяет порядок обработки и защиты персональных данных пользователей сайта.
          </p>
          <p>
            Мы обрабатываем персональные данные исключительно в целях обратной связи, подготовки коммерческих предложений и исполнения договорных обязательств.
          </p>
          <p>
            К персональным данным относятся: имя, номер телефона, адрес электронной почты и иные сведения, которые пользователь добровольно предоставляет через формы сайта.
          </p>
          <p>
            Персональные данные не передаются третьим лицам, за исключением случаев, предусмотренных законодательством Российской Федерации.
          </p>
          <p>
            Пользователь вправе запросить уточнение, блокирование или удаление своих персональных данных, направив обращение на электронную почту компании.
          </p>
        </div>
      </article>
    </section>
  </main>
</template>

<style scoped>
.legal-page {
  font-family: "Manrope", "Segoe UI", sans-serif;
}
</style>
