import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '@/services/config';
import { Cloud, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

interface CloudModelsProps {
  className?: string;
}

interface CloudModel {
  display_name: string;
  model_name: string;
  provider: string;
}

interface ModelProvider {
  name: string;
  models: Array<{
    display_name: string;
    model_name: string;
  }>;
}

export function CloudModels({ className }: CloudModelsProps) {
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/language-models/providers`);
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        setError(`Failed to fetch providers: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Failed to fetch cloud model providers:', error);
      setError('Failed to connect to backend service');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  // Flatten all models from all providers into a single array
  const allModels: CloudModel[] = providers.flatMap(provider =>
    provider.models.map(model => ({
      ...model,
      provider: provider.name
    }))
  ).sort((a, b) => a.provider.localeCompare(b.provider));

  return (
    <div className={cn("space-y-6", className)}>

      {error && (
        <div className="border-2 border-pantheon-accent-red/40 bg-pantheon-accent-red/5 p-4 shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)]">
          <div className="flex items-start gap-3">
            <Cloud className="h-5 w-5 text-pantheon-accent-red mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wider text-pantheon-accent-red">Error</h4>
              <p className="text-sm text-pantheon-text-secondary mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-mythic text-base font-semibold text-pantheon-primary-500">Available Models</h3>
          <span className="text-xs text-pantheon-text-secondary">
            {allModels.length} models from {providers.length} providers
          </span>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-pantheon-text-secondary" />
            <p className="text-sm text-pantheon-text-secondary">Loading cloud models...</p>
          </div>
        ) : allModels.length > 0 ? (
          <div className="space-y-1">
            {allModels.map((model) => (
              <div
                key={`${model.provider}-${model.model_name}`}
                className="group flex items-center justify-between border-2 border-pantheon-border bg-pantheon-cosmic-surface px-3 py-2.5 shadow-[0_0_5px_hsl(var(--pantheon-primary-500)/0.1)] transition-all hover:bg-pantheon-cosmic-bg"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold truncate text-pantheon-primary-500">{model.display_name}</span>
                    {model.model_name !== model.display_name && (
                      <span className="font-mono text-xs text-pantheon-text-secondary">
                        {model.model_name}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge className="text-xs text-pantheon-text-primary bg-pantheon-primary-500/20 border-pantheon-primary-500/30">
                    {model.provider}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          !loading && (
            <div className="text-center py-8">
              <Cloud className="h-8 w-8 mx-auto mb-2 opacity-50 text-pantheon-text-secondary" />
              <p className="text-sm text-pantheon-text-secondary">No models available</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}
