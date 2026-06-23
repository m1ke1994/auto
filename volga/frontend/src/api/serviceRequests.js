import { submitLead } from "./leads"

export async function createServiceRequest(payload) {
  return await submitLead({
    section_key: "services",
    form_name: "Service booking",
    name: payload?.name || "",
    contact: payload?.contact || payload?.phone || "",
    message: payload?.message || "",
    service_type: payload?.service_slug || "",
    service_title: payload?.service_title || payload?.service_slug || "",
    payload: {
      service_slug: payload?.service_slug || "",
      tariff_id: payload?.tariff_id ?? null,
      tariff_title: payload?.tariff_title || "",
    },
  })
}
