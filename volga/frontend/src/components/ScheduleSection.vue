<template>
  <div class="month-schedule">
    <div class="month-schedule__top">

      <div
        class="month-schedule__months"
        role="tablist"
        aria-label="Выбор месяца"
      >
        <button
          v-for="month in groupedEvents"
          :key="month.monthKey"
          class="month-schedule__month-tab"
          :class="{ active: activeMonth === month.monthKey }"
          type="button"
          role="tab"
          :aria-selected="activeMonth === month.monthKey"
          @click="setActiveMonth(month.monthKey)"
        >
          {{ month.monthLabel }}
        </button>
      </div>

      <div
        v-if="activeMonthDays.length"
        ref="daysStripRef"
        class="month-schedule__days"
        aria-label="Расписание по дням"
      >
        <button
          v-for="day in activeMonthDays"
          :key="day.dateKey"
          class="month-schedule__day"
          :class="{
            active: activeDay === day.dateKey,
            today: day.dateKey === todayDateKey
          }"
          type="button"
          :ref="(el) => setDayButtonRef(day.dateKey, el)"
          @click="focusDay(day.dateKey)"
        >
          <span class="month-schedule__day-label">
            {{ day.ribbonWeekday }}
          </span>
          <span class="month-schedule__day-number">
            {{ day.ribbonDay }}
          </span>
        </button>
      </div>

      <div v-if="activeMonthGroup" class="month-schedule__meta">
        <span>
          {{ activeMonthGroup.days.length }}
          {{ pluralizeDays(activeMonthGroup.days.length) }}
        </span>
        <span>•</span>
        <span>
          {{ activeMonthEventsCount }}
          {{ pluralizeEvents(activeMonthEventsCount) }}
        </span>
      </div>
    </div>

    <div class="month-schedule__list">
      <div v-if="loading" class="month-schedule__empty">
        Загрузка расписания...
      </div>

      <div v-else-if="error" class="month-schedule__empty">
        {{ error }}
      </div>

      <section
        v-else-if="activeMonthGroup"
        :key="activeMonthGroup.monthKey"
        class="month-schedule__month"
      >
        <h3 class="month-schedule__month-title">
          {{ activeMonthGroup.monthLabel }}
        </h3>

        <section
          v-for="dayGroup in visibleMonthDays"
          :key="dayGroup.dateKey"
          class="month-schedule__day-group"
          :class="{ 'month-schedule__day-group--open': isDayOpen(dayGroup.dateKey) }"
        >
          <button
            class="month-schedule__date"
            type="button"
            :aria-expanded="isDayOpen(dayGroup.dateKey)"
            @click="toggleDay(dayGroup.dateKey)"
          >
            <span class="month-schedule__date-main">
              <span>{{ dayGroup.dateLabel }}</span>
              <span class="month-schedule__date-count">
                {{ dayGroup.events.length }}
              </span>
            </span>

            <span
              class="month-schedule__date-chevron"
              :class="{ 'month-schedule__date-chevron--open': isDayOpen(dayGroup.dateKey) }"
              aria-hidden="true"
            >
              ▼
            </span>
          </button>

          <div
            class="month-schedule__day-body"
            :class="{ 'month-schedule__day-body--open': isDayOpen(dayGroup.dateKey) }"
          >
            <div class="month-schedule__date-events">
              <div
                v-for="event in visibleEvents(dayGroup)"
                :key="event.id"
                class="program-card"
                @click="openModal(event)"
              >
                <div
                  class="program-card__bar"
                  :style="{ background: event.color }"
                ></div>

                <div class="program-card__content">
                  <div class="program-card__time">
                    {{ event.start }} — {{ event.end }}
                  </div>

                  <div class="program-card__title">
                    {{ event.title }}
                  </div>

                  <div class="program-card__meta">
                    {{ event.category }}
                  </div>
                </div>

                <div class="program-card__price">
                  {{ formatPrice(event.price) }}
                </div>
              </div>

              <button
                v-if="hasHiddenEvents(dayGroup)"
                class="month-schedule__events-more"
                type="button"
                @click="toggleEventsLimit(dayGroup.dateKey)"
              >
                {{ isEventsExpanded(dayGroup.dateKey) ? "Свернуть" : "Показать ещё" }}
              </button>
            </div>
          </div>
        </section>

        <button
          v-if="hasMoreDays"
          class="month-schedule__more"
          type="button"
          @click="showMoreDays"
        >
          Показать больше дат
        </button>
      </section>

      <div v-if="!activeMonthGroup" class="month-schedule__empty">
        В расписании пока нет событий
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="activeEvent"
        class="program-modal"
        @click.self="closeModal"
      >
        <div class="program-modal__card">
          <button
            class="program-modal__close"
            @click="closeModal"
          >
            ✕
          </button>

          <h3>{{ activeEvent.title }}</h3>

          <p class="program-modal__time">
            {{ activeEvent.start }} — {{ activeEvent.end }}
          </p>

          <img
            v-if="activeEvent.image"
            :src="activeEvent.image"
            class="program-modal__image"
          />

          <RichText :content="activeEvent.description" class="program-modal__desc" />
        </div>
      </div>
    </Teleport>
  </div>
