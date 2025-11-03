"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import {
  WagmiProvider,
  cookieToInitialState,
  createConfig,
  http,
  type Config,
} from "wagmi";
import { bsc, bscTestnet } from "wagmi/chains";
import { coinbaseWallet, metaMask, walletConnect } from "wagmi/connectors";

const queryClient = new QueryClient();

// Simple wagmi config without AppKit
const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID as string || "demo-project-id";

const config = createConfig({
  chains: [bsc, bscTestnet],
  connectors: [
    metaMask(),
    walletConnect({
      projectId,
      metadata: {
        name: "Pantheon Elite",
        description: "AI-powered hedge fund trading platform",
        url:
          typeof window !== "undefined"
            ? window.location.origin
            : "http://localhost:5173",
        icons: ["https://avatars.githubusercontent.com/u/37784886"],
      },
    }),
    coinbaseWallet({
      appName: "Pantheon Elite",
      appLogoUrl: "https://avatars.githubusercontent.com/u/37784886",
    }),
  ],
  transports: {
    [bsc.id]: http(),
    [bscTestnet.id]: http(),
  },
});

export default function SimpleWalletProvider({
  children,
  cookies,
}: {
  children: ReactNode;
  cookies: string | null;
}) {
  // Calculate initial state for Wagmi SSR hydration
  const initialState = cookieToInitialState(config as Config, cookies);

  return (
    <WagmiProvider config={config as Config} initialState={initialState}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </WagmiProvider>
  );
}
