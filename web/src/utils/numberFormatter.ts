/**
 * Number formatting utilities for charts and displays
 */

/**
 * Format large numbers to readable format (1B, 500M, 100K, etc)
 * Used for chart axes and displays with large values
 */
export const formatLargeNumber = (value: number): string => {
  if (value >= 1_000_000_000) {
    const billions = value / 1_000_000_000;
    return `${billions.toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    const millions = value / 1_000_000;
    return `${millions.toFixed(0)}M`;
  }
  if (value >= 1_000) {
    const thousands = value / 1_000;
    return `${thousands.toFixed(0)}K`;
  }
  return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
};

/**
 * Format number as Vietnamese currency (VND)
 * Displays full value with locale formatting
 */
export const formatCurrency = (value: number): string => {
  return value.toLocaleString('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  });
};

/**
 * Format number with locale-specific thousands separator
 */
export const formatNumber = (value: number): string => {
  return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
};
