import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Token accessor will be injected by AuthProvider at runtime
let getToken: () => string | null = () => null
let setRefreshToken: (t: string | null) => void = () => {}
let getRefreshToken: () => string | null = () => null

export function setTokenGetter(getter: () => string | null) {
  getToken = getter
}
export function setRefreshTokenHandlers(setter: (t: string | null) => void, getter: () => string | null) {
  setRefreshToken = setter
  getRefreshToken = getter
}

// Request interceptor: attach Authorization header when token present
api.interceptors.request.use((config: any) => {
  const token = getToken()
  if (token) {
    config.headers = config.headers || {}
    ;(config.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 globally (simple logout hook possibility)
// Simple 401 handler with refresh-token support.
let isRefreshing = false
let refreshQueue: Array<(token: string | null) => void> = []

async function doRefreshToken(): Promise<string | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    const resp = await axios.post(`${API_BASE}/api/auth/refresh`, { refresh })
    const { token: newToken, refresh: newRefresh } = resp.data || {}
    if (newToken) {
      // notify setter
      setRefreshToken(newRefresh || null)
      // set in storage too if getter/setter are wired to localStorage
    }
    return newToken || null
  } catch (err) {
    return null
  }
}

api.interceptors.response.use(
  (res: AxiosResponse) => res,
  async (error: any) => {
    const originalReq = error?.config
    if (error?.response?.status === 401 && !originalReq._retry) {
      if (!isRefreshing) {
        isRefreshing = true
        const newToken = await doRefreshToken()
        isRefreshing = false
        // resolve queued requests
        refreshQueue.forEach((cb) => cb(newToken))
        refreshQueue = []
        if (newToken) {
          // retry the original request with new token
          originalReq._retry = true
          originalReq.headers = originalReq.headers || {}
          originalReq.headers['Authorization'] = `Bearer ${newToken}`
          return axios(originalReq)
        }
      } else {
        // queue the request and return a promise that retries when token available
        return new Promise((resolve, reject) => {
          refreshQueue.push((token) => {
            if (!token) return reject(error)
            originalReq._retry = true
            originalReq.headers = originalReq.headers || {}
            originalReq.headers['Authorization'] = `Bearer ${token}`
            resolve(axios(originalReq))
          })
        })
      }
    }
    return Promise.reject(error)
  }
)

export default api
