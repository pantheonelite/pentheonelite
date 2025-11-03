import { AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Separator } from '@/components/ui/separator';
import { Flow } from '@/types/flow';
import FlowItem from './flow-item';

interface FlowItemGroupProps {
  title: string;
  flows: Flow[];
  onLoadFlow: (flow: Flow) => Promise<void>;
  onDeleteFlow: (flow: Flow) => Promise<void>;
  onRefresh: () => Promise<void>;
  currentFlowId?: number | null;
}

export function FlowItemGroup({ title, flows, onLoadFlow, onDeleteFlow, onRefresh, currentFlowId }: FlowItemGroupProps) {
  const groupId = title.toLowerCase().replace(/\s+/g, '-');

  return (
    <AccordionItem value={groupId} className="border-2 border-border">
      <AccordionTrigger className="terminal-text px-4 py-3 uppercase tracking-[0.28em] text-[0.625rem] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--surface-hover))] hover:no-underline">
        <div className="flex items-center justify-between w-full">
          <span className="font-semibold">{title}</span>
          <span className="text-[hsl(var(--muted-foreground))]">({flows.length})</span>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-0 pb-0">
        <div className="space-y-1">
          {flows.map((flow, index) => (
            <div key={flow.id}>
              <FlowItem
                flow={flow}
                onLoadFlow={onLoadFlow}
                onDeleteFlow={onDeleteFlow}
                onRefresh={onRefresh}
                isActive={currentFlowId === flow.id}
              />
              {index < flows.length - 1 && (
                <Separator className="mx-4" />
              )}
            </div>
          ))}
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
