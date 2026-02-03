import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const GA_MEASUREMENT_ID = "G-5DDMG3BT8H";
import { Header } from '@/components/layout/Header';
import { MainLayout } from '@/components/layout/MainLayout';
import { AuthProvider } from '@/providers/AuthProvider';
import { ComingSoonProvider } from '@/providers/ComingSoonProvider';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Virtual AI Coach - Free AI Personal Trainer & Workout Generator",
  description: "Get motivated to exercise at your own pace with Virtual AI Coach. Free AI-powered personalized workout programs for all fitness levels. Build strength, get fitter, or lose weight with 100+ bodyweight exercises. No equipment needed, no judgment.",
  keywords: "AI personal trainer, virtual fitness coach, free workout generator, personalized exercise program, AI-powered fitness app, home workout planner, bodyweight training AI, custom workout creator, beginner-friendly fitness, adaptive training program, HIIT workout generator, strength training app, cardio workout planner, free fitness app",
  authors: [{ name: "Virtual AI Coach" }],
  creator: "Independent Developer",
  publisher: "Virtual AI Coach",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    title: "Virtual AI Coach - Free AI Personal Trainer & Workout Generator",
    description: "Get motivated to exercise without judgment, at your own pace. AI-generated personalized workouts for all fitness levels. 100+ exercise videos, no equipment required.",
    type: "website",
    locale: "en_US",
    siteName: "Virtual AI Coach",
    url: "https://workout-ai-coach.com",
  },
  twitter: {
    card: "summary_large_image",
    title: "Virtual AI Coach - Free AI Personal Trainer",
    description: "Personalized AI workout programs. Get fitter, stronger, or leaner at your own pace. 100+ exercises, no equipment needed.",
    creator: "@virtualaicoach",
  },
  alternates: {
    canonical: "https://workout-ai-coach.com",
  },
  category: "Health & Fitness",
};

// Schema.org structured data for SEO
const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Virtual AI Coach",
  "url": "https://workout-ai-coach.com",
  "logo": "https://workout-ai-coach.com/sport_room.png",
  "description": "Free AI-powered virtual personal trainer providing personalized workout programs for all fitness levels",
  "foundingDate": "2024",
  "sameAs": [
    "https://twitter.com/virtualaicoach"
  ]
};

const webApplicationSchema = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Virtual AI Coach",
  "url": "https://workout-ai-coach.com",
  "applicationCategory": "HealthApplication",
  "operatingSystem": "Any",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "description": "AI-powered personalized workout generator. Free virtual personal trainer for all fitness levels.",
  "featureList": [
    "AI-generated personalized workouts",
    "100+ exercise video library",
    "No equipment required",
    "Beginner-friendly fitness programs",
    "HIIT, strength, and cardio workouts",
    "Adaptive training at your own pace"
  ]
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_MEASUREMENT_ID}');
          `}
        </Script>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(webApplicationSchema) }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <ComingSoonProvider>
            <Header />
            <MainLayout>{children}</MainLayout>
          </ComingSoonProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
