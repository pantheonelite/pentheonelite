import { Button } from '@/components/ui/button';
import { useFlowContext } from '@/contexts/flow-context';
import { cn } from '@/lib/utils';
import { Plus, Save } from 'lucide-react';

interface FlowActionsProps {
  onSave: () => Promise<void>;
  onCreate: () => void;
}

export function FlowActions({ onSave, onCreate }: FlowActionsProps) {
  const { currentFlowName, isUnsaved } = useFlowContext();

  return (
    <div className="px-4 py-3 flex justify-between flex-shrink-0 items-center border-b-2 border-pantheon-border bg-pantheon-cosmic-bg">
      <span className="font-mythic text-xs uppercase tracking-[0.28em] text-pantheon-text-primary font-semibold">
        Councils
        {isUnsaved && <span className="text-pantheon-accent-orange ml-1">*</span>}
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={onSave}
          className={cn(
            "h-7 w-7 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors",
            isUnsaved && "text-pantheon-accent-orange hover:text-pantheon-accent-orange"
          )}
          title={`Save "${currentFlowName}"`}
        >
          <Save size={14} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={onCreate}
          className="h-7 w-7 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors"
          title="Create new council"
        >
          <Plus size={14} />
        </Button>
      </div>
    </div>
  );
}
