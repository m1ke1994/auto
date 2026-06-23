import { computed, ref } from "vue";
import { getServices } from "../api/services";

const servicesTree = ref([]);
const servicesLoading = ref(false);
const servicesLoaded = ref(false);
const servicesError = ref("");

const toNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeMediaUrl = (value) => {
  const raw = String(value || "").trim();
  if (!raw) return "";
  if (/^(https?:)?\/\//i.test(raw)) return raw;
  return raw.startsWith("/") ? raw : `/${raw}`;
};

const byOrder = (a, b) => {
  const diff = toNumber(a?.order, 0) - toNumber(b?.order, 0);
  if (diff !== 0) return diff;
  return String(a?.title || "").localeCompare(String(b?.title || ""), "ru-RU");
};

const hasChildrenArray = (item) =>
  Array.isArray(item?.children) && item.children.length > 0;

const normalizeTariff = (tariff, index = 0) => ({
  id: tariff?.id ?? `${tariff?.slug || "tariff"}-${index}`,
  slug: String(tariff?.slug || ""),
  title: String(tariff?.title || ""),
  description: String(tariff?.description || ""),
  duration: String(tariff?.duration || tariff?.duration_label || ""),
  actionLabel: String(tariff?.action_label || "Выбрать"),
  actionLink: String(tariff?.action_link || ""),
  price: toNumber(tariff?.price, 0),
  order: toNumber(tariff?.order, index),
});

const extractParentRef = (service) => {
  const parentValue = service?.parent ?? service?.parent_id ?? null;
  if (parentValue == null) {
    return { parentId: null, parentSlug: null };
  }

  if (typeof parentValue === "object") {
    return {
      parentId: parentValue.id ?? parentValue.pk ?? null,
      parentSlug: String(parentValue.slug || "").trim() || null,
    };
  }

  const parentString = String(parentValue).trim();
  if (!parentString) {
    return { parentId: null, parentSlug: null };
  }

  return {
    parentId: parentString,
    parentSlug: /^\d+$/.test(parentString) ? null : parentString,
  };
};

const normalizeServiceBase = (service, index = 0) => {
  const slug = String(service?.slug || "").trim();
  const { parentId, parentSlug } = extractParentRef(service);
  const rawId = service?.id ?? service?.pk ?? (slug || `service-${index}`);
  const imageUrl = normalizeMediaUrl(service?.image_url || service?.image);

  const images = Array.isArray(service?.images)
    ? service.images
        .map((item, imageIndex) => ({
          id: item?.id ?? `image-${imageIndex}`,
          image_url: normalizeMediaUrl(item?.image_url || item?.image),
          order: toNumber(item?.order, imageIndex),
        }))
        .filter((item) => item.image_url)
        .sort((a, b) => a.order - b.order)
    : [];

  return {
    id: rawId,
    slug,
    path: "",
    parentSlug,
    parentId,
    title: String(service?.title || ""),
    fullTitle: String(service?.full_title || service?.fullTitle || ""),
    description: String(service?.description || ""),
    durationLabel: String(service?.duration_label || service?.durationLabel || ""),
    intro: String(service?.intro || ""),
    note: String(service?.note || ""),
    image: imageUrl,
    images,
    gallery: Array.isArray(service?.gallery) ? service.gallery : [],
    contentSections: Array.isArray(service?.content_sections)
      ? service.content_sections
      : Array.isArray(service?.contentSections)
        ? service.contentSections
        : [],
    order: toNumber(service?.order, 0),
    isCategory: Boolean(service?.is_category),
    children: [],
    tariffs: (Array.isArray(service?.tariffs) ? service.tariffs : [])
      .map((item, tariffIndex) => normalizeTariff(item, tariffIndex))
      .sort(byOrder),
  };
};

const normalizeNestedService = (service, parentPath = [], index = 0) => {
  const base = normalizeServiceBase(service, index);
  const pathParts = base.slug ? [...parentPath, base.slug] : [...parentPath];
  const path = pathParts.join("/");

  const children = (Array.isArray(service?.children) ? service.children : [])
    .map((item, childIndex) => normalizeNestedService(item, pathParts, childIndex))
    .sort(byOrder);

  return {
    ...base,
    path: path || String(base.id),
    parentSlug: parentPath[parentPath.length - 1] || null,
    children,
  };
};

const setPathsRecursively = (items, parentPath = []) => {
  items.forEach((item) => {
    const pathParts = item.slug
      ? [...parentPath, item.slug]
      : [...parentPath, String(item.id)];
    item.path = pathParts.join("/");
    item.parentSlug = parentPath[parentPath.length - 1] || null;

    if (item.children.length) {
      setPathsRecursively(item.children, pathParts);
    }
  });
};

const sortRecursively = (items) => {
  items.sort(byOrder);
  items.forEach((item) => {
    if (item.children.length) {
      sortRecursively(item.children);
    }
  });
  return items;
};

const buildTreeFromFlat = (items) => {
  const nodes = items.map((item, index) => normalizeServiceBase(item, index));
  const byId = new Map(nodes.map((node) => [String(node.id), node]));
  const bySlug = new Map(nodes.filter((node) => node.slug).map((node) => [node.slug, node]));

  const roots = [];

  nodes.forEach((node) => {
    const parentById = node.parentId != null ? byId.get(String(node.parentId)) : null;
    const parentBySlug = !parentById && node.parentSlug ? bySlug.get(node.parentSlug) : null;
    const parent = parentById || parentBySlug || null;

    if (parent) {
      parent.children.push(node);
      return;
    }

    roots.push(node);
  });

  sortRecursively(roots);
  setPathsRecursively(roots);
  return roots;
};

const normalizeServices = (items) => {
  if (!items.length) return [];

  if (items.some(hasChildrenArray)) {
    return items
      .map((item, index) => normalizeNestedService(item, [], index))
      .sort(byOrder);
  }

  return buildTreeFromFlat(items);
};

const servicePathIndex = computed(() => {
  const map = new Map();
  const traverse = (items) => {
    items.forEach((item) => {
      if (item.path) {
        map.set(item.path, item);
      }
      if (item.children.length) {
        traverse(item.children);
      }
    });
  };
  traverse(servicesTree.value);
  return map;
});

const flattenServicesWithTariffs = (items) =>
  items.flatMap((item) => {
    const current = item.tariffs.length
      ? [
          {
            id: item.path || item.slug || String(item.id),
            path: item.path,
            title: item.title,
            tariffs: item.tariffs,
          },
        ]
      : [];

    return [...current, ...flattenServicesWithTariffs(item.children)];
  });

export const formatPrice = (price) =>
  `${Number(price || 0).toLocaleString("ru-RU")} ₽`;

export const findMinTariffPrice = (service) => {
  const own = service.tariffs.map((tariff) => tariff.price);
  const nested = service.children.flatMap((child) => {
    const nestedMin = findMinTariffPrice(child);
    return Number.isFinite(nestedMin) ? [nestedMin] : [];
  });
  const prices = [...own, ...nested].filter((price) => Number.isFinite(price) && price > 0);
  return prices.length ? Math.min(...prices) : null;
};

export const loadServices = async ({ force = false } = {}) => {
  if (servicesLoaded.value && !force) return;
  if (servicesLoading.value) return;

  servicesLoading.value = true;
  servicesError.value = "";

  try {
    const payload = await getServices();
    servicesTree.value = normalizeServices(Array.isArray(payload) ? payload : []);
    servicesLoaded.value = true;
  } catch (error) {
    console.error("[services] failed to load", error);
    servicesTree.value = [];
    servicesError.value = "Не удалось загрузить услуги.";
  } finally {
    servicesLoading.value = false;
  }
};

export const useServices = () => {
  const servicesWithTariffs = computed(() => flattenServicesWithTariffs(servicesTree.value));

  const getServiceByPath = (slugPath) => {
    const path = Array.isArray(slugPath)
      ? slugPath.filter(Boolean).join("/")
      : String(slugPath || "").replace(/^\/+|\/+$/g, "");
    return path ? servicePathIndex.value.get(path) || null : null;
  };

  return {
    servicesTree,
    servicesWithTariffs,
    servicesLoading,
    servicesLoaded,
    servicesError,
    getServiceByPath,
    loadServices,
  };
};
