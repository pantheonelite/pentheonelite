import { Loader2, Wallet } from "lucide-react";
import React, { useState } from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";
import { BSCWallet } from "./BSCWallet";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";

interface WalletConnectButtonProps {
  variant?: "default" | "outline" | "ghost";
  size?: "sm" | "lg";
  className?: string;
  showModal?: boolean;
}

export const WalletConnectButton: React.FC<WalletConnectButtonProps> = ({
  variant = "default",
  size = "lg",
  className,
  showModal = true,
}) => {
  const { isConnected } = useAccount();
  const { isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const [isOpen, setIsOpen] = useState(false);

  const handleConnect = () => {
    if (isConnected) {
      disconnect();
    } else if (showModal) {
      setIsOpen(true);
    }
  };

  const getButtonText = () => {
    if (isPending) return "Connecting...";
    if (isConnected) return "Disconnect";
    return "Connect Wallet";
  };

  const getButtonIcon = () => {
    if (isPending) return <Loader2 className="w-4 h-4 animate-spin" />;
    return <Wallet className="w-4 h-4" />;
  };

  if (showModal) {
    return (
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button
            variant={variant}
            size={size}
            onClick={handleConnect}
            disabled={isPending}
            className={`bg-[--primary-500] hover:bg-[--primary-600] text-white ${className}`}
          >
            {getButtonIcon()}
            <span className="ml-2">{getButtonText()}</span>
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Connect Your Wallet</DialogTitle>
            <DialogDescription>
              Choose a wallet to connect to the Pantheon Elite platform
            </DialogDescription>
          </DialogHeader>
          <BSCWallet />
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleConnect}
      disabled={isPending}
      className={`bg-[--primary-500] hover:bg-[--primary-600] text-white ${className}`}
    >
      {getButtonIcon()}
      <span className="ml-2">{getButtonText()}</span>
    </Button>
  );
};
