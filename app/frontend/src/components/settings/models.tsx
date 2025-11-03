import { cn } from '@/lib/utils';
import { Cloud } from 'lucide-react';
import { useState } from 'react';
import { CloudModels } from './models/cloud';

interface ModelsProps {
  className?: string;
}

interface ModelSection {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  component: React.ComponentType;
}

export function Models({ className }: ModelsProps) {
  const [selectedSection, setSelectedSection] = useState('cloud');

  const modelSections: ModelSection[] = [
    {
      id: 'cloud',
      label: 'Cloud',
      icon: Cloud,
      description: 'API-based models from cloud providers',
      component: CloudModels,
    },
  ];

  const renderContent = () => {
    const section = modelSections.find(s => s.id === selectedSection);
    if (!section) return null;

    const Component = section.component;
    return <Component />;
  };

  return (
    <div className={cn("space-y-6", className)}>
      <div>
        <h2 className="font-mythic text-xs uppercase tracking-[0.32em] mb-2 text-pantheon-text-primary font-semibold">Models</h2>
        <p className="text-[0.75rem] text-pantheon-text-secondary">
          Manage your AI models from local and cloud providers.
        </p>
      </div>

      {/* Model Type Navigation */}
      <div className="flex space-x-2">
        {modelSections.map((section) => {
          const Icon = section.icon;
          const isSelected = selectedSection === section.id;
          const isDisabled = false; // Enable all tabs now that cloud models is functional

          return (
            <button
              key={section.id}
              onClick={() => !isDisabled && setSelectedSection(section.id)}
              disabled={isDisabled}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 px-4 py-2 text-[0.625rem] uppercase tracking-[0.28em] border-2 border-pantheon-border shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)] transition-all",
                isSelected
                  ? "bg-pantheon-cosmic-bg text-pantheon-primary-500 font-semibold"
                  : isDisabled
                  ? "text-pantheon-text-secondary/50 cursor-not-allowed"
                  : "bg-pantheon-cosmic-surface text-pantheon-text-secondary hover:bg-pantheon-cosmic-bg hover:text-pantheon-text-primary"
              )}
            >
              <Icon className={cn("h-4 w-4", isSelected ? "text-pantheon-primary-500" : "text-pantheon-text-secondary")} />
              {section.label}
              {isDisabled && (
                <span className="text-[0.55rem] px-1.5 py-0.5">
                  Soon
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="mt-6">
        {renderContent()}
      </div>
    </div>
  );
}
