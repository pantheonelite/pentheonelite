export const metadata = {
  title: 'Pantheon Elite',
  description: 'Pantheon Elite is a platform for trading crypto with AI',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
