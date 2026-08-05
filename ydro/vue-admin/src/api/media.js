import http from './http'

const MEDIA_ERROR_MESSAGES = {
  file_required: 'Выберите файл для загрузки.',
  file_too_large: 'Файл слишком большой.',
  invalid_media_type: 'Поддерживаются JPG, PNG, WebP, ICO, MP4 и WebM. SVG не загружается.',
  site_not_found: 'Сайт для загрузки не найден.',
  permission_denied: 'Нет прав на медиатеку этого сайта.',
  media_upload_failed: 'Не удалось загрузить файл.',
}

export function mediaErrorMessage(error, fallback = 'Не удалось выполнить действие с файлом.') {
  const data = error?.response?.data || {}
  const code = String(data.code || '').trim()
  if (code && MEDIA_ERROR_MESSAGES[code]) {
    return MEDIA_ERROR_MESSAGES[code]
  }
  if (typeof data.detail === 'string' && data.detail) {
    return data.detail
  }
  return fallback
}

export async function listMediaFiles({ site, fileType, search = '' }) {
  const { data } = await http.get('/api/client/media/', {
    params: {
      site,
      file_type: fileType,
      search: search || undefined,
    },
  })
  return Array.isArray(data) ? data : data?.results || []
}

export async function uploadMediaFile({ file, site, section, field }) {
  const formData = new FormData()
  formData.append('file', file)
  if (site !== undefined && site !== null && site !== '') {
    formData.append('site', String(site))
  }
  if (section !== undefined && section !== null && section !== '') {
    formData.append('section', String(section))
  }
  if (field !== undefined && field !== null && field !== '') {
    formData.append('field', String(field))
  }

  const { data } = await http.post('/api/uploads/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function updateMediaFile(id, payload) {
  const { data } = await http.patch(`/api/client/media/${id}/`, payload)
  return data
}

export async function deleteMediaFile(id) {
  await http.delete(`/api/client/media/${id}/`)
}
