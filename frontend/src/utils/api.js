import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export const recon = {
  start: (target) => api.post('/recon/start', target),
  status: () => api.get('/recon/status'),
  clear: () => api.delete('/recon/clear'),
}

export const graph = {
  full: () => api.get('/graph/full'),
  attackPaths: () => api.get('/graph/attack-paths'),
  statistics: () => api.get('/graph/statistics'),
}

export const misconfigs = {
  list: () => api.get('/misconfigs/'),
}

export const reports = {
  generate: (req) => api.post('/reports/generate', req),
  list: () => api.get('/reports/list'),
  downloadUrl: (filename) => `/api/reports/download/${filename}`,
}

export default api
