/**
 * CosmicBackground Component
 *
 * Optimized full-page fixed background with animated cosmic elements.
 * Performance optimized: reduced animated elements, GPU acceleration, reduced motion support.
 */

import { useEffect, useState } from "react";

export function CosmicBackground() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handleChange);

    // Pause animations when tab is not visible (Page Visibility API)
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  // If reduced motion or tab not visible, disable animations
  const shouldAnimate = !prefersReducedMotion && isVisible;

  return (
    <div
      className="fixed inset-0 -z-10 overflow-hidden pointer-events-none"
      style={{
        willChange: "transform",
        transform: "translateZ(0)", // Force GPU acceleration
      }}
    >
      {/* Base gradient background - static, no animation */}
      <div className="absolute inset-0 bg-gradient-to-b from-pantheon-cosmic-bg via-pantheon-cosmic-surface to-pantheon-cosmic-bg" />

      {/* Optimized animated gradient mesh overlay - reduced from 3 to 2 */}
      <div className="absolute inset-0 overflow-hidden opacity-30">
        <div
          className={`absolute top-0 left-0 w-96 h-96 bg-pantheon-primary-500/20 rounded-full blur-3xl ${
            shouldAnimate ? "animate-pulse-glow animate-drift-right" : ""
          }`}
          style={{ willChange: "transform, opacity" }}
        />
        <div
          className={`absolute bottom-0 right-0 w-96 h-96 bg-pantheon-secondary-500/20 rounded-full blur-3xl ${
            shouldAnimate ? "animate-pulse-glow animate-drift-left" : ""
          }`}
          style={{ animationDelay: "1.5s", willChange: "transform, opacity" }}
        />
      </div>

      {/* Reduced glowing orbs - from 5 to 3, removed dual animations */}
      <div className="absolute inset-0 overflow-hidden">
        <div
          className={`absolute top-20 right-1/4 w-72 h-72 bg-gradient-to-br from-pantheon-primary-500/30 to-pantheon-secondary-500/20 rounded-full blur-3xl ${
            shouldAnimate ? "animate-cosmic-float" : ""
          }`}
          style={{ willChange: "transform" }}
        />
        <div
          className={`absolute bottom-32 left-1/4 w-96 h-96 bg-gradient-to-br from-pantheon-secondary-500/25 to-pantheon-primary-500/15 rounded-full blur-3xl ${
            shouldAnimate ? "animate-cosmic-float" : ""
          }`}
          style={{ animationDelay: "2s", willChange: "transform" }}
        />
        <div
          className={`absolute top-1/3 right-1/3 w-64 h-64 bg-gradient-to-br from-pantheon-accent-blue/20 to-pantheon-primary-500/10 rounded-full blur-3xl ${
            shouldAnimate ? "animate-slow-rotate" : ""
          }`}
          style={{ animationDelay: "4s", willChange: "transform" }}
        />
      </div>

      {/* Optimized starfield - reduced from ~30+ stars to ~12 strategically placed */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ willChange: "transform", transform: "translateZ(0)" }}
      >
        {/* Key bright stars - reduced from 6 to 4 */}
        <div
          className={`absolute top-10 left-20 w-2 h-2 bg-pantheon-primary-300 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{
            boxShadow: "0 0 6px hsl(var(--pantheon-primary-300))",
            willChange: "opacity",
          }}
        />
        <div
          className={`absolute top-40 right-1/3 w-2 h-2 bg-pantheon-primary-500 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{
            animationDelay: "0.6s",
            boxShadow: "0 0 8px hsl(var(--pantheon-primary-500))",
            willChange: "opacity",
          }}
        />
        <div
          className={`absolute bottom-40 left-60 w-1.5 h-1.5 bg-pantheon-primary-500 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "1s", willChange: "opacity" }}
        />
        <div
          className={`absolute bottom-20 right-80 w-2 h-2 bg-pantheon-primary-300 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{
            animationDelay: "2s",
            boxShadow: "0 0 6px hsl(var(--pantheon-primary-300))",
            willChange: "opacity",
          }}
        />

        {/* Medium stars with subtle drift - reduced from 5 to 3 */}
        <div
          className={`absolute top-48 left-1/2 w-1 h-1 bg-pantheon-primary-500 rounded-full ${
            shouldAnimate ? "animate-star-twinkle animate-drift-left" : ""
          }`}
          style={{ animationDelay: "0.8s", willChange: "opacity, transform" }}
        />
        <div
          className={`absolute top-72 left-1/5 w-1 h-1 bg-pantheon-secondary-500 rounded-full ${
            shouldAnimate ? "animate-star-twinkle animate-scale-pulse" : ""
          }`}
          style={{ animationDelay: "1.8s", willChange: "opacity, transform" }}
        />
        <div
          className={`absolute bottom-48 left-1/4 w-1 h-1 bg-pantheon-primary-300 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "2.3s", willChange: "opacity" }}
        />

        {/* Scattered small stars - reduced from 10+ to 5 */}
        <div
          className={`absolute top-32 left-1/3 w-0.5 h-0.5 bg-white rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "0.4s", willChange: "opacity" }}
        />
        <div
          className={`absolute top-56 right-1/5 w-0.5 h-0.5 bg-pantheon-primary-300 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "0.9s", willChange: "opacity" }}
        />
        <div
          className={`absolute bottom-32 left-3/4 w-0.5 h-0.5 bg-pantheon-secondary-300 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "1.4s", willChange: "opacity" }}
        />
        <div
          className={`absolute top-[400px] left-[25%] w-0.5 h-0.5 bg-pantheon-secondary-300/50 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "1.1s", willChange: "opacity" }}
        />
        <div
          className={`absolute top-[800px] left-[40%] w-1 h-1 bg-pantheon-primary-500/60 rounded-full ${
            shouldAnimate ? "animate-star-twinkle" : ""
          }`}
          style={{ animationDelay: "2.1s", willChange: "opacity" }}
        />

        {/* Single rotating star cluster instead of two */}
        <div
          className={`absolute top-1/5 right-1/5 w-16 h-16 ${
            shouldAnimate ? "animate-slow-rotate" : ""
          }`}
          style={{ animationDelay: "5s", willChange: "transform" }}
        >
          <div
            className={`absolute top-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-pantheon-primary-300 rounded-full ${
              shouldAnimate ? "animate-star-twinkle" : ""
            }`}
          />
          <div
            className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-0.5 h-0.5 bg-pantheon-secondary-300 rounded-full ${
              shouldAnimate ? "animate-star-twinkle" : ""
            }`}
            style={{ animationDelay: "0.5s" }}
          />
        </div>

        {/* Single floating energy particle instead of three */}
        <div
          className={`absolute top-3/4 left-1/4 w-2 h-2 bg-gradient-to-br from-pantheon-primary-500 to-pantheon-secondary-500 rounded-full blur-sm ${
            shouldAnimate ? "animate-scale-pulse" : ""
          }`}
          style={{ willChange: "transform" }}
        />
      </div>

      {/* Subtle grid pattern overlay - static, no animation needed */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(to right, hsl(var(--pantheon-primary-500)) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--pantheon-primary-500)) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
          willChange: "auto", // Static element
        }}
      />
    </div>
  );
}
