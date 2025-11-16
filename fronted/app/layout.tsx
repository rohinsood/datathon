import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "College Mobility Explorer",
  description: "Explore college affordability gaps, graduation outcomes, and causal effect estimates to understand educational mobility.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
