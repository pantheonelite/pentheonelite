import { Button } from '@/components/ui/button';
import { useTabsContext } from '@/contexts/tabs-context';
import { cn } from '@/lib/utils';
import { FileText, Layout, Settings, X } from 'lucide-react';
import { ReactNode, useState } from 'react';

interface TabBarProps {
  className?: string;
}

// Get icon for tab type
const getTabIcon = (type: string): ReactNode => {
  switch (type) {
    case 'flow':
      return <FileText size={13} />;
    case 'settings':
      return <Settings size={13} />;
    default:
      return <Layout size={13} />;
  }
};

export function TabBar({ className }: TabBarProps) {
  const { tabs, activeTabId, setActiveTab, closeTab, reorderTabs } = useTabsContext();
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  if (tabs.length === 0) {
    return null;
  }

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', ''); // Required for some browsers
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    if (draggedIndex !== null && draggedIndex !== index) {
      setDragOverIndex(index);
    }
  };

  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();

    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      reorderTabs(draggedIndex, dropIndex);
    }

    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  return (
    <div className={cn(
      "flex items-center border-b-2 border-pantheon-border bg-pantheon-cosmic-surface shadow-[0_0_10px_hsl(var(--pantheon-primary-500)/0.2)] overflow-x-auto",
      className
    )}>
      <div className="flex items-center min-w-0">
        {tabs.map((tab, index) => {
          const isActive = activeTabId === tab.id;

          return (
            <div
              key={tab.id}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
              className={cn(
                "group relative flex items-center gap-2 px-4 py-2.5 cursor-pointer transition-all duration-150 min-w-0 max-w-52 select-none border-r-2 border-pantheon-border last:border-r-0 uppercase text-xs",
                isActive
                  ? "bg-pantheon-cosmic-bg text-pantheon-primary-500 font-semibold"
                  : "bg-pantheon-cosmic-surface text-pantheon-text-secondary hover:bg-pantheon-cosmic-bg hover:text-pantheon-text-primary",
                draggedIndex === index && "opacity-60 scale-[0.98]",
                dragOverIndex === index && "ring-2 ring-pantheon-primary-500/40",
                "hover:cursor-grab active:cursor-grabbing"
              )}
              onClick={() => setActiveTab(tab.id)}
            >
              {isActive && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-pantheon-primary-500" />
              )}

              <div className={cn(
                "flex-shrink-0 transition-colors duration-150",
                isActive ? "text-pantheon-primary-500" : "text-pantheon-text-secondary"
              )}>
                {getTabIcon(tab.type)}
              </div>

              <span className="text-[0.625rem] font-semibold tracking-[0.28em] truncate min-w-0 transition-colors duration-150">
                {tab.title}
              </span>

              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-5 w-5 p-0 flex-shrink-0 ml-1 rounded-none border border-pantheon-border/30 text-pantheon-text-secondary transition-all duration-150 shadow-none",
                  "opacity-0 group-hover:opacity-100 focus:opacity-100 focus:outline-none hover:bg-pantheon-cosmic-bg hover:text-pantheon-text-primary",
                  isActive && "opacity-80 hover:opacity-100"
                )}
                onClick={(e) => {
                  e.stopPropagation();
                  closeTab(tab.id);
                }}
                onMouseDown={(e) => e.stopPropagation()}
                title="Close tab"
              >
                <X size={11} className="transition-transform duration-150 hover:scale-110" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
