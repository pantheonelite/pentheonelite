import { useState } from 'react';
import { Card } from '../ui/card';

interface AgentCardProps {
  name: string;
  traits: string[];
  imageUrl?: string;
  signal?: {
    type: 'buy' | 'sell' | 'hold';
    value: string;
  };
}

export function AgentCard({ name, traits, imageUrl, signal }: AgentCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const getSignalColor = () => {
    if (!signal) return '';
    switch (signal.type) {
      case 'buy':
        return 'text-pantheon-secondary-500';
      case 'sell':
        return 'text-pantheon-accent-red';
      case 'hold':
        return 'text-pantheon-accent-blue';
      default:
        return '';
    }
  };

  return (
    <Card
      className="relative bg-pantheon-cosmic-surface border-pantheon-border p-4 rounded-lg transition-all duration-300 hover:shadow-[0_0_20px_hsl(var(--pantheon-primary-500)/0.4)] cursor-pointer overflow-hidden"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Holographic glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-pantheon-primary-500/10 via-transparent to-pantheon-secondary-500/10 opacity-0 hover:opacity-100 transition-opacity duration-300" />

      <div className="relative z-10">
        {/* Agent Image/Icon */}
        {imageUrl ? (
          <div className="w-16 h-16 mx-auto mb-3 rounded-full overflow-hidden border-2 border-pantheon-primary-500 shadow-[0_0_15px_hsl(var(--pantheon-primary-500)/0.5)]">
            <img src={imageUrl} alt={name} className="w-full h-full object-cover" />
          </div>
        ) : (
          <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center shadow-[0_0_15px_hsl(var(--pantheon-primary-500)/0.5)]">
            <span className="text-2xl font-mythic text-white">{name.charAt(0)}</span>
          </div>
        )}

        {/* Agent Name */}
        <h3 className="text-lg font-mythic font-semibold text-pantheon-text-primary text-center mb-2">
          {name}
        </h3>

        {/* Traits */}
        <ul className="text-sm text-pantheon-text-secondary space-y-1 mb-3">
          {traits.slice(0, 3).map((trait, index) => (
            <li key={index} className="flex items-center">
              <span className="text-pantheon-primary-500 mr-2">•</span>
              {trait}
            </li>
          ))}
        </ul>

        {/* Signal on Hover */}
        {signal && (
          <div
            className={`text-center text-sm font-semibold uppercase tracking-wider transition-all duration-300 ${
              isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
            } ${getSignalColor()}`}
          >
            {signal.type}: {signal.value}
          </div>
        )}
      </div>
    </Card>
  );
}
