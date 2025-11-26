import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
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
  title: "Virtual AI Coach - Personalized Video Workout Training",
  description: "Your personal virtual sports coach with guided video workouts. Generate customized training sessions adapted to your fitness level, with real-time timers, exercise variety, and advanced customization options. No equipment needed.",
  keywords: "virtual coach, workout videos, personalized training, fitness app, home workout, guided exercises, interval training, cardio, strength training, flexibility",
  authors: [{ name: "Virtual AI Coach" }],
  openGraph: {
    title: "Virtual AI Coach - Personalized Video Workout Training",
    description: "Generate customized video workouts with guided exercises, timers, and personalized intensity levels. Train anywhere, anytime.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Virtual AI Coach - Personalized Video Workout Training",
    description: "Your personal virtual sports coach with guided video workouts and customized training sessions.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
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
