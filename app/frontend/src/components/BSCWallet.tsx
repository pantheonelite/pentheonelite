import {
  AlertCircle,
  CheckCircle,
  Copy,
  ExternalLink,
  Loader2,
  LogOut,
  Wallet,
} from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import { formatEther } from "viem";
import { useAccount, useBalance, useConnect, useDisconnect } from "wagmi";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Separator } from "./ui/separator";

interface BSCWalletProps {
  className?: string;
}

export const BSCWallet: React.FC<BSCWalletProps> = ({ className }) => {
  const { address, isConnected, chain } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const { data: balance } = useBalance({
    address: address,
  });

  const [copied, setCopied] = useState(false);

  // Copy address to clipboard
  const copyAddress = async () => {
    if (address) {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      toast.success("Address copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Format address for display
  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
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

  // Check if connected to BSC network
  const isBSCNetwork = chain?.id === 56 || chain?.id === 97;
  const networkName =
    chain?.id === 56
      ? "BSC Mainnet"
      : chain?.id === 97
      ? "BSC Testnet"
      : "Unknown Network";

  if (!isConnected) {
    return (
      <Card className={`w-full max-w-md mx-auto ${className}`}>
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 bg-gradient-to-br from-[--primary-500] to-[--primary-600] rounded-full flex items-center justify-center">
            <Wallet className="w-6 h-6 text-white" />
          </div>
          <CardTitle className="text-xl font-bold text-[--text-primary]">
            Connect Your Wallet
          </CardTitle>
          <CardDescription className="text-[--text-secondary]">
            Connect your wallet to access the Pantheon Elite trading platform
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {connectors.map((connector) => (
            <Button
              key={connector.uid}
              onClick={() => connect({ connector })}
              disabled={isPending}
              className="w-full h-12 bg-[--surface] border border-[--border] hover:bg-[--primary-500] hover:border-[--primary-500] text-[--text-primary] hover:text-white transition-all duration-300"
            >
              {isPending ? (
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              ) : (
                <Wallet className="w-5 h-5 mr-2" />
              )}
              {connector.name}
            </Button>
          ))}

          <div className="text-center">
            <p className="text-sm text-[--text-secondary]">
              Supported networks: BSC Mainnet, BSC Testnet
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`w-full max-w-md mx-auto ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-[--secondary-500] to-[--secondary-600] rounded-full flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-[--text-primary]">
                Wallet Connected
              </CardTitle>
              <CardDescription className="text-[--text-secondary]">
                {formatAddress(address!)}
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => disconnect()}
            className="text-[--text-secondary] hover:text-[--accent-red]"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Network Status */}
        <div className="flex items-center justify-between p-3 bg-[--surface] rounded-lg">
          <div className="flex items-center space-x-2">
            {isBSCNetwork ? (
              <CheckCircle className="w-4 h-4 text-[--secondary-500]" />
            ) : (
              <AlertCircle className="w-4 h-4 text-[--accent-orange]" />
            )}
            <span className="text-sm font-medium text-[--text-primary]">
              {networkName}
            </span>
          </div>
          <Badge
            variant={isBSCNetwork ? "default" : "destructive"}
            className={
              isBSCNetwork ? "bg-[--secondary-500]" : "bg-[--accent-orange]"
            }
          >
            {isBSCNetwork ? "Connected" : "Wrong Network"}
          </Badge>
        </div>

        {/* Balance */}
        {balance && (
          <div className="p-3 bg-[--surface] rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-[--text-secondary]">Balance</span>
              <span className="text-lg font-semibold text-[--text-primary]">
                {parseFloat(formatEther(balance.value)).toFixed(4)}{" "}
                {balance.symbol}
              </span>
            </div>
          </div>
        )}

        <Separator />

        {/* Actions */}
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={copyAddress}
            className="flex-1 border-[--border] text-[--text-primary] hover:bg-[--surface]"
          >
            {copied ? (
              <CheckCircle className="w-4 h-4 mr-2" />
            ) : (
              <Copy className="w-4 h-4 mr-2" />
            )}
            {copied ? "Copied!" : "Copy Address"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(getExplorerUrl(address!), "_blank")}
            className="flex-1 border-[--border] text-[--text-primary] hover:bg-[--surface]"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            View on BSCScan
          </Button>
        </div>

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
  );
};
