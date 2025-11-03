import { AgentCard } from '../pantheon';

export function HowItWorks() {
  const steps = [
    {
      number: 1,
      title: 'Summon Legends',
      description: 'Choose from legendary crypto agents: CZ, Vitalik Buterin, Michael Saylor, Elon Musk, Satoshi Nakamoto, and more',
      icon: '✨',
    },
    {
      number: 2,
      title: 'Collaborate Signals',
      description: 'Agents debate market conditions, refining strategies through consensus',
      icon: '💬',
    },
    {
      number: 3,
      title: 'Execute on Aster',
      description: 'Automated execution of refined strategies on Aster DEX perpetuals',
      icon: '⚡',
    },
    {
      number: 4,
      title: 'Track Wins',
      description: 'Monitor real-time PnL, debate history, and council performance',
      icon: '📈',
    },
  ];

  const mockAgents = [
    {
      name: 'Value Sovereign',
      traits: ['Deep value analysis', 'Long-term focus', 'Risk-averse'],
      signal: { type: 'buy' as const, value: '+15%' },
    },
    {
      name: 'Growth Oracle',
      traits: ['Innovation focus', 'Disruption seeker', 'High conviction'],
      signal: { type: 'buy' as const, value: '+22%' },
    },
    {
      name: 'Macro Strategist',
      traits: ['Global trends', 'Rate sensitivity', 'Timing expert'],
      signal: { type: 'hold' as const, value: 'Neutral' },
    },
  ];

  return (
    <section id="vision" className="py-20 px-6 bg-pantheon-cosmic-bg">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-mythic font-bold text-pantheon-text-primary mb-4">
            The Edge: Debates + Algorithms = Alpha
          </h2>
          <p className="text-lg text-pantheon-text-secondary max-w-2xl mx-auto">
            Harness the power of collaborative AI intelligence for superior trading outcomes
          </p>
        </div>

        {/* Flow diagram */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-16">
          {steps.map((step, index) => (
            <div key={step.number} className="relative">
              <div className="flex flex-col items-center text-center">
                {/* Icon */}
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 flex items-center justify-center text-4xl mb-4 shadow-[0_0_30px_hsl(var(--pantheon-primary-500)/0.5)] animate-pulse-glow">
                  {step.icon}
                </div>

                {/* Step number */}
                <div className="text-sm font-mono text-pantheon-primary-500 font-bold mb-2">
                  STEP {step.number}
                </div>

                {/* Title */}
                <h3 className="text-xl font-mythic font-semibold text-pantheon-text-primary mb-2">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-sm text-pantheon-text-secondary">{step.description}</p>
              </div>

              {/* Arrow connector (desktop) */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-10 -right-4 w-8 h-0.5 bg-gradient-to-r from-pantheon-primary-500 to-transparent">
                  <div className="absolute right-0 -top-1 w-0 h-0 border-l-8 border-l-pantheon-primary-500 border-t-4 border-t-transparent border-b-4 border-b-transparent" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Agent showcase */}
        <div className="mt-16">
          <h3 className="text-2xl font-mythic font-semibold text-pantheon-text-primary text-center mb-8">
            Meet Your Council
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {mockAgents.map((agent, index) => (
              <div key={index} className="animate-cosmic-float" style={{ animationDelay: `${index * 0.2}s` }}>
                <AgentCard {...agent} />
              </div>
            ))}
          </div>
          <p className="text-center text-pantheon-text-secondary mt-8">
            Choose from <span className="text-pantheon-primary-500 font-bold">20+ legendary agents</span> to build your perfect council
          </p>
        </div>
      </div>
    </section>
  );
}
