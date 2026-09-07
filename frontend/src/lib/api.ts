import axios from "axios"

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1"
export const authTokenStorageKey = "token"

export const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(authTokenStorageKey)
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface ApiErrorResponse {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}

export interface User {
  id: string
  name: string
  email_address: string
}

export interface TokenResponse {
  access_token: string
  token_type: "bearer"
  expires_in: number
}

export interface LinkItem {
  id: string
  target_url: string
  short_code: string
  short_url: string
  clicks: number
  created_at: string
  updated_at: string
}

export interface LinkListResponse {
  items: LinkItem[]
  total: number
}

export const getApiErrorMessage = (error: unknown, fallback: string) => {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    return error.response?.data?.error?.message || fallback
  }
  return fallback
}

export const registerUser = async (payload: {
  name: string
  email_address: string
  password: string
}) => {
  const response = await api.post<User>("/auth/register", payload)
  return response.data
}

export const loginUser = async (payload: { email_address: string; password: string }) => {
  const response = await api.post<TokenResponse>("/auth/token", payload)
  return response.data
}

export const getCurrentUser = async () => {
  const response = await api.get<User>("/auth/me")
  return response.data
}

export const listLinks = async () => {
  const response = await api.get<LinkListResponse>("/links")
  return response.data
}

export const createLink = async (targetUrl: string) => {
  const response = await api.post<LinkItem>("/links", { target_url: targetUrl })
  return response.data
}
