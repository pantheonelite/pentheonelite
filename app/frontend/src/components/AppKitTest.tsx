import { AlertCircle, CheckCircle } from "lucide-react";
import React from "react";
import { useAccount } from "wagmi";
import { AppKitWalletButton } from "./AppKitWalletButton";
import { AppKitWalletStatus } from "./AppKitWalletStatus";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";

export const AppKitTest: React.FC = () => {
  const { isConnected, address, chain } = useAccount();

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            {isConnected ? (
              <CheckCircle className="w-6 h-6 text-[--secondary-500]" />
            ) : (
              <AlertCircle className="w-6 h-6 text-[--accent-orange]" />
            )}
            <span>Reown AppKit Integration Test</span>
          </CardTitle>
          <CardDescription>
            Test the AppKit wallet connection functionality
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h3 className="font-semibold text-[--text-primary]">
              Connection Status
            </h3>
            <p className="text-sm text-[--text-secondary]">
              {isConnected ? "Connected" : "Not Connected"}
            </p>
            {address && (
              <p className="text-sm text-[--text-secondary] font-mono">
                Address: {address}
              </p>
            )}
            {chain && (
              <p className="text-sm text-[--text-secondary]">
                Network: {chain.name} (ID: {chain.id})
              </p>
            )}
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold text-[--text-primary]">
              Wallet Status Component
            </h3>
            <AppKitWalletStatus />
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold text-[--text-primary]">
              Wallet Button Component
            </h3>
            <AppKitWalletButton />
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold text-[--text-primary]">
              AppKit Web Component
            </h3>
            <div className="p-4 border border-[--border] rounded-lg">
              <appkit-button />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
