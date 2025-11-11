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
  title: "Virtual AI Coach",
  description: "Your personal AI-powered workout trainer",
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
