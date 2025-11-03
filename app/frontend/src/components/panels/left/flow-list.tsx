import { FlowItemGroup } from '@/components/panels/left/flow-item-group';
import { SearchBox } from '@/components/panels/search-box';
import { Accordion } from '@/components/ui/accordion';
import { useTabsContext } from '@/contexts/tabs-context';
import { Flow } from '@/types/flow';
import { FolderOpen } from 'lucide-react';

interface FlowListProps {
  flows: Flow[];
  searchQuery: string;
  isLoading: boolean;
  openGroups: string[];
  filteredFlows: Flow[];
  recentFlows: Flow[];
  templateFlows: Flow[];
  onSearchChange: (query: string) => void;
  onAccordionChange: (value: string[]) => void;
  onLoadFlow: (flow: Flow) => Promise<void>;
  onDeleteFlow: (flow: Flow) => Promise<void>;
  onRefresh: () => Promise<void>;
}

export function FlowList({
  flows,
  searchQuery,
  isLoading,
  openGroups,
  filteredFlows,
  recentFlows,
  templateFlows,
  onSearchChange,
  onAccordionChange,
  onLoadFlow,
  onDeleteFlow,
  onRefresh,
}: FlowListProps) {
  const { tabs, activeTabId } = useTabsContext();

  // Only consider a flow active if the current active tab is a flow tab with that flow's ID
  const getActiveFlowId = (): number | null => {
    const activeTab = tabs.find(tab => tab.id === activeTabId);

    // If no active tab or active tab is not a flow tab, no flow should be active
    if (!activeTab || activeTab.type !== 'flow') {
      return null;
    }

    // Return the flow ID from the active flow tab
    return activeTab.flow?.id || null;
  };

  const activeFlowId = getActiveFlowId();

  return (
    <div className="flex-grow overflow-auto text-pantheon-text-primary scrollbar-thin scrollbar-thumb-pantheon-primary-500/30">
      <SearchBox
        value={searchQuery}
        onChange={onSearchChange}
        placeholder="Search councils..."
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-pantheon-text-secondary text-sm">Loading councils...</div>
        </div>
      ) : (
        <Accordion
          type="multiple"
          className="w-full"
          value={openGroups}
          onValueChange={onAccordionChange}
        >
          {recentFlows.length > 0 && (
            <FlowItemGroup
              key="recent-flows"
              title="Recent Councils"
              flows={recentFlows}
              onLoadFlow={onLoadFlow}
              onDeleteFlow={onDeleteFlow}
              onRefresh={onRefresh}
              currentFlowId={activeFlowId}
            />
          )}

          {templateFlows.length > 0 && (
            <FlowItemGroup
              key="templates"
              title="Templates"
              flows={templateFlows}
              onLoadFlow={onLoadFlow}
              onDeleteFlow={onDeleteFlow}
              onRefresh={onRefresh}
              currentFlowId={activeFlowId}
            />
          )}
        </Accordion>
      )}

      {!isLoading && filteredFlows.length === 0 && (
        <div className="text-center py-8 text-pantheon-text-secondary text-sm">
          {flows.length === 0 ? (
            <div className="space-y-2">
              <FolderOpen size={32} className="mx-auto text-pantheon-primary-500" />
              <div className="text-pantheon-text-primary">No councils saved yet</div>
              <div className="text-xs text-pantheon-text-secondary/70">Create your first council to get started</div>
            </div>
          ) : (
            'No councils match your search'
          )}
        </div>
      )}
    </div>
  );
}