</template>


<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { getSchedule } from "../api/schedule";
import RichText from "./ui/RichText.vue";

const pad = (value) => String(value).padStart(2, "0");

const toDateKey = (date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;

const toMonthKey = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;

const parseDateKey = (dateKey) => {
  const [year, month, day] = String(dateKey).split("-").map(Number);
  return new Date(year, month - 1, day);
};

const parseTimeToDate = (dateObj, timeValue) => {
  const [hoursRaw, minutesRaw] = String(timeValue || "").split(":");
  const hours = Number(hoursRaw);
  const minutes = Number(minutesRaw);

  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
    return null;
  }

  if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) {
    return null;
  }

  return new Date(
    dateObj.getFullYear(),
    dateObj.getMonth(),
    dateObj.getDate(),
    hours,
    minutes,
    0,
    0
  );
};

const today = new Date();
const todayDateKey = toDateKey(today);
const INITIAL_VISIBLE_DAYS = 5;
const VISIBLE_DAYS_STEP = 5;
const INITIAL_VISIBLE_EVENTS = 5;

const dayFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
  weekday: "long",
});

const ribbonWeekdayFormatter = new Intl.DateTimeFormat("ru-RU", {
  weekday: "short",
});

const capitalize = (text) => {
  const value = String(text || "").trim();
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
};

const schedule = ref([]);
const loading = ref(true);
const error = ref(null);

const normalizeApiSchedule = (payload) => {
  if (!Array.isArray(payload)) return [];

  const now = new Date();
  const currentDateKey = toDateKey(now);

  return payload.map((month) => {
    const year = Number(month?.year || 0);
    const monthNumber = Number(month?.month_number || 1);
    const monthKey = `${year}-${pad(monthNumber)}`;

    const days = (Array.isArray(month?.days) ? month.days : [])
      .map((day) => {
        const dateKey = String(day?.date || "");
        if (!dateKey || dateKey < currentDateKey) {
          return null;
        }

        const dateObj = parseDateKey(dateKey);
        const weekdayLabel = ribbonWeekdayFormatter.format(dateObj).replace(".", "");
        const isToday = dateKey === currentDateKey;

        const events = (Array.isArray(day?.events) ? day.events : [])
          .map((event) => ({
            id: event?.id,
            start: String(event?.time_start || ""),
            end: String(event?.time_end || ""),
            title: String(event?.title || ""),
            category: String(event?.category || ""),
            description: String(event?.description || ""),
            price: Number(event?.price || 0),
            color: String(event?.color || "#6BA368"),
            image: String(event?.image || ""),
          }))
          .filter((event) => {
            if (!isToday) return true;

            const eventEnd = parseTimeToDate(dateObj, event.end);
            if (!eventEnd) return true;

            return eventEnd.getTime() > now.getTime();
          });

        if (!events.length) {
          return null;
        }

        return {
          dateKey,
          dateLabel: capitalize(dayFormatter.format(dateObj)),
          ribbonWeekday: capitalize(weekdayLabel),
          ribbonDay: dateObj.getDate(),
          events,
        };
      })
      .filter(Boolean);

    return {
      monthKey,
      monthLabel: capitalize(String(month?.month || "")),
      days,
    };
  }).filter((month) => month.days.length > 0);
};

