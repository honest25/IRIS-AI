import type { Metadata } from "next";
import { Space_Mono, Orbitron } from "next/font/google";
import "./globals.css";

const spaceMono = Space_Mono({
  weight: ["400", "700"],
  variable: "--font-mono",
  subsets: ["latin"],
});

const orbitron = Orbitron({
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "IRIS AI — Intelligent Responsive Integrated System",
  description:
    "Your personal AI assistant. Control your devices, manage tasks, and communicate — all from one futuristic command center.",
  keywords: ["AI assistant", "JARVIS", "voice assistant", "device control", "IRIS AI"],
  authors: [{ name: "IRIS AI" }],
  themeColor: "#050a12",
  openGraph: {
    title: "IRIS AI",
    description: "Your personal AI assistant command center.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${spaceMono.variable} ${orbitron.variable} h-full`}
    >
      <body className="min-h-full bg-iris-bg text-iris-cyan antialiased overflow-hidden">
        {children}
      </body>
    </html>
  );
}
