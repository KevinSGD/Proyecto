'use client'

interface Tab<T extends string> {
  key: T
  label: string
}

interface TabsProps<T extends string> {
  tabs: Tab<T>[]
  value: T
  onChange: (key: T) => void
  className?: string
}

export default function Tabs<T extends string>({ tabs, value, onChange, className }: TabsProps<T>) {
  return (
    <div role="tablist" className={`flex gap-1 rounded-lg bg-muted p-1 ${className ?? ''}`}>
      {tabs.map(t => {
        const active = t.key === value
        return (
          <button
            key={t.key}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(t.key)}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
              ${active ? 'bg-card text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}
