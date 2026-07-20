<script setup>
import { computed, ref } from 'vue'
import { submitLead } from '../composables/useLeadApi'

const props = defineProps({ site: { type: Object, required: true }, sections: { type: Array, default: () => [] } })
const byKey = computed(() => Object.fromEntries(props.sections.map((section) => [section.key, section.content || {}])))
const config = computed(() => props.site.builder_config || {})
const hero = computed(() => ({ ...(config.value.hero || {}), ...(byKey.value.hero || {}) }))
const contacts = computed(() => ({ ...config.value, ...(byKey.value.contacts || {}) }))
const form = ref({ name: '', phone: '' })
const sent = ref(false)

async function sendRequest() {
  await submitLead({ section_key: 'contacts', form_name: 'Расчёт проекта', ...form.value })
  sent.value = true
}
</script>

<template>
  <div class="art-site">
    <header class="art-header">
      <a href="#top" class="art-brand">{{ config.company_name || site.name }}</a>
      <nav><a href="#about">О компании</a><a href="#projects">Проекты</a><a href="#contacts">Контакты</a></nav>
      <a class="art-phone" :href="`tel:${contacts.phone || ''}`">{{ contacts.phone }}</a>
    </header>
    <main>
      <section id="top" class="art-hero" :style="{ backgroundImage: `url(${hero.image || '/art-stroy/images/hero.jpg'})` }">
        <div class="art-hero__shade" />
        <div class="art-hero__content">
          <p>Остекление · фасады · металлоконструкции</p>
          <h1>{{ hero.title || config.company_name }}</h1>
          <div class="art-lead">{{ hero.description || config.description }}</div>
          <a class="art-button" href="#contacts">Рассчитать проект</a>
        </div>
      </section>
      <section id="about" class="art-section art-about">
        <p class="art-kicker">О компании</p><h2>{{ byKey.about?.title || 'Инженерия. Эстетика. Надёжность.' }}</h2>
        <p>{{ byKey.about?.description || config.description }}</p>
        <div class="art-stats"><div><strong>10+</strong><span>лет на рынке</span></div><div><strong>250+</strong><span>проектов</span></div><div><strong>98%</strong><span>довольных клиентов</span></div></div>
      </section>
      <section id="projects" class="art-section art-projects">
        <p class="art-kicker">Портфолио</p><h2>{{ byKey.projects?.title }}</h2><p>{{ byKey.projects?.description }}</p>
        <div class="art-project-grid"><article v-for="item in (byKey.projects?.items || [])" :key="item.title"><img :src="item.image" alt=""><h3>{{ item.title }}</h3><p>{{ item.description }}</p></article></div>
      </section>
      <section class="art-section art-reviews"><p class="art-kicker">Отзывы</p><h2>{{ byKey.reviews?.title }}</h2><div class="art-review-grid"><blockquote v-for="item in (byKey.reviews?.items || [])" :key="item.author">“{{ item.text }}”<footer>{{ item.author }}</footer></blockquote></div></section>
      <section id="contacts" class="art-section art-contact">
        <div><p class="art-kicker">Контакты</p><h2>{{ contacts.title }}</h2><p>{{ contacts.description }}</p><p>{{ contacts.city }} · {{ contacts.phone }}<br>{{ contacts.email }}</p></div>
        <form @submit.prevent="sendRequest"><input v-model="form.name" required placeholder="Ваше имя"><input v-model="form.phone" required placeholder="Телефон"><button class="art-button" type="submit">Отправить</button><p v-if="sent">Заявка принята</p></form>
      </section>
    </main>
    <footer class="art-footer"><strong>{{ config.company_name || site.name }}</strong><span>{{ byKey.footer?.copyright }}</span></footer>
  </div>
</template>

<style scoped>
.art-site{min-height:100vh;background:#f3f5f7;color:#14161d;font-family:Inter,Arial,sans-serif}.art-header{position:absolute;z-index:4;display:grid;width:100%;grid-template-columns:1fr auto 1fr;align-items:center;padding:28px 5%;color:#fff}.art-header nav{display:flex;gap:28px}.art-header a{color:inherit;text-decoration:none}.art-brand{font-size:22px;font-weight:800;text-transform:uppercase}.art-phone{text-align:right}.art-hero{position:relative;display:flex;min-height:760px;align-items:center;background-position:center;background-size:cover;color:#fff}.art-hero__shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,12,18,.9),rgba(8,12,18,.18))}.art-hero__content{position:relative;z-index:1;max-width:760px;padding:140px 7% 80px}.art-hero h1,.art-section h2{margin:16px 0;font-size:clamp(42px,7vw,86px);line-height:1}.art-lead{max-width:660px;font-size:19px;line-height:1.7}.art-button{display:inline-flex;margin-top:28px;border:0;border-radius:4px;background:#171b23;padding:16px 24px;color:#fff;text-decoration:none;font-weight:700}.art-section{padding:100px 7%}.art-section>p{max-width:760px;line-height:1.8;color:#606771}.art-section h2{max-width:900px;font-size:clamp(34px,5vw,64px)}.art-kicker{text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:.16em;color:#89909a!important}.art-stats,.art-project-grid,.art-review-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:50px}.art-stats div{display:grid;gap:8px;border-top:1px solid #ccd1d7;padding-top:24px}.art-stats strong{font-size:42px}.art-projects{background:#fff}.art-project-grid article{background:#f3f5f7;padding-bottom:22px}.art-project-grid img{width:100%;aspect-ratio:4/3;object-fit:cover}.art-project-grid h3,.art-project-grid p{margin:16px 20px 0}.art-review-grid blockquote{margin:0;background:#fff;padding:30px;font-size:18px;line-height:1.7}.art-review-grid footer{margin-top:20px;font-weight:800}.art-contact{display:grid;grid-template-columns:1fr 1fr;gap:60px;background:#dfe4e9}.art-contact form{display:grid;align-content:center;gap:14px}.art-contact input{border:1px solid #b9c0c8;background:#fff;padding:16px;font:inherit}.art-contact .art-button{margin:0}.art-footer{display:flex;justify-content:space-between;background:#151922;padding:30px 7%;color:#fff}@media(max-width:760px){.art-header{grid-template-columns:1fr auto}.art-header nav{display:none}.art-hero{min-height:680px}.art-stats,.art-project-grid,.art-review-grid,.art-contact{grid-template-columns:1fr}.art-section{padding:72px 6%}.art-footer{flex-direction:column;gap:10px}}
</style>
