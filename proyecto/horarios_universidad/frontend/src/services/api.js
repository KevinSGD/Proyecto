const API_BASE_URL = import.meta.env.DEV
  ? '/api'
  : (import.meta.env.VITE_API_BASE_URL || 'https://tesisomuerte-production-6d83.up.railway.app/api')

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`

  let response
  try {
    response = await fetch(url, options)
  } catch (error) {
    throw new Error(`No se pudo conectar con la API en ${url}. Verifica que esté levantada.`)
  }

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const body = isJson ? await response.json().catch(() => ({})) : await response.text().catch(() => '')

  if (!response.ok) {
    const detail = typeof body === 'object' ? body?.detail : body
    throw new Error(detail || `HTTP ${response.status} al llamar ${path}`)
  }

  return body
}

export function getApiHealth() {
  return request('/health')
}

export function getDbHealth() {
  return request('/db/health')
}

export function saveData(payload) {
  return request('/save-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getMaterias() {
  return request('/materias')
}

export function getProfesores() {
  return request('/profesores')
}

export function clearData() {
  return request('/clear-data', { method: 'DELETE' })
}

export function runScheduler(payload) {
  return request('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getRunSchedulerStatus(jobId) {
  return request(`/run/${jobId}`)
}

export function verifySchedule(eventos) {
  return request('/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ eventos }),
  })
}
