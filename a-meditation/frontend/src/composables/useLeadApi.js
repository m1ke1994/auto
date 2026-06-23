import { buildApiUrl, siteSlug } from '../config/api'

export async function submitLead(payload) {
  const requestPayload = {
    site_slug: siteSlug,
    source_url: window.location.href,
    ...payload,
  }

  const response = await fetch(buildApiUrl('leads/'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestPayload),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok || data?.success === false) {
    throw new Error(data?.message || 'Не удалось отправить заявку')
  }

  return data
}
