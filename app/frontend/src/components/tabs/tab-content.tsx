import { useTabsContext } from '@/contexts/tabs-context';
import { cn } from '@/lib/utils';
import { TabService } from '@/services/tab-service';
import { FileText, FolderOpen } from 'lucide-react';
import { useEffect } from 'react';

interface TabContentProps {
  className?: string;
}

export function TabContent({ className }: TabContentProps) {
  const { tabs, activeTabId, openTab } = useTabsContext();

  const activeTab = tabs.find(tab => tab.id === activeTabId);

  // Restore content for tabs that don't have it (from localStorage restoration)
  useEffect(() => {
    if (activeTab && !activeTab.content) {
      try {
        const restoredTab = TabService.restoreTab({
          type: activeTab.type,
          title: activeTab.title,
          flow: activeTab.flow,
          metadata: activeTab.metadata,
        });

        // Update the tab with restored content
        openTab({
          id: activeTab.id,
          type: restoredTab.type,
          title: restoredTab.title,
          content: restoredTab.content,
          flow: restoredTab.flow,
          metadata: restoredTab.metadata,
        });
      } catch (error) {
        console.error('Failed to restore tab content:', error);
      }
    }
  }, [activeTab, openTab]);

  if (!activeTab) {
    return (
      <div className={cn(
        "h-full w-full flex items-center justify-center bg-pantheon-cosmic-bg text-pantheon-text-secondary",
        className
      )}>
        <div className="text-center space-y-6 max-w-2xl px-6">
          <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center shadow-[0_0_30px_hsl(var(--pantheon-primary-500)/0.4)] animate-pulse-glow">
            <FolderOpen size={48} className="text-white" />
          </div>
          <div>
            <div className="font-mythic text-3xl md:text-4xl font-bold text-pantheon-text-primary mb-3 tracking-wide">
              Welcome to the Pantheon Elite
            </div>
            <div className="text-base text-pantheon-text-secondary leading-relaxed max-w-lg mx-auto">
              Forge your multi-agent trading strategy. Create a flow from the left sidebar <span className="text-pantheon-primary-500 font-semibold">(⌘B)</span> to begin, or open settings <span className="text-pantheon-primary-500 font-semibold">(⌘,)</span> to configure your divine council.
            </div>
          </div>
          <div className="flex items-center justify-center gap-2 text-xs uppercase tracking-wider text-pantheon-text-secondary border border-pantheon-border rounded-full px-4 py-2 bg-pantheon-cosmic-surface inline-flex mx-auto">
            <FileText size={14} className="text-pantheon-primary-500" />
            <span>Flows Open in Tabs</span>
          </div>
        </div>
      </div>
    );
  }

  // Show loading state if content is being restored
  if (!activeTab.content) {
    return (
      <div className={cn(
        "h-full w-full flex items-center justify-center bg-pantheon-cosmic-bg text-pantheon-text-secondary",
        className
      )}>
        <div className="text-center space-y-3">
          <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center animate-pulse">
            <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div className="font-mythic text-lg font-semibold text-pantheon-text-primary tracking-wide">
            Loading {activeTab.title}...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("h-full w-full bg-pantheon-cosmic-bg overflow-hidden", className)}>
      {activeTab.content}
    </div>
  );
}
