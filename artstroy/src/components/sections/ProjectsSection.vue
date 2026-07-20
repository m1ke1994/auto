<script setup>
import { computed, ref } from 'vue'
import { projectFilters, projects } from '../../data/projects'

const props = defineProps({
  showViewAllButton: {
    type: Boolean,
    default: true,
  },
})

const activeFilter = ref('all')
const loadedImages = ref({})

const filteredProjects = computed(() => {
  if (activeFilter.value === 'all') {
    return projects
  }

  return projects.filter((project) => project.category === activeFilter.value)
})

const getFilterLabel = (categoryId) => {
  const filter = projectFilters.find((item) => item.id === categoryId)
  return filter ? filter.label : 'Проект'
}

const markImageLoaded = (id) => {
  loadedImages.value[id] = true
}

const isImageLoaded = (id) => Boolean(loadedImages.value[id])
</script>

<template>
  <section id="projects" class="projects-root w-full scroll-mt-28 pb-10 pt-3 sm:pb-12 sm:pt-4 lg:pb-14 lg:pt-5">
    <div class="w-full px-5 py-6 sm:px-8 sm:py-8 lg:px-12 lg:py-10">
      <div class="mx-auto max-w-[58rem] text-center">
        <p
          v-reveal="{ type: 'title', delay: 0 }"
          class="text-[0.75rem] font-semibold uppercase tracking-[0.16em] text-[#6b7280]"
        >
          Портфолио
        </p>

        <h2
          v-reveal="{ type: 'title', delay: 0.08 }"
          class="mt-3 text-[2rem] font-semibold leading-[1.05] tracking-[-0.03em] text-[#111827] sm:text-[2.7rem] lg:text-[3.2rem]"
        >
          Наши проекты
        </h2>

        <p
          v-reveal="{ type: 'title', delay: 0.16 }"
          class="mx-auto mt-4 max-w-[46rem] text-[1rem] leading-[1.72] text-[#4b5563] sm:text-[1.05rem]"
        >
          Сложные инженерные проекты любой масштабности, современный дизайн и продуманная эстетика
        </p>
      </div>

      <div
        v-reveal="{ type: 'fade-up', delay: 0.22 }"
        class="mt-7 flex flex-wrap justify-center gap-2.5 sm:mt-8"
      >
        <button
          v-for="filter in projectFilters"
          :key="filter.id"
          type="button"
          class="rounded-full border px-4 py-2 text-[0.875rem] font-medium transition duration-200"
          :class="activeFilter === filter.id
            ? 'border-[#4b5563]/45 bg-[#f8fafc] text-[#111827] shadow-[0_8px_20px_rgba(15,23,42,0.12)]'
            : 'border-[#5b6169]/30 bg-white/45 text-[#4b5563] hover:border-[#5b6169]/45 hover:bg-white/70 hover:text-[#111827]'"
          @click="activeFilter = filter.id"
        >
          {{ filter.label }}
        </button>
      </div>

      <TransitionGroup
        name="project-card"
        tag="div"
        class="mt-8 grid grid-cols-1 gap-4 sm:mt-9 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      >
        <article
          v-for="(project, index) in filteredProjects"
          :key="`${activeFilter}-${project.id}`"
          v-reveal="{ type: 'project-card', delay: index * 0.07 }"
          class="group flex h-full flex-col overflow-hidden rounded-[1.25rem] border border-[#5b6169]/28 bg-white/55 shadow-[0_12px_30px_rgba(15,23,42,0.1)] backdrop-blur-[6px] transition duration-300 hover:-translate-y-[2px] hover:border-[#5b6169]/45 hover:shadow-[0_16px_38px_rgba(15,23,42,0.14)]"
        >
          <div class="relative aspect-[5/3] overflow-hidden">
            <div
              class="absolute inset-0 z-[1] bg-[linear-gradient(120deg,#e7ebf0_20%,#f5f7fa_50%,#e7ebf0_80%)] bg-[length:180%_100%] animate-[projectShimmer_1.8s_ease-in-out_infinite] transition-opacity duration-300"
              :class="isImageLoaded(project.id) ? 'opacity-0' : 'opacity-100'"
            />

            <img
              :src="project.image"
              :alt="project.title"
              class="h-full w-full object-cover object-center transition duration-500 group-hover:scale-[1.04]"
              :class="isImageLoaded(project.id) ? 'opacity-100' : 'opacity-0'"
              loading="lazy"
              decoding="async"
              fetchpriority="low"
              width="960"
              height="576"
              @load="markImageLoaded(project.id)"
              @error="markImageLoaded(project.id)"
            />

            <div class="absolute inset-0 bg-gradient-to-t from-black/30 via-black/5 to-transparent" />
            <span class="absolute left-3 top-3 inline-flex rounded-full border border-white/65 bg-white/80 px-3 py-1 text-[0.72rem] font-medium text-[#374151] backdrop-blur-[3px]">
              {{ getFilterLabel(project.category) }}
            </span>
          </div>

          <div class="flex grow flex-col p-4 sm:p-5">
            <h3 class="text-[1.06rem] font-semibold leading-[1.2] tracking-[-0.01em] text-[#111827]">
              {{ project.title }}
            </h3>
            <p class="mt-2 text-[0.875rem] leading-[1.62] text-[#4b5563]">
              {{ project.shortDescription }}
            </p>
          </div>
        </article>
      </TransitionGroup>

      <div
        v-if="props.showViewAllButton"
        class="mt-8 flex justify-center sm:mt-9"
      >
        <RouterLink
          to="/projects"
          class="inline-flex items-center rounded-full border border-[#4b5563]/40 bg-white/65 px-6 py-2.5 text-[0.9rem] font-medium text-[#111827] shadow-[0_8px_22px_rgba(15,23,42,0.1)] backdrop-blur-[4px] transition duration-200 hover:-translate-y-[1px] hover:border-[#374151]/55 hover:bg-white/85"
        >
          Смотреть все проекты
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.projects-root {
  font-family: "Manrope", "Segoe UI", sans-serif;
}

.project-card-enter-active,
.project-card-leave-active {
  transition: all 0.3s ease;
}

.project-card-enter-from,
.project-card-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.985);
}

.project-card-move {
  transition: transform 0.3s ease;
}

@keyframes projectShimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
