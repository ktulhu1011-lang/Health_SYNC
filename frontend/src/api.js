import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({ baseURL: BASE })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const auth = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
}

export const habits = {
  today: () => api.get('/habits/today'),
  history: (days = 30, category = null) =>
    api.get('/habits/history', { params: { days, ...(category && { category }) } }),
  heatmap: (days = 90) => api.get('/habits/heatmap', { params: { days } }),
}

export const metrics = {
  daily: (days = 30) => api.get('/metrics/daily', { params: { days } }),
  dailyByDate: (date) => api.get(`/metrics/daily/${date}`),
  correlations: (days = 30) => api.get('/metrics/correlations', { params: { days } }),
  syncNow: () => api.post('/metrics/garmin/sync'),
  saveGarminCredentials: (email, password) =>
    api.post('/metrics/garmin/credentials', { email, password }),
}

export const heart = {
  intraday: (date) => api.get('/heart/intraday', { params: { target_date: date } }),
  activities: (date) => api.get('/heart/activities', { params: { target_date: date } }),
  recentActivities: (days = 14) => api.get('/heart/activities', { params: { days } }),
  trend: (days = 30) => api.get('/heart/trend', { params: { days } }),
}

export const insights = {
  list: (limit = 20) => api.get('/insights/', { params: { limit } }),
  generate: (days = 30) => api.post('/insights/generate', null, { params: { days } }),
  ask: (question, days = 30) => api.post('/insights/ask', { question, days }),
  getSettings: () => api.get('/insights/settings'),
  updateSettings: (data) => api.put('/insights/settings', data),
}

export const exportData = {
  csvUrl: (days = 3650) => {
    const token = localStorage.getItem('token')
    const base = import.meta.env.VITE_API_URL || '/api'
    return `${base}/export/csv?days=${days}&token=${token}`
  },
  downloadCsv: async (days = 3650) => {
    const token = localStorage.getItem('token')
    const base = import.meta.env.VITE_API_URL || '/api'
    const resp = await fetch(`${base}/export/csv?days=${days}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    const blob = await resp.blob()
    const cd = resp.headers.get('content-disposition') || ''
    const match = cd.match(/filename=(.+)/)
    const filename = match ? match[1] : 'healthsync.csv'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }
}

export default api
