import { AppKitWalletStatus } from "@/components/AppKitWalletStatus";
import { SimpleWalletButton } from "@/components/SimpleWalletButton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { PanelBottom, PanelLeft, PanelRight, Settings } from "lucide-react";

interface TopBarProps {
  isLeftCollapsed: boolean;
  isRightCollapsed: boolean;
  isBottomCollapsed: boolean;
  onToggleLeft: () => void;
  onToggleRight: () => void;
  onToggleBottom: () => void;
  onSettingsClick: () => void;
}

export function TopBar({
  isLeftCollapsed,
  isRightCollapsed,
  isBottomCollapsed,
  onToggleLeft,
  onToggleRight,
  onToggleBottom,
  onSettingsClick,
}: TopBarProps) {
  return (
    <div className="absolute top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-2 border-b-2 border-pantheon-border bg-pantheon-cosmic-surface shadow-[0_0_10px_hsl(var(--pantheon-primary-500)/0.2)]">
      {/* Left side - Wallet Status */}
      <div className="flex items-center">
        <AppKitWalletStatus className="text-sm" />
      </div>

      {/* Right side - Controls */}
      <div className="flex items-center gap-1">
        {/* Left Sidebar Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleLeft}
          className={cn(
            "h-8 w-8 p-0 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors",
            !isLeftCollapsed &&
              "bg-pantheon-primary-500/20 text-pantheon-primary-500"
          )}
          aria-label="Toggle left sidebar"
          title="Toggle Left Side Bar (⌘B)"
        >
          <PanelLeft size={16} />
        </Button>

        {/* Bottom Panel Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleBottom}
          className={cn(
            "h-8 w-8 p-0 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors",
            !isBottomCollapsed &&
              "bg-pantheon-primary-500/20 text-pantheon-primary-500"
          )}
          aria-label="Toggle bottom panel"
          title="Toggle Bottom Panel (⌘J)"
        >
          <PanelBottom size={16} />
        </Button>

        {/* Right Sidebar Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleRight}
          className={cn(
            "h-8 w-8 p-0 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors",
            !isRightCollapsed &&
              "bg-pantheon-primary-500/20 text-pantheon-primary-500"
          )}
          aria-label="Toggle right sidebar"
          title="Toggle Right Side Bar (⌘I)"
        >
          <PanelRight size={16} />
        </Button>

        {/* Divider */}
        <div className="mx-2 h-6 w-[2px] bg-pantheon-border" />

        {/* Wallet Connect Button */}
        <SimpleWalletButton
          variant="outline"
          size="sm"
          className="h-8 px-3 text-xs"
        />

        {/* Settings */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onSettingsClick}
          className="h-8 w-8 p-0 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors"
          aria-label="Open settings"
          title="Open Settings (⌘,)"
        >
          <Settings size={16} />
        </Button>
      </div>
    </div>
  );
}
