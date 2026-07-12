'use client'

import Sidebar from './Sidebar'
import Header from './Header'
import SkipToContent from '@/components/ui/SkipToContent'

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SkipToContent />
      <Sidebar />
      <div className="lg:pl-64">
        <Header />
        <main id="main-content" className="p-4 lg:p-6">
          {children}
        </main>
      </div>
    </>
  )
}
