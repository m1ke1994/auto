import { submitLead } from "./leads"

export async function createDayScenario(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : []
  const messageParts = [
    payload?.comment || "",
    payload?.date ? `Дата: ${payload.date}` : "",
    payload?.guests_count ? `Гостей: ${payload.guests_count}` : "",
    payload?.total_price ? `Итого: ${payload.total_price}` : "",
    items.length ? `Программы: ${items.map((item) => item.title).join(", ")}` : "",
  ].filter(Boolean)

  return await submitLead({
    section_key: "feedback",
    form_name: "Day scenario",
    name: payload?.name || "",
    email: payload?.email || "",
    phone: payload?.phone || payload?.email || "",
    message: messageParts.join("\n"),
    service_type: "day-scenario",
    service_title: "Сценарий дня",
    payload: {
      date: payload?.date || "",
      guests_count: payload?.guests_count || null,
      total_price: payload?.total_price || null,
      items,
    },
  })
}
