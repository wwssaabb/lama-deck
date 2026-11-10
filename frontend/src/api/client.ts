import axios from 'axios'
import type { HealthInfo, InpaintOptions } from '../types'

const http = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await http.get<HealthInfo>('/health')
  return res.data
}

export interface InpaintResponse {
  blob: Blob
  engine: string
  ms: number
}

async function readDetail(payload: unknown): Promise<string | null> {
  try {
    const text =
      payload instanceof Blob
        ? await payload.text()
        : typeof payload === 'string'
          ? payload
          : JSON.stringify(payload ?? '')
    if (!text) return null
    const parsed = JSON.parse(text) as { detail?: unknown }
    return typeof parsed.detail === 'string' ? parsed.detail : null
  } catch {
    return null
  }
}

export async function inpaint(
  image: Blob,
  mask: Blob,
  options: InpaintOptions,
): Promise<InpaintResponse> {
  const form = new FormData()
  form.append('image', image, 'image.png')
  form.append('mask', mask, 'mask.png')
  form.append('options', JSON.stringify(options))

  try {
    const res = await http.post('/inpaint', form, {
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const engine = String(res.headers['x-inpaint-engine'] ?? 'unknown')
    const ms = Number(res.headers['x-inpaint-ms'] ?? 0)
    return { blob: res.data as Blob, engine, ms: Number.isFinite(ms) ? ms : 0 }
  } catch (err) {
    if (axios.isAxiosError(err) && err.response) {
      const detail = await readDetail(err.response.data)
      throw new Error(detail ?? `修复失败（HTTP ${err.response.status}）`)
    }
    if (err instanceof Error && err.message) throw err
    throw new Error('网络请求失败，请确认后端已启动')
  }
}
