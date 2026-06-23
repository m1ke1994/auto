import { buildApiUrl, siteSlug } from "../config/api"

function splitContact(rawContact, explicitPhone = "", explicitEmail = "") {
  const contact = String(rawContact || "").trim()
  let phone = String(explicitPhone || "").trim()
  let email = String(explicitEmail || "").trim()

  if (contact && contact.includes("@") && !email) {
    email = contact
  } else if (contact && !phone) {
    phone = contact
  }

  return { phone, email }
}

export async function submitLead(payload) {
  const { phone, email } = splitContact(payload?.contact, payload?.phone, payload?.email)
  const requestPayload = {
    site_slug: siteSlug,
    section_key: payload?.section_key || "",
    form_name: payload?.form_name || "",
    name: String(payload?.name || "").trim(),
    phone: phone || email,
    email,
    message: String(payload?.message || "").trim(),
    service_type: String(payload?.service_type || payload?.service_slug || "").trim(),
    service_title: String(payload?.service_title || "").trim(),
    source_url: typeof window !== "undefined" ? window.location.href : "",
    payload: payload?.payload && typeof payload.payload === "object" ? payload.payload : {},
  }

  const response = await fetch(buildApiUrl("leads/"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(requestPayload),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok || data?.success === false) {
    throw new Error(data?.message || "Не удалось отправить заявку. Попробуйте снова.")
  }

  return data
}
