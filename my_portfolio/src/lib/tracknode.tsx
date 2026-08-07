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
  isLoading: boolean;
  error: string;
}

const NAV_ITEMS = [
  { label: "Обо мне", href: "#about" },
  { label: "Услуги", href: "#services" },
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

export const PORTFOLIO_SERVICE_CATEGORY_LABELS: Record<string, string> = {
  development: "Разработка",
  administration: "Администрирование",
  technical_support: "Техническая помощь",
};

const PORTFOLIO_SERVICE_CATEGORY_ORDER = Object.keys(PORTFOLIO_SERVICE_CATEGORY_LABELS);

const DEFAULT_SERVICES = [
  {
    id: "website",
    title: "Разработка сайта",
    description: "Современный сайт под задачи бизнеса: от идеи и дизайна до запуска.",
    category: "development",
    category_label: "Разработка",
    icon: "code",
    is_active: true,
    order: 10,
  },
  {
    id: "site-fixes",
    title: "Доработка существующего сайта",
    description: "Исправление интерфейса, логики, адаптивности и существующих функций.",
    category: "development",
    category_label: "Разработка",
    icon: "wrench",
    is_active: true,
    order: 20,
  },
  {
    id: "shop",
    title: "Интернет-магазин",
    description: "Каталог, карточки товаров, заявки, корзина и необходимые интеграции.",
    category: "development",
    category_label: "Разработка",
    icon: "briefcase",
    is_active: true,
    order: 30,
  },
  {
    id: "api-crm",
    title: "API и CRM интеграции",
    description: "Подключение внешних сервисов, CRM, форм, заявок и обмена данными.",
    category: "development",
    category_label: "Разработка",
    icon: "plug",
    is_active: true,
    order: 40,
  },
  {
    id: "telegram-bots",
    title: "Telegram-боты",
    description: "Боты для заявок, уведомлений, автоматизации и внутренних процессов.",
    category: "development",
    category_label: "Разработка",
    icon: "bot",
    is_active: true,
    order: 50,
  },
  {
    id: "automation",
    title: "Автоматизация процессов",
    description: "Автоматизация повторяющихся операций, интеграции и внутренние инструменты.",
    category: "development",
    category_label: "Разработка",
    icon: "zap",
    is_active: true,
    order: 60,
  },
  {
    id: "server-setup",
    title: "Настройка сервера",
    description: "Подготовка VPS или сервера, установка сервисов и настройка рабочего окружения.",
    category: "administration",
    category_label: "Администрирование",
    icon: "server",
    is_active: true,
    order: 110,
  },
  {
    id: "docker-compose",
    title: "Docker и Docker Compose",
    description: "Контейнеризация приложений, Compose-конфигурации и настройка окружения.",
    category: "administration",
    category_label: "Администрирование",
    icon: "settings",
    is_active: true,
    order: 120,
  },
  {
    id: "nginx",
    title: "Nginx",
    description: "Reverse proxy, домены, статика, маршрутизация и настройка веб-серверов.",
    category: "administration",
    category_label: "Администрирование",
    icon: "server",
    is_active: true,
    order: 130,
  },
  {
    id: "ssl",
    title: "HTTPS / SSL",
    description: "Установка сертификатов, HTTPS, редиректы и проверка безопасного соединения.",
    category: "administration",
    category_label: "Администрирование",
    icon: "shield",
    is_active: true,
    order: 140,
  },
  {
    id: "domains-dns",
    title: "Домены и DNS",
    description: "Настройка DNS-записей, поддоменов и привязка домена к серверу.",
    category: "administration",
    category_label: "Администрирование",
    icon: "globe-2",
    is_active: true,
    order: 150,
  },
  {
    id: "backup",
    title: "Резервное копирование",
    description: "Настройка резервных копий файлов, сервисов и баз данных.",
    category: "administration",
    category_label: "Администрирование",
    icon: "download",
    is_active: true,
    order: 160,
  },
  {
    id: "cryptopro-eds",
    title: "КриптоПро и ЭЦП",
    description: "Установка КриптоПро CSP, сертификатов и настройка электронной подписи.",
    category: "technical_support",
    category_label: "Техническая помощь",
    icon: "key",
    is_active: true,
    order: 210,
  },
  {
    id: "software-setup",
    title: "Установка и настройка ПО",
    description: "Установка программ, компонентов, драйверов и настройка рабочего окружения.",
    category: "technical_support",
    category_label: "Техническая помощь",
    icon: "download",
    is_active: true,
    order: 220,
  },
  {
    id: "windows-linux",
    title: "Windows и Linux",
    description: "Настройка системы, пользователей, прав доступа и решение программных проблем.",
    category: "technical_support",
    category_label: "Техническая помощь",
    icon: "settings",
    is_active: true,
    order: 230,
  },
  {
    id: "vpn-remote-access",
    title: "VPN и удалённый доступ",
    description: "Настройка VPN и безопасного удалённого подключения к компьютеру или серверу.",
    category: "technical_support",
    category_label: "Техническая помощь",
    icon: "network",
    is_active: true,
    order: 240,
  },
  {
    id: "network-equipment",
    title: "Сеть и оборудование",
    description: "Настройка сети, принтеров, сканеров и другого рабочего оборудования.",
    category: "technical_support",
    category_label: "Техническая помощь",
    icon: "settings",
    is_active: true,
    order: 250,
  },
  {
    id: "diagnostics-help",
    title: "Диагностика и техническая помощь",
    description: "Поиск причин ошибок и решение нестандартных программных и системных задач.",
    category: "technical_support",
    category_label: "Техническая помощь",
    icon: "activity",
    is_active: true,
    order: 260,
  },
];

export const DEFAULT_PORTFOLIO_SECTIONS: Record<string, JsonObject> = {
  settings: {
    site_title: "Александр Тишечкин - Full-stack Web Developer",
    logo_text: "Alexandr_Tishechkin",
    logo_image: "",
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
    portrait_image: "",
    portrait_alt: "Александр Тишечкин",
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
    profile_image: "",
    profile_image_alt: "",
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
    logo_image: "",
    description: "Middle Fullstack разработчик. Создаю веб-приложения на Vue.js и Django.",
    nav_title: "Навигация",
    contact_title: "Связаться",
    nav_items: NAV_ITEMS,
    social_links: CONTACTS.filter((item) => item.icon !== "linkedin").map(({ icon, label, href }) => ({ icon, label, href })),
    copyright: "Все права защищены. Разработано с",
  },
};

(DEFAULT_PORTFOLIO_SECTIONS.skills as JsonObject).illustration_image = "";
(DEFAULT_PORTFOLIO_SECTIONS.skills as JsonObject).illustration_alt = "";
(DEFAULT_PORTFOLIO_SECTIONS["why-me"] as JsonObject).illustration_image = "";
(DEFAULT_PORTFOLIO_SECTIONS["why-me"] as JsonObject).illustration_alt = "";
(DEFAULT_PORTFOLIO_SECTIONS.checklist as JsonObject).illustration_image = "";
(DEFAULT_PORTFOLIO_SECTIONS.checklist as JsonObject).illustration_alt = "";
(DEFAULT_PORTFOLIO_SECTIONS.contact as JsonObject).contact_image = "";
(DEFAULT_PORTFOLIO_SECTIONS.contact as JsonObject).contact_image_alt = "";
DEFAULT_PORTFOLIO_SECTIONS.services = {
  title: "Услуги",
  accent: "",
  description: "Разработка, администрирование и техническая помощь — выберите нужное направление.",
  services: DEFAULT_SERVICES,
};

const PortfolioContext = createContext<PortfolioContextValue>({
  site: null,
  sections: DEFAULT_PORTFOLIO_SECTIONS,
  isLoaded: false,
  isLoading: true,
  error: "",
});

const apiBase = () => (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");
const backendBase = () => (import.meta.env.VITE_BACKEND_URL || window.location.origin).replace(/\/$/, "");
const siteSlug = () => import.meta.env.VITE_SITE_SLUG || "my-portfolio";

export function resolveMediaUrl(value: unknown, backendUrl = backendBase()): string {
  const rawValue = typeof value === "string" ? value.trim() : "";
  if (!rawValue) return "";
  if (/^(?:https?:|data:|blob:)/i.test(rawValue)) return rawValue;
  if (rawValue.startsWith("/media/")) {
    return `${backendUrl.replace(/\/$/, "")}${rawValue}`;
  }
  return rawValue;
}

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
      if (item && typeof item === "object") {
        const row = item as JsonObject;
        return String(row.image || row.src || row.url || "");
      }
      return "";
    })
    .map((item) => resolveMediaUrl(item))
    .filter(Boolean);
}

