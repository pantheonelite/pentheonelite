import { Clock, Sparkles } from "lucide-react";
import { Badge } from "./badge";

interface IncomingBadgeProps {
  /** Custom message to display */
  message?: string;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Show icon */
  showIcon?: boolean;
  /** Custom className */
  className?: string;
}

export function IncomingBadge({
  message = "Incoming Soon",
  size = "md",
  showIcon = true,
  className = "",
}: IncomingBadgeProps) {
  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1.5",
    lg: "text-base px-4 py-2",
  };

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  return (
    <Badge
      variant="secondary"
      className={`
        ${sizeClasses[size]}
        ${className}
        bg-gradient-to-r from-pantheon-primary-500/20 to-pantheon-secondary-500/20
        border border-pantheon-primary-500/30
        text-pantheon-text-primary
        font-semibold
        animate-pulse-glow
        shadow-[0_0_10px_hsl(var(--pantheon-primary-500)/0.3)]
        hover:shadow-[0_0_15px_hsl(var(--pantheon-primary-500)/0.5)]
        transition-all duration-300
        inline-flex items-center gap-2
      `}
    >
      {showIcon && (
        <div className="flex items-center gap-1">
          <Clock className={`${iconSizes[size]} text-pantheon-primary-500`} />
          <Sparkles
            className={`${iconSizes[size]} text-pantheon-secondary-500`}
          />
        </div>
      )}
      <span className="bg-gradient-to-r from-pantheon-primary-500 to-pantheon-secondary-500 bg-clip-text text-transparent">
        {message}
      </span>
    </Badge>
  );
}
