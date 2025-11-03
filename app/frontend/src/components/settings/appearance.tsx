import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Monitor, Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

export function ThemeSettings() {
  const { theme, setTheme } = useTheme();

  const themes = [
    {
      id: 'light',
      name: 'Light',
      description: 'A clean, bright interface',
      icon: Sun,
    },
    {
      id: 'dark',
      name: 'Dark',
      description: 'A comfortable dark interface',
      icon: Moon,
    },
    {
      id: 'system',
      name: 'System',
      description: 'Use your system preference',
      icon: Monitor,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-mythic text-lg font-semibold text-pantheon-text-primary mb-2">Theme</h2>
        <p className="text-sm text-pantheon-text-secondary">
          Customize the look and feel of your application.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-mythic text-base text-pantheon-text-primary">
            Theme
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-pantheon-text-secondary">
            Select your preferred theme or use system setting to automatically switch between light and dark modes.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {themes.map((themeOption) => {
              const Icon = themeOption.icon;
              const isSelected = theme === themeOption.id;

              return (
                <Button
                  key={themeOption.id}
                  className={cn(
                    "flex flex-col items-center gap-3 h-auto py-6 px-4 bg-pantheon-cosmic-surface border-2 border-pantheon-border shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)] hover:bg-pantheon-cosmic-bg transition-colors",
                    isSelected && "border-pantheon-primary-500 text-pantheon-primary-500"
                  )}
                  onClick={() => setTheme(themeOption.id)}
                >
                  <Icon className={cn("h-6 w-6", isSelected ? "text-pantheon-primary-500" : "text-pantheon-text-secondary")} />
                  <div className="text-center">
                    <div className="text-sm font-semibold uppercase tracking-wider text-pantheon-text-primary">{themeOption.name}</div>
                    <div className="text-xs text-pantheon-text-secondary mt-1">
                      {themeOption.description}
                    </div>
                  </div>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
