import { LogOut, Wallet } from "lucide-react";
import React from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";
import { Button } from "./ui/button";

interface SimpleWalletButtonProps {
  variant?: "default" | "outline" | "ghost";
  size?: "sm" | "lg";
  className?: string;
}

export const SimpleWalletButton: React.FC<SimpleWalletButtonProps> = ({
  variant = "default",
  size = "lg",
  className,
}) => {
  const { isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();

  const handleClick = () => {
    if (isConnected) {
      disconnect();
    } else if (connectors.length > 0) {
      connect({ connector: connectors[0] });
    }
  };

  const getButtonText = () => {
    if (isPending) return "Connecting...";
    if (isConnected) return "Disconnect";
    return "Connect Wallet";
  };

  const getButtonIcon = () => {
    if (isPending) return <Wallet className="w-4 h-4 animate-pulse" />;
    if (isConnected) return <LogOut className="w-4 h-4" />;
    return <Wallet className="w-4 h-4" />;
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleClick}
      disabled={isPending}
      className={`${
        isConnected
          ? "bg-[--accent-red] hover:bg-[--accent-red]/80"
          : "bg-[--primary-500] hover:bg-[--primary-600]"
      } text-white ${className}`}
    >
      {getButtonIcon()}
      <span className="ml-2">{getButtonText()}</span>
    </Button>
  );
};
