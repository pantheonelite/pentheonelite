import { cn } from '@/lib/utils';
import { CubeIcon } from '@radix-ui/react-icons';
import { Key, Palette } from 'lucide-react';
import { useState } from 'react';
import { ApiKeysSettings, Models } from './';
import { ThemeSettings } from './appearance';

interface SettingsProps {
  className?: string;
}

interface SettingsNavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

export function Settings({ className }: SettingsProps) {
  const [selectedSection, setSelectedSection] = useState('api');

  const navigationItems: SettingsNavItem[] = [
    {
      id: 'api',
      label: 'API Keys',
      icon: Key,
      description: 'API endpoints and authentication',
    },
    {
      id: 'models',
      label: 'Models',
      icon: CubeIcon,
      description: 'Local and cloud AI models',
    },
    {
      id: 'theme',
      label: 'Theme',
      icon: Palette,
      description: 'Theme and display preferences',
    },
  ];

  const renderContent = () => {
    switch (selectedSection) {
      case 'models':
        return <Models />;
      case 'theme':
        return <ThemeSettings />;
      case 'api':
        return <ApiKeysSettings />;
      default:
        return <Models />;
    }
  };

  return (
    <div className={cn("flex justify-center h-full overflow-hidden bg-pantheon-cosmic-bg", className)}>
      <div className="flex w-full max-w-7xl mx-auto border-2 border-pantheon-border bg-pantheon-cosmic-surface shadow-[0_0_15px_hsl(var(--pantheon-primary-500)/0.2)]">
        {/* Left Navigation Pane */}
        <div className="w-60 flex-shrink-0 border-r-2 border-pantheon-border bg-pantheon-cosmic-surface">
          <div className="px-4 py-5 border-b-2 border-pantheon-border">
            <h1 className="font-mythic text-xs uppercase tracking-[0.32em] text-pantheon-text-primary font-semibold">Settings</h1>
          </div>
          <nav className="p-3 space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isSelected = selectedSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setSelectedSection(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 text-left border-2 border-pantheon-border text-[0.625rem] uppercase tracking-[0.28em] transition-all shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)]",
                    isSelected
                      ? "bg-pantheon-cosmic-bg text-pantheon-primary-500 font-semibold"
                      : "bg-pantheon-cosmic-surface text-pantheon-text-secondary hover:bg-pantheon-cosmic-bg hover:text-pantheon-text-primary"
                  )}
                >
                  <Icon className={cn("h-4 w-4 flex-shrink-0", isSelected ? "text-pantheon-primary-500" : "text-pantheon-text-secondary")} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Content Pane */}
        <div className="flex-1 overflow-auto bg-pantheon-cosmic-surface">
          <div className="p-8 max-w-4xl">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