onMounted(async () => {
  console.log("Schedule mounted");

  try {
    const data = await getSchedule();
    console.log("SCHEDULE API DATA:", data);
    schedule.value = normalizeApiSchedule(data);
  } catch (e) {
    console.error("Schedule error:", e);
    error.value = e instanceof Error ? e.message : "Failed to load schedule";
  } finally {
    loading.value = false;
  }
});

const groupedEvents = computed(() => schedule.value);

const activeMonth = ref("");
const activeDay = ref("");
const openedDays = ref({});
const expandedEventDays = ref({});
const visibleDayCount = ref(INITIAL_VISIBLE_DAYS);
const dayButtonRefs = ref({});
const daysStripRef = ref(null);

const activeMonthGroup = computed(
  () => groupedEvents.value.find((month) => month.monthKey === activeMonth.value) || null
);

const activeMonthDays = computed(() => activeMonthGroup.value?.days || []);
const visibleMonthDays = computed(() => activeMonthDays.value.slice(0, visibleDayCount.value));
const hasMoreDays = computed(() => activeMonthDays.value.length > visibleDayCount.value);
const activeMonthEventsCount = computed(() =>
  activeMonthDays.value.reduce((sum, day) => sum + day.events.length, 0)
);

const pluralizeDays = (count) => {
  if (count % 10 === 1 && count % 100 !== 11) return "день";
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "дня";
  return "дней";
};

const pluralizeEvents = (count) => {
  if (count % 10 === 1 && count % 100 !== 11) return "событие";
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "события";
  return "событий";
};

const findNearestUpcomingDay = (days) => {
  if (!days.length) return "";

  const todayStart = new Date(today);
  todayStart.setHours(0, 0, 0, 0);

  const nearest = days.find((day) => {
    const dayDate = parseDateKey(day.dateKey);
    dayDate.setHours(0, 0, 0, 0);
    return dayDate.getTime() >= todayStart.getTime();
  });

  return nearest?.dateKey || days[0].dateKey;
};

const setActiveMonth = (monthKey) => {
  if (activeMonth.value === monthKey) return;
  activeMonth.value = monthKey;
};

const setDayButtonRef = (dayKey, el) => {
  if (!el) {
    delete dayButtonRefs.value[dayKey];
    return;
  }
  dayButtonRefs.value[dayKey] = el;
};

const scrollRibbonToActiveDay = (smooth = true) => {
  const container = daysStripRef.value;
  const button = dayButtonRefs.value[activeDay.value];
  if (!container || !button) return;

  const targetLeft = button.offsetLeft - (container.clientWidth - button.clientWidth) / 2;
  container.scrollTo({
    left: Math.max(0, targetLeft),
    behavior: smooth ? "smooth" : "auto",
  });
};

const resetMonthView = async () => {
  const days = activeMonthDays.value;
  const defaultDay = findNearestUpcomingDay(days);
  const defaultDayIndex = days.findIndex((day) => day.dateKey === defaultDay);
  visibleDayCount.value = Math.max(INITIAL_VISIBLE_DAYS, defaultDayIndex + 1);

  activeDay.value = defaultDay;
  openedDays.value = defaultDay ? { [defaultDay]: true } : {};
  expandedEventDays.value = {};

  await nextTick();
  if (defaultDay) {
    scrollRibbonToActiveDay(false);
  }
};

const isDayOpen = (dayKey) => Boolean(openedDays.value[dayKey]);
const isEventsExpanded = (dayKey) => Boolean(expandedEventDays.value[dayKey]);
const visibleEvents = (dayGroup) => {
  const events = Array.isArray(dayGroup?.events) ? dayGroup.events : [];
  if (isEventsExpanded(dayGroup?.dateKey)) {
    return events;
  }
  return events.slice(0, INITIAL_VISIBLE_EVENTS);
};
const hiddenEventsCount = (dayGroup) =>
  Math.max(0, (Array.isArray(dayGroup?.events) ? dayGroup.events.length : 0) - INITIAL_VISIBLE_EVENTS);
