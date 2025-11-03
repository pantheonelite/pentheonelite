import {
  AlertCircle,
  CheckCircle,
  ExternalLink,
  LogOut,
  Wallet,
} from "lucide-react";
import React from "react";
import { useAccount, useDisconnect } from "wagmi";
import { BSCWallet } from "./BSCWallet";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

interface WalletStatusProps {
  showFullModal?: boolean;
  className?: string;
}

export const WalletStatus: React.FC<WalletStatusProps> = ({
  showFullModal = false,
  className,
}) => {
  const { address, isConnected, chain } = useAccount();
  const { disconnect } = useDisconnect();

  // Check if connected to BSC network
  const isBSCNetwork = chain?.id === 56 || chain?.id === 97;
  const networkName =
    chain?.id === 56 ? "BSC" : chain?.id === 97 ? "BSC Testnet" : "Unknown";

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

  if (!isConnected) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Wallet className="w-4 h-4 text-[--text-secondary]" />
        <span className="text-sm text-[--text-secondary]">Not Connected</span>
        {showFullModal && <BSCWallet />}
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Network Status */}
      <div className="flex items-center space-x-2">
        {isBSCNetwork ? (
          <CheckCircle className="w-4 h-4 text-[--secondary-500]" />
        ) : (
          <AlertCircle className="w-4 h-4 text-[--accent-orange]" />
        )}
        <Badge
          variant={isBSCNetwork ? "default" : "destructive"}
          className={
            isBSCNetwork ? "bg-[--secondary-500]" : "bg-[--accent-orange]"
          }
        >
          {networkName}
        </Badge>
      </div>

      {/* Wallet Address */}
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-2 px-3 py-1 bg-[--surface] rounded-lg border border-[--border]">
          <Wallet className="w-4 h-4 text-[--primary-500]" />
          <span className="text-sm font-medium text-[--text-primary]">
            {formatAddress(address!)}
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(getExplorerUrl(address!), "_blank")}
            className="h-8 w-8 p-0 text-[--text-secondary] hover:text-[--text-primary]"
          >
            <ExternalLink className="w-4 h-4" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => disconnect()}
            className="h-8 w-8 p-0 text-[--text-secondary] hover:text-[--accent-red]"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {!isBSCNetwork && (
        <div className="text-xs text-[--accent-orange] bg-[--accent-orange]/10 px-2 py-1 rounded">
          Switch to BSC
        </div>
      )}
    </div>
  );
};
