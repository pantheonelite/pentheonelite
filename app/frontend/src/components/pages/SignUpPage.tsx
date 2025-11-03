import {
  AlertCircle,
  CheckCircle,
  Copy,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAccount, useDisconnect } from "wagmi";
import { useFeatureFlag } from "../../hooks/useFeatureFlag";
import { CosmicBackground } from "../landing/CosmicBackground";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { IncomingBadge } from "../ui/incoming-badge";

export function SignUpPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { isConnected, address, chain } = useAccount();
  const { disconnect } = useDisconnect();

  // Feature flag for signup functionality
  const isSignupEnabled = useFeatureFlag("enableSignup");

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

  // Handle disconnect
  const handleDisconnect = () => {
    disconnect();
    toast.success("Wallet disconnected successfully!");
  };

  const handleJoinPantheon = async () => {
    setIsSubmitting(true);

    // Mock API call
    setTimeout(() => {
      setSubmitted(true);
      setIsSubmitting(false);
      // Redirect to teaser dashboard using React Router
      setTimeout(() => {
        navigate("/dashboard");
      }, 2000);
    }, 1000);
  };

  if (submitted) {
    return (
      <div className="relative min-h-screen flex items-center justify-center px-6">
        <CosmicBackground />
        <div className="relative z-10 w-full max-w-md">
          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-8 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center animate-pulse-glow">
              <span className="text-4xl">✓</span>
            </div>
            <h2 className="text-2xl font-mythic font-bold text-pantheon-text-primary mb-4">
              Welcome to the Pantheon!
            </h2>
            <p className="text-pantheon-text-secondary mb-2">
              Your spot is secured. Redirecting to your dashboard...
            </p>
            <p className="text-sm text-pantheon-primary-500">
              Your Pantheon Awaits
            </p>
          </Card>
        </div>
      </div>
    );
  }

  // Show incoming status when signup is disabled
  if (!isSignupEnabled) {
    return (
      <div className="relative min-h-screen flex items-center justify-center px-6">
        <CosmicBackground />
        <div className="relative z-10 w-full max-w-md">
          {/* Back to home */}
          <div className="mb-8">
            <button
              onClick={() => navigate("/")}
              className="text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors inline-flex items-center group"
            >
              <span className="mr-2 group-hover:-translate-x-1 transition-transform">
                ←
              </span>{" "}
              Back to Home
            </button>
          </div>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-8 shadow-[0_0_40px_hsl(var(--pantheon-primary-500)/0.2)] text-center">
            {/* Header */}
            <div className="mb-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center animate-pulse-glow">
                <span className="text-white font-mythic text-2xl">Ψ</span>
              </div>
              <h1 className="text-3xl font-mythic font-bold text-pantheon-text-primary mb-2">
                Ascend Now
              </h1>
              <p className="text-pantheon-text-secondary">
                Join the Pantheon Waitlist
              </p>
            </div>

            {/* Incoming Status */}
            <div className="space-y-6">
              <div className="flex justify-center">
                <IncomingBadge
                  message="Incoming Soon"
                  size="lg"
                  showIcon={true}
                />
              </div>

              <div className="text-center">
                <p className="text-pantheon-text-secondary mb-4">
                  The Pantheon is preparing for your arrival. Stay tuned for the
                  grand unveiling.
                </p>
                <p className="text-sm text-pantheon-primary-500 font-semibold">
                  🔥 Early access unlocks exclusive agent blueprints
                </p>
              </div>
            </div>

            {/* Trust indicators */}
            <div className="mt-8 text-center">
              <p className="text-sm text-pantheon-text-secondary mb-2">
                Trusted by leading traders
              </p>
              <div className="flex justify-center items-center space-x-4 text-pantheon-text-secondary">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-2 h-2 bg-pantheon-secondary-500 rounded-full animate-pulse"
                    style={{ animationDelay: "0s" }}
                  />
                  <span className="text-sm font-medium">Non-custodial</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div
                    className="w-2 h-2 bg-pantheon-secondary-500 rounded-full animate-pulse"
                    style={{ animationDelay: "0.5s" }}
                  />
                  <span className="text-sm font-medium">Open Source</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div
                    className="w-2 h-2 bg-pantheon-secondary-500 rounded-full animate-pulse"
                    style={{ animationDelay: "1s" }}
                  />
                  <span className="text-sm font-medium">Audited</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center px-6">
      <CosmicBackground />
      <div className="relative z-10 w-full max-w-md">
        {/* Back to home */}
        <div className="mb-8">
          <button
            onClick={() => navigate("/")}
            className="text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors inline-flex items-center group"
          >
            <span className="mr-2 group-hover:-translate-x-1 transition-transform">
              ←
            </span>{" "}
            Back to Home
          </button>
        </div>

        <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-8 shadow-[0_0_40px_hsl(var(--pantheon-primary-500)/0.2)]">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center">
              <span className="text-white font-mythic text-2xl">Ψ</span>
            </div>
            <h1 className="text-3xl font-mythic font-bold text-pantheon-text-primary mb-2">
              Ascend Now
            </h1>
            <p className="text-pantheon-text-secondary">
              Join the Pantheon Waitlist
            </p>
          </div>

          {/* Wallet Connection Section */}
          <div className="space-y-6">
            {/* Wallet connection */}
            <div className="text-center">
              <label className="block text-sm font-medium text-pantheon-text-primary mb-4">
                Connect Your Wallet
              </label>

              {/* AppKit Button - Centered and Styled */}
              <div className="flex justify-center mb-4">
                <div
                  className="relative"
                  style={{ display: "flex", justifyContent: "center" }}
                >
                  <appkit-button style={{ margin: "0 auto" }} />
                  <div className="absolute inset-0 bg-gradient-to-r from-pantheon-primary-500/20 to-pantheon-secondary-500/20 rounded-lg opacity-0 hover:opacity-100 transition-opacity pointer-events-none" />
                </div>
              </div>

              {/* Supported wallets info */}
              <div className="text-center">
                <p className="text-xs text-pantheon-text-secondary">
                  Supports MetaMask, WalletConnect, Coinbase, and 300+ wallets
                </p>
              </div>
            </div>

            {/* Switch Wallet Button - Only show when connected */}
            {isConnected && (
              <div className="text-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDisconnect}
                  className="text-pantheon-text-secondary hover:text-pantheon-accent-orange border-pantheon-border hover:border-pantheon-accent-orange"
                >
                  Switch Wallet
                </Button>
              </div>
            )}

            {/* Wallet Status */}
            {isConnected && (
              <div className="space-y-4">
                {/* Connection success */}
                <div className="p-4 bg-pantheon-secondary-500/10 border border-pantheon-secondary-500/20 rounded-lg">
                  <div className="flex items-center space-x-2 mb-3">
                    <CheckCircle className="w-5 h-5 text-pantheon-secondary-500" />
                    <span className="font-semibold text-pantheon-text-primary">
                      Wallet Connected Successfully!
                    </span>
                  </div>

                  {/* Network Status */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-pantheon-text-secondary">
                      Network
                    </span>
                    <div className="flex items-center space-x-2">
                      {isBSCNetwork ? (
                        <CheckCircle className="w-4 h-4 text-pantheon-secondary-500" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-pantheon-accent-orange" />
                      )}
                      <Badge
                        variant={isBSCNetwork ? "default" : "destructive"}
                        className={
                          isBSCNetwork
                            ? "bg-pantheon-secondary-500"
                            : "bg-pantheon-accent-orange"
                        }
                      >
                        {networkName}
                      </Badge>
                    </div>
                  </div>

                  {/* Wallet Address Actions */}
                  <div className="flex items-center justify-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={copyAddress}
                      className="h-8 px-3 text-pantheon-text-secondary hover:text-pantheon-text-primary"
                    >
                      <Copy className="w-4 h-4 mr-1" />
                      Copy
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        window.open(getExplorerUrl(address!), "_blank")
                      }
                      className="h-8 px-3 text-pantheon-text-secondary hover:text-pantheon-text-primary"
                    >
                      <ExternalLink className="w-4 h-4 mr-1" />
                      View
                    </Button>
                  </div>

                  {/* Network Warning */}
                  {!isBSCNetwork && (
                    <div className="mt-3 p-3 bg-pantheon-accent-orange/10 border border-pantheon-accent-orange/20 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertCircle className="w-4 h-4 text-pantheon-accent-orange" />
                        <span className="text-sm text-pantheon-accent-orange">
                          Please switch to BSC network for optimal experience
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Join Button - Only show when wallet is connected */}
            {isConnected && (
              <div className="text-center">
                <Button
                  onClick={handleJoinPantheon}
                  disabled={isSubmitting}
                  className="w-full bg-pantheon-secondary-500 hover:bg-pantheon-secondary-600 text-white font-bold py-6 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_hsl(var(--pantheon-secondary-500)/0.4)]"
                >
                  {isSubmitting ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Joining...</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-5 h-5" />
                      <span>Join Pantheon</span>
                    </div>
                  )}
                </Button>
              </div>
            )}
          </div>

          {/* FOMO text - Only show when wallet is connected */}
          {isConnected && (
            <div className="mt-6 text-center">
              <p className="text-sm text-pantheon-accent-orange font-semibold">
                🔥 Early access unlocks exclusive agent blueprints
              </p>
            </div>
          )}
        </Card>

        {/* Trust indicators */}
        <div className="mt-8 text-center">
          <p className="text-sm text-pantheon-text-secondary mb-2">
            Trusted by leading traders
          </p>
          <div className="flex justify-center items-center space-x-4 text-pantheon-text-secondary">
            <div className="flex items-center">
              <span className="text-pantheon-secondary-500 mr-1">✓</span>
              <span className="text-xs">Non-custodial</span>
            </div>
            <div className="flex items-center">
              <span className="text-pantheon-secondary-500 mr-1">✓</span>
              <span className="text-xs">Open Source</span>
            </div>
            <div className="flex items-center">
              <span className="text-pantheon-secondary-500 mr-1">✓</span>
              <span className="text-xs">Audited</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
