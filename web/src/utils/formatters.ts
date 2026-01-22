/**
 * Currency/number formatting utilities for charts
 * Created: 2026-01-20
 */

/**
 * Format large numbers in compact form: 12.5B, 500M, 125K
 * Uses en-US compact notation for brevity on axes.
 */
export const formatCurrencyCompact = (value: number): string => {
  try {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value);
  } catch {
    // Fallback: manual formatting
    if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
    if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return `${Math.round(value)}`;
  }
};

/**
 * Format full currency with thousands separators for tooltips.
 * Default locale: vi-VN (no currency symbol appended).
 */
export const formatCurrencyFull = (value: number): string => {
  try {
    return new Intl.NumberFormat('vi-VN', {
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    // Simple fallback
    return `${Math.round(value)}`;
  }
};

/**
 * Format integer counts (e.g., frequency) with no decimals.
 */
export const formatInteger = (value: number): string => {
  try {
    return new Intl.NumberFormat('vi-VN', {
      maximumFractionDigits: 0,
    }).format(Math.round(value));
  } catch {
    return `${Math.round(value)}`;
  }
};
