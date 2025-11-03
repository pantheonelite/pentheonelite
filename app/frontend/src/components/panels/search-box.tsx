import { Button } from '@/components/ui/button';
import { Search } from 'lucide-react';

interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchBox({
  value,
  onChange,
  placeholder = "Search components..."
}: SearchBoxProps) {
  return (
    <div className="px-4 py-3 sticky top-0 z-10 border-b-2 border-pantheon-border bg-pantheon-cosmic-bg">
      <div className="flex items-center gap-2 border-2 border-pantheon-border bg-pantheon-cosmic-surface px-3 py-2 shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)]">
        <Search className="h-4 w-4 text-pantheon-primary-500 flex-shrink-0" />
        <input
          type="text"
          placeholder={placeholder}
          className="text-[0.625rem] uppercase tracking-[0.28em] bg-transparent focus:outline-none text-pantheon-text-primary w-full placeholder-pantheon-text-secondary"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        {value && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onChange('')}
            className="h-6 w-6 text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors"
            aria-label="Clear search"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </Button>
        )}
      </div>
    </div>
  );
}