const hasHiddenEvents = (dayGroup) => hiddenEventsCount(dayGroup) > 0;
const toggleEventsLimit = (dayKey) => {
  expandedEventDays.value = {
    ...expandedEventDays.value,
    [dayKey]: !expandedEventDays.value[dayKey],
  };
};

const focusDay = async (dayKey) => {
  activeDay.value = dayKey;
  const dayIndex = activeMonthDays.value.findIndex((day) => day.dateKey === dayKey);
  if (dayIndex >= 0 && dayIndex + 1 > visibleDayCount.value) {
    visibleDayCount.value = dayIndex + 1;
  }
  openedDays.value = { [dayKey]: true };

  await nextTick();
  scrollRibbonToActiveDay(true);
};

const toggleDay = (dayKey) => {
  activeDay.value = dayKey;
  if (openedDays.value[dayKey]) {
    openedDays.value = {};
    return;
  }

  openedDays.value = { [dayKey]: true };
};

const showMoreDays = () => {
  visibleDayCount.value += VISIBLE_DAYS_STEP;
};

watch(
  groupedEvents,
  (months) => {
    if (!months.length) {
      activeMonth.value = "";
      activeDay.value = "";
      openedDays.value = {};
      expandedEventDays.value = {};
      return;
    }

    const currentMonthKey = toMonthKey(today);
    const hasActiveMonth = months.some((month) => month.monthKey === activeMonth.value);

    if (!hasActiveMonth) {
      activeMonth.value =
        months.find((month) => month.monthKey === currentMonthKey)?.monthKey || months[0].monthKey;
    }
  },
  { immediate: true }
);

watch(
  activeMonth,
  async () => {
    await resetMonthView();
  },
  { immediate: true }
);

const activeEvent = ref(null);
const savedScrollY = ref(0);

const openModal = async (event) => {
  savedScrollY.value = window.scrollY;
  activeEvent.value = event;
  await nextTick();
  window.scrollTo({ top: savedScrollY.value, behavior: "auto" });
  document.body.style.overflow = "hidden";
};

const closeModal = () => {
  activeEvent.value = null;
  document.body.style.overflow = "";
  window.scrollTo({ top: savedScrollY.value, behavior: "auto" });
};

const formatPrice = (value) => `${Number(value || 0).toLocaleString("ru-RU")} ₽`;

onBeforeUnmount(() => {
  document.body.style.overflow = "";
});
</script>

<style scoped>
.month-schedule {
  padding: 28px 0;
}

.month-schedule__top {
  margin-bottom: 16px;
  display: grid;
  gap: 10px;
}

.month-schedule__months {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
}

.month-schedule__month-tab {
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text);
  border-radius: 999px;
  padding: 9px 14px;
  font-size: var(--font-size-base);
  cursor: pointer;
  white-space: nowrap;
  flex: 0 0 auto;
  transition: transform 120ms ease, background-color 120ms ease, border-color 120ms ease;
}

.month-schedule__month-tab:hover {
  transform: translateY(-1px);
}

.month-schedule__month-tab.active {
  background: var(--primary);
  color: var(--color-dark-deep);
  border-color: var(--primary);
}

.month-schedule__days {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 6px;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x proximity;
}

.month-schedule__day {
  min-width: 92px;
  padding: 9px 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  font-size: var(--font-size-base);
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  flex: 0 0 auto;
  scroll-snap-align: center;
  transition: transform 120ms ease, border-color 120ms ease, background-color 120ms ease;
}

.month-schedule__day:hover {
  transform: translateY(-1px);
}

.month-schedule__day.active {
  background: var(--primary);
  color: var(--color-dark-deep);
  border-color: var(--primary);
}

.month-schedule__day.today:not(.active) {
  border-color: color-mix(in srgb, var(--primary) 70%, var(--border));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--primary) 30%, transparent);
}

