import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PnLChart } from "../pantheon";
import { Button } from "../ui/button";

export function Hero() {
  const navigate = useNavigate();
  const [userCount, setUserCount] = useState(1247);

  const handleNavClick = (
    e: React.MouseEvent<HTMLAnchorElement>,
    targetId: string
  ) => {
    e.preventDefault();
    const element = document.getElementById(targetId);
    if (element) {
      const startPosition = window.pageYOffset || window.scrollY;
      const targetPosition = element.offsetTop - 80; // Account for fixed header
      const distance = targetPosition - startPosition;
      const duration = 300; // Very fast: 300ms

      // Start with immediate small scroll for instant feedback
      const initialScroll = distance * 0.1; // 10% immediate jump
      window.scrollTo(0, startPosition + initialScroll);

      // Then smooth scroll the rest
      const start = performance.now();
      const adjustedStart = startPosition + initialScroll;
      const adjustedDistance = distance - initialScroll;

      const easeInOutCubic = (t: number): number => {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      };

      const animation = (currentTime: number) => {
        const timeElapsed = currentTime - start;
        const progress = Math.min(timeElapsed / duration, 1);
        const ease = easeInOutCubic(progress);

        window.scrollTo(0, adjustedStart + adjustedDistance * ease);

        if (progress < 1) {
          requestAnimationFrame(animation);
        }
      };

      // Start animation immediately - no delay
      requestAnimationFrame(animation);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setUserCount((prev) => prev + Math.floor(Math.random() * 3));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Mock chart data showing debate impact
  const chartLabels = [
    "Day 1",
    "Day 2",
    "Day 3",
    "Day 4",
    "Day 5",
    "Day 6",
    "Day 7",
  ];
  const chartDatasets = [
    {
      label: "Debate Council",
      data: [100, 105, 112, 118, 125, 132, 140],
      color: "rgb(16, 185, 129)", // Emerald green
    },
    {
      label: "Market Average",
      data: [100, 102, 103, 105, 106, 108, 110],
      color: "rgb(159, 166, 178)", // Muted gray
    },
  ];

  return (
    <section
      id="home"
      className="relative min-h-[80vh] w-full flex flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-pantheon-cosmic-bg via-pantheon-cosmic-surface to-pantheon-cosmic-bg"
    >
      {/* Animated gradient mesh overlay */}
      <div className="absolute inset-0 overflow-hidden opacity-30">
        <div className="absolute top-0 left-0 w-96 h-96 bg-pantheon-primary-500/20 rounded-full blur-3xl animate-pulse-glow animate-drift-right" />
        <div
          className="absolute bottom-0 right-0 w-96 h-96 bg-pantheon-secondary-500/20 rounded-full blur-3xl animate-pulse-glow animate-drift-left"
          style={{ animationDelay: "1.5s" }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-pantheon-primary-300/10 rounded-full blur-3xl animate-pulse-glow animate-scale-pulse"
          style={{ animationDelay: "3s" }}
        />
      </div>

      {/* Large glowing orbs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 right-1/4 w-72 h-72 bg-gradient-to-br from-pantheon-primary-500/30 to-pantheon-secondary-500/20 rounded-full blur-3xl animate-cosmic-float animate-drift-up" />
        <div
          className="absolute bottom-32 left-1/4 w-96 h-96 bg-gradient-to-br from-pantheon-secondary-500/25 to-pantheon-primary-500/15 rounded-full blur-3xl animate-cosmic-float animate-diagonal-float"
          style={{ animationDelay: "2s" }}
        />
        <div
          className="absolute top-1/3 right-1/3 w-64 h-64 bg-gradient-to-br from-pantheon-accent-blue/20 to-pantheon-primary-500/10 rounded-full blur-3xl animate-cosmic-float animate-drift-right"
          style={{ animationDelay: "4s" }}
        />

        {/* Rotating gradient orbs */}
        <div className="absolute top-1/4 left-1/3 w-80 h-80 bg-gradient-to-br from-pantheon-primary-500/15 to-pantheon-secondary-500/10 rounded-full blur-3xl animate-slow-rotate" />
        <div
          className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-gradient-to-br from-pantheon-secondary-500/12 to-pantheon-primary-500/8 rounded-full blur-3xl animate-slow-rotate"
          style={{ animationDelay: "10s", animationDirection: "reverse" }}
        />

        {/* Orbiting particles */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0">
          <div className="absolute w-3 h-3 bg-pantheon-primary-300 rounded-full blur-sm animate-orbit" />
          <div
            className="absolute w-2 h-2 bg-pantheon-secondary-300 rounded-full blur-sm animate-orbit-large"
            style={{ animationDelay: "8s" }}
          />
          <div
            className="absolute w-1.5 h-1.5 bg-pantheon-accent-blue rounded-full blur-sm animate-orbit-xl"
            style={{ animationDelay: "12s" }}
          />
        </div>
      </div>

      {/* Enhanced starfield background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Large bright stars */}
        <div className="absolute top-10 left-20 w-2 h-2 bg-pantheon-primary-300 rounded-full animate-star-twinkle shadow-[0_0_6px_hsl(var(--pantheon-primary-300))]" />
        <div
          className="absolute top-24 left-1/4 w-1.5 h-1.5 bg-pantheon-secondary-300 rounded-full animate-star-twinkle"
          style={{ animationDelay: "0.3s" }}
        />
        <div
          className="absolute top-40 right-1/3 w-2 h-2 bg-pantheon-primary-500 rounded-full animate-star-twinkle shadow-[0_0_8px_hsl(var(--pantheon-primary-500))]"
          style={{ animationDelay: "0.6s" }}
        />
        <div
          className="absolute bottom-40 left-60 w-1.5 h-1.5 bg-pantheon-primary-500 rounded-full animate-star-twinkle"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute top-60 right-20 w-1 h-1 bg-pantheon-accent-blue rounded-full animate-star-twinkle"
          style={{ animationDelay: "1.5s" }}
        />
        <div
          className="absolute bottom-20 right-80 w-2 h-2 bg-pantheon-primary-300 rounded-full animate-star-twinkle shadow-[0_0_6px_hsl(var(--pantheon-primary-300))]"
          style={{ animationDelay: "2s" }}
        />

        {/* Medium stars with drift animations */}
        <div
          className="absolute top-16 right-1/4 w-1 h-1 bg-pantheon-secondary-300 rounded-full animate-star-twinkle animate-drift-right"
          style={{ animationDelay: "0.2s" }}
        />
        <div
          className="absolute top-48 left-1/2 w-1 h-1 bg-pantheon-primary-500 rounded-full animate-star-twinkle animate-drift-left"
          style={{ animationDelay: "0.8s" }}
        />
        <div
          className="absolute bottom-60 right-1/3 w-1 h-1 bg-pantheon-accent-blue rounded-full animate-star-twinkle animate-drift-up"
          style={{ animationDelay: "1.2s" }}
        />
        <div
          className="absolute top-72 left-1/5 w-1 h-1 bg-pantheon-secondary-500 rounded-full animate-star-twinkle animate-scale-pulse"
          style={{ animationDelay: "1.8s" }}
        />
        <div
          className="absolute bottom-48 left-1/4 w-1 h-1 bg-pantheon-primary-300 rounded-full animate-star-twinkle animate-drift-right"
          style={{ animationDelay: "2.3s" }}
        />

        {/* Small twinkling stars with various animations */}
        <div
          className="absolute top-32 left-1/3 w-0.5 h-0.5 bg-white rounded-full animate-star-twinkle animate-diagonal-float"
          style={{ animationDelay: "0.4s" }}
        />
        <div
          className="absolute top-56 right-1/5 w-0.5 h-0.5 bg-pantheon-primary-300 rounded-full animate-star-twinkle animate-drift-left"
          style={{ animationDelay: "0.9s" }}
        />
        <div
          className="absolute bottom-32 left-3/4 w-0.5 h-0.5 bg-pantheon-secondary-300 rounded-full animate-star-twinkle animate-drift-up"
          style={{ animationDelay: "1.4s" }}
        />
        <div
          className="absolute top-80 right-2/5 w-0.5 h-0.5 bg-white rounded-full animate-star-twinkle animate-scale-pulse"
          style={{ animationDelay: "1.9s" }}
        />
        <div
          className="absolute bottom-72 left-1/6 w-0.5 h-0.5 bg-pantheon-primary-500 rounded-full animate-star-twinkle animate-drift-right"
          style={{ animationDelay: "2.4s" }}
        />

        {/* Additional distant stars with drift */}
        <div
          className="absolute top-1/4 left-1/6 w-0.5 h-0.5 bg-white/60 rounded-full animate-star-twinkle animate-drift-left"
          style={{ animationDelay: "0.1s" }}
        />
        <div
          className="absolute top-1/3 right-1/6 w-0.5 h-0.5 bg-pantheon-primary-300/60 rounded-full animate-star-twinkle animate-drift-up"
          style={{ animationDelay: "0.7s" }}
        />
        <div
          className="absolute bottom-1/4 left-1/2 w-0.5 h-0.5 bg-pantheon-secondary-300/60 rounded-full animate-star-twinkle animate-diagonal-float"
          style={{ animationDelay: "1.3s" }}
        />
        <div
          className="absolute bottom-1/3 right-1/4 w-0.5 h-0.5 bg-white/60 rounded-full animate-star-twinkle animate-scale-pulse"
          style={{ animationDelay: "1.9s" }}
        />
        <div
          className="absolute top-2/3 left-2/3 w-0.5 h-0.5 bg-pantheon-primary-500/60 rounded-full animate-star-twinkle animate-drift-right"
          style={{ animationDelay: "2.5s" }}
        />

        {/* Rotating star clusters */}
        <div
          className="absolute top-1/5 right-1/5 w-16 h-16 animate-slow-rotate"
          style={{ animationDelay: "5s" }}
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-pantheon-primary-300 rounded-full animate-star-twinkle" />
          <div
            className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0.5 h-0.5 bg-pantheon-secondary-300 rounded-full animate-star-twinkle"
            style={{ animationDelay: "0.5s" }}
          />
          <div
            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-1 bg-pantheon-primary-500 rounded-full animate-star-twinkle"
            style={{ animationDelay: "1s" }}
          />
          <div
            className="absolute right-0 top-1/2 -translate-y-1/2 w-0.5 h-0.5 bg-pantheon-accent-blue rounded-full animate-star-twinkle"
            style={{ animationDelay: "1.5s" }}
          />
        </div>

        <div
          className="absolute bottom-1/5 left-1/5 w-20 h-20 animate-slow-rotate"
          style={{ animationDelay: "7s", animationDirection: "reverse" }}
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-pantheon-secondary-500 rounded-full animate-star-twinkle" />
          <div
            className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-pantheon-primary-300 rounded-full animate-star-twinkle"
            style={{ animationDelay: "0.7s" }}
          />
          <div
            className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-0.5 bg-pantheon-primary-500 rounded-full animate-star-twinkle"
            style={{ animationDelay: "1.2s" }}
          />
          <div
            className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-1 bg-pantheon-secondary-300 rounded-full animate-star-twinkle"
            style={{ animationDelay: "1.7s" }}
          />
        </div>

        {/* Floating energy particles */}
        <div className="absolute top-3/4 left-1/4 w-2 h-2 bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 rounded-full blur-sm animate-diagonal-float animate-scale-pulse" />
        <div
          className="absolute top-1/6 right-1/3 w-1.5 h-1.5 bg-gradient-to-br from-pantheon-secondary-500 to-pantheon-primary-500 rounded-full blur-sm animate-drift-up animate-pulse-glow"
          style={{ animationDelay: "2s" }}
        />
        <div
          className="absolute bottom-1/6 left-2/3 w-2 h-2 bg-gradient-to-br from-pantheon-accent-blue to-pantheon-primary-500 rounded-full blur-sm animate-drift-left animate-scale-pulse"
          style={{ animationDelay: "3s" }}
        />
      </div>

      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(to right, hsl(var(--pantheon-primary-500)) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--pantheon-primary-500)) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
        }}
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 py-12">
        {/* Navbar */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-pantheon-cosmic-bg/80 backdrop-blur-md border-b border-pantheon-border">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <button
              onClick={() => {
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
              className="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity"
              aria-label="Scroll to top"
            >
              <img
                src="/logo.jpeg"
                alt="Crypto Pantheon Logo"
                className="w-8 h-8 rounded object-cover"
              />
              <span className="text-xl font-mythic font-bold text-pantheon-text-primary">
                Pantheon Elite
              </span>
            </button>
            <div className="hidden md:flex items-center space-x-8">
              <a
                href="#home"
                onClick={(e) => handleNavClick(e, "home")}
                className="text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors cursor-pointer"
              >
                Home
              </a>
              <a
                href="#leaderboard"
                onClick={(e) => handleNavClick(e, "leaderboard")}
                className="text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors cursor-pointer"
              >
                Leaderboard
              </a>
              <a
                href="#vision"
                onClick={(e) => handleNavClick(e, "vision")}
                className="text-pantheon-text-secondary hover:text-pantheon-primary-500 transition-colors cursor-pointer"
              >
                Vision
              </a>
              <Button
                className="bg-pantheon-primary-500 hover:bg-pantheon-primary-600 text-white font-semibold shadow-[0_0_20px_hsl(var(--pantheon-primary-500)/0.4)] transition-all"
                onClick={() => navigate("/signup")}
              >
                Join Beta
              </Button>
            </div>
          </div>
        </nav>

        {/* Hero content */}
        <div className="mt-32 text-center space-y-8">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-mythic font-bold text-pantheon-text-primary leading-tight drop-shadow-[0_0_10px_hsl(var(--pantheon-primary-500)/0.5)]">
            Forge AI Councils That{" "}
            <span
              className="inline-block px-3 py-1 rounded-xl font-extrabold text-[--primary-500] text-shadow-glow text-transparent bg-clip-text bg-gradient-to-r from-pantheon-primary-500 via-pantheon-secondary-500 to-pantheon-primary-500 shadow-[0_0_16px_hsl(var(--pantheon-primary-300)/0.8)] animate-pulse-glow"
              style={{
                textShadow:
                  "0 0 16px hsl(var(--pantheon-primary-300)), 0 0 32px hsl(var(--pantheon-primary-500))",
                WebkitTextStroke: "1px hsl(var(--pantheon-primary-300))",
                filter:
                  "drop-shadow(0 0 6px hsl(var(--pantheon-primary-500)/0.7))",
              }}
            >
              Debate to Dominate
            </span>{" "}
            Crypto
          </h1>

          <p className="text-lg md:text-xl text-pantheon-text-secondary max-w-3xl mx-auto">
            Legendary AI agents collaborate on Aster DEX—see real PnL from
            debates powering hedge-level strategies. Powered by Grok.
          </p>

          {/* Chart showcase */}
          <div className="max-w-4xl mx-auto mt-12">
            <PnLChart
              labels={chartLabels}
              datasets={chartDatasets}
              title="Debate Council vs Market Average"
            />
            <p className="mt-4 text-sm text-pantheon-secondary-500 font-semibold">
              Debate Impact: +20% Alpha
            </p>
          </div>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
            <Button
              className="w-full sm:w-auto bg-pantheon-primary-500 hover:bg-pantheon-primary-600 text-white font-bold text-sm sm:text-base md:text-lg px-4 py-3 sm:px-6 sm:py-4 md:px-8 md:py-6 shadow-[0_0_30px_hsl(var(--pantheon-primary-500)/0.5)] hover:shadow-[0_0_40px_hsl(var(--pantheon-primary-500)/0.7)] transition-all animate-pulse-glow"
              onClick={() => navigate("/signup")}
            >
              Enter the Arena – Sign Up
            </Button>
          </div>

          {/* FOMO counter */}
          <div className="mt-6 text-pantheon-text-secondary">
            <span className="font-mono text-pantheon-primary-500 font-bold">
              {userCount.toLocaleString()}
            </span>{" "}
            Architects Joined | Beta in{" "}
            <span className="text-pantheon-accent-orange font-bold">
              14 Days
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
