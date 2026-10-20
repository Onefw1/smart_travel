export type Role = 'user' | 'admin'
export interface User {
  id: string
  username: string
  role: Role
  created_at: string
}
export interface Session {
  user: User
  csrf_token: string
  expires_at: string
}
export interface Credentials { username: string; password: string }
