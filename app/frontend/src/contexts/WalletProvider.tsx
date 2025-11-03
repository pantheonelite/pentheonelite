import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React, { createContext, useContext, useEffect, useState } from "react";
import { WagmiProvider } from "wagmi";
import { config } from "../lib/wallet-config";

// Create a client
const queryClient = new QueryClient();

interface WalletContextType {
  isConnected: boolean;
  address: string | undefined;
  chainId: number | undefined;
  balance: string | undefined;
  isLoading: boolean;
  error: string | null;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error("useWallet must be used within a WalletProvider");
  }
  return context;
};

interface WalletProviderProps {
  children: React.ReactNode;
}

export const WalletProvider: React.FC<WalletProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [address, setAddress] = useState<string | undefined>();
  const [chainId, setChainId] = useState<number | undefined>();

  // Listen for account changes
  useEffect(() => {
    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length > 0) {
        setAddress(accounts[0]);
        setIsConnected(true);
      } else {
        setAddress(undefined);
        setIsConnected(false);
      }
    };

    const handleChainChanged = (chainId: string) => {
      setChainId(parseInt(chainId, 16));
    };

    // Check if wallet is already connected
    if (window.ethereum) {
      (window.ethereum as any)
        .request({ method: "eth_accounts" })
        .then((accounts: string[]) => {
          if (accounts.length > 0) {
            setAddress(accounts[0]);
            setIsConnected(true);
          }
        })
        .catch(console.error);

      (window.ethereum as any)
        .request({ method: "eth_chainId" })
        .then((chainId: string) => {
          setChainId(parseInt(chainId, 16));
        })
        .catch(console.error);

      // Listen for account changes
      (window.ethereum as any).on("accountsChanged", handleAccountsChanged);
      (window.ethereum as any).on("chainChanged", handleChainChanged);
    }

    return () => {
      if (window.ethereum) {
        (window.ethereum as any).removeListener(
          "accountsChanged",
          handleAccountsChanged
        );
        (window.ethereum as any).removeListener(
          "chainChanged",
          handleChainChanged
        );
      }
    };
  }, []);

  const contextValue: WalletContextType = {
    isConnected,
    address,
    chainId,
    balance: undefined,
    isLoading: false,
    error: null,
  };

  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <WalletContext.Provider value={contextValue}>
          {children}
        </WalletContext.Provider>
      </QueryClientProvider>
    </WagmiProvider>
  );
};
