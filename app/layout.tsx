import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { DataProvider } from '@/lib/store'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'HorarioIA – Área de Matemáticas Básicas',
  description: 'Sistema Inteligente para la Generación Automática de Horarios Universitarios',
  generator: 'v0.app',
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#A6061B',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es" className="bg-background">
      <body className={`${inter.className} antialiased`}>
        <DataProvider>
          {children}
        </DataProvider>
      </body>
    </html>
  )
}
