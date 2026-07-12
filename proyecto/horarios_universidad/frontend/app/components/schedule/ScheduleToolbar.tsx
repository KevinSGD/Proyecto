'use client'

import { ZoomIn, ZoomOut, Grid3X3, GanttChart } from 'lucide-react'
import { FilterSelect } from '@/components/ui/Field'
import type { ViewMode, GridType } from './types'
import { VIEW_MODE_LABELS } from './types'

interface ScheduleToolbarProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  gridType: GridType
  onGridTypeChange: (type: GridType) => void
  zoom: number
  onZoomChange: (zoom: number) => void
  availableViewModes?: ViewMode[]
  runSelector?: React.ReactNode
}

const ZOOM_LEVELS = [0.75, 1, 1.25, 1.5]

export default function ScheduleToolbar({
  viewMode,
  onViewModeChange,
  gridType,
  onGridTypeChange,
  zoom,
  onZoomChange,
  availableViewModes = ['docente', 'salon', 'materia', 'grupo', 'area', 'global'],
  runSelector,
}: ScheduleToolbarProps) {
  const zoomIdx = ZOOM_LEVELS.indexOf(zoom)

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        {runSelector}

        <FilterSelect
          value={viewMode}
          onChange={v => onViewModeChange(v as ViewMode)}
          placeholder="Vista"
          options={availableViewModes}
          labels={VIEW_MODE_LABELS}
        />

        <div className="flex items-center rounded-lg border border-border">
          <button
            type="button"
            onClick={() => onGridTypeChange('weekly')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors rounded-l-lg ${
              gridType === 'weekly' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            <Grid3X3 className="size-3.5" />
            Semanal
          </button>
          <button
            type="button"
            onClick={() => onGridTypeChange('gantt')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors rounded-r-lg ${
              gridType === 'gantt' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            <GanttChart className="size-3.5" />
            Gantt
          </button>
        </div>

        <div className="ml-auto flex items-center gap-1">
          <button
            type="button"
            disabled={zoomIdx <= 0}
            onClick={() => onZoomChange(ZOOM_LEVELS[zoomIdx - 1])}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ZoomOut className="size-4" />
          </button>
          <span className="min-w-[3rem] text-center text-xs font-medium text-muted-foreground">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            disabled={zoomIdx >= ZOOM_LEVELS.length - 1}
            onClick={() => onZoomChange(ZOOM_LEVELS[zoomIdx + 1])}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ZoomIn className="size-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
