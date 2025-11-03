import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { LucideIcon, Plus } from "lucide-react";

interface ComponentItemProps {
  icon: LucideIcon;
  label: string;
  onClick?: () => void;
  className?: string;
  isActive?: boolean;
}

export default function ComponentItem({
  icon: Icon,
  label,
  onClick,
  className,
  isActive = false
}: ComponentItemProps) {
  const handlePlusClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the parent onClick
    if (onClick) onClick();
  };

  return (
    <div
      className={cn(
        "group flex items-center gap-2 px-3 py-2 cursor-pointer text-[0.625rem] uppercase tracking-[0.2em] border-2 border-pantheon-border bg-pantheon-cosmic-surface transition-all duration-150 shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)]",
        isActive ? "bg-pantheon-cosmic-bg text-pantheon-primary-500" : "text-pantheon-text-secondary hover:bg-pantheon-cosmic-bg hover:text-pantheon-text-primary",
        className
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' && onClick) {
          onClick();
        }
      }}
    >
      <div className="flex-shrink-0">
        <Icon size={16} className={isActive ? "text-pantheon-primary-500" : "text-pantheon-text-secondary"} />
      </div>
      <span className="truncate">{label}</span>

      {/* Add button using shadcn Button */}
      <div className="ml-auto opacity-0 group-hover:opacity-100">
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors"
          onClick={handlePlusClick}
          aria-label="Add"
        >
          <Plus size={14} />
        </Button>
      </div>
    </div>
  );
}
