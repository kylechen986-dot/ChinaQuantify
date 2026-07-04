import axios from 'axios'

import type { ApiResponse } from '../types/api'

export const http = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export async function getData<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await http.get<ApiResponse<T>>(url, { params })
  return response.data.data
}

export async function postData<T>(url: string): Promise<T> {
  const response = await http.post<ApiResponse<T>>(url)
  return response.data.data
}
