import { LogOut } from "lucide-react";
import React from "react";
import { useAccount, useDisconnect } from "wagmi";
import { Button } from "./ui/button";

interface AppKitWalletButtonProps {
  variant?: "default" | "outline" | "ghost";
  size?: "sm" | "lg";
  className?: string;
}

export const AppKitWalletButton: React.FC<AppKitWalletButtonProps> = ({
  variant = "default",
  size = "lg",
  className,
}) => {
  const { isConnected } = useAccount();
  const { disconnect } = useDisconnect();

  const handleClick = () => {
    if (isConnected) {
      disconnect();
    }
  };

  if (isConnected) {
    return (
      <Button
        variant={variant}
        size={size}
        onClick={handleClick}
        className={`bg-[--accent-red] hover:bg-[--accent-red]/80 text-white ${className}`}
      >
        <LogOut className="w-4 h-4 mr-2" />
        Disconnect
      </Button>
    );
  }

  return <appkit-button />;
};
