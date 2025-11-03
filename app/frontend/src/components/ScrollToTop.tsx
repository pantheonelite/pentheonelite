import { useEffect } from "react";
import { useLocation } from "react-router-dom";

export function ScrollToTop() {
  const location = useLocation();

  useEffect(() => {
    // Scroll to top on route change (pathname change)
    if (!location.hash) {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      return;
    }

    // Handle hash fragments for smooth scrolling to sections
    const elementId = location.hash.substring(1); // Remove the # symbol
    const element = document.getElementById(elementId);

    if (element) {
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    } else {
      // If element not found, scroll to top
      window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    }
  }, [location.pathname, location.hash]);

  return null;
}
