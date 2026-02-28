import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ClientLayout from "@/components/ClientLayout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RepoDocAI — AI-Powered Repository Documentation",
  description:
    "Generate comprehensive project documentation from any GitHub repository using AI, accelerated by AMD GPUs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ClientLayout>
          {/* Top bar */}
          <nav className="fixed top-0 w-full z-50 bg-black/60 backdrop-blur-md border-b border-white/5">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
              <a href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-amd-red flex items-center justify-center font-bold text-white text-sm">
                  RD
                </div>
                <span className="text-xl font-bold text-white">
                  Repo<span className="text-amd-red">Doc</span>AI
                </span>
              </a>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                <span className="hidden sm:inline">Powered by</span>
                <span className="text-amd-red font-semibold">AMD ROCm</span>
              </div>
            </div>
          </nav>

          <main className="pt-16 min-h-screen">{children}</main>

          {/* Footer */}
          <footer className="border-t border-white/5 py-8 text-center text-gray-500 text-sm">
            <p>
              RepoDocAI &mdash; Built for{" "}
              <span className="text-amd-red font-medium">AMD Slingshot 2026</span>
            </p>
            <p className="mt-1">AI-powered documentation &bull; AMD GPU accelerated</p>
          </footer>
        </ClientLayout>
      </body>
    </html>
  );
}
