import {
  AlertCircle,
  CheckCircle,
  Copy,
  ExternalLink,
  Shield,
  TrendingUp,
  Wallet,
  Zap,
} from "lucide-react";
import React from "react";
import { toast } from "sonner";
import { formatEther } from "viem";
import { useAccount, useBalance } from "wagmi";
import { AppKitWalletButton } from "../AppKitWalletButton";
import { AppKitWalletStatus } from "../AppKitWalletStatus";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";

export const AppKitWalletPage: React.FC = () => {
  const { address, isConnected, chain } = useAccount();
  const { data: balance } = useBalance({
    address: address,
  });

  // Check if connected to BSC network
  const isBSCNetwork = chain?.id === 56 || chain?.id === 97;
  const networkName =
    chain?.id === 56
      ? "BSC Mainnet"
      : chain?.id === 97
      ? "BSC Testnet"
      : "Unknown Network";

  // Copy address to clipboard
  const copyAddress = async () => {
    if (address) {
      await navigator.clipboard.writeText(address);
      toast.success("Address copied to clipboard!");
    }
  };

  // Get BSC explorer URL
  const getExplorerUrl = (addr: string) => {
    if (chain?.id === 56) {
      return `https://bscscan.com/address/${addr}`;
    } else if (chain?.id === 97) {
      return `https://testnet.bscscan.com/address/${addr}`;
    }
    return `https://bscscan.com/address/${addr}`;
  };

  return (
    <div className="min-h-screen bg-[--background] p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-[--text-primary]">
            Pantheon Elite Wallet
          </h1>
          <p className="text-lg text-[--text-secondary] max-w-2xl mx-auto">
            Connect your BSC wallet to access the AI-powered trading platform.
            Manage your digital assets and participate in the decentralized
            hedge fund ecosystem.
          </p>
        </div>

        {/* Quick Status Card */}
        <Card className="bg-[--surface] border-[--border]">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Wallet className="w-6 h-6 text-[--primary-500]" />
              <span>Wallet Status</span>
            </CardTitle>
            <CardDescription>
              Current connection status and network information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {isConnected ? (
                    <CheckCircle className="w-5 h-5 text-[--secondary-500]" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-[--accent-orange]" />
                  )}
                  <span className="font-medium text-[--text-primary]">
                    {isConnected ? "Connected" : "Not Connected"}
                  </span>
                </div>

                {isConnected && (
                  <Badge
                    variant={isBSCNetwork ? "default" : "destructive"}
                    className={
                      isBSCNetwork
                        ? "bg-[--secondary-500]"
                        : "bg-[--accent-orange]"
                    }
                  >
                    {networkName}
                  </Badge>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <AppKitWalletStatus />
                <AppKitWalletButton variant="outline" size="sm" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Wallet Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Wallet Connection */}
          <Card className="bg-[--surface] border-[--border]">
            <CardHeader>
              <CardTitle>Connect Wallet</CardTitle>
              <CardDescription>
                Connect your BSC wallet to start trading
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <AppKitWalletButton
                  variant="default"
                  size="lg"
                  className="w-full"
                />
              </div>

              <div className="text-center">
                <p className="text-sm text-[--text-secondary]">
                  Supported networks: BSC Mainnet, BSC Testnet
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Wallet Information */}
          {isConnected && (
            <Card className="bg-[--surface] border-[--border]">
              <CardHeader>
                <CardTitle>Wallet Information</CardTitle>
                <CardDescription>Your connected wallet details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-[--text-secondary]">
                    Address
                  </label>
                  <div className="flex items-center space-x-2 p-3 bg-[--background] rounded-lg border border-[--border]">
                    <span className="font-mono text-sm text-[--text-primary] flex-1">
                      {address}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={copyAddress}
                      className="text-[--text-secondary] hover:text-[--text-primary]"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        window.open(getExplorerUrl(address!), "_blank")
                      }
                      className="text-[--text-secondary] hover:text-[--text-primary]"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-[--text-secondary]">
                    Network
                  </label>
                  <div className="flex items-center space-x-2">
                    {isBSCNetwork ? (
                      <CheckCircle className="w-4 h-4 text-[--secondary-500]" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-[--accent-orange]" />
                    )}
                    <span className="text-sm text-[--text-primary]">
                      {networkName}
                    </span>
                  </div>
                </div>

                {balance && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[--text-secondary]">
                      Balance
                    </label>
                    <div className="p-3 bg-[--background] rounded-lg border border-[--border]">
                      <div className="text-lg font-semibold text-[--text-primary]">
                        {parseFloat(formatEther(balance.value)).toFixed(4)}{" "}
                        {balance.symbol}
                      </div>
                    </div>
                  </div>
                )}

                {!isBSCNetwork && (
                  <div className="p-3 bg-[--accent-orange]/10 border border-[--accent-orange]/20 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-[--accent-orange]" />
                      <span className="text-sm text-[--accent-orange]">
                        Please switch to BSC network to use this platform
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Features Section */}
        <Card className="bg-[--surface] border-[--border]">
          <CardHeader>
            <CardTitle>Platform Features</CardTitle>
            <CardDescription>
              What you can do with your connected wallet
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-[--primary-500]/20 rounded-full flex items-center justify-center mx-auto">
                  <Wallet className="w-6 h-6 text-[--primary-500]" />
                </div>
                <h3 className="font-semibold text-[--text-primary]">
                  Secure Trading
                </h3>
                <p className="text-sm text-[--text-secondary]">
                  Execute trades with your connected wallet using advanced AI
                  strategies
                </p>
              </div>

              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-[--secondary-500]/20 rounded-full flex items-center justify-center mx-auto">
                  <TrendingUp className="w-6 h-6 text-[--secondary-500]" />
                </div>
                <h3 className="font-semibold text-[--text-primary]">
                  Portfolio Management
                </h3>
                <p className="text-sm text-[--text-secondary]">
                  Track your investments and performance across multiple
                  strategies
                </p>
              </div>

              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-[--accent-blue]/20 rounded-full flex items-center justify-center mx-auto">
                  <Shield className="w-6 h-6 text-[--accent-blue]" />
                </div>
                <h3 className="font-semibold text-[--text-primary]">
                  DeFi Integration
                </h3>
                <p className="text-sm text-[--text-secondary]">
                  Access decentralized finance protocols and yield farming
                  opportunities
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AppKit Features */}
        <Card className="bg-[--surface] border-[--border]">
          <CardHeader>
            <CardTitle>Powered by Reown AppKit</CardTitle>
            <CardDescription>
              Modern wallet connection with enhanced security and user
              experience
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-semibold text-[--text-primary]">
                  Enhanced Security
                </h4>
                <ul className="space-y-2 text-sm text-[--text-secondary]">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-[--secondary-500]" />
                    <span>Multi-signature support</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-[--secondary-500]" />
                    <span>Hardware wallet integration</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-[--secondary-500]" />
                    <span>Social login options</span>
                  </li>
                </ul>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold text-[--text-primary]">
                  User Experience
                </h4>
                <ul className="space-y-2 text-sm text-[--text-secondary]">
                  <li className="flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-[--primary-500]" />
                    <span>One-click wallet connection</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-[--primary-500]" />
                    <span>Cross-platform compatibility</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-[--primary-500]" />
                    <span>Mobile-first design</span>
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
