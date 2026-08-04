import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { projects as localProjects, categories as localCategories } from "@/data/projects";
import { skillGroups as localSkillGroups } from "@/data/skills";

type JsonObject = Record<string, unknown>;

interface PublicSite {
  id: number;
  name: string;
  slug: string;
  domain: string;
  seo?: JsonObject;
  tracker_key?: string;
}

interface PublicSection {
  key: string;
  title: string;
  content?: JsonObject;
}

interface PublicBundle {
  site?: PublicSite;
  sections?: PublicSection[];
}

interface PortfolioContextValue {
  site: PublicSite | null;
  sections: Record<string, JsonObject>;
  isLoaded: boolean;
}

const NAV_ITEMS = [
  { label: "Обо мне", href: "#about" },
  { label: "Навыки", href: "#skills" },
  { label: "Проекты", href: "#projects" },
  { label: "Контакты", href: "#contact" },
];

const CONTACTS = [
  { icon: "message", label: "Telegram", value: "@M1ke994", href: "https://t.me/M1ke994" },
  { icon: "mail", label: "Email", value: "Tishechkin1994@gmail.com", href: "mailto:Tishechkin1994@gmail.com" },
  { icon: "github", label: "GitHub", value: "github.com/m1ke1994", href: "https://github.com/m1ke1994" },
  {
    icon: "instagram",
    label: "Instagram",
    value: "instagram.com/alexandr_tishechkin",
    href: "https://instagram.com/alexandr_tishechkin",
  },
  {
    icon: "linkedin",
    label: "LinkedIn",
    value: "linkedin.com/in/alexandr-tishechkin",
    href: "https://linkedin.com/in/alexandr-tishechkin",
  },
];

