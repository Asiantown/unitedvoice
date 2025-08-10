import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
  weight: ["100", "200", "300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: {
    default: "United Voice Agent",
    template: "%s | United Voice Agent",
  },
  description: "Advanced AI-powered voice assistant for United Airlines booking and customer service",
  keywords: [
    "voice assistant",
    "AI",
    "United Airlines",
    "flight booking",
    "customer service",
    "speech recognition",
    "text to speech",
  ],
  authors: [
    {
      name: "United Voice Agent Team",
    },
  ],
  creator: "United Voice Agent",
  publisher: "United Airlines",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://voice-agent.united.com"),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: process.env.NEXT_PUBLIC_SITE_URL || "https://voice-agent.united.com",
    siteName: "United Voice Agent",
    title: "United Voice Agent - AI-Powered Flight Assistant",
    description: "Advanced AI-powered voice assistant for United Airlines booking and customer service",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "United Voice Agent",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "United Voice Agent - AI-Powered Flight Assistant",
    description: "Advanced AI-powered voice assistant for United Airlines booking and customer service",
    images: ["/twitter-image.png"],
    creator: "@united",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/icon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/icon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/icon-192x192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512x512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
  },
  verification: {
    google: process.env.GOOGLE_VERIFICATION_ID,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body
        className={`${inter.variable} ${jetBrainsMono.variable} font-sans antialiased bg-background text-foreground min-h-screen`}
        suppressHydrationWarning
      >
        <div className="relative min-h-screen bg-gradient-to-br from-background via-background-secondary to-background">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-accent-purple/5 to-transparent" />
          <main className="relative z-10">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
