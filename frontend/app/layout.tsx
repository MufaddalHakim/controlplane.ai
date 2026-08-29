import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  title: 'ControlPlane.ai - Runtime AI Risk Gateway',
  description: 'Policy enforcement and evidence-backed risk operations for enterprise AI.',
  openGraph: {
    title: 'ControlPlane.ai',
    description: 'Runtime AI Risk Gateway',
    images: [{ url: '/og.png', width: 1200, height: 630, alt: 'ControlPlane.ai Runtime AI Risk Gateway' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ControlPlane.ai',
    description: 'Runtime AI Risk Gateway',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
