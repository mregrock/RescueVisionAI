export function shortId(prefix = 'id'): string {
  const rnd = Math.random().toString(36).slice(2, 8)
  const ts = Date.now().toString(36).slice(-4)
  return `${prefix}-${ts}${rnd}`
}
