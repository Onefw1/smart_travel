import type { Credentials } from './types'

export function validateCredentials(value: Credentials): Record<string, string> {
  const errors: Record<string, string> = {}
  const username = value.username.trim()
  if (!/^[\u3400-\u4dbf\u4e00-\u9fffA-Za-z0-9_]{3,20}$/u.test(username)) {
    errors.username = '用户名需为 3～20 个中文、英文字母、数字或下划线'
  }
  if (Array.from(value.password).length < 8 || Array.from(value.password).length > 64) {
    errors.password = '密码需为 8～64 个字符'
  }
  return errors
}
