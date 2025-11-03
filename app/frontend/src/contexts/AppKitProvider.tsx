"use client";

import { createAppKit } from "@reown/appkit/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { WagmiProvider, cookieToInitialState, type Config } from "wagmi";
// Import config, networks, projectId, and wagmiAdapter from your config file
import { config, networks, projectId, wagmiAdapter } from "@/config";
// Import the default network separately if needed
import { bsc } from "@reown/appkit/networks";

const queryClient = new QueryClient();

const metadata = {
  name: process.env.NEXT_PUBLIC_APP_NAME || "Pantheon Elite",
  description:
    process.env.NEXT_PUBLIC_APP_DESCRIPTION ||
    "AI-powered hedge fund trading platform",
  url:
    typeof window !== "undefined"
      ? window.location.origin
      : process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  icons: ["https://avatars.githubusercontent.com/u/37784886"],
};

// Initialize AppKit *outside* the component render cycle
// Only initialize if we're in the browser
if (typeof window !== "undefined") {
  try {
    createAppKit({
      adapters: [wagmiAdapter],
      projectId: projectId,
      networks: networks,
      defaultNetwork: bsc, // BSC as default network
      metadata,
      features: {
        analytics: true,
        email: false, // Disable email login
        socials: [], // Disable social logins (Google, Discord, GitHub, etc.)
      },
      // Only show specific wallets
      featuredWalletIds: [
        "1ae92b26df02f0abca6304df07debccd18262fdf5fe82daa81593582dac9a369", // MetaMask
        "4622a2b2d6af1c9844944291e5e7351a6aa24cd7b23099efac1b2fd875da31a0", // Trust Wallet
        "walletConnect", // WalletConnect
      ],
    });
  } catch (error) {
    console.error("AppKit Initialization Error:", error);
  }
}

export default function AppKitProvider({
  children,
  cookies,
}: {
  children: ReactNode;
  cookies: string | null; // Cookies from server for hydration
}) {
  // Calculate initial state for Wagmi SSR hydration
  const initialState = cookieToInitialState(config as Config, cookies);

  return (
    // Cast config as Config for WagmiProvider
    <WagmiProvider config={config as Config} initialState={initialState}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </WagmiProvider>
  );
}
