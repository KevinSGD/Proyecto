'use client'

import { useEffect, useRef } from 'react'
import { Terminal, X } from 'lucide-react'
import Card from '@/components/ui/Card'
import type { ExecutionLogEntry } from '@/lib/types/scheduling'

const STAGE_ORDER = [
  'inicializando',
  'validando',
  'construyendo_modelo',
  'generando_variables',
  'aplicando_restricciones',
  'optimizando',
  'extrayendo_solucion',
  'guardando',
  'publicado',
]

const STAGE_LABELS: Record<string, string> = {
  inicializando: 'Inicializando',
  validando: 'Validando datos',
  construyendo_modelo: 'Construyendo modelo',
  generando_variables: 'Generando variables',
  aplicando_restricciones: 'Aplicando restricciones',
  optimizando: 'Optimizando (CP-SAT)',
  extrayendo_solucion: 'Extrayendo solución',
  guardando: 'Guardando resultados',
  publicado: 'Completado',
}

const TERMINAL_STATUSES = ['optimal', 'feasible', 'published', 'blocked', 'error']

interface Props {
  status: string
  logs: ExecutionLogEntry[]
  onDismiss?: () => void
}

function currentStage(logs: ExecutionLogEntry[]): string | null {
  for (let i = logs.length - 1; i >= 0; i--) {
    const stage = logs[i].metadata?.stage
    if (typeof stage === 'string') return stage
  }
  return null
}

export default function GenerationProgress({ status, logs, onDismiss }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const isError = status === 'error'
  const isDone = TERMINAL_STATUSES.includes(status) && !isError
  const stage = currentStage(logs)
  const stageIndex = stage ? STAGE_ORDER.indexOf(stage) : -1
  const progressPct = isDone ? 100 : stageIndex >= 0 ? Math.round(((stageIndex + 1) / STAGE_ORDER.length) * 100) : 5

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [logs])

  return (
    <Card>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="size-4 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">
              {isError ? 'Ejecución fallida' : isDone ? 'Ejecución completada' : (stage ? STAGE_LABELS[stage] ?? stage : 'Iniciando...')}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{progressPct}%</span>
            {(isDone || isError) && onDismiss && (
              <button onClick={onDismiss} aria-label="Cerrar" className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground">
                <X className="size-3.5" />
              </button>
            )}
          </div>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={`h-full rounded-full transition-all duration-500 ${isError ? 'bg-danger' : isDone ? 'bg-success' : 'bg-primary'}`}
            style={{ width: `${progressPct}%` }}
          />
        </div>

        <div
          ref={scrollRef}
          className="max-h-64 overflow-y-auto rounded-lg bg-foreground/95 p-3 font-mono text-[11px] leading-relaxed text-background"
        >
          {logs.length === 0 ? (
            <p className="opacity-60">Esperando eventos del solver...</p>
          ) : (
            logs.map(l => (
              <div key={l.id} className="flex gap-2">
                <span className="shrink-0 opacity-50">
                  {l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : ''}
                </span>
                <span className={l.eventType === 'error' ? 'text-danger' : ''}>{l.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  )
}