export function normalizeProjectImages(project: JsonObject): string[] {
  const primaryImage = resolveMediaUrl(project.image);
  const galleryImages = normalizeImageList(project.images);
  return [primaryImage, ...galleryImages].filter((item, index, items) => item && items.indexOf(item) === index);
}

export function normalizePortfolioProject(project: JsonObject): JsonObject {
  return {
    ...project,
    techStack: normalizeStringList(project.techStack),
    images: normalizeProjectImages(project),
    image_alt: String(project.image_alt || project.title || ""),
  };
}

export interface PortfolioService {
  id?: string;
  title: string;
  description?: string;
  category?: string;
  category_label?: string;
  icon?: string;
  is_active?: boolean;
  active?: boolean;
  order?: number;
}

export interface PortfolioServiceGroup {
  key: string;
  label: string;
  services: PortfolioService[];
}

export function normalizePortfolioServices(value: unknown): PortfolioService[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item, index) => {
      if (!item || typeof item !== "object") return null;
      const row = item as JsonObject;
      const title = String(row.title || row.label || "").trim();
      if (!title) return null;
      return {
        id: String(row.id || title),
        title,
        description: String(row.description || ""),
        category: normalizeServiceCategoryKey(row.category),
        category_label: normalizeServiceCategoryLabel(row.category, row.category_label),
        icon: String(row.icon || ""),
        is_active: row.is_active !== false && row.active !== false,
        active: row.is_active !== false && row.active !== false,
        order: typeof row.order === "number" ? row.order : index,
      };
    })
    .filter((service): service is PortfolioService => Boolean(service?.is_active))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0) || a.title.localeCompare(b.title));
}

