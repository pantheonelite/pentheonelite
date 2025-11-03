interface Props {
  tradingMode: "paper" | "real";
  tradingType: "futures" | "spot";
}

export function TradingModeBadge({ tradingMode, tradingType }: Props) {
  const getModeDisplay = () => {
    if (tradingMode === "paper") {
      return {
        icon: "📝",
        text: "Paper",
        className: "bg-pantheon-accent-blue/20 text-pantheon-accent-blue",
      };
    }
    return {
      icon: "💰",
      text: "Live",
      className: "bg-pantheon-accent-orange/20 text-pantheon-accent-orange",
    };
  };

  const getTypeDisplay = () => {
    if (tradingType === "futures") {
      return {
        icon: "📊",
        text: "Futures",
        className: "bg-pantheon-primary-500/20 text-pantheon-primary-500",
      };
    }
    return {
      icon: "💵",
      text: "Spot",
      className: "bg-pantheon-secondary-500/20 text-pantheon-secondary-500",
    };
  };

  const mode = getModeDisplay();
  const type = getTypeDisplay();

  return (
    <div className="flex gap-2">
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${mode.className}`}>
        {mode.icon} {mode.text}
      </span>
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${type.className}`}>
        {type.icon} {type.text}
      </span>
    </div>
  );
}

