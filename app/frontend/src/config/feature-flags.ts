/**
 * Feature Flags Configuration
 * Controls various features in the application
 */

export interface FeatureFlags {
  /** Enable/disable signup functionality */
  enableSignup: boolean;
  /** Enable/disable wallet connection */
  enableWalletConnection: boolean;
  /** Enable/disable trading features */
  enableTrading: boolean;
  /** Enable/disable backtesting features */
  enableBacktesting: boolean;
}

/**
 * Default feature flags configuration
 * Can be overridden by environment variables
 */
export const defaultFeatureFlags: FeatureFlags = {
  enableSignup: (process.env.NEXT_PUBLIC_ENABLE_SIGNUP || '').toLowerCase() === 'true' || false,
  enableWalletConnection: (process.env.NEXT_PUBLIC_ENABLE_WALLET_CONNECTION || '').toLowerCase() === 'true' || true,
  enableTrading: (process.env.NEXT_PUBLIC_ENABLE_TRADING || '').toLowerCase() === 'true' || false,
  enableBacktesting: (process.env.NEXT_PUBLIC_ENABLE_BACKTESTING || '').toLowerCase() === 'true' || false,
};

/**
 * Get current feature flags
 * In a real application, this could fetch from an API or database
 */
export const getFeatureFlags = (): FeatureFlags => {
  return defaultFeatureFlags;
};

/**
 * Check if a specific feature is enabled
 */
export const isFeatureEnabled = (feature: keyof FeatureFlags): boolean => {
  const flags = getFeatureFlags();
  return flags[feature];
};

/**
 * Feature flag hook for React components
 */
export const useFeatureFlag = (feature: keyof FeatureFlags): boolean => {
  return isFeatureEnabled(feature);
};
