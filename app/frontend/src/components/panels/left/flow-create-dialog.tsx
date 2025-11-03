import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useToastManager } from '@/hooks/use-toast-manager';
import { flowService } from '@/services/flow-service';
import { Flow } from '@/types/flow';
import { useEffect, useState } from 'react';

interface FlowCreateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onFlowCreated: (flow: Flow) => void;
}

export function FlowCreateDialog({ isOpen, onClose, onFlowCreated }: FlowCreateDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { success, error } = useToastManager();

  // Reset form when dialog opens
  useEffect(() => {
    if (isOpen) {
      setName('');
      setDescription('');
    }
  }, [isOpen]);

  const handleCreate = async () => {
    if (!name.trim()) {
      error('Council name is required');
      return;
    }

    setIsLoading(true);
    try {
      const newFlow = await flowService.createFlow({
        name: name.trim(),
        description: description.trim() || undefined,
        nodes: [],
        edges: [],
        viewport: { x: 0, y: 0, zoom: 1 },
      });

      success(`"${newFlow.name}" created!`);
      onFlowCreated(newFlow);
      onClose();
    } catch (err) {
      console.error('Failed to create council:', err);
      error('Failed to create council');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setName('');
    setDescription('');
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux)
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (name.trim()) {
        handleCreate();
      }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Council</DialogTitle>
          <DialogDescription>
            Create a new trading council with a custom name and description.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <label htmlFor="create-name" className="text-[0.7rem] uppercase tracking-[0.28em] text-pantheon-text-primary font-semibold">
              Name
            </label>
            <Input
              id="create-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter council name"
              className="col-span-3"
              autoFocus
            />
          </div>

          <div className="grid gap-2">
            <label htmlFor="create-description" className="text-[0.7rem] uppercase tracking-[0.28em] text-pantheon-text-primary font-semibold">
              Description
            </label>
            <Input
              id="create-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter council description (optional)"
              className="col-span-3"
            />
          </div>
        </div>

        <DialogFooter className="gap-3">
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={isLoading || !name.trim()}
          >
            {isLoading ? 'Creating...' : 'Create Council'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
