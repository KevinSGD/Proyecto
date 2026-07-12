'use client'

import { useId, useState, type ReactNode } from 'react'

const inputBase =
  'w-full rounded-lg border bg-card px-3 py-2 text-sm text-foreground placeholder:text-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
const borderOk = 'border-border'
const borderErr = 'border-danger'

function Label({ htmlFor, children }: { htmlFor: string; children: ReactNode }) {
  return <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-strong">{children}</label>
}
function ErrorText({ children }: { children?: string }) {
  return children ? <p className="mt-1 text-xs text-danger">{children}</p> : null
}

export function Field({ label, value, onChange, placeholder, error, type = 'text' }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; error?: string; type?: string
}) {
  const id = useId()
  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <input id={id} type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        aria-invalid={!!error} className={`${inputBase} ${error ? borderErr : borderOk}`} />
      <ErrorText>{error}</ErrorText>
    </div>
  )
}

export function NumberField({ label, value, onChange, error }: {
  label: string; value: number; onChange: (v: number) => void; error?: string
}) {
  const id = useId()
  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <input id={id} type="number" value={value} onChange={e => onChange(Number(e.target.value))}
        aria-invalid={!!error} className={`${inputBase} ${error ? borderErr : borderOk}`} />
      <ErrorText>{error}</ErrorText>
    </div>
  )
}

export function SelectField({ label, value, onChange, options, labels, ariaLabel, error }: {
  label?: string; value: string; onChange: (v: string) => void; options: string[]; labels?: Record<string, string>; ariaLabel?: string; error?: string
}) {
  const id = useId()
  return (
    <div>
      {label ? <Label htmlFor={id}>{label}</Label> : null}
      <select id={id} aria-label={!label ? (ariaLabel ?? 'Selecciona una opción') : undefined} value={value} onChange={e => onChange(e.target.value)} className={`${inputBase} ${error ? borderErr : borderOk}`}>
        {options.map(o => <option key={o} value={o}>{labels?.[o] ?? o}</option>)}
      </select>
      <ErrorText>{error}</ErrorText>
    </div>
  )
}

export function Textarea({ label, value, onChange, placeholder, rows = 3 }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; rows?: number
}) {
  const id = useId()
  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <textarea id={id} value={value} onChange={e => onChange(e.target.value)} rows={rows} placeholder={placeholder}
        className={`${inputBase} ${borderOk} resize-none`} />
    </div>
  )
}

export function Chips({ label, value, onChange, placeholder }: {
  label: string; value: string[]; onChange: (v: string[]) => void; placeholder: string
}) {
  const id = useId()
  const [text, setText] = useState('')
  const add = () => { const t = text.trim(); if (t && !value.includes(t)) { onChange([...value, t]); setText('') } }
  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <div className="flex flex-wrap items-center gap-1.5 rounded-lg border border-border bg-card px-2 py-2 focus-within:ring-2 focus-within:ring-ring">
        {value.map(t => (
          <span key={t} className="inline-flex items-center gap-1 rounded-md bg-primary-soft px-2 py-0.5 text-xs font-medium text-primary">
            {t}<button type="button" aria-label={`Quitar ${t}`} onClick={() => onChange(value.filter(x => x !== t))} className="hover:text-primary-hover">×</button>
          </span>
        ))}
        <input id={id} value={text} onChange={e => setText(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
          placeholder={placeholder} className="min-w-[120px] flex-1 border-0 bg-transparent px-1 py-0.5 text-sm text-foreground placeholder:text-subtle focus:outline-none" />
      </div>
    </div>
  )
}

export function SearchInput({ value, onChange, placeholder }: {
  value: string; onChange: (v: string) => void; placeholder?: string
}) {
  return (
    <div className="relative min-w-[220px] flex-1">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
      </span>
      <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} aria-label={placeholder ?? 'Buscar'}
        className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
    </div>
  )
}

export function FilterSelect({ value, onChange, placeholder, options, labels, ariaLabel }: {
  value: string; onChange: (v: string) => void; placeholder: string; options: string[]; labels?: Record<string, string>; ariaLabel?: string
}) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} aria-label={ariaLabel ?? placeholder}
      className={`rounded-lg border border-border bg-card px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${value ? 'text-foreground' : 'text-subtle'}`}>
      <option value="">{placeholder}</option>
      {options.map(o => <option key={o} value={o}>{labels?.[o] ?? o}</option>)}
    </select>
  )
}
