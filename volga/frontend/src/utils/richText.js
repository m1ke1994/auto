const BLOCK_SEPARATOR = /\n{2,}/;
const UNORDERED_LIST_MARKER = /^[-*\u2022]\s+/;
const ALLOWED_TAGS = new Set([
  "p",
  "br",
  "strong",
  "b",
  "em",
  "i",
  "u",
  "s",
  "ul",
  "ol",
  "li",
  "a",
  "blockquote",
]);

const escapeHtml = (value) =>
  String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const normalizeInput = (value) => {
  if (Array.isArray(value)) {
    return value
      .map((item) => String(item || "").trim())
      .filter(Boolean)
      .join("\n\n");
  }

  return String(value || "");
};

const normalizeText = (value) => normalizeInput(value).replace(/\r\n?/g, "\n").trim();

const isUnorderedListLine = (line) => UNORDERED_LIST_MARKER.test(line);
const isOrderedListLine = (line) => /^\d+[.)]\s+/.test(line);

const sanitizeLink = (href) => {
  const value = String(href || "").trim();
  if (!value) return null;

  if (/^(https?:|mailto:|tel:)/i.test(value)) {
    return value;
  }

  return null;
};

const hasHtmlLikeMarkup = (value) => /<\/?[a-z][\s\S]*>/i.test(value || "");

const sanitizeNode = (node, doc) => {
  if (node.nodeType === Node.TEXT_NODE) {
    return doc.createTextNode(node.textContent || "");
  }

  if (node.nodeType !== Node.ELEMENT_NODE) {
    return doc.createTextNode("");
  }

  const tagName = node.tagName.toLowerCase();
  const fragment = doc.createDocumentFragment();

  for (const childNode of Array.from(node.childNodes)) {
    fragment.appendChild(sanitizeNode(childNode, doc));
  }

  if (!ALLOWED_TAGS.has(tagName)) {
    return fragment;
  }

  const element = doc.createElement(tagName);

  if (tagName === "a") {
    const safeHref = sanitizeLink(node.getAttribute("href"));
    if (safeHref) {
      element.setAttribute("href", safeHref);
      element.setAttribute("target", "_blank");
      element.setAttribute("rel", "noopener noreferrer");
    }
  }

  element.appendChild(fragment);
  return element;
};

const sanitizeHtml = (html) => {
  if (typeof window === "undefined" || typeof DOMParser === "undefined") {
    return escapeHtml(html);
  }

  const parser = new DOMParser();
  const parsed = parser.parseFromString(String(html || ""), "text/html");
  const safeDoc = document.implementation.createHTMLDocument("");
  const container = safeDoc.createElement("div");

  for (const node of Array.from(parsed.body.childNodes)) {
    container.appendChild(sanitizeNode(node, safeDoc));
  }

  return container.innerHTML;
};

const lineToHtml = (line) => escapeHtml(line.trim());

const paragraphToHtml = (block) => {
  const lines = block
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) return "";

  if (lines.every(isUnorderedListLine)) {
    const items = lines
      .map((line) => line.replace(UNORDERED_LIST_MARKER, ""))
      .map((item) => `<li>${lineToHtml(item)}</li>`)
      .join("");
    return `<ul>${items}</ul>`;
  }

  if (lines.every(isOrderedListLine)) {
    const items = lines
      .map((line) => line.replace(/^\d+[.)]\s+/, ""))
      .map((item) => `<li>${lineToHtml(item)}</li>`)
      .join("");
    return `<ol>${items}</ol>`;
  }

  const joined = lines.map(lineToHtml).join("<br>");
  return `<p>${joined}</p>`;
};

const textToHtml = (value) => {
  const normalized = normalizeText(value);
  if (!normalized) return "";

  return normalized
    .split(BLOCK_SEPARATOR)
    .map((block) => paragraphToHtml(block))
    .filter(Boolean)
    .join("");
};

export const formatRichText = (value) => {
  const normalized = normalizeText(value);
  if (!normalized) return "";

  if (hasHtmlLikeMarkup(normalized)) {
    return sanitizeHtml(normalized);
  }

  return textToHtml(normalized);
};