export function groupPortfolioServicesByCategory(services: PortfolioService[]): PortfolioServiceGroup[] {
  const groups = services.reduce<Map<string, PortfolioServiceGroup>>((result, service) => {
    const key = normalizeServiceCategoryKey(service.category);
    const existing = result.get(key);
    if (existing) {
      existing.services.push(service);
    } else {
      result.set(key, {
        key,
        label: normalizeServiceCategoryLabel(key, service.category_label),
        services: [service],
      });
    }
    return result;
  }, new Map());

  return Array.from(groups.values()).sort(
    (a, b) => categoryOrderIndex(a.key) - categoryOrderIndex(b.key) || a.label.localeCompare(b.label),
  );
}

function normalizeServiceCategoryKey(value: unknown): string {
  const rawValue = String(value || "development").trim();
  if (!rawValue) return "development";

  const legacyCategory = Object.entries(PORTFOLIO_SERVICE_CATEGORY_LABELS).find(([, label]) => label === rawValue);
  return legacyCategory ? legacyCategory[0] : rawValue;
}

function normalizeServiceCategoryLabel(category: unknown, label: unknown): string {
  const rawLabel = String(label || "").trim();
  if (rawLabel) return rawLabel;

  const key = normalizeServiceCategoryKey(category);
  return PORTFOLIO_SERVICE_CATEGORY_LABELS[key] || key;
}

function categoryOrderIndex(category: string): number {
  const index = PORTFOLIO_SERVICE_CATEGORY_ORDER.indexOf(category);
  return index === -1 ? PORTFOLIO_SERVICE_CATEGORY_ORDER.length : index;
}

export interface PortfolioLeadPayload {
  name: string;
  phone: string;
  serviceTitle: string;
  comment?: string;
}