export const DEFAULT_PORTFOLIO_SECTIONS: Record<string, JsonObject> = {
  settings: {
    site_title: "Александр Тишечкин - Full-stack Web Developer",
    logo_text: "Alexandr_Tishechkin",
    description: "Middle Fullstack разработчик. Создаю веб-приложения на Vue.js и Django.",
    favicon: "/favicon.ico",
    contacts: CONTACTS,
    nav_items: NAV_ITEMS,
  },
  hero: {
    status_text: "Открыт для проектов",
    title: "Создаю современные веб-приложения",
    accent_title: "Web Developer",
    subtitle: "Vue.js + Django • REST API • Fixing & Building Web Apps",
    primary_button_text: "Смотреть проекты",
    primary_button_target: "#projects",
    secondary_button_text: "Связаться",
    secondary_button_target: "#contact",
    badges: [
      { icon: "code", label: "Fullstack" },
      { icon: "briefcase", label: "Проектная работа" },
      { icon: "wrench", label: "Поддержка / доработки" },
      { icon: "user", label: "Самозанятый" },
    ],
  },
  about: {
    title: "Обо",
    accent: "мне",
    paragraphs: [
      { text: "Я fullstack-разработчик с опытом создания веб-приложений на стеке Vue.js + Django. Работаю с проектами от MVP до production-ready решений." },
      { text: "Моя сильная сторона — быстро разбираться в чужом коде, находить и исправлять проблемы, доводить задачи до рабочего результата. Понимаю полный цикл разработки: от проектирования БД и API до frontend-компонентов и деплоя." },
      { text: "Открыт для проектной работы, доработки существующих систем и долгосрочного сотрудничества." },
    ],
    services_title: "Чем я могу помочь",
    services: [
      { icon: "code", title: "Разработка веб-приложений", description: "SPA, дашборды, CRM-системы под ваши бизнес-задачи" },
      { icon: "refresh", title: "Доработка и стабилизация", description: "Исправление багов, рефакторинг, оптимизация legacy-кода" },
      { icon: "plug", title: "API и интеграции", description: "REST API, webhooks, подключение внешних сервисов" },
      { icon: "bot", title: "Telegram-боты", description: "Боты для автоматизации процессов и работы с клиентами" },
      { icon: "server", title: "Деплой и инфраструктура", description: "VPS, Docker, Nginx — настройка и поддержка окружений" },
    ],
  },
  skills: {
    title: "Технические",
    accent: "навыки",
    description: "Стек технологий, с которыми работаю ежедневно на уровне профессионала.",
    groups: localSkillGroups.map(({ id, title, skills }) => ({
      id,
      title,
      icon: id === "backend" ? "server" : id === "tools" ? "wrench" : id === "practices" ? "book" : "code",
      skills: skills.map((label) => ({ label })),
    })),
  },
  projects: {
    title: "Мои",
    accent: "проекты",
    description: "Примеры работ из разных сфер — от сервисов и дашбордов до лендингов",
    categories: localCategories,
    projects: localProjects,
  },
  "why-me": {
    title: "Почему",
    accent: "я подойду",
    description: "Качества, которые ценят работодатели и заказчики",
    reasons: [
      { icon: "code", text: "Быстро разбираюсь в чужом коде и legacy-проектах" },
      { icon: "target", text: "Довожу задачи до рабочего результата" },
      { icon: "layout", text: "Понимаю полный цикл: frontend + backend + деплой" },
      { icon: "users", text: "Умею оценивать сроки/риски, коммуницировать с командой" },
      { icon: "shield", text: "Аккуратность к деталям UI и API-контрактам" },
      { icon: "zap", text: "Могу брать ответственность за модуль или фичу" },
      { icon: "bug", text: "Умею фиксить прод-проблемы и стабилизировать систему" },
    ],
  },
  checklist: {
    title: "Компетенции, закрывающие задачи",
    accent: "веб-разработки",
    description: "Чек-лист компетенций, которыми я владею",
    items: [
      { text: "Самостоятельно реализовывать фичи end-to-end (UI → API → БД)" },
      { text: "Работать с Git-ветками, PR, код-ревью" },
      { text: "Понимать архитектуру проекта, слои, разделение ответственности" },
      { text: "Уверенно работать с REST, статус-кодами, контрактами, валидацией" },
      { text: "Уметь диагностировать баги (логи, воспроизведение, фиксы)" },
      { text: "Писать понятный код, соблюдать стиль, делать рефакторинг" },
      { text: "Базово понимать деплой и окружения (dev/stage/prod)" },
      { text: "Коммуницировать: уточнять требования, предлагать решения, оценивать сроки" },
    ],
  },
  contact: {
    title: "Контакты",
    description: "Свяжитесь со мной удобным способом — я отвечу на все вопросы.",
    contacts: CONTACTS,
  },
  footer: {
    logo_text: "Alexandr_Tishechkin",
    description: "Middle Fullstack разработчик. Создаю веб-приложения на Vue.js и Django.",
    nav_title: "Навигация",
    contact_title: "Связаться",
    nav_items: NAV_ITEMS,
    social_links: CONTACTS.filter((item) => item.icon !== "linkedin").map(({ icon, label, href }) => ({ icon, label, href })),
    copyright: "Все права защищены. Разработано с",
  },
};

const PortfolioContext = createContext<PortfolioContextValue>({
  site: null,
  sections: DEFAULT_PORTFOLIO_SECTIONS,
  isLoaded: false,
});

const apiBase = () => (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");
const backendBase = () => (import.meta.env.VITE_BACKEND_URL || window.location.origin).replace(/\/$/, "");
const siteSlug = () => import.meta.env.VITE_SITE_SLUG || "my-portfolio";

export function mergePortfolioContent(base: Record<string, JsonObject>, remoteSections: PublicSection[] = []) {
  return remoteSections.reduce<Record<string, JsonObject>>((result, section) => {
    const remoteContent = section.content && typeof section.content === "object" ? section.content : {};
    result[section.key] = { ...(result[section.key] || {}), ...remoteContent };
    return result;
  }, { ...base });
}

export function normalizeStringList(value: unknown, key = "label"): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") return String((item as JsonObject)[key] || "");
      return "";
    })
    .filter(Boolean);
}

