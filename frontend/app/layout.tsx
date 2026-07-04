import type { Metadata } from 'next'
import './globals.css'
import Providers from './providers'

export const metadata: Metadata = {
  title: 'NEXUS',
  description: 'Unified security operations platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-cyber-grid min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
