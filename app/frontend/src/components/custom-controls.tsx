import { ResetIcon } from '@radix-ui/react-icons';
import { ControlButton, Controls } from '@xyflow/react';

type CustomControlsProps = {
  onReset: () => void;
};

export function CustomControls({ onReset }: CustomControlsProps) {
  return (
    <Controls
      position="bottom-center"
      orientation="horizontal"
      style={{ bottom: 20, borderRadius: 4, gap: 10 }}
      className="terminal-text text-[0.625rem] uppercase tracking-[0.28em] border-2 border-border bg-[hsl(var(--surface))] px-4 py-2 shadow-[var(--shadow-sm)] [&_button]:border-0 [&_button]:outline-0 [&_button]:shadow-none"
    >
              <ControlButton onClick={onReset} title="Reset Flow">
              <ResetIcon />
            </ControlButton>
    </Controls>
  );
}