.month-schedule__meta {
  font-size: var(--font-size-base);
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.month-schedule__list {
  display: grid;
  gap: 14px;
}

.month-schedule__month {
  display: grid;
  gap: 10px;
}

.month-schedule__month-title {
  margin: 0;
  font-size: 22px;
  line-height: 1.2;
  color: var(--text-strong);
}

.month-schedule__day-group {
  display: grid;
  gap: 6px;
}

.month-schedule__date {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-strong);
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: color-mix(in srgb, var(--bg-elevated) 84%, transparent);
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
  transition: border-color 140ms ease, background-color 140ms ease;
}

.month-schedule__date:hover {
  border-color: color-mix(in srgb, var(--primary) 45%, var(--border));
}

.month-schedule__date-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.month-schedule__date-count {
  min-width: 22px;
  height: 22px;
  border-radius: 999px;
  padding: 0 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-base);
  font-weight: 700;
  color: var(--text-strong);
  background: color-mix(in srgb, var(--primary) 22%, var(--bg-elevated));
}

.month-schedule__date-chevron {
  font-size: 14px;
  color: var(--muted);
  transition: transform 180ms ease;
}

.month-schedule__date-chevron--open {
  transform: rotate(180deg);
}

.month-schedule__day-body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 220ms ease;
}

.month-schedule__day-body--open {
  grid-template-rows: 1fr;
}

.month-schedule__date-events {
  overflow: hidden;
  display: grid;
  gap: 8px;
}

.month-schedule__day-group--open .month-schedule__date-events {
  padding-top: 1px;
}

.month-schedule__more {
  justify-self: center;
  margin-top: 2px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-strong);
  border-radius: 999px;
  padding: 9px 14px;
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: transform 120ms ease, border-color 120ms ease;
}

.month-schedule__more:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--primary) 50%, var(--border));
}

.month-schedule__empty {
  padding: 14px;
  border-radius: 10px;
  border: 1px dashed var(--border);
  color: var(--muted);
}

.program-card {
  display: grid;
  grid-template-columns: 6px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 9px 11px;
  border-radius: 9px;
  border: 1px solid var(--border);
  background: var(--card);
  cursor: pointer;
}

.program-card__bar {
  height: 100%;
  border-radius: 4px;
}

.program-card__time {
  font-size: 0.92em;
  color: var(--muted);
}

.program-card__title {
  font-weight: 600;
  margin: 1px 0;
  line-height: 1.25;
}

.program-card__meta {
  font-size: 0.92em;
  color: var(--muted);
}

.program-card__price {
  font-weight: 600;
  white-space: nowrap;
}

.month-schedule__events-more {
  justify-self: start;
  margin-top: 2px;
  border: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-elevated) 80%, transparent);
  color: var(--text);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.92em;
  cursor: pointer;
  transition: background 140ms ease, border-color 140ms ease;
}

.month-schedule__events-more:hover {
  background: color-mix(in srgb, var(--bg-elevated) 90%, transparent);
  border-color: color-mix(in srgb, var(--primary) 45%, var(--border));
}

.program-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  overflow-y: auto;
  z-index: 2100;
}

.program-modal__card {
  width: min(560px, 92vw);
  max-height: 90vh;
  overflow-y: auto;
  background: var(--card);
  border-radius: 14px;
  padding: 24px;
  position: relative;
}

.program-modal__close {
  position: absolute;
  right: 16px;
  top: 16px;
  border: none;
  background: none;
  cursor: pointer;
}

.program-modal__image {
  width: 100%;
  border-radius: 10px;
  margin: 12px 0;
}

.program-modal__desc {
  margin: 0;
  line-height: 1.7;
  color: var(--text);
}

@media (max-width: 720px) {
  .month-schedule {
    padding: 20px 0;
  }

  .month-schedule__month-tab {
    white-space: nowrap;
  }

  .month-schedule__day {
    min-width: 86px;
  }

  .program-card {
    grid-template-columns: 6px 1fr;
  }

  .program-card__price {
    grid-column: 2;
    justify-self: start;
  }

  .program-modal__card {
    width: min(420px, 92vw);
  }
}
</style>