export function normalizeImageList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") return String((item as JsonObject).src || (item as JsonObject).url || "");
      return "";
    })
    .filter(Boolean);
}

export function usePortfolioSection<T extends JsonObject = JsonObject>(key: string): T {
  const { sections } = useContext(PortfolioContext);
  return (sections[key] || DEFAULT_PORTFOLIO_SECTIONS[key] || {}) as T;
}

export function usePortfolioSite() {
  return useContext(PortfolioContext).site;
}

export function PortfolioProvider({ children }: { children: ReactNode }) {
  const [bundle, setBundle] = useState<PublicBundle>({});

  useEffect(() => {
    let ignore = false;
    const host = window.location.hostname;
    const isLocal = ["localhost", "127.0.0.1", ""].includes(host);
    const primaryUrl = isLocal
      ? `${apiBase()}/sites/${siteSlug()}/`
      : `${apiBase()}/public/by-domain/?domain=${encodeURIComponent(host)}`;
    const fallbackUrl = `${apiBase()}/sites/${siteSlug()}/`;

    const load = async () => {
      try {
        const response = await fetch(primaryUrl);
        if (!response.ok) throw new Error(`Public bundle request failed: ${response.status}`);
        const data = (await response.json()) as PublicBundle;
        if (!ignore) setBundle(data);
      } catch {
        try {
          const response = await fetch(fallbackUrl);
          if (!response.ok) throw new Error(`Fallback bundle request failed: ${response.status}`);
          const data = (await response.json()) as PublicBundle;
          if (!ignore) setBundle(data);
        } catch {
          if (!ignore) setBundle({});
        }
      }
    };

    load();
    return () => {
      ignore = true;
    };
  }, []);

  const sections = useMemo(
    () => mergePortfolioContent(DEFAULT_PORTFOLIO_SECTIONS, bundle.sections || []),
    [bundle.sections],
  );

  useEffect(() => {
    applySeo(bundle.site);
    injectTracker(bundle.site?.tracker_key);
  }, [bundle.site]);

  return (
    <PortfolioContext.Provider value={{ site: bundle.site || null, sections, isLoaded: Boolean(bundle.site) }}>
      {children}
    </PortfolioContext.Provider>
  );
}

function applySeo(site?: PublicSite) {
  const seo = site?.seo || {};
  const settings = DEFAULT_PORTFOLIO_SECTIONS.settings;
  const title = String(seo.title || settings.site_title || document.title);
  const description = String(seo.description || settings.description || "");

  document.title = title;
  setMeta("description", description);
  setMeta("keywords", String(seo.keywords || ""));
  setMeta("og:title", String(seo.og_title || title), "property");
  setMeta("og:description", String(seo.og_description || description), "property");
  setMeta("og:type", "website", "property");
  setMeta("twitter:card", String(seo.twitter_card || "summary_large_image"));

  const ogImage = String(seo.og_image || "");
  if (ogImage) setMeta("og:image", ogImage, "property");

  const canonical = String(seo.canonical || `${window.location.origin}/`);
  let link = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!link) {
    link = document.createElement("link");
    link.rel = "canonical";
    document.head.appendChild(link);
  }
  link.href = canonical;
}

function setMeta(name: string, content: string, attr: "name" | "property" = "name") {
  if (!content) return;
  let meta = document.querySelector<HTMLMetaElement>(`meta[${attr}="${name}"]`);
  if (!meta) {
    meta = document.createElement("meta");
    meta.setAttribute(attr, name);
    document.head.appendChild(meta);
  }
  meta.content = content;
}

function injectTracker(trackerKey?: string) {
  if (!trackerKey || document.querySelector("script[data-tracknode-portfolio-tracker]")) return;
  const script = document.createElement("script");
  script.src = `${backendBase()}/tracker.js`;
  script.async = true;
  script.defer = true;
  script.dataset.siteKey = trackerKey;
  script.dataset.apiKey = trackerKey;
  script.dataset.tracknodePortfolioTracker = "1";
  document.head.appendChild(script);
}
