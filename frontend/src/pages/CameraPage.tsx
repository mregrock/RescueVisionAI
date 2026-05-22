import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { AnalyzeResponse } from '../api/types'
import { AnalysisResult } from '../components/AnalysisResult'
import { ErrorView, Spinner } from '../components/states'
import { shortId } from '../utils/ids'

type CamState =
  | { kind: 'idle' }
  | { kind: 'starting' }
  | { kind: 'live' }
  | { kind: 'cam_error'; message: string }

type AnalyzeState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'success'; data: AnalyzeResponse; previewUrl: string }
  | { kind: 'error'; message: string }

export function CameraPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const previewUrlRef = useRef<string | null>(null)

  const [cam, setCam] = useState<CamState>({ kind: 'idle' })
  const [analyze, setAnalyze] = useState<AnalyzeState>({ kind: 'idle' })

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setCam({ kind: 'idle' })
  }, [])

  const startCamera = useCallback(async () => {
    setCam({ kind: 'starting' })
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Браузер не поддерживает getUserMedia')
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => undefined)
      }
      setCam({ kind: 'live' })
    } catch (err) {
      setCam({
        kind: 'cam_error',
        message:
          err instanceof Error
            ? err.message
            : 'Не удалось получить доступ к камере',
      })
    }
  }, [])

  useEffect(() => {
    return () => {
      stopCamera()
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
        previewUrlRef.current = null
      }
    }
  }, [stopCamera])

  const snapAndSend = useCallback(async () => {
    const video = videoRef.current
    if (!video || video.readyState < 2) return

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    const blob: Blob | null = await new Promise((resolve) =>
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.85),
    )
    if (!blob) {
      setAnalyze({ kind: 'error', message: 'Не удалось сделать снимок' })
      return
    }

    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current)
    const previewUrl = URL.createObjectURL(blob)
    previewUrlRef.current = previewUrl

    setAnalyze({ kind: 'loading' })
    try {
      const data = await api.analyzeImage({
        image: blob,
        filename: 'frame.jpg',
        incident_id: shortId('inc'),
        rescuer_id: 'resc-demo',
      })
      setAnalyze({ kind: 'success', data, previewUrl })
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Неизвестная ошибка'
      setAnalyze({ kind: 'error', message })
    }
  }, [])

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">
          Камера · real-режим
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Снимок с камеры устройства отправляется на{' '}
          <code className="font-mono text-xs">POST /analyze/image</code>. Для
          работы нужен HTTPS или localhost.
        </p>
      </header>

      <div className="card space-y-3">
        <div className="relative overflow-hidden rounded-xl bg-black aspect-video">
          <video
            ref={videoRef}
            playsInline
            muted
            className="h-full w-full object-cover"
          />
          {cam.kind !== 'live' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/60 text-slate-300 text-sm">
              {cam.kind === 'starting' ? (
                <>
                  <Spinner /> Включаем камеру…
                </>
              ) : cam.kind === 'cam_error' ? (
                <div className="text-red-300 text-center px-4">
                  {cam.message}
                </div>
              ) : (
                <div>Камера выключена</div>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          {cam.kind !== 'live' ? (
            <button
              type="button"
              onClick={startCamera}
              disabled={cam.kind === 'starting'}
              className="btn-primary w-full sm:w-auto"
            >
              {cam.kind === 'starting' && <Spinner />}
              Включить камеру
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={snapAndSend}
                disabled={analyze.kind === 'loading'}
                className="btn-primary w-full sm:w-auto text-lg px-6 py-4"
              >
                {analyze.kind === 'loading' && <Spinner />}
                {analyze.kind === 'loading'
                  ? 'Анализируем кадр…'
                  : 'Сделать снимок и анализировать'}
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="btn-ghost w-full sm:w-auto"
              >
                Остановить камеру
              </button>
            </>
          )}
        </div>
      </div>

      <section>
        {analyze.kind === 'idle' && cam.kind === 'live' && (
          <div className="card text-sm text-slate-400">
            Наведите камеру на сцену и нажмите «Сделать снимок».
          </div>
        )}
        {analyze.kind === 'loading' && (
          <div className="card flex items-center gap-3 text-slate-200">
            <Spinner /> Отправляем кадр в backend…
          </div>
        )}
        {analyze.kind === 'error' && (
          <ErrorView
            title="Не удалось проанализировать кадр"
            message={analyze.message}
            onRetry={snapAndSend}
          />
        )}
        {analyze.kind === 'success' && (
          <div className="space-y-4">
            <div className="card">
              <div className="text-xs uppercase tracking-wider text-slate-500">
                Отправленный кадр
              </div>
              <img
                src={analyze.previewUrl}
                alt="snapshot"
                className="mt-2 max-h-80 w-full rounded-xl object-contain bg-black"
              />
            </div>
            <AnalysisResult result={analyze.data} />
          </div>
        )}
      </section>
    </div>
  )
}
