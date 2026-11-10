export interface HealthInfo {
  status: string
  version: string
  engine: 'lama' | 'opencv'
  model: string | null
  device: string
  model_ready: boolean
  torch_available: boolean
  fallback_reason: string | null
}

export interface InpaintOptions {
  engine: 'auto' | 'lama' | 'opencv'
  refine: boolean
  radius: number
  dilate: number
}

export interface InpaintResult {
  id: number
  url: string
  blob: Blob
  engine: string
  ms: number
  width: number
  height: number
  createdAt: string
}

export interface SourceImage {
  element: HTMLImageElement
  blob: Blob
  name: string
  width: number
  height: number
}

export type Tool = 'brush' | 'eraser' | 'pan'
export type EngineChoice = 'auto' | 'lama' | 'opencv'
export type EngineName = 'lama' | 'opencv'
