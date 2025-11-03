import { Accordion } from '@/components/ui/accordion';
import { ComponentGroup } from '@/data/sidebar-components';
import { SearchBox } from '../search-box';
import { ComponentItemGroup } from './component-item-group';

interface ComponentListProps {
  componentGroups: ComponentGroup[];
  searchQuery: string;
  isLoading: boolean;
  openGroups: string[];
  filteredGroups: ComponentGroup[];
  activeItem: string | null;
  onSearchChange: (query: string) => void;
  onAccordionChange: (value: string[]) => void;
}

export function ComponentList({
  componentGroups,
  searchQuery,
  isLoading,
  openGroups,
  filteredGroups,
  activeItem,
  onSearchChange,
  onAccordionChange,
}: ComponentListProps) {
  return (
    <div className="flex-grow overflow-auto text-pantheon-text-primary scrollbar-thin scrollbar-thumb-pantheon-primary-500/30">
      <SearchBox
        value={searchQuery}
        onChange={onSearchChange}
        placeholder="Search components..."
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-pantheon-text-secondary text-sm">Loading components...</div>
        </div>
      ) : (
        <Accordion
          type="multiple"
          className="w-full"
          value={openGroups}
          onValueChange={onAccordionChange}
        >
          {filteredGroups.map(group => (
            <ComponentItemGroup
              key={group.name}
              group={group}
              activeItem={activeItem}
            />
          ))}
        </Accordion>
      )}

      {!isLoading && filteredGroups.length === 0 && (
        <div className="text-center py-8 text-pantheon-text-secondary text-sm">
          {componentGroups.length === 0 ? (
            <div className="space-y-2">
              <div>No components available</div>
              <div className="text-xs text-pantheon-text-secondary/70">Components will appear here when loaded</div>
            </div>
          ) : (
            'No components match your search'
          )}
        </div>
      )}
    </div>
  );
}
