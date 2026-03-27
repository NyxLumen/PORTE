// Cache bust: 2026-03-27T00:00:00Z
import type { Metadata } from 'next'
import { Instrument_Serif, Inter } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

const instrumentSerif = Instrument_Serif({ 
  subsets: ["latin"],
  weight: "400",
  variable: "--font-serif"
});

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-sans"
});

export const metadata: Metadata = {
  title: 'Porte',
  description: 'Move from Model-Centric to Me-Centric. AI-powered virtual try-on technology.',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${instrumentSerif.variable} ${inter.variable} font-sans antialiased bg-zinc-900 text-zinc-50`}>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
