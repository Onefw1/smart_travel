import { request } from '../../shared/api/client'
import type { Credentials, Session, User } from './types'

export const authApi = {
  register: (body: Credentials) => request<User>('/auth/register', body),
  login: (body: Credentials) => request<Session>('/auth/login', body),
  me: () => request<Session>('/auth/me'),
  logout: () => request<void>('/auth/logout', {}),
}
