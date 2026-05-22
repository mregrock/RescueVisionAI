import type {
  AnalyzeRequest,
  AnalyzeResponse,
  HealthResponse,
  Protocol,
  ProtocolsList,
} from './types'

const ENV_BASE = import.meta.env.VITE_API_BASE_URL as string | undefined

const RAW_BASE =
  ENV_BASE === undefined
    ? 'http://localhost:8000'
    : ENV_BASE.replace(/\/$/, '')

export const API_BASE_URL = RAW_BASE
export const API_BASE_LABEL = RAW_BASE || `${window.location.origin} (same origin)`
const API_PREFIX = '/api/v1'

export class ApiError extends Error {
  status: number
  detail?: string

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function parseError(res: Response): Promise<never> {
  let detail: string | undefined
  try {
    const body = await res.json()
    if (typeof body?.detail === 'string') detail = body.detail
    else if (Array.isArray(body?.detail)) detail = JSON.stringify(body.detail)
  } catch {
    // ignore
  }
  const msg =
    detail ||
    (res.status === 404
      ? 'Не найдено'
      : res.status === 422
        ? 'Невалидные данные запроса'
        : res.status >= 500
          ? 'Внутренняя ошибка сервера'
          : `Ошибка ${res.status}`)
  throw new ApiError(msg, res.status, detail)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
      headers: {
        Accept: 'application/json',
        ...(init?.body && !(init.body instanceof FormData)
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...(init?.headers || {}),
      },
      ...init,
    })
  } catch (err) {
    throw new ApiError(
      `Не удалось связаться с backend (${API_BASE_URL}). Проверьте, что сервер запущен.`,
      0,
      err instanceof Error ? err.message : undefined,
    )
  }

  if (!res.ok) {
    await parseError(res)
  }

  return (await res.json()) as T
}

export const api = {
  health(): Promise<HealthResponse> {
    return request<HealthResponse>('/health')
  },
  analyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
    return request<AnalyzeResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },
  analyzeImage(args: {
    image: Blob
    filename?: string
    incident_id: string
    rescuer_id: string
  }): Promise<AnalyzeResponse> {
    const form = new FormData()
    form.append('image', args.image, args.filename ?? 'frame.jpg')
    form.append('incident_id', args.incident_id)
    form.append('rescuer_id', args.rescuer_id)
    return request<AnalyzeResponse>('/analyze/image', {
      method: 'POST',
      body: form,
    })
  },
  listProtocols(): Promise<ProtocolsList> {
    return request<ProtocolsList>('/protocols')
  },
  getProtocol(id: string): Promise<Protocol> {
    return request<Protocol>(`/protocols/${encodeURIComponent(id)}`)
  },
}
