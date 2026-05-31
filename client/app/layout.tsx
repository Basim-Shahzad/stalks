import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Providers from "./providers";
import "./globals.css";

const geistSans = Geist({
   variable: "--font-geist-sans",
   subsets: ["latin"],
});

const geistMono = Geist_Mono({
   variable: "--font-geist-mono",
   subsets: ["latin"],
});

export const metadata: Metadata = {
   title: "Stalks",
   description: "by @basimshahzad",
   icons: {
      icon: "/logo.png",
   },
};

export default function RootLayout({
   children,
}: Readonly<{
   children: React.ReactNode;
}>) {
   return (
      <Providers>
         <html
            lang="en"
            className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
            data-theme="dark"
            suppressHydrationWarning
         >
            <body suppressHydrationWarning className="min-h-full flex flex-col">
               {children}
            </body>
         </html>
      </Providers>
   );
}
