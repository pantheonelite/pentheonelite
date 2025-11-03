
interface ComponentActionsProps {
}

export function ComponentActions({ }: ComponentActionsProps) {
  return (
    <div className="px-4 py-3 flex justify-between flex-shrink-0 items-center border-b-2 border-pantheon-border bg-pantheon-cosmic-bg">
      <span className="font-mythic text-xs uppercase tracking-[0.28em] text-pantheon-text-primary font-semibold">Components</span>
      {/* <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="h-6 w-6 text-primary hover:bg-ramp-grey-700"
          aria-label="Toggle sidebar"
          title={`Toggle Components Panel (${formatKeyboardShortcut(['B'])})`}
        >
          <PanelRight size={16} />
        </Button>
      </div> */}
    </div>
  );
}
