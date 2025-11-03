import {
  Hero,
  CouncilRankingSection,
  GlobalActivityFeed,
  HowItWorks,
  Footer,
  CosmicBackground
} from '../landing';

export function LandingPage() {
  return (
    <div className="relative min-h-screen">
      {/* Fixed cosmic background visible throughout the page */}
      <CosmicBackground />

      {/* Content sections - relative positioning to appear above background */}
      <div className="relative z-10">
        <Hero />
        <CouncilRankingSection />
        <GlobalActivityFeed />
        <HowItWorks />
        <Footer />
      </div>
    </div>
  );
}
