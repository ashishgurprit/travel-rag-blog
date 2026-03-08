import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Travel Search",
  description: "AI-powered travel search with streaming answers",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
