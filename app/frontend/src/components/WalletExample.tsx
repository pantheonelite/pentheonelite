import React from "react";
import { BSCWallet } from "./BSCWallet";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { WalletConnectButton } from "./WalletConnectButton";
import { WalletStatus } from "./WalletStatus";

/**
 * Example component demonstrating wallet integration usage.
 * This shows how to integrate wallet functionality into your existing components.
 */
export const WalletExample: React.FC = () => {
  return (
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-[--text-primary]">
            Pantheon Elite - Wallet Integration
          </CardTitle>
          <CardDescription className="text-[--text-secondary]">
            Connect your BSC wallet to access the AI-powered trading platform
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Wallet Connect Button */}
          <div>
            <h3 className="text-lg font-semibold text-[--text-primary] mb-3">
              Quick Connect
            </h3>
            <WalletConnectButton
              variant="default"
              size="lg"
              className="w-full"
            />
          </div>

          {/* Wallet Status */}
          <div>
            <h3 className="text-lg font-semibold text-[--text-primary] mb-3">
              Wallet Status
            </h3>
            <WalletStatus className="p-4 bg-[--surface] rounded-lg border border-[--border]" />
          </div>

          {/* Full Wallet Component */}
          <div>
            <h3 className="text-lg font-semibold text-[--text-primary] mb-3">
              Full Wallet Interface
            </h3>
            <BSCWallet />
          </div>

          {/* Usage Instructions */}
          <div className="p-4 bg-[--primary-500]/10 border border-[--primary-500]/20 rounded-lg">
            <h4 className="font-semibold text-[--primary-500] mb-2">
              How to Use in Your Components:
            </h4>
            <div className="text-sm text-[--text-secondary] space-y-2">
              <p>1. Import the wallet components:</p>
              <code className="block bg-[--surface] p-2 rounded text-xs">
                {`import { WalletConnectButton, WalletStatus } from './components'`}
              </code>

              <p>2. Add wallet connect button:</p>
              <code className="block bg-[--surface] p-2 rounded text-xs">
                {`<WalletConnectButton variant="outline" size="sm" />`}
              </code>

              <p>3. Show wallet status:</p>
              <code className="block bg-[--surface] p-2 rounded text-xs">
                {`<WalletStatus className="ml-auto" />`}
              </code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
