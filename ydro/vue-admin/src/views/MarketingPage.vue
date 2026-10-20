<script setup>
import { computed } from 'vue'
import { ArrowRight, ArrowUpRight, ChevronRight, MoveDownRight } from '@lucide/vue'
import TrackNodeIcon from '../components/TrackNodeIcon.vue'
import { marketingPages, marketingPageList } from '../content/marketingPages.js'

const props = defineProps({ pageKey: { type: String, required: true } })
const page = computed(() => marketingPages[props.pageKey] || marketingPages.sites)
</script>

<template>
  <div class="marketing">
    <a class="marketing-skip" href="#marketing-content">Перейти к содержимому</a>
    <header class="marketing-header">
      <div class="marketing-container marketing-header-inner">
        <RouterLink class="marketing-brand" to="/" aria-label="TrackNode — на главную">
          <TrackNodeIcon :size="31" />
          <strong>tracknode<span>.</span></strong>
        </RouterLink>
        <nav class="marketing-navigation" aria-label="Услуги TrackNode">
          <RouterLink v-for="item in marketingPageList" :key="item.key" :to="item.path"
            :aria-current="page.key === item.key ? 'page' : undefined">{{ item.short }}</RouterLink>
        </nav>
        <a class="marketing-header-cta" href="/#contact">Обсудить проект <ArrowUpRight :size="16" /></a>
      </div>
    </header>

    <main id="marketing-content">
      <section class="marketing-hero">
        <div class="marketing-glow" aria-hidden="true"></div>
        <div class="marketing-container marketing-hero-grid">
          <div class="marketing-copy">
            <nav class="marketing-crumb" aria-label="Навигационная цепочка">
              <RouterLink to="/">Главная</RouterLink><ChevronRight :size="13" aria-hidden="true" />
              <span aria-current="page">{{ page.short }}</span>
            </nav>
            <p class="marketing-overline"><span class="marketing-pulse" aria-hidden="true"></span>{{ page.eyebrow }}</p>
            <h1>{{ page.headline }}</h1>
            <p class="marketing-lead">{{ page.lead }}</p>
            <div class="marketing-actions">
              <a class="marketing-button" href="/#contact">Обсудить задачу <ArrowRight :size="17" /></a>
              <RouterLink class="marketing-text-link" to="/">Смотреть 3D-фильм <ArrowUpRight :size="16" /></RouterLink>
            </div>
            <p class="marketing-caption">TrackNode / Решения для сайтов и бизнеса</p>
          </div>
          <div class="marketing-visual">
            <div class="marketing-visual-top">
              <span>TRACKNODE / {{ page.number }}</span>
              <span>СИСТЕМА В ДЕЙСТВИИ <span class="marketing-led" aria-hidden="true"></span></span>
            </div>
            <div class="marketing-visual-core">
              <div class="marketing-orbit marketing-orbit-outer" aria-hidden="true"></div>
              <div class="marketing-orbit marketing-orbit-inner" aria-hidden="true"></div>
              <div class="marketing-symbol" aria-hidden="true"><TrackNodeIcon :size="82" /></div>
              <p class="marketing-visual-heading">{{ page.visualTitle }}</p>
              <p class="marketing-visual-description">{{ page.visualIntro }}</p>
              <div class="marketing-steps" role="list">
                <div class="marketing-step" v-for="(entry, i) in page.visual" :key="entry.code" role="listitem">
                  <span class="marketing-step-index">{{ entry.code }}</span>
                  <div><strong>{{ entry.name }}</strong><small>{{ entry.detail }}</small></div>
                  <span class="marketing-step-track" :class="{ 'is-last': i === page.visual.length - 1 }" aria-hidden="true"></span>
                </div>
              </div>
            </div>
            <div class="marketing-visual-bottom"><span>НЕ ДЕМО-СТАТИСТИКА · СХЕМА ПРОЦЕССА</span><span>↗ 2026</span></div>
          </div>
        </div>
        <div class="marketing-hero-index marketing-container">
          <span>ОТ ИДЕИ К СИСТЕМЕ</span>
          <MoveDownRight :size="18" aria-hidden="true" />
          <span>{{ page.number }} / 04</span>
        </div>
      </section>

      <section class="marketing-statement marketing-container" aria-labelledby="statement-title">
        <p class="marketing-section-label">/ Подход</p>
        <div>
          <h2 id="statement-title">{{ page.statement }}</h2>
          <p>{{ page.statementText }}</p>
        </div>
      </section>

      <section class="marketing-features marketing-container" aria-labelledby="benefits-title">
        <div class="marketing-section-top"><p class="marketing-section-label">/ Возможности</p><h2 id="benefits-title">{{ page.benefitTitle }}</h2></div>
        <div class="marketing-feature-grid">
          <article class="marketing-feature" v-for="item in page.benefits" :key="item.label">
            <span>{{ item.label }}</span><h3>{{ item.title }}</h3><p>{{ item.text }}</p>
          </article>
        </div>
      </section>

      <section class="marketing-process">
        <div class="marketing-container marketing-process-inner">
          <div class="marketing-process-intro"><p class="marketing-section-label">/ Сценарий</p>
            <h2>{{ page.processTitle }}</h2>
            <p>Понятные этапы без лишних обещаний. Конкретный состав и доступность возможностей согласуем под проект.</p>
          </div>
          <ol class="marketing-process-list">
            <li v-for="(item, index) in page.process" :key="item.title">
              <span>0{{ index + 1 }}</span>
              <div><h3>{{ item.title }}</h3><p>{{ item.text }}</p></div>
              <ArrowUpRight :size="18" aria-hidden="true" />
            </li>
          </ol>
        </div>
      </section>

      <section class="marketing-faq marketing-container" aria-labelledby="faq-heading">
        <div><p class="marketing-section-label">/ Вопросы и ответы</p><h2 id="faq-heading">Разберём важное.</h2></div>
        <div class="marketing-questions">
          <details v-for="item in page.faq" :key="item.q">
            <summary>{{ item.q }}<span aria-hidden="true">+</span></summary>
            <p>{{ item.a }}</p>
          </details>
        </div>
      </section>

      <section class="marketing-cta" aria-labelledby="cta-title">
        <div class="marketing-container marketing-cta-inner">
          <div><p class="marketing-section-label">/ Следующий шаг</p><h2 id="cta-title">Сложное можно<br><em>сделать понятным.</em></h2>
            <p>Расскажите о задаче. Обсудим подходящий формат работы, возможности платформы и следующие шаги.</p>
          </div>
          <a class="marketing-button marketing-button-large" href="/#contact">Обсудить проект <ArrowUpRight :size="19" /></a>
        </div>
      </section>
    </main>

    <footer class="marketing-footer">
      <div class="marketing-container">
        <div class="marketing-footer-top">
          <RouterLink class="marketing-brand" to="/"><TrackNodeIcon :size="27" /><strong>tracknode<span>.</span></strong></RouterLink>
          <p>Сайт, аналитика и развитие бизнеса в единой системе.</p>
        </div>
        <nav aria-label="Другие разделы TrackNode" class="marketing-footer-links">
          <RouterLink to="/">Главная</RouterLink>
          <RouterLink v-for="item in marketingPageList" :key="item.key" :to="item.path">{{ item.short }}</RouterLink>
          <RouterLink to="/privacy">Персональные данные</RouterLink>
          <RouterLink to="/terms">Условия использования</RouterLink>
          <RouterLink to="/consent">Согласие</RouterLink>
          <RouterLink to="/cookies">Cookies</RouterLink>
        </nav>
        <div class="marketing-footer-bottom"><span>© {{ new Date().getFullYear() }} TrackNode</span><span>Важен каждый следующий шаг.</span></div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.marketing{--m-blue:#467dff;--m-line:rgba(255,255,255,.13);--m-muted:#a8b3c7;background:#101216;color:#f1f3f7;min-height:100vh;font-family:Inter,ui-sans-serif,system-ui,sans-serif;overflow:clip}
.marketing *{box-sizing:border-box}
.marketing a{color:inherit;text-decoration:none}
.marketing :focus-visible{outline:2px solid #8cb0ff;outline-offset:4px}
.marketing-container{width:min(calc(100% - 96px),1280px);margin-inline:auto}
.marketing-skip{position:fixed;top:8px;left:8px;z-index:100;background:#356cf1;padding:12px;transform:translateY(-160%)}
.marketing-skip:focus{transform:none}
.marketing-header{border-bottom:1px solid var(--m-line);position:relative;z-index:5;background:#101216eb}
.marketing-header-inner{display:flex;align-items:center;gap:32px;min-height:86px}
.marketing-brand{display:inline-flex;align-items:center;gap:10px;font-size:25px;letter-spacing:-1.1px;white-space:nowrap}
.marketing-brand strong{font-weight:750}
.marketing-brand strong span{color:var(--m-blue)}
.marketing-navigation{display:flex;flex:1;justify-content:center;gap:clamp(13px,2vw,30px)}
.marketing-navigation a,.marketing-header-cta{font-size:12px;font-weight:580;white-space:nowrap;color:#abb5c8}
.marketing-navigation a:hover,.marketing-navigation a[aria-current="page"]{color:#fff}
.marketing-navigation a[aria-current="page"]{text-decoration:underline;text-decoration-color:#648fff;text-underline-offset:9px}
.marketing-header-cta{display:inline-flex;align-items:center;gap:9px;color:#fff}
.marketing-header-cta:hover,.marketing-text-link:hover{color:#7aa1ff}
.marketing-hero{position:relative;isolation:isolate;padding-top:clamp(70px,8vw,138px);border-bottom:1px solid var(--m-line)}
.marketing-glow{position:absolute;z-index:-1;inset:0;background:radial-gradient(ellipse 44% 55% at 78% 35%,rgba(55,98,201,.15),transparent),radial-gradient(ellipse 55% 80% at -16% 18%,rgba(30,48,79,.2),transparent);pointer-events:none}
.marketing-hero-grid{display:grid;grid-template-columns:minmax(0,1.03fr) minmax(0,.97fr);align-items:center;gap:clamp(35px,6vw,92px);min-height:620px}
.marketing-copy{padding-bottom:45px}
.marketing-crumb{display:flex;align-items:center;gap:10px;color:#8f9bad;font-size:11px;margin-bottom:70px}
.marketing-crumb a:hover{color:white}
.marketing-overline,.marketing-section-label{font-size:11px;text-transform:uppercase;letter-spacing:.19em;color:#86a8f8;font-weight:650}
.marketing-overline{display:flex;gap:13px;align-items:center;margin:0 0 24px}
.marketing-pulse,.marketing-led{width:6px;height:6px;border-radius:50%;background:#7ca2ff;display:inline-block;box-shadow:0 0 15px #648fff80}
.marketing h1{font-size:clamp(46px,5.2vw,82px);line-height:1.045;letter-spacing:-.07em;font-weight:550;max-width:850px;margin:0}
.marketing-lead{font-size:clamp(15px,1.38vw,19px);line-height:1.85;max-width:585px;color:#aeb9ca;margin-top:30px}
.marketing-actions{display:flex;flex-wrap:wrap;align-items:center;gap:24px;margin-top:39px}
.marketing-button{display:inline-flex;align-items:center;justify-content:space-between;gap:30px;min-height:56px;padding:0 23px;border:1px solid #6a96ff;border-radius:7px;background:#356cf1;color:#fff!important;font-weight:650;font-size:13px;transition:background .22s,transform .22s}
.marketing-button:hover{background:#4c80fa;transform:translateY(-2px)}
.marketing-text-link{display:inline-flex;align-items:center;gap:12px;font-size:13px;color:#b5c2db}
.marketing-caption{font-size:10px;letter-spacing:.2em;color:#68748a;text-transform:uppercase;margin-top:70px}
.marketing-visual{min-width:0;border:1px solid #334052;background:linear-gradient(145deg,#17202c,#10151d 62%,#141b27);box-shadow:0 35px 90px #0006;position:relative;overflow:hidden}
.marketing-visual:before{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 65%,rgba(113,146,209,.04) 65.2%);pointer-events:none}
.marketing-visual-top,.marketing-visual-bottom{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:9px;letter-spacing:.14em;color:#91a2b8;text-transform:uppercase;padding:23px 26px;border-bottom:1px solid #ffffff19}
.marketing-visual-bottom{border-top:1px solid #ffffff19;border-bottom:0;font-size:8px}
.marketing-visual-core{padding:clamp(30px,4vw,56px);position:relative;isolation:isolate}
.marketing-orbit{position:absolute;border:1px solid #ffffff09;border-radius:50%;z-index:-1;pointer-events:none}
.marketing-orbit-outer{width:370px;height:370px;right:-100px;top:-122px}
.marketing-orbit-inner{width:235px;height:235px;right:-35px;top:-50px}
.marketing-symbol{width:120px;height:120px;display:grid;place-items:center;border:1px solid #5d7eb54d;background:radial-gradient(circle,#3657973d,transparent 72%);transform:rotate(-9deg);margin-bottom:42px}
.marketing-visual-heading{font-size:clamp(23px,2vw,31px);letter-spacing:-.05em;line-height:1.2;font-weight:530;margin:0}
.marketing-visual-description{font-size:13px;line-height:1.65;color:#9facbe;max-width:370px;margin:12px 0 26px}
.marketing-steps{border-top:1px solid #ffffff25}
.marketing-step{display:flex;align-items:center;gap:19px;position:relative;border-bottom:1px solid #ffffff18;padding:17px 0;min-height:76px}
.marketing-step-index{font-size:11px;color:#6d96f0;font-variant-numeric:tabular-nums}
.marketing-step strong{display:block;font-size:14px;font-weight:550}
.marketing-step small{display:block;font-size:11px;color:#8fa0b8;margin-top:5px}
.marketing-step-track{margin-left:auto;width:30px;height:5px;border-radius:8px;background:linear-gradient(90deg,#507cff,#80a8ff)}
.marketing-step-track.is-last{background:#7bb39b}
.marketing-hero-index{display:flex;align-items:center;gap:24px;padding-top:70px;padding-bottom:27px;color:#7a8da9;font-size:10px;letter-spacing:.18em}
.marketing-hero-index span:last-child{margin-left:auto}
.marketing-statement{padding-block:clamp(85px,10vw,160px);display:grid;grid-template-columns:.3fr 1fr;gap:30px}
.marketing-statement h2{font-size:clamp(32px,4.35vw,66px);line-height:1.13;letter-spacing:-.055em;max-width:920px;font-weight:520;margin:0}
.marketing-statement>div>p{font-size:16px;line-height:1.8;color:#a2aec2;max-width:720px;margin-top:30px}
.marketing-features{padding-bottom:clamp(85px,10vw,160px)}
.marketing-section-top{display:grid;grid-template-columns:.3fr 1fr;gap:30px;align-items:baseline;margin-bottom:36px}
.marketing-section-top h2{font-size:clamp(30px,3.2vw,48px);font-weight:520;letter-spacing:-.05em;margin:0}
.marketing-feature-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:1px solid var(--m-line);border-left:1px solid var(--m-line)}
.marketing-feature{padding:clamp(27px,4vw,52px);min-height:250px;border-right:1px solid var(--m-line);border-bottom:1px solid var(--m-line);transition:background .2s}
.marketing-feature:hover{background:#ffffff08}
.marketing-feature>span{font-size:10px;color:#8aabf6;letter-spacing:.13em;text-transform:uppercase}
.marketing-feature h3{font-weight:540;font-size:clamp(21px,2vw,27px);letter-spacing:-.04em;margin:34px 0 13px}
.marketing-feature p{color:#a9b4c5;line-height:1.85;font-size:14px;max-width:460px;margin:0}
.marketing-process{background:#171c25;border-block:1px solid #ffffff13;padding-block:clamp(75px,9vw,135px)}
.marketing-process-inner{display:grid;grid-template-columns:1fr 1.05fr;gap:clamp(40px,6vw,100px)}
.marketing-process-intro h2,.marketing-faq h2{font-size:clamp(34px,4.5vw,62px);letter-spacing:-.06em;line-height:1.15;margin:25px 0;font-weight:520}
.marketing-process-intro>p:last-child{color:#a3b1c5;line-height:1.85;max-width:440px}
.marketing-process-list{padding:0;margin:0;list-style:none;border-top:1px solid #ffffff29}
.marketing-process-list li{display:grid;grid-template-columns:35px 1fr 20px;gap:20px;padding:28px 0;border-bottom:1px solid #ffffff24}
.marketing-process-list li>span{font-size:11px;color:#79a0ff;margin-top:5px}
.marketing-process-list h3{font-size:22px;font-weight:530;letter-spacing:-.04em;margin:0 0 11px}
.marketing-process-list p{margin:0;color:#a2afc0;line-height:1.75;font-size:14px}
.marketing-process-list svg{color:#7996ca}
.marketing-faq{padding-block:clamp(90px,10vw,155px);display:grid;grid-template-columns:1fr 1.1fr;gap:clamp(35px,6vw,100px)}
.marketing-questions{border-top:1px solid var(--m-line)}
.marketing-questions details{border-bottom:1px solid var(--m-line);padding:22px 0}
.marketing-questions summary{display:flex;align-items:center;justify-content:space-between;gap:12px;cursor:pointer;font-size:16px;font-weight:520;list-style:none}
.marketing-questions summary::-webkit-details-marker{display:none}
.marketing-questions summary span{font-size:25px;font-weight:300;color:#80a6ff;transition:transform .2s}
.marketing-questions details[open] summary span{transform:rotate(45deg)}
.marketing-questions details p{font-size:14px;line-height:1.8;color:#aab6c8;max-width:620px;margin:15px 35px 0 0}
.marketing-cta{background:radial-gradient(ellipse at 85% 60%,#315bad30,transparent 55%),#111924;border-block:1px solid #ffffff15;padding-block:clamp(80px,9vw,140px)}
.marketing-cta-inner{display:flex;align-items:end;justify-content:space-between;gap:35px}
.marketing-cta h2{font-size:clamp(40px,5.3vw,78px);line-height:1.1;letter-spacing:-.06em;margin:25px 0;font-weight:530}
.marketing-cta h2 em{font-style:normal;color:#7ca1ff}
.marketing-cta p:last-child{color:#aab8cb;max-width:530px;line-height:1.8}
.marketing-button-large{min-height:65px;white-space:nowrap}
.marketing-footer{background:#101216;padding-block:68px 26px}
.marketing-footer-top{display:flex;align-items:center;justify-content:space-between;gap:25px}
.marketing-footer-top p{font-size:13px;color:#9eaabd}
.marketing-footer-links{display:flex;flex-wrap:wrap;gap:18px 28px;padding-block:38px;margin-top:38px;border-block:1px solid var(--m-line)}
.marketing-footer-links a{color:#9daabd;font-size:12px}
.marketing-footer-links a:hover{color:white}
.marketing-footer-bottom{display:flex;justify-content:space-between;gap:20px;color:#7c8ba2;font-size:11px;padding-top:25px}
@media(max-width:1120px){.marketing-header-inner{flex-wrap:wrap;gap:12px 24px;padding-top:14px}.marketing-navigation{display:flex;order:3;flex-basis:100%;justify-content:flex-start;overflow-x:auto;white-space:nowrap;padding-bottom:16px}.marketing-header-cta{margin-left:auto}.marketing-hero-grid{gap:35px}.marketing-container{width:min(calc(100% - 60px),1280px)}}
@media(max-width:800px){.marketing-hero-grid{grid-template-columns:1fr;min-height:0}.marketing-copy{padding:0}.marketing-crumb{margin-bottom:45px}.marketing-visual{max-width:650px;width:100%}.marketing-statement,.marketing-section-top,.marketing-process-inner,.marketing-faq{grid-template-columns:1fr;gap:18px}.marketing-section-top{margin-bottom:24px}.marketing-cta-inner{align-items:start;flex-direction:column}.marketing-container{width:min(calc(100% - 44px),1280px)}.marketing-hero-index{padding-top:45px}.marketing-caption{margin-top:42px}}
@media(max-width:560px){.marketing-header-inner{min-height:72px;gap:12px}.marketing-brand{font-size:21px}.marketing-header-cta{font-size:11px}.marketing-header-cta svg{display:none}.marketing-hero{padding-top:45px}.marketing h1{font-size:clamp(41px,11vw,62px)}.marketing-lead{font-size:15px}.marketing-actions{gap:17px}.marketing-button{min-height:52px}.marketing-visual-top,.marketing-visual-bottom{padding:16px;font-size:8px}.marketing-visual-core{padding:28px}.marketing-symbol{width:90px;height:90px;margin-bottom:27px}.marketing-feature-grid{grid-template-columns:1fr}.marketing-feature{min-height:auto;padding:29px}.marketing-feature h3{margin-top:23px}.marketing-process-list li{grid-template-columns:25px 1fr 17px;gap:13px}.marketing-footer-top,.marketing-footer-bottom{align-items:start;flex-direction:column}.marketing-cta h2{font-size:42px}}
@media(prefers-reduced-motion:reduce){.marketing *{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
</style>
