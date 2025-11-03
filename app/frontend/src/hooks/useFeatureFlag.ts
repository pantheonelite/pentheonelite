import { useEffect, useState } from 'react';
import { getFeatureFlags, type FeatureFlags } from '../config/feature-flags';

/**
 * React hook for accessing feature flags
 */
export const useFeatureFlag = (feature: keyof FeatureFlags): boolean => {
  const [flags, setFlags] = useState<FeatureFlags>(getFeatureFlags());

  useEffect(() => {
    // In a real application, you might want to fetch flags from an API
    // For now, we'll use the static configuration
    setFlags(getFeatureFlags());
  }, []);

  return flags[feature];
};

/**
 * Hook to get all feature flags
 */
export const useFeatureFlags = (): FeatureFlags => {
  const [flags, setFlags] = useState<FeatureFlags>(getFeatureFlags());

  useEffect(() => {
    setFlags(getFeatureFlags());
  }, []);

  return flags;
};
