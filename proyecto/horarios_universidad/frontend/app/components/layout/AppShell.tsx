'use client'

import Sidebar from './Sidebar'
import Header from './Header'
import CoordinatorSidebar from './CoordinatorSidebar'
import CoordinatorHeader from './CoordinatorHeader'
import SkipToContent from '@/components/ui/SkipToContent'
import { useAuthStore } from '@/lib/stores/auth.store'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((s) => s.user?.role)
  const isCoordinador = role === 'coordinador'

  return (
    <>
      <SkipToContent />
      {isCoordinador ? <CoordinatorSidebar /> : <Sidebar />}
      <div className="lg:pl-64">
        {isCoordinador ? <CoordinatorHeader /> : <Header />}
        <main id="main-content" className={isCoordinador ? 'p-6 lg:p-8' : 'p-4 lg:p-6'}>
          {children}
        </main>
      </div>
    </>
  )
}
