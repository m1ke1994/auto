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
  accent: "и техническая помощь",
  description: "Список редактируется в TrackNode и используется в блоке услуг и форме заявки.",
  services: [
    { id: "website", title: "Разработка сайта", description: "Новый сайт под задачу бизнеса.", category: "Разработка", icon: "code", is_active: true, order: 10 },
    { id: "landing", title: "Лендинг", description: "Одностраничный сайт с понятной структурой и CTA.", category: "Разработка", icon: "layout", is_active: true, order: 20 },
    { id: "corporate", title: "Корпоративный сайт", description: "Страницы, услуги, контакты и управление контентом.", category: "Разработка", icon: "briefcase", is_active: true, order: 30 },
    { id: "shop", title: "Интернет-магазин", description: "Каталог, карточки товаров и базовая интеграция заказов.", category: "Разработка", icon: "cart", is_active: true, order: 40 },
    { id: "site-fixes", title: "Доработка существующего сайта", description: "Правки интерфейса, логики и интеграций.", category: "Разработка", icon: "wrench", is_active: true, order: 50 },
    { id: "bugfix", title: "Исправление ошибок на сайте", description: "Диагностика и исправление проблем в существующем проекте.", category: "Разработка", icon: "bug", is_active: true, order: 60 },
    { id: "responsive", title: "Адаптивная версия сайта", description: "Приведение страниц к нормальной работе на телефонах.", category: "Разработка", icon: "smartphone", is_active: true, order: 70 },
    { id: "api", title: "Интеграция API", description: "Подключение внешних сервисов и обмен данными.", category: "Разработка", icon: "plug", is_active: true, order: 80 },
    { id: "crm", title: "Интеграция CRM", description: "Передача заявок и событий в CRM.", category: "Разработка", icon: "database", is_active: true, order: 90 },
    { id: "telegram-bot", title: "Telegram-бот", description: "Бот для заявок, уведомлений или внутренних процессов.", category: "Разработка", icon: "bot", is_active: true, order: 100 },
    { id: "automation", title: "Автоматизация бизнес-процессов", description: "Скрипты, панели и интеграции для ручных операций.", category: "Разработка", icon: "zap", is_active: true, order: 110 },
    { id: "analytics", title: "Подключение аналитики", description: "События, цели, формы и базовая аналитика сайта.", category: "Разработка", icon: "chart", is_active: true, order: 120 },
    { id: "seo-audit", title: "SEO-аудит", description: "Техническая проверка страниц и базовые рекомендации.", category: "Разработка", icon: "search", is_active: true, order: 130 },
    { id: "competitors", title: "Анализ конкурентов", description: "Сравнение структуры, контента и технических решений.", category: "Разработка", icon: "target", is_active: true, order: 140 },
    { id: "forms", title: "Настройка форм и заявок", description: "Формы, валидация, хранение и уведомления.", category: "Разработка", icon: "inbox", is_active: true, order: 150 },
    { id: "dev-other", title: "Другое по разработке", description: "Нестандартная задача по сайту или веб-сервису.", category: "Разработка", icon: "code", is_active: true, order: 160 },
    { id: "software-install", title: "Установка программного обеспечения", description: "Установка нужных программ и компонентов.", category: "Техническая помощь", icon: "download", is_active: true, order: 210 },
    { id: "software-setup", title: "Настройка программного обеспечения", description: "Настройка программ под рабочие задачи.", category: "Техническая помощь", icon: "settings", is_active: true, order: 220 },
    { id: "cryptopro", title: "Установка и настройка КриптоПро CSP", description: "Подготовка КриптоПро и связанных компонентов.", category: "Техническая помощь", icon: "shield", is_active: true, order: 230 },
    { id: "eds", title: "Настройка электронной подписи / ЭЦП", description: "Настройка ЭЦП, сертификатов и браузера.", category: "Техническая помощь", icon: "key", is_active: true, order: 240 },
    { id: "certificates", title: "Установка сертификатов", description: "Установка и проверка сертификатов.", category: "Техническая помощь", icon: "file-check", is_active: true, order: 250 },
    { id: "browser-eds", title: "Настройка браузера для работы с ЭЦП", description: "Расширения, плагины и параметры браузера.", category: "Техническая помощь", icon: "globe", is_active: true, order: 260 },
    { id: "gov-workplace", title: "Настройка рабочего места для государственных порталов", description: "Подготовка компьютера для порталов и ЭЦП.", category: "Техническая помощь", icon: "landmark", is_active: true, order: 270 },
    { id: "drivers", title: "Установка драйверов", description: "Поиск, установка и проверка драйверов.", category: "Техническая помощь", icon: "hard-drive", is_active: true, order: 280 },
    { id: "windows", title: "Настройка Windows", description: "Система, учетные записи, сеть и рабочее окружение.", category: "Техническая помощь", icon: "monitor", is_active: true, order: 290 },
    { id: "linux", title: "Настройка Linux", description: "Базовая настройка системы и сервисов.", category: "Техническая помощь", icon: "terminal", is_active: true, order: 300 },
    { id: "users", title: "Создание локальных пользователей", description: "Учетные записи и базовые права доступа.", category: "Техническая помощь", icon: "users", is_active: true, order: 310 },
    { id: "permissions", title: "Настройка прав пользователей", description: "Права доступа, группы и ограничения.", category: "Техническая помощь", icon: "lock", is_active: true, order: 320 },
    { id: "office", title: "Установка офисных программ", description: "Офисные пакеты и сопутствующие настройки.", category: "Техническая помощь", icon: "file-text", is_active: true, order: 330 },
    { id: "remote-access", title: "Настройка удаленного доступа", description: "Безопасный доступ к рабочему месту или серверу.", category: "Техническая помощь", icon: "mouse-pointer", is_active: true, order: 340 },
    { id: "vpn", title: "Настройка VPN", description: "Подключение и проверка VPN-доступа.", category: "Техническая помощь", icon: "network", is_active: true, order: 350 },
    { id: "network", title: "Настройка сети", description: "Локальная сеть, доступы и диагностика.", category: "Техническая помощь", icon: "wifi", is_active: true, order: 360 },
    { id: "printer", title: "Настройка принтера / сканера", description: "Подключение, драйверы и проверка печати.", category: "Техническая помощь", icon: "printer", is_active: true, order: 370 },
    { id: "migration", title: "Перенос программ и данных на новый компьютер", description: "Перенос рабочих данных и настройка окружения.", category: "Техническая помощь", icon: "copy", is_active: true, order: 380 },
    { id: "diagnostics", title: "Диагностика программных ошибок", description: "Поиск причин сбоев и рекомендации по исправлению.", category: "Техническая помощь", icon: "activity", is_active: true, order: 390 },
    { id: "docker", title: "Настройка Docker", description: "Контейнеры, compose и окружение сервиса.", category: "Техническая помощь", icon: "container", is_active: true, order: 400 },
    { id: "server", title: "Настройка сервера", description: "Базовая подготовка VPS или выделенного сервера.", category: "Техническая помощь", icon: "server", is_active: true, order: 410 },
    { id: "deploy", title: "Развертывание сайта на сервере", description: "Деплой, переменные окружения и проверка запуска.", category: "Техническая помощь", icon: "upload-cloud", is_active: true, order: 420 },
    { id: "nginx", title: "Настройка Nginx", description: "Проксирование, статика и конфигурация домена.", category: "Техническая помощь", icon: "route", is_active: true, order: 430 },
    { id: "ssl", title: "Настройка HTTPS / SSL", description: "Сертификаты, редиректы и проверка HTTPS.", category: "Техническая помощь", icon: "lock-keyhole", is_active: true, order: 440 },
    { id: "domain", title: "Настройка домена", description: "DNS-записи и привязка домена к сервису.", category: "Техническая помощь", icon: "globe-2", is_active: true, order: 450 },
    { id: "backup", title: "Резервное копирование", description: "Бэкапы файлов, данных и базовая стратегия восстановления.", category: "Техническая помощь", icon: "archive", is_active: true, order: 460 },
    { id: "it-other", title: "Другая техническая помощь", description: "Опишите задачу, если ее нет в списке.", category: "Техническая помощь", icon: "help-circle", is_active: true, order: 470 },
  ],
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
  icon?: string;
  is_active?: boolean;
  order?: number;
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
        category: String(row.category || "Услуги"),
        icon: String(row.icon || ""),
        is_active: row.is_active !== false,
        order: typeof row.order === "number" ? row.order : index,
      };
    })
    .filter((service): service is PortfolioService => Boolean(service?.is_active))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0) || a.title.localeCompare(b.title));
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