export async function submitPortfolioLead(payload: PortfolioLeadPayload) {
  const response = await fetch(`${apiBase()}/public/sites/${encodeURIComponent(siteSlug())}/leads/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: payload.name,
      phone: payload.phone,
      message: payload.comment || "",
      section_key: "contact",
      form_name: "Portfolio contact modal",
      service_type: "my_portfolio_contact",
      service_title: payload.serviceTitle,
      source_url: window.location.href,
      payload: {
        source: "my_portfolio_contact",
        selected_service: payload.serviceTitle,
        comment: payload.comment || "",
        page_path: window.location.pathname,
        referrer: document.referrer || "",
      },
    }),
  });

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message =
      data && typeof data === "object" && "message" in data
        ? String((data as JsonObject).message)
        : "Не удалось отправить заявку. Попробуйте еще раз.";
    throw new Error(message);
  }

  return data;
}

export function usePortfolioSection<T extends JsonObject = JsonObject>(key: string): T {
  const { sections } = useContext(PortfolioContext);
  return (sections[key] || DEFAULT_PORTFOLIO_SECTIONS[key] || {}) as T;
}

export function usePortfolioSite() {
  return useContext(PortfolioContext).site;
}

export function usePortfolioStatus() {
  const { isLoaded, isLoading, error } = useContext(PortfolioContext);
  return { isLoaded, isLoading, error };
}

export function PortfolioProvider({ children }: { children: ReactNode }) {
  const [bundle, setBundle] = useState<PublicBundle>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    const host = window.location.hostname;
    const isLocal = ["localhost", "127.0.0.1", ""].includes(host);
    const primaryUrl = isLocal
      ? `${apiBase()}/sites/${siteSlug()}/`
      : `${apiBase()}/public/by-domain/?domain=${encodeURIComponent(host)}`;
    const fallbackUrl = `${apiBase()}/sites/${siteSlug()}/`;

    const load = async () => {
      setIsLoading(true);
      setError("");
      try {
        const response = await fetch(primaryUrl);
        if (!response.ok) throw new Error(`Public bundle request failed: ${response.status}`);
        const data = (await response.json()) as PublicBundle;
        if (!ignore) setBundle(data);
      } catch (primaryError) {
        try {
          const response = await fetch(fallbackUrl);
          if (!response.ok) throw new Error(`Fallback bundle request failed: ${response.status}`);
          const data = (await response.json()) as PublicBundle;
          if (!ignore) setBundle(data);
        } catch (fallbackError) {
          console.error("Failed to load TrackNode portfolio content", { primaryError, fallbackError });
          if (!ignore) {
            setBundle({});
            setError("Не удалось загрузить актуальные данные сайта. Показана резервная версия.");
          }
        }
      } finally {
        if (!ignore) setIsLoading(false);
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
    applySeo(bundle.site, sections.settings);
    injectTracker(bundle.site?.tracker_key);
  }, [bundle.site, sections]);

  return (
    <PortfolioContext.Provider
      value={{ site: bundle.site || null, sections, isLoaded: Boolean(bundle.site), isLoading, error }}
    >
      {children}
    </PortfolioContext.Provider>
  );
}

export function applySeo(site?: PublicSite, settingsContent: JsonObject = DEFAULT_PORTFOLIO_SECTIONS.settings) {
  const seo = site?.seo || {};
  const settings = settingsContent || DEFAULT_PORTFOLIO_SECTIONS.settings;
  const title = String(seo.title || settings.site_title || document.title);
  const description = String(seo.description || settings.description || "");

  document.title = title;
  setMeta("description", description);
  setMeta("keywords", String(seo.keywords || ""));
  setMeta("og:title", String(seo.og_title || title), "property");
  setMeta("og:description", String(seo.og_description || description), "property");
  setMeta("og:type", "website", "property");
  setMeta("twitter:card", String(seo.twitter_card || "summary_large_image"));

  const ogImage = resolveMediaUrl(String(seo.og_image || ""));
  if (ogImage) setMeta("og:image", ogImage, "property");

  const favicon = resolveMediaUrl(settings.favicon);
  if (favicon) setIconLink(favicon);

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

function setIconLink(href: string) {
  let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
  if (!link) {
    link = document.createElement("link");
    link.rel = "icon";
    document.head.appendChild(link);
  }
  link.href = href;
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
