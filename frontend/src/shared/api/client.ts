export interface FieldError { field: string; message: string }

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: FieldError[] = [],
  ) { super(message) }
}

let csrfToken: string | null = null
let unauthorized: () => void = () => {}

export function setCsrfToken(value: string | null) { csrfToken = value }
export function onUnauthorized(handler: () => void) { unauthorized = handler }

export async function request<T>(path: string, body?: unknown): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)
  try {
    const headers: Record<string, string> = {}
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json'
      if (csrfToken) headers['X-CSRF-Token'] = csrfToken
    }
    const response = await fetch(`/api/v1${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      credentials: 'same-origin', headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
    if (response.status === 401) unauthorized()
    if (response.status === 204) return undefined as T
    const data = await response.json()
    if (!response.ok) {
      throw new ApiError(response.status, data.error?.code ?? 'HTTP_ERROR',
        data.error?.message ?? '请求失败，请稍后重试', data.error?.details ?? [])
    }
    return data as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(0, 'NETWORK_ERROR', '暂时无法连接服务，请检查网络后重试')
  } finally {
    clearTimeout(timer)
  }
}
