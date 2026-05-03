const API_BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    let detail = '请求失败，请稍后重试。'
    try {
      const data = await response.json()
      detail = typeof data.detail === 'string' ? data.detail : detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }

  return response.json()
}

export function analyzeVideo(url) {
  return request('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
}

export function createDownloadJob(url, formatId, qualityLabel) {
  return request('/api/jobs', {
    method: 'POST',
    body: JSON.stringify({
      url,
      format_id: formatId,
      quality_label: qualityLabel,
    }),
  })
}

export function getJob(jobId) {
  return request(`/api/jobs/${jobId}`)
}
